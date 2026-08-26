from sqlalchemy.orm import Session

from src.models.product import Product
from src.repository.base import BaseRepository
from src.schemas.product import ProductCreate, ProductUpdate


class ProductRepository(BaseRepository[Product, ProductCreate, ProductUpdate]):
    def __init__(self, db: Session):
        super().__init__(Product, db)
