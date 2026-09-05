from datetime import datetime, time, timedelta, timezone
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.models.product import Product
from src.models.transaction import Transaction, TransactionType
from src.repository.dashboard_repository import LOW_STOCK_THRESHOLD


def _period_bounds(period: str) -> tuple[datetime, datetime]:
    today = datetime.now(timezone.utc).date()
    start_date = today if period == "today" else today - timedelta(days=today.weekday())
    end_date = start_date + timedelta(days=1) if period == "today" else today + timedelta(days=1)
    return datetime.combine(start_date, time.min), datetime.combine(end_date, time.min)


def _sum_transactions(db: Session, transaction_type: TransactionType, period: str, owner_id: str | None = None) -> Decimal:
    start, end = _period_bounds(period)
    value = db.execute(
        select(func.coalesce(func.sum(Transaction.total), 0)).where(
            Transaction.type == transaction_type,
            Transaction.created_at >= start,
            Transaction.created_at < end,
            *(() if owner_id is None else (Transaction.owner_id == owner_id,)),
        )
    ).scalar_one()
    return Decimal(value or 0)


def daily_earnings(db: Session, owner_id: str | None = None) -> dict[str, object]:
    return {"period": "today", "amount": _sum_transactions(db, TransactionType.SALE, "today", owner_id)}


def weekly_spend(db: Session, owner_id: str | None = None) -> dict[str, object]:
    purchases = _sum_transactions(db, TransactionType.PURCHASE, "week", owner_id)
    expenses = _sum_transactions(db, TransactionType.EXPENSE, "week", owner_id)
    return {"period": "this_week", "purchases": purchases, "expenses": expenses, "total_spend": purchases + expenses}


def best_selling_product(db: Session, owner_id: str | None = None) -> dict[str, object] | None:
    product_name = func.coalesce(Product.name, Transaction.item)
    row = db.execute(
        select(product_name, func.sum(Transaction.quantity).label("quantity"))
        .select_from(Transaction)
        .outerjoin(Product, Product.id == Transaction.product_id)
        .where(Transaction.type == TransactionType.SALE, *(() if owner_id is None else (Transaction.owner_id == owner_id,)))
        .group_by(product_name)
        .order_by(func.sum(Transaction.quantity).desc(), product_name.asc())
        .limit(1)
    ).first()
    if row is None:
        return None
    return {"product": row[0], "quantity": int(row[1])}


def restock_recommendations(db: Session, owner_id: str | None = None) -> list[dict[str, object]]:
    products = db.scalars(
        select(Product).where(Product.stock < LOW_STOCK_THRESHOLD, *(() if owner_id is None else (Product.owner_id == owner_id,))).order_by(Product.stock.asc(), Product.name.asc())
    ).all()
    return [
        {"product": product.name, "stock": product.stock, "threshold": LOW_STOCK_THRESHOLD, "units_needed_to_threshold": LOW_STOCK_THRESHOLD - product.stock}
        for product in products
    ]


def classify_question(question: str) -> str | None:
    text = question.lower()
    if "restock" in text or "low stock" in text:
        return "restock"
    if "best-selling" in text or "best selling" in text or "top-selling" in text or "top selling" in text:
        return "best_selling"
    if "spend" in text or "spent" in text:
        return "weekly_spend"
    if ("make" in text or "made" in text or "earn" in text or "sale" in text) and "today" in text:
        return "daily_earnings"
    return None


def answer_question(db: Session, question: str, owner_id: str | None = None) -> tuple[str | None, dict[str, object]]:
    intent = classify_question(question)
    if intent == "daily_earnings":
        return intent, daily_earnings(db, owner_id)
    if intent == "weekly_spend":
        return intent, weekly_spend(db, owner_id)
    if intent == "best_selling":
        return intent, {"result": best_selling_product(db, owner_id)}
    if intent == "restock":
        return intent, {"items": restock_recommendations(db, owner_id)}
    return None, {}