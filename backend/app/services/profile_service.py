from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.models.models import Profile, MedicalHistory, Allergy, Preference, HabitHistory
from app.repositories.repositories import (
    ProfileRepository, MedicalHistoryRepository, AllergyRepository, PreferenceRepository, HabitHistoryRepository
)
from app.schemas.schemas import ProfileCreate, ProfileUpdate, MedicalHistoryCreate

class ProfileService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.profile_repo = ProfileRepository(db)
        self.medical_repo = MedicalHistoryRepository(db)
        self.allergy_repo = AllergyRepository(db)
        self.pref_repo = PreferenceRepository(db)
        self.habit_repo = HabitHistoryRepository(db)

    async def get_profile(self, user_id: int) -> Optional[Profile]:
        return await self.profile_repo.get_by_user_id(user_id)

    async def create_or_update_profile(self, user_id: int, profile_in: ProfileCreate) -> Profile:
        existing = await self.profile_repo.get_by_user_id(user_id)
        
        # Calculate BMI
        height_m = profile_in.height / 100.0
        bmi = round(profile_in.weight / (height_m * height_m), 1) if height_m > 0 else 0.0
        
        # Check vegetarian status
        is_veg = profile_in.food_preference.lower() in ["vegetarian", "vegan", "veg (with egg)"]
        
        if existing:
            existing.name = profile_in.name
            existing.age = profile_in.age
            existing.gender = profile_in.gender
            existing.height = profile_in.height
            existing.weight = profile_in.weight
            existing.bmi = bmi
            existing.native_place = profile_in.native_place
            existing.country = profile_in.country
            existing.state = profile_in.state
            existing.food_preference = profile_in.food_preference
            existing.is_vegetarian = is_veg
            existing.religion = profile_in.religion
            existing.occupation = profile_in.occupation
            existing.activity_level = profile_in.activity_level
            existing.sleep_schedule = profile_in.sleep_schedule
            existing.economic_condition = profile_in.economic_condition
            existing.regional_cuisine = profile_in.regional_cuisine
            
            await self.db.commit()
            await self.db.refresh(existing)
            profile = existing
        else:
            profile = Profile(
                user_id=user_id,
                name=profile_in.name,
                age=profile_in.age,
                gender=profile_in.gender,
                height=profile_in.height,
                weight=profile_in.weight,
                bmi=bmi,
                native_place=profile_in.native_place,
                country=profile_in.country,
                state=profile_in.state,
                food_preference=profile_in.food_preference,
                is_vegetarian=is_veg,
                religion=profile_in.religion,
                occupation=profile_in.occupation,
                activity_level=profile_in.activity_level,
                sleep_schedule=profile_in.sleep_schedule,
                economic_condition=profile_in.economic_condition,
                regional_cuisine=profile_in.regional_cuisine
            )
            profile = await self.profile_repo.create(profile)

        # Initialize HabitHistory if not exists
        habit = await self.habit_repo.get_by_user_id(user_id)
        if not habit:
            new_habit = HabitHistory(
                user_id=user_id,
                favorite_foods={},
                skipped_foods={},
                average_meal_completion_rate=1.0,
                water_intake_avg=0.0
            )
            await self.habit_repo.create(new_habit)

        return profile

    async def get_medical_history(self, user_id: int) -> Optional[MedicalHistory]:
        return await self.medical_repo.get_by_user_id(user_id)

    async def create_or_update_medical_history(
        self, user_id: int, med_in: MedicalHistoryCreate
    ) -> MedicalHistory:
        existing = await self.medical_repo.get_by_user_id(user_id)
        if existing:
            existing.diabetes = med_in.diabetes
            existing.hypertension = med_in.hypertension
            existing.heart_disease = med_in.heart_disease
            existing.kidney_disease = med_in.kidney_disease
            existing.liver_disease = med_in.liver_disease
            existing.thyroid = med_in.thyroid
            existing.cholesterol = med_in.cholesterol
            existing.arthritis = med_in.arthritis
            existing.osteoporosis = med_in.osteoporosis
            existing.digestive_disorders = med_in.digestive_disorders
            existing.others = med_in.others
            
            await self.db.commit()
            await self.db.refresh(existing)
            return existing
        else:
            med_hist = MedicalHistory(
                user_id=user_id,
                diabetes=med_in.diabetes,
                hypertension=med_in.hypertension,
                heart_disease=med_in.heart_disease,
                kidney_disease=med_in.kidney_disease,
                liver_disease=med_in.liver_disease,
                thyroid=med_in.thyroid,
                cholesterol=med_in.cholesterol,
                arthritis=med_in.arthritis,
                osteoporosis=med_in.osteoporosis,
                digestive_disorders=med_in.digestive_disorders,
                others=med_in.others
            )
            return await self.medical_repo.create(med_hist)

    async def get_allergies(self, user_id: int) -> List[Allergy]:
        return await self.allergy_repo.get_by_user_id(user_id)

    async def update_allergies(self, user_id: int, allergies_list: List[str]) -> List[Allergy]:
        await self.allergy_repo.delete_by_user_id(user_id)
        
        result_allergies = []
        for name in allergies_list:
            if name.strip():
                allergy = Allergy(user_id=user_id, allergy_name=name.strip())
                created = await self.allergy_repo.create(allergy)
                result_allergies.append(created)
        return result_allergies

    async def get_preferences(self, user_id: int) -> List[Preference]:
        return await self.pref_repo.get_by_user_id(user_id)

    async def update_preferences(
        self, user_id: int, likes: List[str], dislikes: List[str]
    ) -> List[Preference]:
        await self.pref_repo.delete_by_user_id(user_id)
        
        result_prefs = []
        for item in likes:
            if item.strip():
                pref = Preference(user_id=user_id, like_dislike="LIKE", food_item=item.strip())
                created = await self.pref_repo.create(pref)
                result_prefs.append(created)
                
        for item in dislikes:
            if item.strip():
                pref = Preference(user_id=user_id, like_dislike="DISLIKE", food_item=item.strip())
                created = await self.pref_repo.create(pref)
                result_prefs.append(created)
                
        return result_prefs
