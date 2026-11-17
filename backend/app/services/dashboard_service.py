import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.models import Profile, MedicalHistory, MealPlan, MealLog
from app.repositories.repositories import (
    ProfileRepository, MedicalHistoryRepository, MealPlanRepository, MealLogRepository
)
from app.schemas.schemas import DashboardResponse, DailyNutritionSummary

class DashboardService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.profile_repo = ProfileRepository(db)
        self.med_repo = MedicalHistoryRepository(db)
        self.plan_repo = MealPlanRepository(db)
        self.log_repo = MealLogRepository(db)

    async def get_dashboard_data(self, user_id: int, date: str) -> DashboardResponse:
        profile = await self.profile_repo.get_by_user_id(user_id)
        if not profile:
            raise ValueError("Profile not found")

        meds = await self.med_repo.get_by_user_id(user_id)
        
        # 1. BMI from current height (cm) and weight (kg)
        height_m = (profile.height or 0) / 100.0
        if height_m > 0 and (profile.weight or 0) > 0:
            bmi = round(profile.weight / (height_m * height_m), 1)
        else:
            bmi = round(float(profile.bmi or 0), 1)
        if bmi < 18.5:
            bmi_status = "Underweight"
        elif bmi < 25.0:
            bmi_status = "Normal"
        elif bmi < 30.0:
            bmi_status = "Overweight"
        else:
            bmi_status = "Obese"

        # 2. Get today's plan
        plan = await self.plan_repo.get_by_date(user_id, date)
        logs = await self.log_repo.get_by_date(user_id, date)

        # 3. Calculate nutrient consumption
        logged_cal = 0.0
        logged_prot = 0.0
        logged_carbs = 0.0
        logged_fat = 0.0
        logged_fib = 0.0
        total_water = 0
        
        warnings = []
        extra_sweet_count = 0
        extra_salted_count = 0

        # Build plan map for quick access
        plan_meals = {m.category: m for m in plan.meals} if plan else {}
        
        logged_meals_count = 0
        completed_meals_weight = 0.0
        
        for log in logs:
            if log.meal_category == "WATER_TRACKER":
                total_water += log.water_intake_ml
                continue
                
            logged_meals_count += 1
            weight = 0.0
            if log.status == "FULL":
                weight = 1.0
            elif log.status == "HALF":
                weight = 0.5
            
            completed_meals_weight += weight
            total_water += log.water_intake_ml
            
            # Add nutrients from plan
            planned_meal = plan_meals.get(log.meal_category)
            if planned_meal:
                logged_cal += planned_meal.calories * weight
                logged_prot += planned_meal.protein * weight
                logged_carbs += planned_meal.carbohydrates * weight
                logged_fat += planned_meal.fat * weight
                logged_fib += planned_meal.fiber * weight

            # Add nutrients from extra foods
            if log.extra_foods_consumed:
                for extra in log.extra_foods_consumed:
                    name = extra.get("name", "").lower()
                    qty_str = extra.get("quantity", "1 pc")
                    
                    # Estimate extra food values
                    # Simple heuristic parser
                    ext_cal = 120.0
                    ext_prot = 2.0
                    ext_carb = 15.0
                    ext_fat = 4.0
                    
                    if "sweet" in name or "sugar" in name or "jalebi" in name or "gulab" in name or "chocolate" in name:
                        ext_cal = 200.0
                        ext_carb = 35.0
                        ext_fat = 8.0
                        ext_prot = 1.0
                        extra_sweet_count += 1
                    elif "samosa" in name or "pakora" in name or "fried" in name or "papad" in name or "pickle" in name:
                        ext_cal = 250.0
                        ext_carb = 25.0
                        ext_fat = 15.0
                        ext_prot = 3.0
                        extra_salted_count += 1
                    elif "egg" in name:
                        ext_cal = 78.0
                        ext_prot = 6.0
                        ext_carb = 0.6
                        ext_fat = 5.0
                    elif "milk" in name:
                        ext_cal = 100.0
                        ext_prot = 5.0
                        ext_carb = 8.0
                        ext_fat = 3.0
                        
                    logged_cal += ext_cal
                    logged_prot += ext_prot
                    logged_carbs += ext_carb
                    logged_fat += ext_fat

        # Target thresholds
        target_calories = 2000.0 if profile.gender.lower() == "male" else 1700.0
        target_protein = 60.0 if not (meds and meds.kidney_disease) else 45.0
        target_carbs = 240.0 if not (meds and meds.diabetes) else 180.0
        target_fat = 60.0 if not (meds and meds.heart_disease) else 45.0
        target_fiber = 28.0

        meal_completion_rate = (completed_meals_weight / logged_meals_count * 100.0) if logged_meals_count > 0 else 0.0

        # Calculate Weekly Trends (Last 7 Days)
        weekly_water = {}
        weekly_completion = {}
        
        today_dt = datetime.datetime.strptime(date, "%Y-%m-%d").date()
        for i in range(6, -1, -1):
            day_dt = today_dt - datetime.timedelta(days=i)
            day_str = day_dt.strftime("%Y-%m-%d")
            day_name = day_dt.strftime("%a") # e.g. Mon, Tue
            
            day_logs = await self.log_repo.get_by_date(user_id, day_str)
            
            # Water sum
            day_water = sum(l.water_intake_ml for l in day_logs)
            weekly_water[day_name] = day_water
            
            # Completion
            day_meals = [l for l in day_logs if l.meal_category != "WATER_TRACKER"]
            if day_meals:
                sc_map = {"FULL": 1.0, "HALF": 0.5, "SKIPPED": 0.0}
                day_score = sum(sc_map.get(l.status, 0.0) for l in day_meals)
                weekly_completion[day_name] = round((day_score / len(day_meals)) * 100.0, 1)
            else:
                weekly_completion[day_name] = 0.0

        # Generate warnings
        if meds:
            if meds.diabetes and extra_sweet_count > 0:
                warnings.append("Alert: You logged sweet/sugary items today. As a diabetic, please avoid sweets to maintain stable blood sugar levels.")
            if meds.hypertension and extra_salted_count > 0:
                warnings.append("Alert: Extra salted/fried foods logged. High sodium increases blood pressure.")
            if meds.kidney_disease and logged_prot > target_protein:
                warnings.append("Alert: Protein intake has exceeded recommended kidney-safe limits. Try reducing lentils or dairy later today.")
                
        if total_water < 1500:
            warnings.append(f"Reminder: Hydration level is low ({total_water} ml). Drink at least 1.5 - 2 liters of fluids daily to prevent dehydration.")
        if logged_meals_count > 0 and meal_completion_rate < 40.0:
            warnings.append("Note: Meal completion is very low. Please ensure regular eating to meet nutrient demands.")

        nutr_summary = DailyNutritionSummary(
            target_calories=target_calories,
            logged_calories=round(logged_cal, 1),
            target_protein=target_protein,
            logged_protein=round(logged_prot, 1),
            target_carbs=target_carbs,
            logged_carbs=round(logged_carbs, 1),
            target_fat=target_fat,
            logged_fat=round(logged_fat, 1),
            target_fiber=target_fiber,
            logged_fiber=round(logged_fib, 1)
        )

        return DashboardResponse(
            bmi=bmi,
            bmi_status=bmi_status,
            calories_today=round(logged_cal, 1),
            protein_today=round(logged_prot, 1),
            meal_completion_rate=round(meal_completion_rate, 1),
            water_intake_ml=total_water,
            weekly_water=weekly_water,
            weekly_completion=weekly_completion,
            daily_nutrition=nutr_summary,
            warnings=warnings
        )
