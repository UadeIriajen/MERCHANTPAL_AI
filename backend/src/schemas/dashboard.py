from decimal import Decimal

from pydantic import BaseModel


class DashboardStats(BaseModel):
    total_sales: Decimal
    total_transactions: int
    inventory_value: Decimal
    low_stock_count: int
