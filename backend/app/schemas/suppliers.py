from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional
from datetime import datetime


class SupplierCreate(BaseModel):
    name: str
    email: EmailStr
    categories: list[str] = []
    lead_time_days: int = 3


class SupplierUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    categories: Optional[list[str]] = None
    lead_time_days: Optional[int] = None


class SupplierOut(BaseModel):
    id: int
    name: str
    email: str
    categories: list[str]
    lead_time_days: int
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
