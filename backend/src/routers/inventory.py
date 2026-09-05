import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from src.auth import get_current_user, scope_id
from src.dependencies import get_db
from src.repository.product_repository import ProductRepository
from src.schemas.product import ProductCreate, ProductRead, ProductUpdate

router = APIRouter(prefix="/inventory", tags=["inventory"], dependencies=[Depends(get_current_user)])


@router.post("", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
def create_inventory_item(payload: ProductCreate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)) -> ProductRead:
    return ProductRepository(db).create(payload, scope_id(current_user))


@router.get("", response_model=list[ProductRead])
def get_inventory(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)) -> list[ProductRead]:
    return ProductRepository(db).list_owned(scope_id(current_user), skip=skip, limit=limit)


@router.get("/{product_id}", response_model=ProductRead)
def get_inventory_item(product_id: uuid.UUID, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)) -> ProductRead:
    return ProductRepository(db).get_owned(product_id, scope_id(current_user))


@router.patch("/{product_id}", response_model=ProductRead)
def update_inventory(
    product_id: uuid.UUID, payload: ProductUpdate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)
) -> ProductRead:
    return ProductRepository(db).update(product_id, payload, scope_id(current_user))


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_inventory_item(product_id: uuid.UUID, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)) -> None:
    ProductRepository(db).delete_owned(product_id, scope_id(current_user))
