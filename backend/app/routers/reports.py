from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from datetime import datetime, timezone, timedelta

from ..database import get_db
from ..models import Product, Supplier, StockHistory, PurchaseOrder, POLineItem, Invoice
from ..auth.dependencies import get_current_user

router = APIRouter(prefix="/reports", tags=["reports"], dependencies=[Depends(get_current_user)])


@router.get("/stock-by-category")
def stock_by_category(db: Session = Depends(get_db)):
    rows = (
        db.query(Product.category, func.sum(Product.stock_qty).label("total_stock"))
        .filter(Product.is_active == True)
        .group_by(Product.category)
        .order_by(func.sum(Product.stock_qty).desc())
        .all()
    )
    return [{"category": r.category, "total_stock": int(r.total_stock or 0)} for r in rows]


@router.get("/low-stock")
def low_stock_products(db: Session = Depends(get_db)):
    products = (
        db.query(Product)
        .filter(Product.is_active == True, Product.stock_qty <= Product.reorder_threshold)
        .order_by(Product.stock_qty.asc())
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
            "gap": p.reorder_threshold - p.stock_qty,
        }
        for p in products
    ]


@router.get("/expiring-soon")
def expiring_soon(db: Session = Depends(get_db)):
    now = datetime.now(timezone.utc)
    cutoff = now + timedelta(days=30)
    products = (
        db.query(Product)
        .filter(
            Product.is_active == True,
            Product.expiry_date != None,
            Product.expiry_date <= cutoff,
        )
        .order_by(Product.expiry_date.asc())
        .all()
    )
    return [
        {
            "id": p.id,
            "name": p.name,
            "sku": p.sku,
            "stock_qty": p.stock_qty,
            "expiry_date": p.expiry_date.isoformat() if p.expiry_date else None,
            "days_left": (p.expiry_date.replace(tzinfo=timezone.utc) - now).days if p.expiry_date else None,
        }
        for p in products
    ]


@router.get("/stock-history")
def stock_history(db: Session = Depends(get_db)):
    rows = (
        db.query(
            func.date(StockHistory.recorded_at).label("date"),
            func.sum(
                case((StockHistory.change_type == "restock", StockHistory.change_qty), else_=0)
            ).label("restocked"),
            func.sum(
                case((StockHistory.change_type == "sale", func.abs(StockHistory.change_qty)), else_=0)
            ).label("sold"),
        )
        .group_by(func.date(StockHistory.recorded_at))
        .order_by(func.date(StockHistory.recorded_at).asc())
        .limit(30)
        .all()
    )
    return [
        {"date": str(r.date), "restocked": int(r.restocked or 0), "sold": int(r.sold or 0)}
        for r in rows
    ]


@router.get("/po-summary")
def po_summary(db: Session = Depends(get_db)):
    rows = (
        db.query(PurchaseOrder.status, func.count(PurchaseOrder.id).label("count"))
        .group_by(PurchaseOrder.status)
        .all()
    )
    return [{"status": r.status, "count": r.count} for r in rows]
