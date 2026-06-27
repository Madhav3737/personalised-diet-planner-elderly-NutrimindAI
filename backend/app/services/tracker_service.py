import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.models import MealLog, HabitHistory, MealPlan, Meal
from app.repositories.repositories import MealLogRepository, HabitHistoryRepository, MealPlanRepository
from app.schemas.schemas import MealLogCreate

class TrackerService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.log_repo = MealLogRepository(db)
        self.habit_repo = HabitHistoryRepository(db)
        self.plan_repo = MealPlanRepository(db)

    async def log_meal_status(self, user_id: int, date: str, meal_category: str, log_in: MealLogCreate) -> MealLog:
        """Logs completion status of a specific meal, extra foods, and water intake."""
        existing = await self.log_repo.get_by_category(user_id, date, meal_category)
        
        if existing:
            existing.status = log_in.status
            if log_in.extra_foods_consumed is not None:
                existing.extra_foods_consumed = log_in.extra_foods_consumed
            if log_in.water_intake_ml > 0:
                existing.water_intake_ml += log_in.water_intake_ml
            
            await self.db.commit()
            await self.db.refresh(existing)
            log_result = existing
        else:
            log_result = MealLog(
                user_id=user_id,
                date=date,
                meal_category=meal_category,
                status=log_in.status,
                extra_foods_consumed=log_in.extra_foods_consumed or [],
                water_intake_ml=log_in.water_intake_ml
            )
            log_result = await self.log_repo.create(log_result)

        # Trigger habit updating
        await self._update_habits(user_id, date, meal_category, log_result)
        
        return log_result

    async def log_water(self, user_id: int, date: str, water_ml: int) -> MealLog:
        """Helper to log water intake directly."""
        # Find any existing log for this date to add water, e.g. BREAKFAST or create a dummy log
        existing_logs = await self.log_repo.get_by_date(user_id, date)
        if existing_logs:
            # Add to first log
            first_log = existing_logs[0]
            first_log.water_intake_ml += water_ml
            await self.db.commit()
            await self.db.refresh(first_log)
            log_result = first_log
        else:
            # Create a dedicated log for water tracking
            log_result = MealLog(
                user_id=user_id,
                date=date,
                meal_category="WATER_TRACKER",
                status="COMPLETED",
                extra_foods_consumed=[],
                water_intake_ml=water_ml
            )
            log_result = await self.log_repo.create(log_result)
            
        await self._update_habits(user_id, date, "WATER_TRACKER", log_result)
        return log_result

    async def get_daily_logs(self, user_id: int, date: str) -> List[MealLog]:
        return await self.log_repo.get_by_date(user_id, date)

    async def _update_habits(self, user_id: int, date: str, meal_category: str, log: MealLog):
        """Asynchronously recalculate eating habit metrics and frequencies."""
        habit = await self.habit_repo.get_by_user_id(user_id)
        if not habit:
            habit = HabitHistory(user_id=user_id, favorite_foods={}, skipped_foods={})
            habit = await self.habit_repo.create(habit)

        # 1. Update skipped foods frequency
        # If skipped, retrieve what was planned for that meal
        if log.status == "SKIPPED":
            plan = await self.plan_repo.get_by_date(user_id, date)
            if plan:
                meal_item = next((m for m in plan.meals if m.category == meal_category), None)
                if meal_item:
                    for food in meal_item.food_items:
                        name = food.get("name", "Unknown Food")
                        skipped_dict = dict(habit.skipped_foods or {})
                        skipped_dict[name] = skipped_dict.get(name, 0) + 1
                        habit.skipped_foods = skipped_dict

        # 2. Update favorite/completed foods frequency
        elif log.status == "FULL":
            plan = await self.plan_repo.get_by_date(user_id, date)
            if plan:
                meal_item = next((m for m in plan.meals if m.category == meal_category), None)
                if meal_item:
                    for food in meal_item.food_items:
                        name = food.get("name", "Unknown Food")
                        fav_dict = dict(habit.favorite_foods or {})
                        fav_dict[name] = fav_dict.get(name, 0) + 1
                        habit.favorite_foods = fav_dict

        # 3. Recalculate completion rate (completed / total logged)
        all_logs = await self.log_repo.get_range(
            user_id, 
            (datetime.date.today() - datetime.timedelta(days=30)).strftime("%Y-%m-%d"), 
            datetime.date.today().strftime("%Y-%m-%d")
        )
        if all_logs:
            score_map = {"FULL": 1.0, "HALF": 0.5, "SKIPPED": 0.0}
            total_score = sum(score_map.get(l.status, 0.0) for l in all_logs if l.meal_category != "WATER_TRACKER")
            total_count = sum(1 for l in all_logs if l.meal_category != "WATER_TRACKER")
            
            habit.average_meal_completion_rate = round(total_score / total_count, 2) if total_count > 0 else 1.0
            
            # Recalculate water average
            date_water = {}
            for l in all_logs:
                date_water[l.date] = date_water.get(l.date, 0) + l.water_intake_ml
            habit.water_intake_avg = float(round(sum(date_water.values()) / len(date_water), 1)) if date_water else 0.0
            
        await self.db.commit()
