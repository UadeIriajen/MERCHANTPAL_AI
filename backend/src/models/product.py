from decimal import Decimal

from sqlalchemy import Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base
from src.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Product(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """An inventory item. Mirrors FRONTEND's MockProduct shape."""

    __tablename__ = "products"

    owner_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)

    name: Mapped[str] = mapped_column(String(200))
    category: Mapped[str] = mapped_column(String(100))
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    cost: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    stock: Mapped[int] = mapped_column(Integer, default=0)
    unit: Mapped[str] = mapped_column(String(50))
