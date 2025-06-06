from sqlalchemy.orm import Session
from budget_planner.models.data_models import Goal, User # Assuming models.data_models is accessible
import datetime

def create_goal(db: Session, user_id: int, name: str, target_amount: float,
                current_amount: float = 0.0, target_date: datetime.datetime | None = None) -> Goal | None:
    """Creates a new goal for the user."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None

    db_goal = Goal(
        name=name,
        target_amount=target_amount,
        current_amount=current_amount,
        target_date=target_date,
        user_id=user_id
    )
    db.add(db_goal)
    db.commit()
    db.refresh(db_goal)
    return db_goal

def get_goal_by_id(db: Session, goal_id: int, user_id: int) -> Goal | None:
    """Retrieves a specific goal by its ID, ensuring it belongs to the user."""
    return db.query(Goal).filter(Goal.id == goal_id, Goal.user_id == user_id).first()

def get_goals_by_user(db: Session, user_id: int) -> list[Goal]:
    """Retrieves all goals for a given user, ordered by creation date."""
    return db.query(Goal).filter(Goal.user_id == user_id).order_by(Goal.creation_date.desc()).all()

def update_goal(db: Session, goal_id: int, user_id: int,
                name: str | None = None,
                target_amount: float | None = None,
                current_amount: float | None = None,
                target_date: datetime.datetime | None = None,
                clear_target_date: bool = False) -> Goal | None: # Added clear_target_date
    """Updates a goal's details. Ensures the goal belongs to the user."""
    db_goal = get_goal_by_id(db, goal_id, user_id)
    if not db_goal:
        return None

    if name is not None:
        db_goal.name = name
    if target_amount is not None:
        db_goal.target_amount = target_amount
    if current_amount is not None:
        db_goal.current_amount = current_amount
    if clear_target_date:
        db_goal.target_date = None
    elif target_date is not None:
        db_goal.target_date = target_date

    db.commit()
    db.refresh(db_goal)
    return db_goal

def delete_goal(db: Session, goal_id: int, user_id: int) -> bool:
    """Deletes a goal. Ensures it belongs to the user. Returns True if successful."""
    db_goal = get_goal_by_id(db, goal_id, user_id)
    if not db_goal:
        return False

    db.delete(db_goal)
    db.commit()
    return True

def update_goal_progress(db: Session, goal_id: int, user_id: int, contributed_amount: float) -> Goal | None:
    """
    Adds the contributed_amount to the goal's current_amount.
    Ensures the goal belongs to the user.
    Returns the updated goal or None if not found.
    """
    db_goal = get_goal_by_id(db, goal_id, user_id)
    if not db_goal:
        return None

    db_goal.current_amount += contributed_amount
    db.commit()
    db.refresh(db_goal)
    return db_goal
