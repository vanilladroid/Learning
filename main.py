from budget_planner.models.database import engine, init_db
from budget_planner.models.data_models import create_tables

if __name__ == "__main__":
    print("Initializing database and creating tables...")
    # init_db() # init_db in the template doesn't create tables
    create_tables(engine) # Explicitly create tables
    print("Database initialized and tables created (if they didn't exist).")
    print("Run this script again to ensure it doesn't crash, but it won't recreate tables.")
