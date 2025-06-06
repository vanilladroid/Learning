from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from budget_planner.core import user_management
from budget_planner.api import schemas, dependencies

router = APIRouter(
    prefix="/auth",
    tags=["authentication"]
)

@router.post("/register", response_model=schemas.UserResponse)
def register_user(user: schemas.UserCreate, db: Session = Depends(dependencies.get_db)):
    db_user = user_management.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already registered")
    created_user = user_management.create_user(db=db, username=user.username, password=user.password)
    if not created_user:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="User could not be created")
    return created_user

@router.post("/login", response_model=schemas.Token)
def login_for_access_token(form_data: schemas.UserCreate, db: Session = Depends(dependencies.get_db)): # Using UserCreate for simplicity
    user = user_management.authenticate_user(db, username=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # For now, returning a dummy token. Real implementation would use JWT.
    access_token = f"dummytoken_for_user_{user.id}"
    return {"access_token": access_token, "token_type": "bearer"}
