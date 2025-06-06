import datetime
from decimal import Decimal # For precise assertions if needed, though models use Float
from sqlalchemy.orm import Session # Import Session
from budget_planner.models.database import SessionLocal, engine
from budget_planner.models.data_models import create_tables, User, Category, Transaction, TransactionType
from budget_planner.core.user_management import create_user, get_user_by_username
from budget_planner.core.transaction_management import create_category as core_create_category
from budget_planner.core.transaction_management import create_transaction as core_create_transaction
from budget_planner.core.trend_analysis import get_monthly_summary, get_spending_trend

def setup_test_data(db: Session, user_id: int):
    # Categories
    cat_food = core_create_category(db, name="Food", user_id=user_id)
    cat_salary = core_create_category(db, name="Salary", user_id=user_id)
    cat_rent = core_create_category(db, name="Rent", user_id=user_id)
    cat_fun = core_create_category(db, name="Fun", user_id=user_id)
    assert cat_food and cat_salary and cat_rent and cat_fun, "Category creation failed in test setup"

    today = datetime.datetime.utcnow()
    current_month = today.month
    current_year = today.year

    last_month_date = today.replace(day=15) - datetime.timedelta(days=30) # Approx last month
    two_months_ago_date = today.replace(day=15) - datetime.timedelta(days=60) # Approx 2 months ago

    # Transactions for current month
    core_create_transaction(db, 2000.00, TransactionType.INCOME, today.replace(day=1), user_id, cat_salary.id, "Monthly Salary CM")
    core_create_transaction(db, 150.00, TransactionType.EXPENSE, today.replace(day=5), user_id, cat_food.id, "Groceries CM")
    core_create_transaction(db, 500.00, TransactionType.EXPENSE, today.replace(day=2), user_id, cat_rent.id, "Rent CM")
    core_create_transaction(db, 70.00, TransactionType.EXPENSE, today.replace(day=10), user_id, cat_fun.id, "Movies CM")
    core_create_transaction(db, 30.00, TransactionType.EXPENSE, today.replace(day=12), user_id, cat_food.id, "Eating out CM")


    # Transactions for last month
    core_create_transaction(db, 1900.00, TransactionType.INCOME, last_month_date.replace(day=1), user_id, cat_salary.id, "Monthly Salary LM")
    core_create_transaction(db, 160.00, TransactionType.EXPENSE, last_month_date.replace(day=5), user_id, cat_food.id, "Groceries LM")
    core_create_transaction(db, 500.00, TransactionType.EXPENSE, last_month_date.replace(day=2), user_id, cat_rent.id, "Rent LM")

    # Transactions for two months ago
    core_create_transaction(db, 1800.00, TransactionType.INCOME, two_months_ago_date.replace(day=1), user_id, cat_salary.id, "Monthly Salary 2M_Ago")
    core_create_transaction(db, 170.00, TransactionType.EXPENSE, two_months_ago_date.replace(day=5), user_id, cat_food.id, "Groceries 2M_Ago")
    core_create_transaction(db, 50.00, TransactionType.EXPENSE, two_months_ago_date.replace(day=10), user_id, cat_fun.id, "Concert 2M_Ago")

    db.commit()
    print(f"Test data setup complete for user {user_id}")
    return {
        "current_month": current_month, "current_year": current_year,
        "last_month": last_month_date.month, "last_year": last_month_date.year,
        "two_months_ago_month": two_months_ago_date.month, "two_months_ago_year": two_months_ago_date.year,
        "cat_food_name": cat_food.name, "cat_rent_name": cat_rent.name, "cat_fun_name": cat_fun.name
    }

