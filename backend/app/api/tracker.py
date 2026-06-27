from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
import datetime
from typing import List
from app.core.database import get_db
from app.models.models import User
from app.schemas.schemas import MealLogCreate, MealLogResponse, WaterLogCreate
from app.services.auth_service import get_current_user
from app.services.tracker_service import TrackerService

router = APIRouter()

@router.post("/log-meal", response_model=MealLogResponse)
async def log_meal(
    log_in: MealLogCreate,
    date: str = Query(None, description="Format YYYY-MM-DD"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not date:
        date = datetime.date.today().strftime("%Y-%m-%d")
        
    tracker = TrackerService(db)
    return await tracker.log_meal_status(current_user.id, date, log_in.meal_category, log_in)

@router.post("/update-meal", response_model=MealLogResponse)
async def update_meal(
    log_in: MealLogCreate,
    date: str = Query(None, description="Format YYYY-MM-DD"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Log meal behaves as upsert, so update-meal can map to the exact same logic
    if not date:
        date = datetime.date.today().strftime("%Y-%m-%d")
        
    tracker = TrackerService(db)
    return await tracker.log_meal_status(current_user.id, date, log_in.meal_category, log_in)

@router.post("/water", response_model=MealLogResponse)
async def log_water(
    water_in: WaterLogCreate,
    date: str = Query(None, description="Format YYYY-MM-DD"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not date:
        date = datetime.date.today().strftime("%Y-%m-%d")
        
    tracker = TrackerService(db)
    return await tracker.log_water(current_user.id, date, water_in.water_intake_ml)

@router.get("/history", response_model=List[MealLogResponse])
async def get_history(
    date: str = Query(None, description="Format YYYY-MM-DD"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not date:
        date = datetime.date.today().strftime("%Y-%m-%d")
        
    tracker = TrackerService(db)
    return await tracker.get_daily_logs(current_user.id, date)
