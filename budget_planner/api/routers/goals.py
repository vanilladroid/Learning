from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from budget_planner.core import goal_management
from budget_planner.api import schemas, dependencies # Ensure schemas is correctly imported
from budget_planner.models.data_models import User
import datetime

router = APIRouter(
    prefix="/goals",
    tags=["goals"],
    dependencies=[Depends(dependencies.get_current_user_placeholder)]
)

def calculate_progress(current: float, target: float) -> float:
    if target <= 0:
        return 0.0
    progress = (current / target) * 100
    return round(min(progress, 100.0), 2)

@router.post("/", response_model=schemas.GoalResponse, status_code=status.HTTP_201_CREATED)
def create_goal_api(
    goal: schemas.GoalCreate,
    db: Session = Depends(dependencies.get_db),
    current_user: User = Depends(dependencies.get_current_user_placeholder)
):
    created_goal_orm = goal_management.create_goal(
        db=db,
        user_id=current_user.id,
        name=goal.name,
        target_amount=goal.target_amount,
        current_amount=goal.current_amount,
        target_date=goal.target_date
    )
    if not created_goal_orm:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not create goal")

    # Convert ORM model to Pydantic model for response, calculating dynamic fields
    response_goal = schemas.GoalResponse.from_orm(created_goal_orm)
    response_goal.progress_percentage = calculate_progress(created_goal_orm.current_amount, created_goal_orm.target_amount)
    return response_goal

@router.get("/", response_model=List[schemas.GoalResponse])
def read_goals_api(
    db: Session = Depends(dependencies.get_db),
    current_user: User = Depends(dependencies.get_current_user_placeholder)
):
    goals_orm = goal_management.get_goals_by_user(db, user_id=current_user.id)
    response_goals = []
    for goal_orm in goals_orm:
        response_goal = schemas.GoalResponse.from_orm(goal_orm)
        response_goal.progress_percentage = calculate_progress(goal_orm.current_amount, goal_orm.target_amount)
        response_goals.append(response_goal)
    return response_goals

@router.get("/{goal_id}", response_model=schemas.GoalResponse)
def read_goal_api(
    goal_id: int,
    db: Session = Depends(dependencies.get_db),
    current_user: User = Depends(dependencies.get_current_user_placeholder)
):
    db_goal_orm = goal_management.get_goal_by_id(db, goal_id=goal_id, user_id=current_user.id)
    if db_goal_orm is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")
    response_goal = schemas.GoalResponse.from_orm(db_goal_orm)
    response_goal.progress_percentage = calculate_progress(db_goal_orm.current_amount, db_goal_orm.target_amount)
    return response_goal

@router.put("/{goal_id}", response_model=schemas.GoalResponse)
def update_goal_api(
    goal_id: int,
    goal_update: schemas.GoalUpdate,
    db: Session = Depends(dependencies.get_db),
    current_user: User = Depends(dependencies.get_current_user_placeholder)
):
    updated_goal_orm = goal_management.update_goal(
        db,
        goal_id=goal_id,
        user_id=current_user.id,
        name=goal_update.name,
        target_amount=goal_update.target_amount,
        current_amount=goal_update.current_amount,
        target_date=goal_update.target_date,
        clear_target_date=goal_update.clear_target_date or False
    )
    if not updated_goal_orm:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found or update failed")
    response_goal = schemas.GoalResponse.from_orm(updated_goal_orm)
    response_goal.progress_percentage = calculate_progress(updated_goal_orm.current_amount, updated_goal_orm.target_amount)
    return response_goal

@router.delete("/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_goal_api(
    goal_id: int,
    db: Session = Depends(dependencies.get_db),
    current_user: User = Depends(dependencies.get_current_user_placeholder)
):
    if not goal_management.delete_goal(db, goal_id=goal_id, user_id=current_user.id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found or could not be deleted")
    return None # FastAPI handles 204

@router.post("/{goal_id}/contribute", response_model=schemas.GoalResponse)
def contribute_to_goal_api(
    goal_id: int,
    contribution: schemas.GoalContribution,
    db: Session = Depends(dependencies.get_db),
    current_user: User = Depends(dependencies.get_current_user_placeholder)
):
    updated_goal_orm = goal_management.update_goal_progress(
        db, goal_id=goal_id, user_id=current_user.id, contributed_amount=contribution.amount
    )
    if not updated_goal_orm:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found or contribution failed")
    response_goal = schemas.GoalResponse.from_orm(updated_goal_orm)
    response_goal.progress_percentage = calculate_progress(updated_goal_orm.current_amount, updated_goal_orm.target_amount)
    return response_goal
