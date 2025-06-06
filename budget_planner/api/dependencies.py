from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status
from budget_planner.models.database import SessionLocal, engine
from budget_planner.models.data_models import User, create_tables
from budget_planner.core.user_management import get_user_by_username
from budget_planner.api.schemas import TokenData # Basic token data

# Create tables if they don't exist (e.g. first run)
create_tables(engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Placeholder for current user - INSECURE, FOR DEVELOPMENT ONLY
# In a real app, this would involve token decoding and validation
async def get_current_user_placeholder(db: Session = Depends(get_db), user_id: int = 1): # Assume user_id 1 for now
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        # Create a dummy user if no user exists for placeholder to work
        from budget_planner.core.user_management import create_user as core_create_user
        user = core_create_user(db, "testuser_api", "testpass")
        if user is None: # Should not happen unless db error
             raise HTTPException(status_code=500, detail="Could not create test user for placeholder")
        print(f"Created placeholder user with ID: {user.id} and username: {user.username}")
        # Fallback to the newly created user_id if the hardcoded one (1) was not found initially
        # This is hacky, real auth is needed.
        if user_id != user.id: # if user_id 1 was not found, and we created a new one.
             user = db.query(User).filter(User.id == user.id).first()


    if user is None: # If still none, something is wrong.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Placeholder user not found, cannot proceed",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
