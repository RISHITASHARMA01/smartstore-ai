from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class ProductCreate(BaseModel):
    sku: str
    name: str
    category: str
    stock_qty: int = 0
    unit_price: float
    reorder_threshold: int = 10
    expiry_date: Optional[datetime] = None


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    stock_qty: Optional[int] = None
    unit_price: Optional[float] = None
    reorder_threshold: Optional[int] = None
    expiry_date: Optional[datetime] = None


class ProductOut(BaseModel):
    id: int
    sku: str
    name: str
    category: str
    stock_qty: int
    unit_price: float
    reorder_threshold: int
    expiry_date: Optional[datetime]
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)
