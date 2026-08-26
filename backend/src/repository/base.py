import uuid
from typing import Generic, TypeVar

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.exceptions import NotFoundError
from src.database import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """Common CRUD used by every table-specific repository below."""

    def __init__(self, model: type[ModelType], db: Session):
        self.model = model
        self.db = db

    def get(self, id: uuid.UUID) -> ModelType:
        obj = self.db.get(self.model, id)
        if obj is None:
            raise NotFoundError(self.model.__name__, id)
        return obj

    def list(self, *, skip: int = 0, limit: int = 100) -> list[ModelType]:
        stmt = select(self.model).offset(skip).limit(limit)
        return list(self.db.scalars(stmt).all())

    def create(self, obj_in: CreateSchemaType) -> ModelType:
        obj = self.model(**obj_in.model_dump())
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def update(self, id: uuid.UUID, obj_in: UpdateSchemaType) -> ModelType:
        obj = self.get(id)
        for field, value in obj_in.model_dump(exclude_unset=True).items():
            setattr(obj, field, value)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def delete(self, id: uuid.UUID) -> None:
        obj = self.get(id)
        self.db.delete(obj)
        self.db.commit()
