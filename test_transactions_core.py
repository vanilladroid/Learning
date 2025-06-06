import datetime
from budget_planner.models.database import SessionLocal, engine
from budget_planner.models.data_models import create_tables, User, Category, Transaction, TransactionType
from budget_planner.core.user_management import create_user, get_user_by_username # For test setup
from budget_planner.core.transaction_management import (
    create_category, get_categories_by_user, get_category_by_name, update_category, delete_category, get_category_by_id,
    create_transaction, get_transactions_by_user, get_transaction_by_id, update_transaction, delete_transaction
)

def run_transaction_tests():
    print("Running transaction and category management core logic tests...")
    create_tables(engine) # Ensure tables are created

    db = SessionLocal()

    # --- Test User Setup ---
    test_username = "tx_user1"
    test_password = "tx_password123"
    user = get_user_by_username(db, test_username)
    if user: # Clean up existing user and their data for idempotency
        db.query(Transaction).filter(Transaction.user_id == user.id).delete()
        db.query(Category).filter(Category.user_id == user.id).delete()
        db.delete(user)
        db.commit()
    user = create_user(db, username=test_username, password=test_password)
    assert user is not None, "Test user setup failed."
    user_id = user.id
    print(f"Test user '{test_username}' set up with ID: {user_id}")

    # --- Category Tests ---
    print("Testing category creation...")
    cat1 = create_category(db, name="Groceries", user_id=user_id)
    assert cat1 is not None and cat1.name == "Groceries", "Category 'Groceries' creation failed"
    cat2 = create_category(db, name="Salary", user_id=user_id)
    assert cat2 is not None and cat2.name == "Salary", "Category 'Salary' creation failed"
    print("Categories created.")

    print("Testing duplicate category creation (should fail)...")
    cat_dup = create_category(db, name="Groceries", user_id=user_id) # Case-insensitive check in function
    assert cat_dup is None, "Duplicate category 'Groceries' was created."
    cat_dup_case = create_category(db, name="groceries", user_id=user_id)
    assert cat_dup_case is None, "Duplicate category 'groceries' (case) was created."
    print("Duplicate category creation prevented.")

    print("Testing fetching categories for user...")
    user_cats = get_categories_by_user(db, user_id=user_id)
    assert len(user_cats) == 2, f"Expected 2 categories, got {len(user_cats)}"
    assert "Groceries" in [c.name for c in user_cats], "Groceries category not found"
    print("Categories fetched.")

    print("Testing fetching category by name...")
    fetched_cat_g = get_category_by_name(db, name="Groceries", user_id=user_id)
    assert fetched_cat_g is not None and fetched_cat_g.id == cat1.id
    fetched_cat_s = get_category_by_name(db, name="SALARY", user_id=user_id) # Test case-insensitivity
    assert fetched_cat_s is not None and fetched_cat_s.id == cat2.id
    print("Category fetched by name.")

    print("Testing category update...")
    updated_cat = update_category(db, category_id=cat1.id, user_id=user_id, name="Supermarket")
    assert updated_cat is not None and updated_cat.name == "Supermarket", "Category update failed"
    assert get_category_by_id(db, cat1.id, user_id).name == "Supermarket"
    print("Category updated.")

    print("Testing category update conflict...")
    # Try updating 'Supermarket' (cat1) to 'Salary' (cat2's name)
    conflict_update_cat = update_category(db, category_id=cat1.id, user_id=user_id, name="Salary")
    assert conflict_update_cat is None, "Category update conflict not handled"
    print("Category update conflict handled.")


    # --- Transaction Tests ---
    print("Testing transaction creation...")
    tx1_date = datetime.datetime.now() - datetime.timedelta(days=1)
    tx1 = create_transaction(db, amount=50.0, type=TransactionType.EXPENSE, date=tx1_date,
                             user_id=user_id, category_id=cat1.id, description="Weekly shopping")
    assert tx1 is not None and tx1.amount == 50.0, "Transaction 1 creation failed"

    tx2_date = datetime.datetime.now()
    tx2 = create_transaction(db, amount=2000.0, type=TransactionType.INCOME, date=tx2_date,
                             user_id=user_id, category_id=cat2.id, description="Monthly pay")
    assert tx2 is not None and tx2.amount == 2000.0, "Transaction 2 creation failed"
    print("Transactions created.")

    print("Testing transaction creation with invalid category for user...")
    other_user = create_user(db, "other_user_tx", "pass")
    other_cat = create_category(db, "Other Cat", other_user.id)
    invalid_tx = create_transaction(db, amount=10, type=TransactionType.EXPENSE, date=datetime.datetime.now(),
                                    user_id=user_id, category_id=other_cat.id, description="Bad cat")
    assert invalid_tx is None, "Transaction creation with invalid category should fail"
    print("Transaction creation with invalid category prevented.")


    print("Testing fetching transactions for user...")
    user_txs = get_transactions_by_user(db, user_id=user_id)
    assert len(user_txs) == 2, f"Expected 2 transactions, got {len(user_txs)}"
    # Transactions are ordered by date desc
    assert user_txs[0].id == tx2.id # tx2 is more recent
    assert user_txs[1].id == tx1.id
    print("Transactions fetched.")

    print("Testing fetching transaction by ID...")
    fetched_tx = get_transaction_by_id(db, transaction_id=tx1.id, user_id=user_id)
    assert fetched_tx is not None and fetched_tx.description == "Weekly shopping"
    print("Transaction fetched by ID.")

    print("Testing transaction update...")
    updated_tx = update_transaction(db, transaction_id=tx1.id, user_id=user_id, amount=55.0, description="Updated shopping")
    assert updated_tx is not None and updated_tx.amount == 55.0 and updated_tx.description == "Updated shopping"
    assert get_transaction_by_id(db, tx1.id, user_id).amount == 55.0
    print("Transaction updated.")

    print("Testing transaction update with category change to invalid category...")
    fail_update_tx = update_transaction(db, transaction_id=tx1.id, user_id=user_id, category_id=other_cat.id)
    assert fail_update_tx is None, "Transaction update to invalid category should fail"
    assert get_transaction_by_id(db, tx1.id, user_id).category_id == cat1.id # Ensure it didn't change
    print("Transaction update to invalid category prevented.")

    # --- Deletion Tests (Transaction first, then Category) ---
    print("Testing transaction deletion...")
    del_tx_result = delete_transaction(db, transaction_id=tx1.id, user_id=user_id)
    assert del_tx_result is True, "Transaction deletion failed"
    assert get_transaction_by_id(db, tx1.id, user_id) is None, "Deleted transaction still found"
    assert len(get_transactions_by_user(db, user_id=user_id)) == 1
    print("Transaction deleted.")

    print("Testing category deletion (with linked transaction - should fail)...")
    # cat2 (Salary) still has tx2 linked
    del_cat_fail_result = delete_category(db, category_id=cat2.id, user_id=user_id)
    assert del_cat_fail_result is False, "Category deletion with linked transaction should not succeed"
    assert get_category_by_id(db, cat2.id, user_id) is not None, "Category was deleted despite linked transaction"
    print("Category deletion with linked transaction correctly prevented.")

    # Delete the remaining transaction, then the category
    delete_transaction(db, transaction_id=tx2.id, user_id=user_id) # tx2 linked to cat2

    print("Testing category deletion (no linked transactions - should succeed)...")
    # cat1 (Supermarket) should have no linked transactions now
    # Need to get its ID again as it was updated
    supermarket_cat_id = get_category_by_name(db, "Supermarket", user_id).id
    del_cat_supermarket_result = delete_category(db, category_id=supermarket_cat_id, user_id=user_id)
    assert del_cat_supermarket_result is True, "Category 'Supermarket' deletion failed"
    assert get_category_by_id(db, supermarket_cat_id, user_id) is None, "Deleted category 'Supermarket' still found"

    del_cat_salary_result = delete_category(db, category_id=cat2.id, user_id=user_id)
    assert del_cat_salary_result is True, "Category 'Salary' deletion failed"
    assert get_category_by_id(db, cat2.id, user_id) is None, "Deleted category 'Salary' still found"
    print("Categories without linked transactions deleted.")

    # Cleanup test users
    db.delete(user)
    # Need to explicitly delete other_user's category if it wasn't deleted before other_user
    if other_cat:
        db.delete(other_cat)
    if other_user:
        db.delete(other_user)
    db.commit()
    print(f"Test user {test_username} and related data cleaned up.")

    db.close()
    print("Transaction and category management core logic tests completed successfully.")

if __name__ == "__main__":
    run_transaction_tests()
