from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
import datetime
from app.core.database import get_db
from app.models.models import User
from app.schemas.schemas import DashboardResponse, HabitHistoryResponse
from app.services.auth_service import get_current_user
from app.services.dashboard_service import DashboardService
from app.repositories.repositories import HabitHistoryRepository

router = APIRouter()

@router.get("", response_model=DashboardResponse)
async def get_dashboard(
    date: str = Query(None, description="Format YYYY-MM-DD"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not date:
        date = datetime.date.today().strftime("%Y-%m-%d")
        
    dash_service = DashboardService(db)
    try:
        return await dash_service.get_dashboard_data(current_user.id, date)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error compiling dashboard data: {e}"
        )

@router.get("/habits", response_model=HabitHistoryResponse)
async def get_habits(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    habit_repo = HabitHistoryRepository(db)
    habit = await habit_repo.get_by_user_id(current_user.id)
    if not habit:
        return HabitHistoryResponse(
            favorite_foods={},
            skipped_foods={},
            average_meal_completion_rate=1.0,
            water_intake_avg=0.0
        )
    return habit
