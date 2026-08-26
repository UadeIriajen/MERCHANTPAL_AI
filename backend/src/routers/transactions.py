import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from src.dependencies import get_db
from src.repository.transaction_repository import TransactionRepository
from src.schemas.transaction import TransactionCreate, TransactionRead, TransactionUpdate

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.post("", response_model=TransactionRead, status_code=status.HTTP_201_CREATED)
def create_transaction(payload: TransactionCreate, db: Session = Depends(get_db)) -> TransactionRead:
    return TransactionRepository(db).create(payload)


@router.get("", response_model=list[TransactionRead])
def list_transactions(
    skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
) -> list[TransactionRead]:
    return TransactionRepository(db).list(skip=skip, limit=limit)


@router.get("/{transaction_id}", response_model=TransactionRead)
def get_transaction(transaction_id: uuid.UUID, db: Session = Depends(get_db)) -> TransactionRead:
    return TransactionRepository(db).get(transaction_id)


@router.patch("/{transaction_id}", response_model=TransactionRead)
def update_transaction(
    transaction_id: uuid.UUID, payload: TransactionUpdate, db: Session = Depends(get_db)
) -> TransactionRead:
    return TransactionRepository(db).update(transaction_id, payload)


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(transaction_id: uuid.UUID, db: Session = Depends(get_db)) -> None:
    TransactionRepository(db).delete(transaction_id)
