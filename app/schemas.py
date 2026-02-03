from datetime import datetime
from typing import List
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.models import OrderStatus

class UserCreate(BaseModel):
    email: EmailStr


class UserOut(BaseModel):
    id: UUID
    email: EmailStr
    created_at: datetime

    class Config:
        from_attributes = True


class OrderItemIn(BaseModel):
    product_sku: str = Field(min_length=1, max_length=64)
    quantity: int = Field(ge=1)
    unit_price: float = Field(gt=0)


class OrderCreate(BaseModel):
    user_id: UUID
    currency: str = Field(min_length=3, max_length=3)
    items: List[OrderItemIn]


class OrderItemOut(BaseModel):
    product_sku: str
    quantity: int
    unit_price: float

    class Config:
        from_attributes = True


class OrderOut(BaseModel):
    id: UUID
    user_id: UUID
    status: OrderStatus
    total_amount: float
    currency: str
    created_at: datetime
    updated_at: datetime
    items: List[OrderItemOut]

    class Config:
        from_attributes = True
        use_enum_values = True
