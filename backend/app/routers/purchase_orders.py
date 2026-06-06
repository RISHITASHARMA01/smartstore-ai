from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from typing import Optional

from ..database import get_db
from ..models import PurchaseOrder, POLineItem, Product, Supplier, StockHistory
from ..schemas.purchase_orders import POCreate, POUpdate, POOut, VALID_STATUSES

router = APIRouter(prefix="/purchase-orders", tags=["purchase-orders"])


def _load(po_id: int, db: Session) -> PurchaseOrder:
    po = (
        db.query(PurchaseOrder)
        .options(
            joinedload(PurchaseOrder.supplier),
            joinedload(PurchaseOrder.line_items).joinedload(POLineItem.product),
        )
        .filter(PurchaseOrder.id == po_id)
        .first()
    )
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    return po


@router.get("/", response_model=list[POOut])
def list_purchase_orders(
    status: Optional[str] = Query(None),
    supplier_id: Optional[int] = Query(None),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    q = db.query(PurchaseOrder).options(
        joinedload(PurchaseOrder.supplier),
        joinedload(PurchaseOrder.line_items).joinedload(POLineItem.product),
    )
    if status:
        q = q.filter(PurchaseOrder.status == status)
    if supplier_id:
        q = q.filter(PurchaseOrder.supplier_id == supplier_id)
    return q.order_by(PurchaseOrder.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/{po_id}", response_model=POOut)
def get_purchase_order(po_id: int, db: Session = Depends(get_db)):
    return _load(po_id, db)


@router.post("/", response_model=POOut, status_code=201)
def create_purchase_order(payload: POCreate, db: Session = Depends(get_db)):
    if not db.query(Supplier).filter(Supplier.id == payload.supplier_id, Supplier.is_active == True).first():
        raise HTTPException(status_code=404, detail="Supplier not found")

    po = PurchaseOrder(supplier_id=payload.supplier_id, notes=payload.notes)
    db.add(po)
    db.flush()

    total = 0.0
    for item in payload.line_items:
        if not db.query(Product).filter(Product.id == item.product_id, Product.is_active == True).first():
            raise HTTPException(status_code=404, detail=f"Product {item.product_id} not found")
        db.add(POLineItem(po_id=po.id, **item.model_dump()))
        total += item.quantity * item.unit_price

    po.total_value = total
    db.commit()
    return _load(po.id, db)


@router.put("/{po_id}", response_model=POOut)
def update_purchase_order(po_id: int, payload: POUpdate, db: Session = Depends(get_db)):
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    if po.status != "Draft":
        raise HTTPException(status_code=400, detail="Only Draft orders can be edited")

    if payload.notes is not None:
        po.notes = payload.notes

    if payload.line_items is not None:
        db.query(POLineItem).filter(POLineItem.po_id == po_id).delete()
        total = 0.0
        for item in payload.line_items:
            if not db.query(Product).filter(Product.id == item.product_id, Product.is_active == True).first():
                raise HTTPException(status_code=404, detail=f"Product {item.product_id} not found")
            db.add(POLineItem(po_id=po.id, **item.model_dump()))
            total += item.quantity * item.unit_price
        po.total_value = total

    db.commit()
    return _load(po.id, db)


@router.patch("/{po_id}/status", response_model=POOut)
def advance_status(po_id: int, db: Session = Depends(get_db)):
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")

    idx = VALID_STATUSES.index(po.status)
    if idx == len(VALID_STATUSES) - 1:
        raise HTTPException(status_code=400, detail="Purchase order is already Received")

    po.status = VALID_STATUSES[idx + 1]

    # On receipt: restock each product and record history
    if po.status == "Received":
        for li in db.query(POLineItem).filter(POLineItem.po_id == po_id).all():
            product = db.query(Product).filter(Product.id == li.product_id).first()
            if product:
                product.stock_qty += li.quantity
                db.add(StockHistory(
                    product_id=li.product_id,
                    change_qty=li.quantity,
                    change_type="restock",
                ))

    db.commit()
    return _load(po.id, db)


@router.delete("/{po_id}", status_code=204)
def delete_purchase_order(po_id: int, db: Session = Depends(get_db)):
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    if po.status != "Draft":
        raise HTTPException(status_code=400, detail="Only Draft orders can be deleted")
    db.query(POLineItem).filter(POLineItem.po_id == po_id).delete()
    db.delete(po)
    db.commit()
