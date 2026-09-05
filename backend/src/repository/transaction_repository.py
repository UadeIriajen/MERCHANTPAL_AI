from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models.transaction import Transaction, TransactionStatus, TransactionType
from src.repository.base import BaseRepository
from src.schemas.transaction import TransactionCreate, TransactionUpdate


class TransactionRepository(BaseRepository[Transaction, TransactionCreate, TransactionUpdate]):
    def __init__(self, db: Session):
        super().__init__(Transaction, db)

    def list_filtered(
        self,
        *,
        type: TransactionType | None = None,
        status: TransactionStatus | None = None,
        skip: int = 0,
        limit: int = 100,
        owner_id: str | None = None,
    ) -> list[Transaction]:
        stmt = select(Transaction)
        if owner_id is not None:
            stmt = stmt.where(Transaction.owner_id == owner_id)
        if type is not None:
            stmt = stmt.where(Transaction.type == type)
        if status is not None:
            stmt = stmt.where(Transaction.status == status)
        stmt = stmt.order_by(Transaction.created_at.desc()).offset(skip).limit(limit)
        return list(self.db.scalars(stmt).all())

    def get_owned(self, id, owner_id: str | None) -> Transaction:
        transaction = self.db.get(Transaction, id)
        if transaction is None or owner_id is not None and transaction.owner_id != owner_id:
            from src.core.exceptions import NotFoundError
            raise NotFoundError("Transaction", id)
        return transaction
