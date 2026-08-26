import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.dependencies import get_db
from src.repository.product_repository import ProductRepository
from src.schemas.product import ProductRead, ProductUpdate

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.get("", response_model=list[ProductRead])
def get_inventory(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)) -> list[ProductRead]:
    return ProductRepository(db).list(skip=skip, limit=limit)


@router.get("/{product_id}", response_model=ProductRead)
def get_inventory_item(product_id: uuid.UUID, db: Session = Depends(get_db)) -> ProductRead:
    return ProductRepository(db).get(product_id)


@router.patch("/{product_id}", response_model=ProductRead)
def update_inventory(
    product_id: uuid.UUID, payload: ProductUpdate, db: Session = Depends(get_db)
) -> ProductRead:
    return ProductRepository(db).update(product_id, payload)
