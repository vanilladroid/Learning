from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from budget_planner.models.data_models import Transaction, TransactionType, Category, User
import datetime
from typing import Dict, List, Any

def get_monthly_summary(db: Session, user_id: int, year: int, month: int) -> Dict[str, Any]:
    """
    Calculates total income, total expenses, expenses by category, and net savings
    for a specific user, month, and year.
    """
    # Validate user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        # Or raise an exception, or return empty/error structure
        return {
            "error": "User not found",
            "year": year,
            "month": month,
            "total_income": 0,
            "total_expenses": 0,
            "expenses_by_category": {},
            "net_savings": 0
        }

    # Total Income
    total_income_query = db.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == user_id,
        Transaction.type == TransactionType.INCOME,
        extract('year', Transaction.date) == year,
        extract('month', Transaction.date) == month
    )
    total_income = total_income_query.scalar() or 0.0

    # Total Expenses
    total_expenses_query = db.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == user_id,
        Transaction.type == TransactionType.EXPENSE,
        extract('year', Transaction.date) == year,
        extract('month', Transaction.date) == month
    )
    total_expenses = total_expenses_query.scalar() or 0.0

    # Expenses by Category
    expenses_by_category_query = db.query(
        Category.name,
        func.sum(Transaction.amount)
    ).join(Transaction.category).filter(
        Transaction.user_id == user_id,
        Transaction.type == TransactionType.EXPENSE,
        extract('year', Transaction.date) == year,
        extract('month', Transaction.date) == month
    ).group_by(Category.name)

    expenses_by_category_result = expenses_by_category_query.all()
    expenses_by_category_dict = {name: amount for name, amount in expenses_by_category_result}

    net_savings = total_income - total_expenses

    return {
        "year": year,
        "month": month,
        "total_income": round(total_income, 2),
        "total_expenses": round(total_expenses, 2),
        "expenses_by_category": expenses_by_category_dict,
        "net_savings": round(net_savings, 2)
    }

def get_spending_trend(db: Session, user_id: int, period_count: int = 3) -> List[Dict[str, Any]]:
    """
    Retrieves monthly summaries for the last 'period_count' months for a given user.
    Includes the current month.
    """
    # Validate user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return [{"error": "User not found"}] # Or raise exception

    trend_data = []
    today = datetime.date.today()

    for i in range(period_count):
        # Calculate year and month for the i-th period ago
        # current_period_date is the first day of the month we are calculating for
        year_to_query = today.year
        month_to_query = today.month - i

        while month_to_query <= 0: # Adjust for year change
            month_to_query += 12
            year_to_query -= 1

        monthly_summary = get_monthly_summary(db, user_id, year_to_query, month_to_query)
        trend_data.append(monthly_summary)

    return trend_data # Data will be from most recent month to oldest
