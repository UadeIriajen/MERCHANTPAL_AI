import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from src.dependencies import get_db
from src.models.transaction import TransactionStatus, TransactionType
from src.repository.transaction_repository import TransactionRepository
from src.schemas.transaction import TransactionCreate, TransactionRead, TransactionUpdate
from src.services import transaction_service

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.post("", response_model=TransactionRead, status_code=status.HTTP_201_CREATED)
def create_transaction(payload: TransactionCreate, db: Session = Depends(get_db)) -> TransactionRead:
    return transaction_service.create_transaction(db, payload)


@router.get("", response_model=list[TransactionRead])
def list_transactions(
    type: TransactionType | None = None,
    status: TransactionStatus | None = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
) -> list[TransactionRead]:
    """Get transactions — optionally narrowed to sales, purchases, or
    expenses via ?type=, and/or by ?status=paid|pending."""
    return TransactionRepository(db).list_filtered(type=type, status=status, skip=skip, limit=limit)


@router.get("/{transaction_id}", response_model=TransactionRead)
def get_transaction(transaction_id: uuid.UUID, db: Session = Depends(get_db)) -> TransactionRead:
    return TransactionRepository(db).get(transaction_id)


@router.patch("/{transaction_id}", response_model=TransactionRead)
def update_transaction(
    transaction_id: uuid.UUID, payload: TransactionUpdate, db: Session = Depends(get_db)
) -> TransactionRead:
    # Note: does not re-adjust stock even if quantity/type/product_id change.
    # Void the transaction (delete) and create a fresh one if the stock
    # effect needs to change.
    return TransactionRepository(db).update(transaction_id, payload)


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(transaction_id: uuid.UUID, db: Session = Depends(get_db)) -> None:
    transaction_service.delete_transaction(db, transaction_id)
