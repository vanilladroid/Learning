from sqlalchemy.orm import Session
from sqlalchemy import func # For count
from budget_planner.models.data_models import Category, Transaction, TransactionType, User
import datetime

# --- Category Management ---

def get_category_by_name(db: Session, name: str, user_id: int) -> Category | None:
    """Retrieves a category by its name for a specific user."""
    return db.query(Category).filter(Category.user_id == user_id, func.lower(Category.name) == func.lower(name)).first()

def create_category(db: Session, name: str, user_id: int) -> Category | None:
    """Creates a new category for the given user. Prevents duplicate category names (case-insensitive) for the same user."""
    # Check if user exists (optional, assuming user_id is validated upstream)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        # This case should ideally be handled before calling this function
        return None # Or raise an exception

    existing_category = get_category_by_name(db, name, user_id)
    if existing_category:
        return None # Duplicate category for this user

    db_category = Category(name=name, user_id=user_id)
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

def get_categories_by_user(db: Session, user_id: int) -> list[Category]:
    """Retrieves all categories for a given user."""
    return db.query(Category).filter(Category.user_id == user_id).order_by(Category.name).all()

def get_category_by_id(db: Session, category_id: int, user_id: int) -> Category | None:
    """Retrieves a category by its ID, ensuring it belongs to the user."""
    return db.query(Category).filter(Category.id == category_id, Category.user_id == user_id).first()

def update_category(db: Session, category_id: int, user_id: int, name: str | None = None) -> Category | None:
    """Updates a category's name. Ensures the category belongs to the user."""
    db_category = get_category_by_id(db, category_id, user_id)
    if not db_category:
        return None # Category not found or doesn't belong to user

    if name is not None:
        # Check if the new name would conflict with an existing category for this user
        existing_category_with_new_name = get_category_by_name(db, name, user_id)
        if existing_category_with_new_name and existing_category_with_new_name.id != category_id:
            # Another category with this name already exists for the user
            return None # Or raise a specific exception

        db_category.name = name

    db.commit()
    db.refresh(db_category)
    return db_category

def delete_category(db: Session, category_id: int, user_id: int) -> bool:
    """
    Deletes a category. Ensures the category belongs to the user.
    Prevents deletion if there are transactions linked to this category.
    Returns True if deletion is successful, False otherwise.
    """
    db_category = get_category_by_id(db, category_id, user_id)
    if not db_category:
        return False # Category not found or doesn't belong to user

    # Check for linked transactions
    transaction_count = db.query(Transaction).filter(Transaction.category_id == category_id).count()
    if transaction_count > 0:
        # Cannot delete category with linked transactions
        # Consider raising an error or returning a specific status
        return False

    db.delete(db_category)
    db.commit()
    return True

# --- Transaction Management ---

def create_transaction(db: Session, amount: float, type: TransactionType, date: datetime.datetime,
                       user_id: int, category_id: int, description: str | None = None) -> Transaction | None:
    """
    Creates a new transaction. Ensures the category belongs to the user.
    Returns the Transaction object or None if category validation fails.
    """
    # Validate that the category belongs to the user
    category = get_category_by_id(db, category_id, user_id)
    if not category:
        return None # Category not found for this user or does not exist

    db_transaction = Transaction(
        amount=amount,
        type=type,
        date=date,
        description=description,
        category_id=category_id,
        user_id=user_id
    )
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    return db_transaction

def get_transactions_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> list[Transaction]:
    """Retrieves transactions for a user with pagination, ordered by date descending."""
    return db.query(Transaction).filter(Transaction.user_id == user_id).order_by(Transaction.date.desc()).offset(skip).limit(limit).all()

def get_transaction_by_id(db: Session, transaction_id: int, user_id: int) -> Transaction | None:
    """Retrieves a specific transaction by its ID, ensuring it belongs to the user."""
    return db.query(Transaction).filter(Transaction.id == transaction_id, Transaction.user_id == user_id).first()

def update_transaction(db: Session, transaction_id: int, user_id: int,
                       amount: float | None = None, type: TransactionType | None = None,
                       date: datetime.datetime | None = None, description: str | None = None,
                       category_id: int | None = None) -> Transaction | None:
    """
    Updates a transaction. Ensures it belongs to the user.
    If category_id is changed, ensures the new category also belongs to the user.
    Returns the updated Transaction object or None if validation fails.
    """
    db_transaction = get_transaction_by_id(db, transaction_id, user_id)
    if not db_transaction:
        return None # Transaction not found or doesn't belong to user

    if category_id is not None:
        # Validate that the new category belongs to the user
        new_category = get_category_by_id(db, category_id, user_id)
        if not new_category:
            return None # New category not found for this user or does not exist
        db_transaction.category_id = category_id

    if amount is not None:
        db_transaction.amount = amount
    if type is not None:
        db_transaction.type = type
    if date is not None:
        db_transaction.date = date
    if description is not None: # Allow setting description to empty string
        db_transaction.description = description

    db.commit()
    db.refresh(db_transaction)
    return db_transaction

def delete_transaction(db: Session, transaction_id: int, user_id: int) -> bool:
    """Deletes a transaction. Ensures it belongs to the user. Returns True if successful."""
    db_transaction = get_transaction_by_id(db, transaction_id, user_id)
    if not db_transaction:
        return False # Transaction not found or doesn't belong to user

    db.delete(db_transaction)
    db.commit()
    return True
