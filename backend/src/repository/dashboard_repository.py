from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.models.product import Product
from src.models.transaction import Transaction
from src.schemas.dashboard import DashboardStats

LOW_STOCK_THRESHOLD = 10


class DashboardRepository:
    """Read-only aggregate queries across products + transactions."""

    def __init__(self, db: Session):
        self.db = db

    def get_stats(self) -> DashboardStats:
        total_sales, total_transactions = self.db.execute(
            select(func.coalesce(func.sum(Transaction.total), 0), func.count(Transaction.id))
        ).one()

        inventory_value = self.db.execute(
            select(func.coalesce(func.sum(Product.price * Product.stock), 0))
        ).scalar_one()

        low_stock_count = self.db.execute(
            select(func.count(Product.id)).where(Product.stock < LOW_STOCK_THRESHOLD)
        ).scalar_one()

        return DashboardStats(
            total_sales=Decimal(total_sales),
            total_transactions=total_transactions,
            inventory_value=Decimal(inventory_value),
            low_stock_count=low_stock_count,
        )
