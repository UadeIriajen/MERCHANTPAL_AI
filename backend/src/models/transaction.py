import enum
import uuid
from decimal import Decimal

from sqlalchemy import Enum, ForeignKey, Integer, Numeric, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base
from src.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class TransactionStatus(str, enum.Enum):
    PAID = "paid"
    PENDING = "pending"


class Transaction(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A sale. Mirrors FRONTEND's MockTransaction shape."""

    __tablename__ = "transactions"

    item: Mapped[str] = mapped_column(String(200))
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    total: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    customer: Mapped[str] = mapped_column(String(200), default="Walk-in customer")
    status: Mapped[TransactionStatus] = mapped_column(
        Enum(TransactionStatus, name="transaction_status"), default=TransactionStatus.PENDING
    )
    # Optional link back to the product sold, so stock/profit can be derived later.
    product_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("products.id", ondelete="SET NULL"), nullable=True
    )
