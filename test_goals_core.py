import datetime
import time # To ensure distinct creation_date for ordering tests
from budget_planner.models.database import SessionLocal, engine
from budget_planner.models.data_models import create_tables, User, Goal # Corrected import path if needed
from budget_planner.core.user_management import create_user, get_user_by_username
from budget_planner.core.goal_management import (
    create_goal, get_goals_by_user, get_goal_by_id, update_goal, delete_goal, update_goal_progress
)

def run_goal_tests():
    print("Running goal management core logic tests...")
    # Explicitly call create_tables here to ensure schema is updated before tests
    # This is crucial if running tests in isolation or if the schema changed.
    create_tables(engine)
    print("Database tables ensured/updated.")

    db = SessionLocal()

    # --- Test User Setup ---
    test_username = "goal_user_v2" # Changed username to avoid potential old state issues
    user = get_user_by_username(db, test_username)
    if user:
        print(f"Found existing test user '{test_username}', cleaning up their goals...")
        db.query(Goal).filter(Goal.user_id == user.id).delete()
        # Do not delete the user here if other tests might rely on it or if cleanup is complex.
        # For full idempotency, user should be deleted and recreated.
        db.delete(user)
        db.commit()
        print(f"Old user '{test_username}' and their goals deleted.")

    user = create_user(db, username=test_username, password="goal_password123")
    assert user is not None, "Test user setup failed."
    user_id = user.id
    print(f"Test user '{test_username}' set up with ID: {user_id}")

    # --- Goal Tests ---
    print("Testing goal creation...")
    goal1_target_date = datetime.datetime.now() + datetime.timedelta(days=30)
    goal1 = create_goal(db, user_id=user_id, name="Vacation Fund", target_amount=1000.0, target_date=goal1_target_date)
    assert goal1 is not None and goal1.name == "Vacation Fund", "Goal 'Vacation Fund' creation failed"
    assert goal1.current_amount == 0.0, "Default current_amount is not 0.0"
    assert goal1.creation_date is not None, "Creation date not set"
    print(f"Goal 1 '{goal1.name}' created with ID {goal1.id} and creation_date {goal1.creation_date}")

    time.sleep(0.01) # Ensure distinct creation_date for ordering test if system clock resolution is low

    goal2 = create_goal(db, user_id=user_id, name="New Laptop", target_amount=1500.0, current_amount=100.0)
    assert goal2 is not None and goal2.current_amount == 100.0, "Goal 'New Laptop' creation with initial amount failed"
    print(f"Goal 2 '{goal2.name}' created with ID {goal2.id} and creation_date {goal2.creation_date}")
    print("Goals created.")


    print("Testing fetching goals for user...")
    user_goals = get_goals_by_user(db, user_id=user_id)
    assert len(user_goals) == 2, f"Expected 2 goals, got {len(user_goals)}"
    # Goals are ordered by creation_date desc by default in get_goals_by_user
    if user_goals: # Add check to prevent index error if no goals
        assert user_goals[0].name == "New Laptop", f"Order incorrect, expected New Laptop first, got {user_goals[0].name}"
        assert user_goals[1].name == "Vacation Fund", f"Order incorrect, expected Vacation Fund second, got {user_goals[1].name}"
    print("Goals fetched and order verified.")

    print("Testing fetching goal by ID...")
    fetched_goal = get_goal_by_id(db, goal_id=goal1.id, user_id=user_id)
    assert fetched_goal is not None and fetched_goal.name == "Vacation Fund"
    print("Goal fetched by ID.")

    print("Testing goal update...")
    new_target_date = datetime.datetime.now() + datetime.timedelta(days=60)
    updated_goal = update_goal(db, goal_id=goal1.id, user_id=user_id, name="Dream Vacation", current_amount=50.0, target_date=new_target_date)
    assert updated_goal is not None
    assert updated_goal.name == "Dream Vacation"
    assert updated_goal.current_amount == 50.0
    # Compare date part only if that's the intention, or ensure time part is consistent
    assert updated_goal.target_date.date() == new_target_date.date()

    # Test clearing target_date
    update_goal(db, goal_id=goal1.id, user_id=user_id, clear_target_date=True)
    refetched_goal1 = get_goal_by_id(db, goal1.id, user_id=user_id)
    assert refetched_goal1.target_date is None, "Target date was not cleared."
    print("Goal updated, including clearing target date.")


    print("Testing goal progress update...")
    # current amount for goal1 (Dream Vacation) is 50.0
    progress_updated_goal = update_goal_progress(db, goal_id=goal1.id, user_id=user_id, contributed_amount=100.0)
    assert progress_updated_goal is not None and progress_updated_goal.current_amount == 150.0 # 50 + 100
    print("Goal progress updated.")

    print("Testing goal deletion...")
    del_goal_result = delete_goal(db, goal_id=goal1.id, user_id=user_id)
    assert del_goal_result is True, "Goal deletion failed for goal1"
    assert get_goal_by_id(db, goal1.id, user_id) is None, "Deleted goal1 still found"

    remaining_goals = get_goals_by_user(db, user_id=user_id)
    assert len(remaining_goals) == 1, f"Expected 1 goal after deleting one, got {len(remaining_goals)}"
    assert remaining_goals[0].id == goal2.id, "Incorrect goal remaining after deletion."
    print("Goal deleted successfully.")

    # Clean up remaining goal and test user
    print(f"Cleaning up remaining goal ID {goal2.id} and user ID {user_id}")
    db.delete(goal2)
    db.delete(user) # User created in this test run
    db.commit()
    print(f"Test user {test_username} and related data cleaned up.")

    db.close()
    print("Goal management core logic tests completed successfully.")

if __name__ == "__main__":
    run_goal_tests()
