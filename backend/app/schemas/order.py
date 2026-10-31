"""
Pydantic schemas for Approved Customer Orders.
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class OrderItemBase(BaseModel):
    sku: Optional[str] = None
    description: str
    quantity: Decimal = Field(..., ge=0)
    unit: str = "PCS"
    unit_price: Decimal = Field(..., ge=0)
    line_total: Decimal = Field(..., ge=0)


class OrderItemCreate(OrderItemBase):
    pass


class OrderItemResponse(OrderItemBase):
    id: str
    order_id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrderBase(BaseModel):
    order_number: Optional[str] = None
    customer_name: str
    currency: str = "USD"
    quantity: Optional[Decimal] = None
    unit_price: Optional[Decimal] = None
    subtotal: Optional[Decimal] = None
    tax: Optional[Decimal] = Decimal("0.00")
    freight: Optional[Decimal] = None
    grand_total: Decimal
    destination: Optional[str] = None
    package_count: Optional[int] = None
    notes: Optional[str] = None
    is_authoritative: bool = True


class OrderCreate(OrderBase):
    order_id: Optional[str] = None  # If provided, used as primary ID (e.g. ORD-10245)
    items: List[OrderItemCreate] = []


class OrderResponse(OrderBase):
    id: str
    order_number: str
    version: int
    is_authoritative: bool
    items: List[OrderItemResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
