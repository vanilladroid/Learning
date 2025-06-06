from sqlalchemy.orm import Session
from budget_planner.models.data_models import User
from passlib.context import CryptContext

# Initialize CryptContext for password hashing
# Schemes chosen: bcrypt. Others like argon2 could also be used.
# Deprecated="auto" will handle upgrading password hashes if schemes change in the future.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Hashes a password using bcrypt."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)

def get_user_by_username(db: Session, username: str) -> User | None:
    """Retrieves a user by their username."""
    return db.query(User).filter(User.username == username).first()

def create_user(db: Session, username: str, password: str) -> User | None:
    """
    Creates a new user.
    Hashes the password before saving.
    Returns the created user object or None if username already exists.
    """
    if get_user_by_username(db, username):
        # User already exists
        return None
    hashed_pass = hash_password(password)
    db_user = User(username=username, password_hash=hashed_pass)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def authenticate_user(db: Session, username: str, password: str) -> User | None:
    """
    Authenticates a user.
    Checks if the user exists and if the provided password is correct.
    Returns the user object if authentication is successful, otherwise None.
    """
    user = get_user_by_username(db, username)
    if not user:
        return None # User not found
    if not verify_password(password, user.password_hash):
        return None # Incorrect password
    return user
