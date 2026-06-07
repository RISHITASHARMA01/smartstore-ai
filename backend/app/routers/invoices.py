import os
import re
import json
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel, Field
from typing import List, Optional
from sqlalchemy.orm import Session
from google import genai
from google.genai import types

from ..database import get_db
from ..auth.dependencies import get_current_user
from ..models import Invoice, Product, StockHistory

logger = logging.getLogger(__name__)

router = APIRouter(dependencies=[Depends(get_current_user)])

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

PARSE_PROMPT = (
    "Extract the following from this invoice image and return ONLY valid JSON with no markdown:\n"
    "{\n"
    '  "supplier_name": "string",\n'
    '  "invoice_date": "YYYY-MM-DD",\n'
    '  "line_items": [{"name": "string", "qty": number, "unit_price": number, "total": number}],\n'
    '  "grand_total": number\n'
    "}\n"
    "If any field cannot be found, use null."
)

ALLOWED_MIME = {
    "image/jpeg": "image/jpeg",
    "image/png": "image/png",
    "image/jpg": "image/jpeg",
    "application/pdf": "application/pdf",
}


def _gemini_client():
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        raise HTTPException(status_code=500, detail="AI service not configured")
    return genai.Client(api_key=key)


def _parse_gemini_json(text: str) -> dict:
    text = re.sub(r"```json\s*", "", text)
    text = re.sub(r"```\s*", "", text)
    text = text.strip()
    return json.loads(text)


# ── POST /invoices/parse ──────────────────────────────────────────────────────
@router.post("/parse")
async def parse_invoice(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    # Validate MIME type from Content-Type only (don't trust filename)
    content_type = file.content_type or ""
    mime = ALLOWED_MIME.get(content_type)
    if not mime:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Upload a JPG, PNG, or PDF.",
        )

    file_bytes = await file.read()

    # Enforce file size limit
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)} MB.",
        )

    client = _gemini_client()

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                types.Part.from_bytes(data=file_bytes, mime_type=mime),
                PARSE_PROMPT,
            ],
        )
    except Exception as e:
        logger.error("Gemini Vision error: %s", e)
        raise HTTPException(status_code=500, detail="AI service error. Please try again.")

    try:
        data = _parse_gemini_json(response.text)
    except Exception as e:
        logger.error("Failed to parse Gemini JSON response: %s", e)
        raise HTTPException(status_code=422, detail="Could not extract invoice data. Please try a clearer image.")

    invoice = Invoice(
        supplier_name=data.get("supplier_name"),
        invoice_date=data.get("invoice_date"),
        line_items=data.get("line_items", []),
        grand_total=data.get("grand_total"),
        confirmed=False,
    )
    db.add(invoice)
    db.commit()
    db.refresh(invoice)

    return {
        "id": invoice.id,
        "supplier_name": invoice.supplier_name,
        "invoice_date": invoice.invoice_date,
        "line_items": invoice.line_items,
        "grand_total": invoice.grand_total,
        "confirmed": invoice.confirmed,
    }


# ── POST /invoices/confirm/{invoice_id} ───────────────────────────────────────
class ConfirmLineItem(BaseModel):
    product_name: str = Field(min_length=1, max_length=255)
    qty: int = Field(gt=0, le=100000)
    unit_price: float = Field(ge=0)


class ConfirmRequest(BaseModel):
    line_items: List[ConfirmLineItem] = Field(min_length=1, max_length=500)


@router.post("/confirm/{invoice_id}")
def confirm_invoice(
    invoice_id: int,
    payload: ConfirmRequest,
    db: Session = Depends(get_db),
):
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    if invoice.confirmed:
        raise HTTPException(status_code=400, detail="Invoice already confirmed")

    updated_products = []
    not_found = []

    for item in payload.line_items:
        # Escape wildcard chars to prevent ReDoS via LIKE
        safe_name = item.product_name.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        product = (
            db.query(Product)
            .filter(
                Product.name.ilike(f"%{safe_name}%"),
                Product.is_active == True,
            )
            .first()
        )
        if product:
            product.stock_qty += item.qty
            history = StockHistory(
                product_id=product.id,
                change_qty=item.qty,
                change_type="restock",
                recorded_at=datetime.now(timezone.utc),
            )
            db.add(history)
            updated_products.append(
                {"product_id": product.id, "name": product.name, "added_qty": item.qty}
            )
        else:
            not_found.append(item.product_name)

    invoice.confirmed = True
    db.commit()

    return {
        "confirmed": True,
        "updated_products": updated_products,
        "not_found": not_found,
    }


# ── GET /invoices ─────────────────────────────────────────────────────────────
@router.get("/")
def list_invoices(db: Session = Depends(get_db)):
    invoices = db.query(Invoice).order_by(Invoice.created_at.desc()).all()
    return [
        {
            "id": inv.id,
            "supplier_name": inv.supplier_name,
            "invoice_date": inv.invoice_date,
            "grand_total": inv.grand_total,
            "confirmed": inv.confirmed,
            "created_at": inv.created_at,
            "line_items_count": len(inv.line_items) if inv.line_items else 0,
        }
        for inv in invoices
    ]
