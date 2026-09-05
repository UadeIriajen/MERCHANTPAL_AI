from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.auth import get_current_user, scope_id
from src.dependencies import get_db
from src.models.product import Product
from src.repository.dashboard_repository import LOW_STOCK_THRESHOLD

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("")
def get_notifications(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)) -> list[dict[str, object]]:
    filters = [Product.stock < LOW_STOCK_THRESHOLD]
    if scope_id(current_user) is not None:
        filters.append(Product.owner_id == scope_id(current_user))
    products = db.scalars(select(Product).where(*filters).order_by(Product.stock.asc())).all()
    now = datetime.now(timezone.utc).isoformat()
    return [
        {"id": f"low-stock-{product.id}", "kind": "low_stock", "title": "Stock is running low", "body": f"{product.name} has {product.stock} {product.unit}s left.", "created_at": now, "read": False}
        for product in products
    ]