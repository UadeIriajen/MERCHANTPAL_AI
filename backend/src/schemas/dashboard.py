from decimal import Decimal

from pydantic import BaseModel


class DashboardStats(BaseModel):
    total_sales: Decimal
    total_purchases: Decimal
    total_expenses: Decimal
    net_cash_flow: Decimal  # sales - purchases - expenses
    total_transactions: int
    inventory_value: Decimal
    low_stock_count: int
