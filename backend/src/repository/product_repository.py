from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.core.exceptions import ConflictError
from src.models.product import Product
from src.repository.base import BaseRepository
from src.schemas.product import ProductCreate, ProductUpdate


class ProductRepository(BaseRepository[Product, ProductCreate, ProductUpdate]):
    def __init__(self, db: Session):
        super().__init__(Product, db)

    def create(self, obj_in: ProductCreate, owner_id: str | None = None) -> Product:
        name = obj_in.name.strip()
        filters = [func.lower(Product.name) == name.lower()]
        if owner_id is not None:
            filters.append(Product.owner_id == owner_id)
        existing = self.db.scalar(select(Product).where(*filters))
        if existing is not None:
            raise ConflictError(f"A product named '{existing.name}' already exists")
        product = Product(**obj_in.model_copy(update={"name": name}).model_dump(), owner_id=owner_id)
        self.db.add(product)
        self.db.commit()
        self.db.refresh(product)
        return product

    def update(self, id, obj_in: ProductUpdate, owner_id: str | None = None) -> Product:
        product = self.db.get(Product, id)
        if product is None or owner_id is not None and product.owner_id != owner_id:
            from src.core.exceptions import NotFoundError
            raise NotFoundError("Product", id)
        if obj_in.name is not None:
            name = obj_in.name.strip()
            filters = [func.lower(Product.name) == name.lower(), Product.id != id]
            if owner_id is not None:
                filters.append(Product.owner_id == owner_id)
            existing = self.db.scalar(
                select(Product).where(*filters)
            )
            if existing is not None:
                raise ConflictError(f"A product named '{existing.name}' already exists")
            obj_in = obj_in.model_copy(update={"name": name})
        return super().update(id, obj_in)

    def list_owned(self, owner_id: str | None, *, skip: int = 0, limit: int = 100) -> list[Product]:
        stmt = select(Product)
        if owner_id is not None:
            stmt = stmt.where(Product.owner_id == owner_id)
        return list(self.db.scalars(stmt.offset(skip).limit(limit)).all())

    def get_owned(self, id, owner_id: str | None) -> Product:
        product = self.db.get(Product, id)
        if product is None or owner_id is not None and product.owner_id != owner_id:
            from src.core.exceptions import NotFoundError
            raise NotFoundError("Product", id)
        return product

    def delete_owned(self, id, owner_id: str | None) -> None:
        product = self.get_owned(id, owner_id)
        self.db.delete(product)
        self.db.commit()
