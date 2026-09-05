from fastapi import APIRouter, Depends
from sqlalchemy import Date, cast, func, select
from sqlalchemy.orm import Session

from src.auth import get_current_user, scope_id
from src.dependencies import get_db
from src.models.product import Product
from src.models.transaction import Transaction, TransactionType
from src.repository.dashboard_repository import DashboardRepository, LOW_STOCK_THRESHOLD
from src.schemas.dashboard import DashboardStats
from src.schemas.product import ProductRead

router = APIRouter(prefix="/dashboard", tags=["dashboard"], dependencies=[Depends(get_current_user)])


@router.get("/stats", response_model=DashboardStats)
def get_dashboard_statistics(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)) -> DashboardStats:
    return DashboardRepository(db, scope_id(current_user)).get_stats()


@router.get("/summary", response_model=DashboardStats)
def get_dashboard_summary(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)) -> DashboardStats:
    return DashboardRepository(db, scope_id(current_user)).get_stats()


@router.get("/low-stock", response_model=list[ProductRead])
def get_low_stock_products(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)) -> list[ProductRead]:
    filters = [Product.stock < LOW_STOCK_THRESHOLD]
    if scope_id(current_user) is not None:
        filters.append(Product.owner_id == scope_id(current_user))
    stmt = select(Product).where(*filters).order_by(Product.name.asc())
    return list(db.scalars(stmt).all())


@router.get("/analytics")
def get_analytics(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)) -> dict[str, object]:
    owner = scope_id(current_user)
    filters = [Transaction.type == TransactionType.SALE]
    if owner is not None:
        filters.append(Transaction.owner_id == owner)
    rows = db.execute(
        select(cast(Transaction.created_at, Date), func.coalesce(func.sum(Transaction.total), 0))
        .where(*filters)
        .group_by(cast(Transaction.created_at, Date))
        .order_by(cast(Transaction.created_at, Date).desc())
        .limit(30)
    ).all()
    return {
        "stats": DashboardRepository(db, owner).get_stats().model_dump(mode="json"),
        "daily_sales": [{"date": str(day), "amount": str(amount)} for day, amount in reversed(rows)],
    }