def run_trend_analysis_tests():
    print("Running trend analysis core logic tests...")
    create_tables(engine)
    db = SessionLocal()

    # --- Test User Setup ---
    test_username = "trend_user1"
    user = get_user_by_username(db, test_username)
    if user:
        print(f"Cleaning up old test user '{test_username}' and their data...")
        db.query(Transaction).filter(Transaction.user_id == user.id).delete()
        db.query(Category).filter(Category.user_id == user.id).delete()
        db.delete(user)
        db.commit()
    user = create_user(db, username=test_username, password="trend_password123")
    assert user is not None, "Test user setup failed."
    user_id = user.id
    print(f"Test user '{test_username}' set up with ID: {user_id}")

    dates_info = setup_test_data(db, user_id)

    # --- Test get_monthly_summary ---
    print("Testing get_monthly_summary for current month...")
    summary_cm = get_monthly_summary(db, user_id, dates_info["current_year"], dates_info["current_month"])
    print(f"Current month summary: {summary_cm}")
    assert summary_cm["total_income"] == 2000.00
    assert summary_cm["total_expenses"] == (150.00 + 500.00 + 70.00 + 30.00) # 750
    assert summary_cm["expenses_by_category"][dates_info["cat_food_name"]] == (150.00 + 30.00) # 180
    assert summary_cm["expenses_by_category"][dates_info["cat_rent_name"]] == 500.00
    assert summary_cm["expenses_by_category"][dates_info["cat_fun_name"]] == 70.00
    assert summary_cm["net_savings"] == (2000.00 - 750.00) # 1250

    print("Testing get_monthly_summary for last month...")
    summary_lm = get_monthly_summary(db, user_id, dates_info["last_year"], dates_info["last_month"])
    print(f"Last month summary: {summary_lm}")
    assert summary_lm["total_income"] == 1900.00
    assert summary_lm["total_expenses"] == (160.00 + 500.00) # 660
    assert summary_lm["expenses_by_category"][dates_info["cat_food_name"]] == 160.00
    assert summary_lm["net_savings"] == (1900.00 - 660.00) # 1240

    print("Testing get_monthly_summary for a month with no transactions...")
    summary_empty = get_monthly_summary(db, user_id, 1990, 1) # Assuming no data for this old date
    assert summary_empty["total_income"] == 0
    assert summary_empty["total_expenses"] == 0
    assert not summary_empty["expenses_by_category"] # Empty dict
    assert summary_empty["net_savings"] == 0

    # --- Test get_spending_trend ---
    print("Testing get_spending_trend (default 3 periods)...")
    trend_data = get_spending_trend(db, user_id=user_id) # Default 3 periods
    assert len(trend_data) == 3, f"Expected 3 periods in trend data, got {len(trend_data)}"

    # First period in trend_data should be current month's summary
    assert trend_data[0]["year"] == dates_info["current_year"]
    assert trend_data[0]["month"] == dates_info["current_month"]
    assert trend_data[0]["total_income"] == summary_cm["total_income"]
    assert trend_data[0]["total_expenses"] == summary_cm["total_expenses"]

    # Second period should be last month's summary
    assert trend_data[1]["year"] == dates_info["last_year"]
    assert trend_data[1]["month"] == dates_info["last_month"]
    assert trend_data[1]["total_income"] == summary_lm["total_income"]

    # Third period should be two months ago summary
    summary_2m_ago = get_monthly_summary(db, user_id, dates_info["two_months_ago_year"], dates_info["two_months_ago_month"])
    assert trend_data[2]["year"] == dates_info["two_months_ago_year"]
    assert trend_data[2]["month"] == dates_info["two_months_ago_month"]
    assert trend_data[2]["total_income"] == summary_2m_ago["total_income"]
    assert trend_data[2]["total_expenses"] == (170.00 + 50.00) # 220

    print("Testing get_spending_trend for 1 period...")
    trend_data_1 = get_spending_trend(db, user_id=user_id, period_count=1)
    assert len(trend_data_1) == 1
    assert trend_data_1[0]["month"] == dates_info["current_month"]


    # --- Cleanup ---
    print(f"Cleaning up test user '{test_username}' and their data...")
    db.query(Transaction).filter(Transaction.user_id == user.id).delete()
    db.query(Category).filter(Category.user_id == user.id).delete() # Categories created in setup_test_data
    db.delete(user)
    db.commit()

    db.close()
    print("Trend analysis core logic tests completed successfully.")

if __name__ == "__main__":
    run_trend_analysis_tests()
