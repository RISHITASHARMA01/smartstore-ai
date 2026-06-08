from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timezone, timedelta

from ..database import get_db
from ..models import Product, Supplier, StockHistory, PurchaseOrder
from ..auth.bypass import get_user_dependency
get_current_user = get_user_dependency()

router = APIRouter(prefix="/dashboard", tags=["dashboard"], dependencies=[Depends(get_current_user)])


@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    now = datetime.now(timezone.utc)

    total_products = db.query(func.count(Product.id)).filter(Product.is_active == True).scalar()

    low_stock = db.query(func.count(Product.id)).filter(
        Product.is_active == True,
        Product.stock_qty <= Product.reorder_threshold,
    ).scalar()

    expired = db.query(func.count(Product.id)).filter(
        Product.is_active == True,
        Product.expiry_date != None,
        Product.expiry_date <= now,
    ).scalar()

    total_suppliers = db.query(func.count(Supplier.id)).filter(Supplier.is_active == True).scalar()

    # recent stock movements (last 30 days)
    thirty_days_ago = now - timedelta(days=30)
    recent_restocks = (
        db.query(func.coalesce(func.sum(StockHistory.change_qty), 0))
        .filter(StockHistory.change_type == "restock", StockHistory.recorded_at >= thirty_days_ago)
        .scalar()
    )

    return {
        "total_products": total_products,
        "low_stock_alerts": low_stock,
        "expired_items": expired,
        "total_suppliers": total_suppliers,
        "total_restocked": int(recent_restocks),
    }
