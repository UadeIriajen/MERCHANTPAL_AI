"""Coordinates Transaction + Product together, since a sale/purchase moves
stock as a side effect. Routers call this instead of TransactionRepository
directly whenever the transaction should also affect inventory.
"""

import uuid

from sqlalchemy.orm import Session

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


def _adjust_stock(db: Session, transaction: Transaction, sign: int) -> None:
    """sign=+1 applies the transaction's stock effect, sign=-1 reverses it
    (used when deleting a transaction)."""
    if transaction.product_id is None:
        return
    direction = _STOCK_DIRECTION[transaction.type]
    if direction == 0:
        return
    products = ProductRepository(db)
    product = products.get(transaction.product_id)
    product.stock = max(0, product.stock + sign * direction * transaction.quantity)
    db.commit()


def create_transaction(db: Session, payload: TransactionCreate) -> Transaction:
    transaction = TransactionRepository(db).create(payload)
    _adjust_stock(db, transaction, sign=1)
    return transaction


def delete_transaction(db: Session, transaction_id: uuid.UUID) -> None:
    repo = TransactionRepository(db)
    transaction = repo.get(transaction_id)
    _adjust_stock(db, transaction, sign=-1)
    repo.delete(transaction_id)
