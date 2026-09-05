from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class DashboardStats(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    revenue: Decimal
    total_sales: Decimal
    total_purchases: Decimal
    expenses: Decimal
    total_expenses: Decimal
    profit: Decimal
    net_cash_flow: Decimal  # sales - purchases - expenses
    total_transactions: int = 0
    inventory_value: Decimal = Decimal("0.00")
    low_stock_count: int = 0
    low_stock_threshold: int = 10
    low_stock_items: list[str] = Field(default_factory=list)
