from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import pathlib

from budget_planner.api.routers import auth, categories, transactions, goals
from budget_planner.models.database import engine #, Base # create_tables is in dependencies

# Base.metadata.create_all(bind=engine) # Ensure tables are created (also done in dependencies)

app = FastAPI(
    title="Budget Planner API",
    description="API for managing personal budgets, categories, and transactions.",
    version="0.1.0"
)

# Determine base path for static files and templates
# Assumes this script is in budget_planner/api/main.py
# So, web_ui is ../web_ui relative to this file's parent directory
BASE_DIR = pathlib.Path(__file__).resolve().parent.parent # This should be budget_planner directory
WEB_UI_DIR = BASE_DIR / "web_ui"

app.mount("/static", StaticFiles(directory=WEB_UI_DIR / "static"), name="static")
templates = Jinja2Templates(directory=WEB_UI_DIR / "templates")

app.include_router(auth.router)
app.include_router(categories.router)
app.include_router(transactions.router)
app.include_router(goals.router)

# Serve index.html from the root of the web UI part, not API root
@app.get("/", response_class=HTMLResponse)
async def serve_index(request: Request):
    # This / is the API root, maybe we want a dedicated path for the UI's index.html
    # For now, let's make API root show the UI index.
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/ui", response_class=HTMLResponse)
async def serve_ui_explicitly(request: Request):
    # An explicit path for the UI's entry point
    return templates.TemplateResponse("index.html", {"request": request})


# Original API root message, if you want to keep it separate
# @app.get("/api-status")
# async def api_status():
#    return {"message": "Welcome to the Budget Planner API!"}

# To run the app (from the project root directory):
# uvicorn budget_planner.api.main:app --reload --port 8000
# Access UI at http://localhost:8000/ or http://localhost:8000/ui
# Access API docs at http://localhost:8000/docs
