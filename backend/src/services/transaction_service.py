"""Coordinates Transaction + Product together, since a sale/purchase moves
stock as a side effect. Routers call this instead of TransactionRepository
directly whenever the transaction should also affect inventory.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.exceptions import ConflictError
from src.models.transaction import Transaction, TransactionType
from src.repository.product_repository import ProductRepository
from src.repository.transaction_repository import TransactionRepository
from src.schemas.transaction import TransactionCreate

# Each 1 unit of `quantity` moves the linked product's stock by this much.
_STOCK_DIRECTION = {
    TransactionType.SALE: -1,
    TransactionType.PURCHASE: 1,
    TransactionType.EXPENSE: 0,
}


def _adjust_stock(db: Session, transaction: Transaction, sign: int, owner_id: str | None = None) -> None:
    """sign=+1 applies the transaction's stock effect, sign=-1 reverses it
    (used when deleting a transaction)."""
    if transaction.product_id is None:
        return
    direction = _STOCK_DIRECTION[transaction.type]
    if direction == 0:
        return
    products = ProductRepository(db)
    product = products.get_owned(transaction.product_id, owner_id)
    product.stock = max(0, product.stock + sign * direction * transaction.quantity)
    db.commit()


def create_transaction(db: Session, payload: TransactionCreate, owner_id: str | None = None) -> Transaction:
    request_key = payload.source_transcript
    if request_key and request_key.startswith("idempotency:"):
        existing = db.scalar(
            select(Transaction).where(Transaction.source_transcript == request_key, *(() if owner_id is None else (Transaction.owner_id == owner_id,)))
        )
        if existing is not None:
            raise ConflictError("This transaction has already been recorded")
    transaction = Transaction(**payload.model_dump(), owner_id=owner_id)
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    _adjust_stock(db, transaction, sign=1, owner_id=owner_id)
    return transaction


def delete_transaction(db: Session, transaction_id: uuid.UUID, owner_id: str | None = None) -> None:
    repo = TransactionRepository(db)
    transaction = repo.get_owned(transaction_id, owner_id)
    _adjust_stock(db, transaction, sign=-1, owner_id=owner_id)
    db.delete(transaction)
    db.commit()