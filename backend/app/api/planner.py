from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
import datetime
from app.core.database import get_db
from app.models.models import User
from app.schemas.schemas import MealPlanResponse
from app.services.auth_service import get_current_user
from app.services.recommendation_service import RecommendationService

router = APIRouter()

@router.get("/generate-plan", response_model=MealPlanResponse)
async def generate_plan(
    date: str = Query(None, description="Format YYYY-MM-DD"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not date:
        date = datetime.date.today().strftime("%Y-%m-%d")
        
    rec_service = RecommendationService(db)
    try:
        plan = await rec_service.generate_daily_plan(current_user.id, date)
        return plan
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while generating your diet recommendation: {e}"
        )

@router.get("/recommendation", response_model=MealPlanResponse)
async def get_current_recommendation(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve the recommendation for today (triggers generation if it doesn't exist)."""
    date = datetime.date.today().strftime("%Y-%m-%d")
    rec_service = RecommendationService(db)
    try:
        return await rec_service.generate_daily_plan(current_user.id, date)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
