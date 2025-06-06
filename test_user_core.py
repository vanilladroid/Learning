from budget_planner.models.database import SessionLocal, engine
from budget_planner.models.data_models import create_tables, User
from budget_planner.core.user_management import create_user, authenticate_user, get_user_by_username, verify_password

def run_user_tests():
    print("Running user management core logic tests...")
    # Ensure tables are created
    create_tables(engine)

    db = SessionLocal()

    # Test user creation
    print("Testing user creation...")
    test_username = "testuser1"
    test_password = "testpassword123"

    # Clean up if user exists from previous failed run
    existing_user = get_user_by_username(db, test_username)
    if existing_user:
        print(f"User {test_username} already exists, deleting for test.")
        db.delete(existing_user)
        db.commit()

    created_user = create_user(db, username=test_username, password=test_password)
    assert created_user is not None, "User creation failed."
    assert created_user.username == test_username, "Created username does not match."
    print(f"User {created_user.username} created successfully with ID {created_user.id}.")

    # Test creating a duplicate user
    print("Testing duplicate user creation...")
    duplicate_user = create_user(db, username=test_username, password="anotherpassword")
    assert duplicate_user is None, "Duplicate user creation should fail."
    print("Duplicate user creation correctly prevented.")

    # Test fetching user
    print("Testing fetching user...")
    fetched_user = get_user_by_username(db, test_username)
    assert fetched_user is not None, "Fetching user failed."
    assert fetched_user.username == test_username, "Fetched username does not match."
    print(f"User {fetched_user.username} fetched successfully.")

    # Test password verification
    print("Testing password verification...")
    assert verify_password(test_password, fetched_user.password_hash), "Password verification failed for correct password."
    assert not verify_password("wrongpassword", fetched_user.password_hash), "Password verification succeeded for incorrect password."
    print("Password verification works as expected.")

    # Test authentication
    print("Testing authentication...")
    authenticated_user = authenticate_user(db, username=test_username, password=test_password)
    assert authenticated_user is not None, "Authentication failed for correct credentials."
    assert authenticated_user.username == test_username, "Authenticated username does not match."
    print(f"User {authenticated_user.username} authenticated successfully.")

    unauthenticated_user = authenticate_user(db, username=test_username, password="wrongpassword")
    assert unauthenticated_user is None, "Authentication succeeded for incorrect password."
    print("Authentication correctly failed for incorrect password.")

    non_existent_user = authenticate_user(db, username="nosuchuser", password="password")
    assert non_existent_user is None, "Authentication succeeded for non-existent user."
    print("Authentication correctly failed for non-existent user.")

    # Clean up test user
    db.delete(fetched_user)
    db.commit()
    print(f"Test user {test_username} cleaned up.")

    db.close()
    print("User management core logic tests completed successfully.")

if __name__ == "__main__":
    run_user_tests()
