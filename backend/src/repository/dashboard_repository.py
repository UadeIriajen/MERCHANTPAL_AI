from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.models.product import Product
from src.models.transaction import Transaction, TransactionType
from src.schemas.dashboard import DashboardStats

LOW_STOCK_THRESHOLD = 10


class DashboardRepository:
    """Read-only aggregate queries across products + transactions."""

    def __init__(self, db: Session, owner_id: str | None = None):
        self.db = db
        self.owner_id = owner_id

    def _owned(self, model):
        return () if self.owner_id is None else (model.owner_id == self.owner_id,)

    def _sum_by_type(self, transaction_type: TransactionType) -> Decimal:
        value = self.db.execute(
            select(func.coalesce(func.sum(Transaction.total), 0)).where(
                Transaction.type == transaction_type,
                *self._owned(Transaction),
            )
        ).scalar_one()
        return Decimal(value or 0)

    def _sum_cost_of_goods_sold(self) -> Decimal:
        value = self.db.execute(
            select(func.coalesce(func.sum(Transaction.quantity * Product.cost), 0))
            .select_from(Transaction)
            .outerjoin(Product, Product.id == Transaction.product_id)
            .where(Transaction.type == TransactionType.SALE, *self._owned(Transaction), *self._owned(Product))
        ).scalar_one()
        return Decimal(value or 0)

    def get_stats(self) -> DashboardStats:
        revenue = self._sum_by_type(TransactionType.SALE)
        total_purchases = self._sum_by_type(TransactionType.PURCHASE)
        expenses = self._sum_by_type(TransactionType.EXPENSE)
        cost_of_goods_sold = self._sum_cost_of_goods_sold()
        profit = revenue - expenses - cost_of_goods_sold

        total_transactions = self.db.execute(
            select(func.count(Transaction.id)).where(*self._owned(Transaction))
        ).scalar_one()

        inventory_value = Decimal(
            self.db.execute(
                select(func.coalesce(func.sum(Product.price * Product.stock), 0)).where(*self._owned(Product))
            ).scalar_one()
        )

        low_stock_products = self.db.execute(
            select(Product.name).where(Product.stock < LOW_STOCK_THRESHOLD, *self._owned(Product)).order_by(Product.name.asc())
        ).scalars().all()
        low_stock_count = len(low_stock_products)

        return DashboardStats(
            revenue=revenue,
            total_sales=revenue,
            total_purchases=total_purchases,
            expenses=expenses,
            total_expenses=expenses,
            profit=profit,
            net_cash_flow=revenue - total_purchases - expenses,
            total_transactions=total_transactions,
            inventory_value=inventory_value,
            low_stock_count=low_stock_count,
            low_stock_threshold=LOW_STOCK_THRESHOLD,
            low_stock_items=list(low_stock_products),
        )
