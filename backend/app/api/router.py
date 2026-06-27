from fastapi import APIRouter
from app.api import auth, profile, planner, tracker, chat, dashboard

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(profile.router, prefix="/profile", tags=["profile"])
api_router.include_router(planner.router, prefix="/planner", tags=["planner"])
api_router.include_router(tracker.router, prefix="/tracker", tags=["tracker"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
