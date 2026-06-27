from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete
from typing import List, Optional, Type, TypeVar, Generic
from app.models.models import User, Profile, MedicalHistory, Allergy, Preference, MealPlan, Meal, MealLog, HabitHistory, ChatHistory, Recommendation

T = TypeVar('T')

class BaseRepository(Generic[T]):
    def __init__(self, model: Type[T], db: AsyncSession):
        self.model = model
        self.db = db

    async def get(self, id: int) -> Optional[T]:
        result = await self.db.execute(select(self.model).filter(self.model.id == id))
        return result.scalars().first()

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        result = await self.db.execute(select(self.model).offset(skip).limit(limit))
        return result.scalars().all()

    async def create(self, obj_in: T) -> T:
        self.db.add(obj_in)
        await self.db.commit()
        await self.db.refresh(obj_in)
        return obj_in

    async def delete(self, id: int) -> bool:
        db_obj = await self.get(id)
        if db_obj:
            await self.db.delete(db_obj)
            await self.db.commit()
            return True
        return False


class UserRepository(BaseRepository[User]):
    def __init__(self, db: AsyncSession):
        super().__init__(User, db)

    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self.db.execute(select(User).filter(User.email == email))
        return result.scalars().first()


class ProfileRepository(BaseRepository[Profile]):
    def __init__(self, db: AsyncSession):
        super().__init__(Profile, db)

    async def get_by_user_id(self, user_id: int) -> Optional[Profile]:
        result = await self.db.execute(select(Profile).filter(Profile.user_id == user_id))
        return result.scalars().first()


class MedicalHistoryRepository(BaseRepository[MedicalHistory]):
    def __init__(self, db: AsyncSession):
        super().__init__(MedicalHistory, db)

    async def get_by_user_id(self, user_id: int) -> Optional[MedicalHistory]:
        result = await self.db.execute(select(MedicalHistory).filter(MedicalHistory.user_id == user_id))
        return result.scalars().first()


class AllergyRepository(BaseRepository[Allergy]):
    def __init__(self, db: AsyncSession):
        super().__init__(Allergy, db)

    async def get_by_user_id(self, user_id: int) -> List[Allergy]:
        result = await self.db.execute(select(Allergy).filter(Allergy.user_id == user_id))
        return result.scalars().all()

    async def delete_by_user_id(self, user_id: int):
        await self.db.execute(delete(Allergy).filter(Allergy.user_id == user_id))
        await self.db.commit()


class PreferenceRepository(BaseRepository[Preference]):
    def __init__(self, db: AsyncSession):
        super().__init__(Preference, db)

    async def get_by_user_id(self, user_id: int) -> List[Preference]:
        result = await self.db.execute(select(Preference).filter(Preference.user_id == user_id))
        return result.scalars().all()

    async def delete_by_user_id(self, user_id: int):
        await self.db.execute(delete(Preference).filter(Preference.user_id == user_id))
        await self.db.commit()


class MealPlanRepository(BaseRepository[MealPlan]):
    def __init__(self, db: AsyncSession):
        super().__init__(MealPlan, db)

    async def get_by_date(self, user_id: int, date: str) -> Optional[MealPlan]:
        result = await self.db.execute(
            select(MealPlan)
            .filter(MealPlan.user_id == user_id, MealPlan.date == date)
        )
        plan = result.scalars().first()
        if plan:
            # Eager load meals
            meals_result = await self.db.execute(
                select(Meal).filter(Meal.meal_plan_id == plan.id)
            )
            plan.meals = meals_result.scalars().all()
        return plan


class MealLogRepository(BaseRepository[MealLog]):
    def __init__(self, db: AsyncSession):
        super().__init__(MealLog, db)

    async def get_by_date(self, user_id: int, date: str) -> List[MealLog]:
        result = await self.db.execute(
            select(MealLog).filter(MealLog.user_id == user_id, MealLog.date == date)
        )
        return result.scalars().all()

    async def get_by_category(self, user_id: int, date: str, category: str) -> Optional[MealLog]:
        result = await self.db.execute(
            select(MealLog).filter(
                MealLog.user_id == user_id,
                MealLog.date == date,
                MealLog.meal_category == category
            )
        )
        return result.scalars().first()

    async def get_range(self, user_id: int, start_date: str, end_date: str) -> List[MealLog]:
        result = await self.db.execute(
            select(MealLog).filter(
                MealLog.user_id == user_id,
                MealLog.date >= start_date,
                MealLog.date <= end_date
            )
        )
        return result.scalars().all()


class HabitHistoryRepository(BaseRepository[HabitHistory]):
    def __init__(self, db: AsyncSession):
        super().__init__(HabitHistory, db)

    async def get_by_user_id(self, user_id: int) -> Optional[HabitHistory]:
        result = await self.db.execute(select(HabitHistory).filter(HabitHistory.user_id == user_id))
        return result.scalars().first()


class ChatHistoryRepository(BaseRepository[ChatHistory]):
    def __init__(self, db: AsyncSession):
        super().__init__(ChatHistory, db)

    async def get_by_user_id(self, user_id: int, limit: int = 50) -> List[ChatHistory]:
        result = await self.db.execute(
            select(ChatHistory)
            .filter(ChatHistory.user_id == user_id)
            .order_back_by_date(ChatHistory.created_at.desc()) # Note: ordering logic is handled correctly below
        )
        # Fix: order by created_at desc
        result = await self.db.execute(
            select(ChatHistory)
            .filter(ChatHistory.user_id == user_id)
            .order_by(ChatHistory.created_at.desc())
            .limit(limit)
        )
        return list(reversed(result.scalars().all()))
