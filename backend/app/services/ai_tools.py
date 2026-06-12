from datetime import datetime, timezone, timedelta
from sqlalchemy import func
from sqlalchemy.orm import Session
from ..models import Product, PurchaseOrder, Supplier, POLineItem, StockHistory


def get_restock_recommendations(db: Session, limit: int = 10):
    """Return urgency-sorted restock data for the AI chat to reason about."""
    now = datetime.now(timezone.utc)
    thirty_days_ago = now - timedelta(days=30)

    products = db.query(Product).filter(Product.is_active == True).all()
    product_ids = [p.id for p in products]

    sales_map = {}
    if product_ids:
        sales_map = dict(
            db.query(StockHistory.product_id, func.sum(func.abs(StockHistory.change_qty)))
            .filter(
                StockHistory.change_type == "sale",
                StockHistory.recorded_at >= thirty_days_ago,
                StockHistory.product_id.in_(product_ids),
            )
            .group_by(StockHistory.product_id)
            .all()
        )

    items = []
    for p in products:
        sales_30d = int(sales_map.get(p.id, 0))
        daily_vel = sales_30d / 30
        days_of_stock = round(p.stock_qty / daily_vel, 1) if daily_vel > 0 else None
        items.append({
            "id": p.id,
            "name": p.name,
            "sku": p.sku,
            "category": p.category,
            "stock_qty": p.stock_qty,
            "reorder_threshold": p.reorder_threshold,
            "unit_price": float(p.unit_price) if p.unit_price else 0,
            "sales_last_30_days": sales_30d,
            "daily_sales_velocity": round(daily_vel, 2),
            "estimated_days_of_stock": days_of_stock,
            "is_low_stock": p.stock_qty <= p.reorder_threshold,
        })

    items.sort(key=lambda x: (
        0 if x["is_low_stock"] else 1,
        x["estimated_days_of_stock"] if x["estimated_days_of_stock"] is not None else 9999,
    ))
    return items[:max(1, min(limit, 20))]


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
        safe = product_name.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        product = db.query(Product).filter(Product.name.ilike(f"%{safe}%"), Product.is_active == True).first()
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
        safe = supplier_name.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        q = q.filter(Supplier.name.ilike(f"%{safe}%"))

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
