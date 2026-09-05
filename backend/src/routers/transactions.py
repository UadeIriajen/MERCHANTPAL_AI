import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from src.auth import get_current_user, scope_id
from src.dependencies import get_db
from src.models.transaction import TransactionStatus, TransactionType
from src.repository.transaction_repository import TransactionRepository
from src.schemas.transaction import TransactionCreate, TransactionRead, TransactionUpdate
from src.services import transaction_service

router = APIRouter(prefix="/transactions", tags=["transactions"], dependencies=[Depends(get_current_user)])


@router.post("", response_model=TransactionRead, status_code=status.HTTP_201_CREATED)
def create_transaction(payload: TransactionCreate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)) -> TransactionRead:
    return transaction_service.create_transaction(db, payload, scope_id(current_user))


@router.get("", response_model=list[TransactionRead])
def list_transactions(
    type: TransactionType | None = None,
    status: TransactionStatus | None = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db), current_user: dict = Depends(get_current_user),
) -> list[TransactionRead]:
    """Get transactions — optionally narrowed to sales, purchases, or
    expenses via ?type=, and/or by ?status=paid|pending."""
    return TransactionRepository(db).list_filtered(type=type, status=status, skip=skip, limit=limit, owner_id=scope_id(current_user))


@router.get("/{transaction_id}", response_model=TransactionRead)
def get_transaction(transaction_id: uuid.UUID, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)) -> TransactionRead:
    return TransactionRepository(db).get_owned(transaction_id, scope_id(current_user))


@router.patch("/{transaction_id}", response_model=TransactionRead)
def update_transaction(
    transaction_id: uuid.UUID, payload: TransactionUpdate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)
) -> TransactionRead:
    # Note: does not re-adjust stock even if quantity/type/product_id change.
    # Void the transaction (delete) and create a fresh one if the stock
    # effect needs to change.
    transaction = TransactionRepository(db).get_owned(transaction_id, scope_id(current_user))
    return TransactionRepository(db).update(transaction.id, payload)


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(transaction_id: uuid.UUID, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)) -> None:
    transaction_service.delete_transaction(db, transaction_id, scope_id(current_user))
