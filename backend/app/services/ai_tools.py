from datetime import datetime, timezone, timedelta
from sqlalchemy import func
from sqlalchemy.orm import Session
from ..models import Product, PurchaseOrder, Supplier, POLineItem, StockHistory


def get_low_stock_products(db: Session, threshold_pct: int = 20):
    products = (
        db.query(Product)
        .filter(Product.is_active == True, Product.stock_qty <= Product.reorder_threshold)
        .all()
    )
    return [
        {
            "id": p.id,
            "name": p.name,
            "sku": p.sku,
            "category": p.category,
            "stock_qty": p.stock_qty,
            "reorder_threshold": p.reorder_threshold,
            "unit_price": p.unit_price,
        }
        for p in products
    ]


def get_product_detail(db: Session, product_id: int = None, product_name: str = None):
    if product_id is not None:
        product = db.query(Product).filter(Product.id == product_id, Product.is_active == True).first()
    elif product_name:
        product = db.query(Product).filter(Product.name.ilike(f"%{product_name}%"), Product.is_active == True).first()
    else:
        return {"error": "Must provide product_id or product_name"}

    if not product:
        return {"error": "Product not found"}

    return {
        "id": product.id,
        "sku": product.sku,
        "name": product.name,
        "category": product.category,
        "stock_qty": product.stock_qty,
        "unit_price": product.unit_price,
        "reorder_threshold": product.reorder_threshold,
        "expiry_date": product.expiry_date.isoformat() if product.expiry_date else None,
        "is_active": product.is_active,
        "created_at": product.created_at.isoformat() if product.created_at else None,
    }


def get_po_history(db: Session, supplier_name: str = None, days: int = 30):
    since = datetime.now(timezone.utc) - timedelta(days=days)
    q = (
        db.query(PurchaseOrder, Supplier)
        .join(Supplier, PurchaseOrder.supplier_id == Supplier.id)
        .filter(PurchaseOrder.created_at >= since)
    )
    if supplier_name:
        q = q.filter(Supplier.name.ilike(f"%{supplier_name}%"))

    rows = q.all()
    po_ids = [po.id for po, _ in rows]
    counts = dict(
        db.query(POLineItem.po_id, func.count(POLineItem.id))
        .filter(POLineItem.po_id.in_(po_ids))
        .group_by(POLineItem.po_id)
        .all()
    ) if po_ids else {}

    return [
        {
            "id": po.id,
            "supplier_name": supplier.name,
            "status": po.status,
            "total_value": po.total_value,
            "created_at": po.created_at.isoformat() if po.created_at else None,
            "line_items_count": counts.get(po.id, 0),
        }
        for po, supplier in rows
    ]


def get_expiring_products(db: Session, days_ahead: int = 14):
    now = datetime.now(timezone.utc)
    cutoff = now + timedelta(days=days_ahead)
    products = (
        db.query(Product)
        .filter(
            Product.is_active == True,
            Product.expiry_date.isnot(None),
            Product.expiry_date >= now,
            Product.expiry_date <= cutoff,
        )
        .all()
    )
    return [
        {
            "id": p.id,
            "name": p.name,
            "sku": p.sku,
            "stock_qty": p.stock_qty,
            "expiry_date": p.expiry_date.isoformat() if p.expiry_date else None,
            "days_until_expiry": (p.expiry_date - now).days,
        }
        for p in products
    ]
