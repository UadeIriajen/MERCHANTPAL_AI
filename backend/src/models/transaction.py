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


class TransactionType(str, enum.Enum):
    SALE = "sale"
    PURCHASE = "purchase"
    EXPENSE = "expense"


class Transaction(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A money-in or money-out event: a sale, a purchase, or an expense.

    Mirrors FRONTEND's MockTransaction shape, generalized with `type` instead
    of three separate tables — a sale, a purchase and an expense differ only
    in which way the money/stock moves, not in their fields.
    """

    __tablename__ = "transactions"

    owner_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)

    type: Mapped[TransactionType] = mapped_column(
        Enum(TransactionType, name="transaction_type"), default=TransactionType.SALE
    )
    item: Mapped[str] = mapped_column(String(200))
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    total: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    # The other party: customer for a sale, supplier for a purchase, payee for an expense.
    counterparty: Mapped[str] = mapped_column(String(200), default="Walk-in customer")
    status: Mapped[TransactionStatus] = mapped_column(
        Enum(TransactionStatus, name="transaction_status"), default=TransactionStatus.PENDING
    )
    # Optional link to the product this transaction moves stock for (sale = out, purchase = in).
    product_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("products.id", ondelete="SET NULL"), nullable=True
    )
    # Raw transcript this row was created from, when it came through the voice pipeline.
    source_transcript: Mapped[str | None] = mapped_column(String(1000), nullable=True)
