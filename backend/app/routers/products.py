import asyncio
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from ..database import get_db
from ..models import Product, StockHistory, User
from ..schemas.products import ProductCreate, ProductUpdate, ProductOut, StockAdjustIn, StockAdjustOut
from ..auth.dependencies import get_current_user
from ..websocket_manager import manager

router = APIRouter(
    prefix="/products",
    tags=["products"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/", response_model=list[ProductOut])
def list_products(
    search: Optional[str] = Query(None, max_length=100),
    category: Optional[str] = Query(None, max_length=100),
    low_stock: Optional[bool] = Query(None),
    skip: int = Query(0, ge=0, le=10000),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    q = db.query(Product).filter(Product.is_active == True)
    if search:
        q = q.filter(
            Product.name.ilike(f"%{search}%") | Product.sku.ilike(f"%{search}%")
        )
    if category:
        q = q.filter(Product.category == category)
    if low_stock:
        q = q.filter(Product.stock_qty <= Product.reorder_threshold)
    return q.offset(skip).limit(limit).all()


@router.get("/{product_id}", response_model=ProductOut)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = (
        db.query(Product)
        .filter(Product.id == product_id, Product.is_active == True)
        .first()
    )
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.post("/", response_model=ProductOut, status_code=201)
def create_product(payload: ProductCreate, db: Session = Depends(get_db)):
    if db.query(Product).filter(Product.sku == payload.sku).first():
        raise HTTPException(status_code=400, detail="SKU already exists")
    product = Product(**payload.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.put("/{product_id}", response_model=ProductOut)
def update_product(product_id: int, payload: ProductUpdate, db: Session = Depends(get_db)):
    product = (
        db.query(Product)
        .filter(Product.id == product_id, Product.is_active == True)
        .first()
    )
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(product, field, value)
    db.commit()
    db.refresh(product)
    return product


@router.delete("/{product_id}", status_code=204)
def delete_product(product_id: int, db: Session = Depends(get_db)):
    product = (
        db.query(Product)
        .filter(Product.id == product_id, Product.is_active == True)
        .first()
    )
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    product.is_active = False
    db.commit()


@router.post("/{product_id}/adjust", response_model=StockAdjustOut)
async def adjust_stock(
    product_id: int,
    payload: StockAdjustIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    product = (
        db.query(Product)
        .filter(Product.id == product_id, Product.is_active == True)
        .first()
    )
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # sales and write-offs reduce stock; restocks and adjustments increase it
    if payload.change_type in ("sale", "write_off"):
        delta = -payload.qty
    else:
        delta = payload.qty

    if product.stock_qty + delta < 0:
        raise HTTPException(status_code=400, detail="Stock cannot go below 0")

    product.stock_qty += delta
    db.add(StockHistory(
        product_id=product.id,
        user_id=current_user.id,
        change_qty=delta,
        change_type=payload.change_type,
    ))
    db.commit()
    db.refresh(product)

    asyncio.create_task(manager.broadcast("stock_updated", {
        "product_id": product.id,
        "product_name": product.name,
        "new_stock_qty": product.stock_qty,
        "status": "low" if product.stock_qty <= product.reorder_threshold else "ok",
    }))

    return StockAdjustOut(
        product_id=product.id,
        new_stock_qty=product.stock_qty,
        change_qty=delta,
        change_type=payload.change_type,
    )


@router.get("/{product_id}/history")
def stock_history(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id, Product.is_active == True).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    rows = (
        db.query(StockHistory)
        .filter(StockHistory.product_id == product_id)
        .order_by(StockHistory.recorded_at.desc())
        .limit(50)
        .all()
    )
    return [
        {
            "id": r.id,
            "change_qty": r.change_qty,
            "change_type": r.change_type,
            "recorded_at": r.recorded_at.isoformat(),
        }
        for r in rows
    ]
