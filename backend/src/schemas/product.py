import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class ProductBase(BaseModel):
    name: str
    category: str
    price: Decimal
    cost: Decimal
    stock: int
    unit: str


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    """All fields optional so callers can send a partial patch."""

    name: str | None = None
    category: str | None = None
    price: Decimal | None = None
    cost: Decimal | None = None
    stock: int | None = None
    unit: str | None = None


class ProductRead(ProductBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
