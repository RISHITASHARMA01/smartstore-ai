from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional
from datetime import datetime

VALID_STATUSES = ["Draft", "Sent", "Acknowledged", "Received"]


class POLineItemCreate(BaseModel):
    product_id: int
    quantity: int
    unit_price: float


class ProductSummary(BaseModel):
    id: int
    sku: str
    name: str
    model_config = ConfigDict(from_attributes=True)


class SupplierSummary(BaseModel):
    id: int
    name: str
    email: str
    model_config = ConfigDict(from_attributes=True)


class POLineItemOut(BaseModel):
    id: int
    product_id: int
    product: ProductSummary
    quantity: int
    unit_price: float
    model_config = ConfigDict(from_attributes=True)


class POCreate(BaseModel):
    supplier_id: int
    notes: Optional[str] = None
    line_items: list[POLineItemCreate]

    @field_validator("line_items")
    @classmethod
    def at_least_one(cls, v):
        if not v:
            raise ValueError("At least one line item is required")
        return v


class POUpdate(BaseModel):
    notes: Optional[str] = None
    line_items: Optional[list[POLineItemCreate]] = None


class POOut(BaseModel):
    id: int
    supplier_id: int
    supplier: SupplierSummary
    status: str
    total_value: float
    notes: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    line_items: list[POLineItemOut]
    model_config = ConfigDict(from_attributes=True)
