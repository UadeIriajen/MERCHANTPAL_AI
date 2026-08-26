import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from src.models.transaction import TransactionStatus


class TransactionBase(BaseModel):
    item: str
    quantity: int
    total: Decimal
    customer: str = "Walk-in customer"
    status: TransactionStatus = TransactionStatus.PENDING
    product_id: uuid.UUID | None = None


class TransactionCreate(TransactionBase):
    pass


class TransactionUpdate(BaseModel):
    """All fields optional so callers can send a partial patch."""

    item: str | None = None
    quantity: int | None = None
    total: Decimal | None = None
    customer: str | None = None
    status: TransactionStatus | None = None
    product_id: uuid.UUID | None = None


class TransactionRead(TransactionBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
