from sqlalchemy.orm import Session

from src.models.transaction import Transaction
from src.repository.base import BaseRepository
from src.schemas.transaction import TransactionCreate, TransactionUpdate


class TransactionRepository(BaseRepository[Transaction, TransactionCreate, TransactionUpdate]):
    def __init__(self, db: Session):
        super().__init__(Transaction, db)
