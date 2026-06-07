import os
import re
import json
import base64
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session
from google import genai
from google.genai import types

from ..database import get_db
from ..auth.dependencies import get_current_user
from ..models import Invoice, Product, StockHistory

router = APIRouter(dependencies=[Depends(get_current_user)])

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
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY not configured")
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
    content_type = file.content_type or ""
    mime = ALLOWED_MIME.get(content_type)
    if not mime:
        # Try by extension
        name = (file.filename or "").lower()
        if name.endswith(".jpg") or name.endswith(".jpeg"):
            mime = "image/jpeg"
        elif name.endswith(".png"):
            mime = "image/png"
        elif name.endswith(".pdf"):
            mime = "application/pdf"
        else:
            raise HTTPException(
                status_code=400,
                detail="Unsupported file type. Upload a JPG, PNG, or PDF.",
            )

    file_bytes = await file.read()
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
        raise HTTPException(status_code=500, detail=f"Gemini Vision error: {e}")

    try:
        data = _parse_gemini_json(response.text)
    except Exception:
        raise HTTPException(
            status_code=422,
            detail=f"Could not parse Gemini response as JSON: {response.text[:300]}",
        )

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
    product_name: str
    qty: int
    unit_price: float


class ConfirmRequest(BaseModel):
    line_items: List[ConfirmLineItem]


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
        product = (
            db.query(Product)
            .filter(
                Product.name.ilike(f"%{item.product_name}%"),
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
    invoices = (
        db.query(Invoice).order_by(Invoice.created_at.desc()).all()
    )
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
