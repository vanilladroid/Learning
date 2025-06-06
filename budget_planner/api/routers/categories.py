from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from budget_planner.core import transaction_management
from budget_planner.api import schemas, dependencies
from budget_planner.models.data_models import User # For Depends

router = APIRouter(
    prefix="/categories",
    tags=["categories"],
    dependencies=[Depends(dependencies.get_current_user_placeholder)] # Apply placeholder auth to all routes here
)

@router.post("/", response_model=schemas.CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category_api(
    category: schemas.CategoryCreate,
    db: Session = Depends(dependencies.get_db),
    current_user: User = Depends(dependencies.get_current_user_placeholder)
):
    db_category = transaction_management.get_category_by_name(db, name=category.name, user_id=current_user.id)
    if db_category:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Category with this name already exists")
    created_cat = transaction_management.create_category(db=db, name=category.name, user_id=current_user.id)
    if not created_cat: # Should not happen if previous check passed, but as safeguard
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not create category")
    return created_cat

@router.get("/", response_model=List[schemas.CategoryResponse])
def read_categories_api(
    db: Session = Depends(dependencies.get_db),
    current_user: User = Depends(dependencies.get_current_user_placeholder)
):
    categories = transaction_management.get_categories_by_user(db, user_id=current_user.id)
    return categories

@router.put("/{category_id}", response_model=schemas.CategoryResponse)
def update_category_api(
    category_id: int,
    category_update: schemas.CategoryCreate,
    db: Session = Depends(dependencies.get_db),
    current_user: User = Depends(dependencies.get_current_user_placeholder)
):
    updated_cat = transaction_management.update_category(
        db, category_id=category_id, user_id=current_user.id, name=category_update.name
    )
    if not updated_cat:
        # Check if category exists first to give a more specific error
        cat_exists = transaction_management.get_category_by_id(db, category_id, current_user.id)
        if not cat_exists:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
        else: # Exists, but update failed (e.g. name conflict)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Category name conflict or other update error")
    return updated_cat

@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category_api(
    category_id: int,
    db: Session = Depends(dependencies.get_db),
    current_user: User = Depends(dependencies.get_current_user_placeholder)
):
    category = transaction_management.get_category_by_id(db, category_id=category_id, user_id=current_user.id)
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    # transaction_management.delete_category returns False if deletion is blocked (e.g. linked transactions)
    if not transaction_management.delete_category(db, category_id=category_id, user_id=current_user.id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Category cannot be deleted (e.g., has linked transactions)")
    return None # FastAPI handles 204 No Content response automatically
