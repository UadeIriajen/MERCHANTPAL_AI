from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base


class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), default="Merchant")
    business: Mapped[str] = mapped_column(String(200), default="My business")
    category: Mapped[str] = mapped_column(String(100), default="other")
    description: Mapped[str] = mapped_column(String(1000), default="")