from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.models.product import Product
from src.models.transaction import Transaction, TransactionType
from src.schemas.dashboard import DashboardStats

LOW_STOCK_THRESHOLD = 10


class DashboardRepository:
    """Read-only aggregate queries across products + transactions."""

    def __init__(self, db: Session):
        self.db = db

    def _sum_by_type(self, transaction_type: TransactionType) -> Decimal:
        return Decimal(
            self.db.execute(
                select(func.coalesce(func.sum(Transaction.total), 0)).where(
                    Transaction.type == transaction_type
                )
            ).scalar_one()
        )

    def get_stats(self) -> DashboardStats:
        total_sales = self._sum_by_type(TransactionType.SALE)
        total_purchases = self._sum_by_type(TransactionType.PURCHASE)
        total_expenses = self._sum_by_type(TransactionType.EXPENSE)

        total_transactions = self.db.execute(
            select(func.count(Transaction.id))
        ).scalar_one()

        inventory_value = Decimal(
            self.db.execute(
                select(func.coalesce(func.sum(Product.price * Product.stock), 0))
            ).scalar_one()
        )

        low_stock_count = self.db.execute(
            select(func.count(Product.id)).where(Product.stock < LOW_STOCK_THRESHOLD)
        ).scalar_one()

        return DashboardStats(
            total_sales=total_sales,
            total_purchases=total_purchases,
            total_expenses=total_expenses,
            net_cash_flow=total_sales - total_purchases - total_expenses,
            total_transactions=total_transactions,
            inventory_value=inventory_value,
            low_stock_count=low_stock_count,
        )
