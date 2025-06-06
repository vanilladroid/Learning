from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
import datetime
from budget_planner.models.data_models import TransactionType # Enum

# --- User Schemas ---
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)

class UserCreate(UserBase):
    password: str = Field(..., min_length=6)

class UserResponse(UserBase):
    id: int
    # Consider not returning username in every response if not needed
    # username: str

    class Config:
        orm_mode = True

# --- Token Schemas (Basic for now) ---
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# --- Category Schemas ---
class CategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)

class CategoryCreate(CategoryBase):
    pass

class CategoryResponse(CategoryBase):
    id: int
    user_id: int # Or fetch from current user context

    class Config:
        orm_mode = True

# --- Transaction Schemas ---
class TransactionBase(BaseModel):
    amount: float = Field(..., gt=0) # Greater than 0
    type: TransactionType
    date: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)
    description: Optional[str] = Field(None, max_length=255)
    category_id: int

class TransactionCreate(TransactionBase):
    pass

class TransactionResponse(TransactionBase):
    id: int
    user_id: int # Or fetch from current user context
    category: CategoryResponse # Nested category information

    class Config:
        orm_mode = True

# --- Goal Schemas ---
class GoalBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    target_amount: float = Field(..., gt=0)
    current_amount: float = Field(default=0.0, ge=0)
    target_date: Optional[datetime.datetime] = None

class GoalCreate(GoalBase):
    pass

class GoalUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    target_amount: Optional[float] = Field(None, gt=0)
    current_amount: Optional[float] = Field(None, ge=0)
    target_date: Optional[datetime.datetime] = None # Handled by ORM if None
    clear_target_date: Optional[bool] = False

class GoalResponse(GoalBase):
    id: int
    user_id: int
    creation_date: datetime.datetime
    progress_percentage: float = 0.0

    class Config:
        orm_mode = True

class GoalContribution(BaseModel):
    amount: float = Field(..., gt=0)
