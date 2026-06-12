from datetime import datetime, timezone, timedelta
from sqlalchemy import func
from sqlalchemy.orm import Session
from ..models import Product, StockHistory


def get_recommendation_data(db: Session, product_id: int = None):
    """
    Gather product inventory data for Gemini recommendation analysis.
    If product_id is given, scopes to that product's category.
    """
    now = datetime.now(timezone.utc)
    thirty_days_ago = now - timedelta(days=30)

    q = db.query(Product).filter(Product.is_active == True)
    focus_category = None

    if product_id:
        target = db.query(Product).filter(
            Product.id == product_id, Product.is_active == True
        ).first()
        if target:
            focus_category = target.category
            q = q.filter(Product.category == focus_category)

    products = q.limit(30).all()
    if not products:
        return {"products": [], "focus_product_id": product_id, "focus_category": focus_category}

    product_ids = [p.id for p in products]
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

    result = []
    for p in products:
        sales_30d = int(sales_map.get(p.id, 0))
        daily_vel = sales_30d / 30
        days_of_stock = round(p.stock_qty / daily_vel, 1) if daily_vel > 0 else None
        days_until_expiry = None
        if p.expiry_date:
            days_until_expiry = (p.expiry_date - now).days

        result.append({
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
            "days_until_expiry": days_until_expiry,
            "is_low_stock": p.stock_qty <= p.reorder_threshold,
        })

    return {
        "products": result,
        "focus_product_id": product_id,
        "focus_category": focus_category,
    }
