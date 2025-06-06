from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from budget_planner.core import transaction_management
from budget_planner.api import schemas, dependencies
from budget_planner.models.data_models import User, TransactionType # For Depends and types
import datetime

router = APIRouter(
    prefix="/transactions",
    tags=["transactions"],
    dependencies=[Depends(dependencies.get_current_user_placeholder)] # Apply placeholder auth
)

@router.post("/", response_model=schemas.TransactionResponse, status_code=status.HTTP_201_CREATED)
def create_transaction_api(
    transaction: schemas.TransactionCreate,
    db: Session = Depends(dependencies.get_db),
    current_user: User = Depends(dependencies.get_current_user_placeholder)
):
    # Ensure category belongs to user (done by core.create_transaction, but good to be aware)
    created_tx = transaction_management.create_transaction(
        db=db,
        amount=transaction.amount,
        type=transaction.type,
        date=transaction.date,
        description=transaction.description,
        category_id=transaction.category_id,
        user_id=current_user.id
    )
    if not created_tx:
        # This usually means the category_id is invalid or doesn't belong to the user
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid category ID or category does not belong to user")
    return created_tx

@router.get("/", response_model=List[schemas.TransactionResponse])
def read_transactions_api(
    skip: int = 0, limit: int = 100,
    db: Session = Depends(dependencies.get_db),
    current_user: User = Depends(dependencies.get_current_user_placeholder)
):
    transactions = transaction_management.get_transactions_by_user(db, user_id=current_user.id, skip=skip, limit=limit)
    return transactions

@router.get("/{transaction_id}", response_model=schemas.TransactionResponse)
def read_transaction_api(
    transaction_id: int,
    db: Session = Depends(dependencies.get_db),
    current_user: User = Depends(dependencies.get_current_user_placeholder)
):
    db_transaction = transaction_management.get_transaction_by_id(db, transaction_id=transaction_id, user_id=current_user.id)
    if db_transaction is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    return db_transaction


@router.put("/{transaction_id}", response_model=schemas.TransactionResponse)
def update_transaction_api(
    transaction_id: int,
    transaction_update: schemas.TransactionBase, # Use TransactionBase as all fields are optional for update
    db: Session = Depends(dependencies.get_db),
    current_user: User = Depends(dependencies.get_current_user_placeholder)
):
    updated_tx = transaction_management.update_transaction(
        db,
        transaction_id=transaction_id,
        user_id=current_user.id,
        amount=transaction_update.amount,
        type=transaction_update.type,
        date=transaction_update.date,
        description=transaction_update.description,
        category_id=transaction_update.category_id
    )
    if not updated_tx:
        # Check if tx exists first
        tx_exists = transaction_management.get_transaction_by_id(db, transaction_id, current_user.id)
        if not tx_exists:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
        else: # Exists, but update failed (e.g. invalid new category_id)
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid category ID or other update error")
    return updated_tx

@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction_api(
    transaction_id: int,
    db: Session = Depends(dependencies.get_db),
    current_user: User = Depends(dependencies.get_current_user_placeholder)
):
    if not transaction_management.delete_transaction(db, transaction_id=transaction_id, user_id=current_user.id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found or could not be deleted")
    return None
