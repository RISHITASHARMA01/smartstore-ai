from pydantic import BaseModel, EmailStr, ConfigDict, Field
from typing import Optional
from datetime import datetime


class SupplierCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    email: EmailStr = Field(max_length=254)
    categories: list[str] = Field(default=[], max_length=20)
    lead_time_days: int = Field(default=3, ge=0, le=365)


class SupplierUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=255)
    email: Optional[EmailStr] = Field(default=None, max_length=254)
    categories: Optional[list[str]] = Field(default=None, max_length=20)
    lead_time_days: Optional[int] = Field(default=None, ge=0, le=365)


class SupplierOut(BaseModel):
    id: int
    name: str
    email: str
    categories: list[str]
    lead_time_days: int
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
