from pydantic import BaseModel, ConfigDict, field_validator, Field
from typing import Optional, Literal
from datetime import datetime


class ProductCreate(BaseModel):
    sku: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=255)
    category: str = Field(min_length=1, max_length=100)
    stock_qty: int = Field(default=0, ge=0)
    unit_price: float = Field(gt=0)
    reorder_threshold: int = Field(default=10, ge=0)
    expiry_date: Optional[datetime] = None


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=255)
    category: Optional[str] = Field(default=None, max_length=100)
    unit_price: Optional[float] = Field(default=None, gt=0)
    reorder_threshold: Optional[int] = Field(default=None, ge=0)
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


class StockAdjustIn(BaseModel):
    change_type: Literal["sale", "restock", "write_off", "adjustment"]
    qty: int = Field(gt=0, le=100000)
    note: Optional[str] = Field(default=None, max_length=500)

    @field_validator("qty")
    @classmethod
    def qty_positive(cls, v):
        if v <= 0:
            raise ValueError("qty must be greater than 0")
        return v


class StockAdjustOut(BaseModel):
    product_id: int
    new_stock_qty: int
    change_qty: int
    change_type: str
