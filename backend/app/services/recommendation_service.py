import os
import json
import logging
import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
import numpy as np

from app.core.config import settings
from app.prompts.prompts import SYSTEM_DIETICIAN_PROMPT
from app.rag.rag_pipeline import RAGPipeline
from app.models.models import MealPlan, Meal, Profile, MedicalHistory, Allergy, Preference, MealLog
from app.repositories.repositories import (
    MealPlanRepository, ProfileRepository, MedicalHistoryRepository,
    AllergyRepository, PreferenceRepository, MealLogRepository
)

logger = logging.getLogger(__name__)

# Try importing openai, fallback if not installed/configured
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI library not installed. Falling back to rule-based template generation.")

class RecommendationService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.profile_repo = ProfileRepository(db)
        self.med_repo = MedicalHistoryRepository(db)
        self.allergy_repo = AllergyRepository(db)
        self.pref_repo = PreferenceRepository(db)
        self.log_repo = MealLogRepository(db)
        self.plan_repo = MealPlanRepository(db)
        self.rag = RAGPipeline(settings.DOCUMENTS_DIR, settings.VECTOR_DB_DIR)
        
        # Load RAG index on startup asynchronously/silently
        try:
            self.rag.load_index()
        except Exception as e:
            logger.error(f"Could not load RAG index: {e}")

        # Initialize OpenAI Client
        self.client = None
        if OPENAI_AVAILABLE and settings.OPENAI_API_KEY:
            try:
                self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
            except Exception as e:
                logger.error(f"Error initializing OpenAI client: {e}")

    async def generate_daily_plan(self, user_id: int, date: str) -> MealPlan:
        """Generates a complete, personalized 6-meal plan for the given date."""
        # 1. Fetch user data
        profile = await self.profile_repo.get_by_user_id(user_id)
        if not profile:
            raise ValueError("User profile not found. Please complete the intake wizard first.")
        
        meds = await self.med_repo.get_by_user_id(user_id)
        allergies = await self.allergy_repo.get_by_user_id(user_id)
        preferences = await self.pref_repo.get_by_user_id(user_id)
        
        # Check if plan already exists for this date
        existing_plan = await self.plan_repo.get_by_date(user_id, date)
        if existing_plan:
            return existing_plan

        # 2. Get RAG context
        # Construct search query from diseases
        disease_list = []
        if meds:
            if meds.diabetes: disease_list.append("diabetes mellitus type 2")
            if meds.hypertension: disease_list.append("hypertension high blood pressure")
            if meds.heart_disease: disease_list.append("cardiovascular heart disease")
            if meds.kidney_disease: disease_list.append("chronic kidney disease ckd")
            if meds.liver_disease: disease_list.append("liver disease cirrhosis")
            if meds.thyroid: disease_list.append("thyroid diet thyroidism")
            if meds.cholesterol: disease_list.append("high cholesterol dyslipidemia")
            if meds.arthritis: disease_list.append("arthritis anti-inflammatory joints")
            if meds.osteoporosis: disease_list.append("osteoporosis calcium vitamin d bone health")
            if meds.digestive_disorders: disease_list.append("digestive disorders gerd stomach fiber")
        
        query = f"geriatric nutrition elderly diet " + " ".join(disease_list) + f" {profile.regional_cuisine} cuisine"
        retrieved_chunks = self.rag.retrieve(query, k=3)
        rag_context = "\n\n".join([f"Source: {c['source']}\n{c['text']}" for c in retrieved_chunks])

        # 3. Check logs for today to apply compensation logic
        today_logs = await self.log_repo.get_by_date(user_id, date)
        log_summary = ""
        skipped_meals = []
        extra_sugars = False
        protein_lacking = False
        
        for l in today_logs:
            if l.status == "SKIPPED":
                skipped_meals.append(l.meal_category)
            elif l.status == "HALF":
                skipped_meals.append(f"Half-completed {l.meal_category}")
            
            # Check extra foods
            if l.extra_foods_consumed:
                for extra in l.extra_foods_consumed:
                    name = extra.get("name", "").lower()
                    if any(w in name for w in ["sweet", "sugar", "samosa", "chocolate", "cake", "ice cream", "jalebi", "gulab jamun"]):
                        extra_sugars = True
        
        if skipped_meals:
            log_summary += f"- The user partially or fully skipped: {', '.join(skipped_meals)} today. Please redistribute the missing calories/nutrition to subsequent meals.\n"
        if extra_sugars:
            log_summary += f"- The user consumed sugary/high-carb extra foods today. Reduce sugars and carbohydrates in the remaining meals.\n"

        # 4. Execute AI Generation or Fallback
        meal_plan_data = None
        if self.client:
            try:
                meal_plan_data = self._generate_with_llm(profile, meds, allergies, preferences, rag_context, log_summary, date)
            except Exception as e:
                logger.error(f"LLM Generation failed: {e}. Falling back to Rule-Based templates.")
        
        if not meal_plan_data:
            meal_plan_data = self._generate_rule_based(profile, meds, allergies, preferences, log_summary, date)

        # 5. Save generated plan to database
        db_plan = MealPlan(user_id=user_id, date=date)
        self.db.add(db_plan)
        await self.db.commit()
        await self.db.refresh(db_plan)

        for m_data in meal_plan_data["meals"]:
            db_meal = Meal(
                meal_plan_id=db_plan.id,
                category=m_data["category"],
                food_items=m_data["food_items"],
                calories=m_data["calories"],
                protein=m_data["protein"],
                carbohydrates=m_data["carbohydrates"],
                fat=m_data["fat"],
                fiber=m_data["fiber"],
                cost=m_data.get("cost", 0.0),
                selection_reason=m_data.get("selection_reason", "")
            )
            self.db.add(db_meal)
        
        await self.db.commit()
        
        # Reload plan to return with populated meals relationship
        return await self.plan_repo.get_by_date(user_id, date)

    def _generate_with_llm(
        self, profile: Profile, meds: Optional[MedicalHistory],
        allergies: List[Allergy], preferences: List[Preference],
        rag_context: str, log_summary: str, date: str
    ) -> Dict[str, Any]:
        """Call OpenAI to generate structured meal plans."""
        allergies_str = ", ".join([a.allergy_name for a in allergies]) or "None"
        likes_str = ", ".join([p.food_item for p in preferences if p.like_dislike == "LIKE"]) or "None"
        dislikes_str = ", ".join([p.food_item for p in preferences if p.like_dislike == "DISLIKE"]) or "None"
        
        med_dict = {k: v for k, v in meds.__dict__.items() if not k.startswith('_') and isinstance(v, bool) and v} if meds else {}
        diseases_str = ", ".join(med_dict.keys()) or "None"

        prompt = f"""
Generate a daily diet meal plan for {date}.

USER HEALTH AND PERSONAL PROFILE:
- Name: {profile.name}
- Age: {profile.age} years old
- Gender: {profile.gender}
- BMI: {profile.bmi}
- Activity Level: {profile.activity_level}
- Regional Food Habits: {profile.regional_cuisine}
- Economic Class: {profile.economic_condition}
- Diet Type: {profile.food_preference}
- Sleep Schedule: {profile.sleep_schedule or 'Normal'}

CLINICAL RESTRICTIONS:
- Medical Conditions: {diseases_str}
- Allergies: {allergies_str}
- Likes: {likes_str}
- Dislikes (Strictly avoid): {dislikes_str}

TODAY'S DIET ADJUSTMENTS (COMPENSATION LOGIC):
{log_summary if log_summary else "No skips or extra foods logged yet today. Plan normal balanced diet."}

CLINICAL NUTRITION CONTEXT (RAG):
{rag_context}

RESPONSE FORMAT:
You MUST respond with a single, valid JSON block. Do not wrap in markdown quotes. The JSON must exactly conform to this schema:
{{
  "date": "{date}",
  "meals": [
    {{
      "category": "BREAKFAST",
      "food_items": [
        {{ "name": "Food item name", "quantity": "e.g. 2 pcs or 1 cup" }}
      ],
      "calories": 350.0,
      "protein": 12.0,
      "carbohydrates": 45.0,
      "fat": 8.0,
      "fiber": 5.0,
      "cost": 30.0,
      "selection_reason": "Provide short medical reasoning (e.g., oats are rich in soluble fiber which stabilizes blood sugar in diabetes)."
    }},
    ... (continue for MORNING_SNACK, LUNCH, EVENING_SNACK, DINNER, BEDTIME)
  ]
}}
"""
        response = self.client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_DIETICIAN_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content
        return json.loads(content)

    def _generate_rule_based(
        self, profile: Profile, meds: Optional[MedicalHistory],
        allergies: List[Allergy], preferences: List[Preference],
        log_summary: str, date: str
    ) -> Dict[str, Any]:
        """Rules-based fallback meal planner generating custom diets based on inputs."""
        logger.info("Executing rule-based plan generator.")
        
        # Basic parameters
        is_veg = profile.is_vegetarian
        budget = profile.economic_condition.upper() # LOW, MEDIUM, HIGH
        cuisine = profile.regional_cuisine.lower()
        
        # Check medical states
        has_diabetes = meds.diabetes if meds else False
        has_hypertension = meds.hypertension if meds else False
        has_kidney = meds.kidney_disease if meds else False
        has_heart = meds.heart_disease if meds else False
        
        # Gather dislikes & allergies to filter items
        avoid_items = [a.allergy_name.lower() for a in allergies] + [p.food_item.lower() for p in preferences if p.like_dislike == "DISLIKE"]
        
        # Calorie calculations: BMR/TDEE approximation for elderlies
        target_calories = 1900.0 if profile.gender.lower() == "male" else 1650.0
        if profile.activity_level.lower() == "sedentary":
            target_calories -= 150
        elif "active" in profile.activity_level.lower():
            target_calories += 150
            
        # Apply compensation logic overrides
        if "skipped" in log_summary.lower() or "half" in log_summary.lower():
            target_calories += 200 # Add a bit of compensation
            
        # Standard meal items templates
        meals = []
        
        # Build Breakfast
        bf_name = "Oats Porridge"
        bf_qty = "1 bowl"
        bf_reason = "Rich in complex fiber and slow-release carbohydrates."
        bf_cost = 25.0 if budget == "LOW" else (45.0 if budget == "MEDIUM" else 75.0)
        
        if "south indian" in cuisine or "andhra" in cuisine or "tamil" in cuisine or "kerala" in cuisine:
            if has_diabetes:
                bf_name = "Ragi Idli"
                bf_qty = "2 pcs with Mint Chutney"
                bf_reason = "Ragi (Finger Millet) is high in calcium and fiber, helping regulate glycemic levels."
            else:
                bf_name = "Steamed Rice Idli"
                bf_qty = "2 pcs with Sambar"
                bf_reason = "Light, fermented, steamed, easily digestible breakfast."
        elif "north indian" in cuisine or "punjabi" in cuisine:
            if has_diabetes:
                bf_name = "Besan (Chickpea) Chilla"
                bf_qty = "1 pc with Mint Chutney"
                bf_reason = "Chickpea flour crepe provides plant-based protein and low glycemic index energy."
            else:
                bf_name = "Wheat Dalia Porridge"
                bf_qty = "1 bowl"
                bf_reason = "Whole grain broken wheat porridge, rich in iron and B-vitamins."
        else: # Default
            if has_diabetes:
                bf_name = "Oats Upma"
                bf_qty = "1 bowl with vegetables"
                bf_reason = "High in beta-glucan soluble fiber, improving insulin sensitivity."
                
        meals.append({
            "category": "BREAKFAST",
            "food_items": [{"name": bf_name, "quantity": bf_qty}],
            "calories": target_calories * 0.22,
            "protein": 10.0 if not has_kidney else 6.0,
            "carbohydrates": 45.0 if not has_diabetes else 30.0,
            "fat": 6.0 if not has_heart else 3.5,
            "fiber": 4.5,
            "cost": bf_cost,
            "selection_reason": bf_reason
        })

        # Build Morning Snack
        ms_name = "Fresh Seasonal Banana"
        ms_qty = "1 medium"
        ms_reason = "Provides potassium and natural energy. Easily chewable for elderly."
        ms_cost = 10.0
        
        if has_diabetes:
            ms_name = "Roasted Makhana (Foxnuts)"
            ms_qty = "1 small cup"
            ms_reason = "Low glycemic index, crunchy snack rich in calcium and antioxidants."
            ms_cost = 15.0
        elif has_kidney:
            ms_name = "Apple slices"
            ms_qty = "1/2 cup"
            ms_reason = "Low potassium fruit suitable for kidney health."
            ms_cost = 25.0
            
        meals.append({
            "category": "MORNING_SNACK",
            "food_items": [{"name": ms_name, "quantity": ms_qty}],
            "calories": target_calories * 0.08,
            "protein": 1.5,
            "carbohydrates": 15.0 if not has_diabetes else 8.0,
            "fat": 1.0,
            "fiber": 2.0,
            "cost": ms_cost,
            "selection_reason": ms_reason
        })

        # Build Lunch
        lunch_items = [{"name": "Yellow Moong Dal", "quantity": "1 bowl"}, {"name": "Mixed Vegetable Sabzi", "quantity": "1 bowl"}]
        lunch_cost = 40.0 if budget == "LOW" else 80.0
        
        if "south indian" in cuisine or "kerala" in cuisine or "andhra" in cuisine:
            lunch_items.append({"name": "Brown Rice", "quantity": "1 small cup"})
            lunch_items.append({"name": "Curd/Yogurt", "quantity": "1 small cup"})
            lunch_reason = "Traditional brown rice and lentil combo providing complete protein with probiotics for gut health."
        else:
            lunch_items.append({"name": "Whole Wheat Phulka (no ghee)", "quantity": "2 pcs"})
            lunch_items.append({"name": "Cucumber Salad", "quantity": "1 plate"})
            lunch_reason = "Whole wheat roti with easily digestible yellow dal and green leafy vegetable curry."
            
        if not is_veg:
            if budget == "HIGH":
                lunch_items[0] = {"name": "Grilled Fish or Salmon", "quantity": "80g"}
                lunch_reason += " Salmon provides omega-3 fatty acids for joint and heart health."
                lunch_cost += 100.0
            else:
                lunch_items[0] = {"name": "Boiled Egg White Curry", "quantity": "2 egg whites"}
                lunch_reason += " Egg whites are an excellent source of highly bioavailable protein without cholesterol."
                lunch_cost += 15.0
                
        if has_kidney:
            # Reduce dal portion or change to low-potassium/phosphorus
            lunch_items = [item for item in lunch_items if "Dal" not in item["name"]]
            lunch_items.append({"name": "Sautéed Bottle Gourd (Lauki)", "quantity": "1 bowl"})
            lunch_reason = "Low-protein, low-potassium lunch designed to reduce nephron strain."
            
        meals.append({
            "category": "LUNCH",
            "food_items": lunch_items,
            "calories": target_calories * 0.35,
            "protein": 22.0 if not has_kidney else 12.0,
            "carbohydrates": 70.0 if not has_diabetes else 45.0,
            "fat": 10.0 if not has_heart else 5.0,
            "fiber": 6.0,
            "cost": lunch_cost,
            "selection_reason": lunch_reason
        })

        # Evening Snack
        es_name = "Warm Ginger Tea"
        es_qty = "1 cup (sugar-free)"
        es_reason = "Ginger aids digestion and acts as an anti-inflammatory agent for joint pain."
        es_cost = 10.0
        
        es_items = [{"name": es_name, "quantity": es_qty}]
        if budget == "HIGH":
            es_items.append({"name": "Almonds & Walnuts", "quantity": "4-5 pcs each"})
            es_reason += " Nuts supply healthy unsaturated fats (MUFAs/PUFAs) and vitamin E."
            es_cost += 40.0
        else:
            es_items.append({"name": "Roasted Chana (Chickpeas)", "quantity": "1 small handful"})
            es_reason += " Roasted chickpeas are a budget-friendly source of fiber and minerals."
            es_cost += 5.0

        meals.append({
            "category": "EVENING_SNACK",
            "food_items": es_items,
            "calories": target_calories * 0.08,
            "protein": 4.0,
            "carbohydrates": 15.0,
            "fat": 2.0 if budget == "LOW" else 6.0,
            "fiber": 3.0,
            "cost": es_cost,
            "selection_reason": es_reason
        })

        # Dinner
        din_items = [{"name": "Khichdi (Rice & Lentil Porridge)", "quantity": "1 large bowl"}, {"name": "Steamed Kaddu/Pumpkin Sabzi", "quantity": "1 bowl"}]
        din_reason = "Light and comforting evening meal. Khichdi is soft, easy to chew, and gentle on the stomach."
        din_cost = 30.0 if budget == "LOW" else 60.0
        
        if has_diabetes:
            din_items[0] = {"name": "Oats Khichdi", "quantity": "1 bowl"}
            din_reason = "Beta-glucan in oats manages postprandial glucose surges in elderly diabetic patients."
        elif has_hypertension:
            din_reason += " Prepared with strictly under 1g of salt to manage hypertension."

        meals.append({
            "category": "DINNER",
            "food_items": din_items,
            "calories": target_calories * 0.22,
            "protein": 12.0 if not has_kidney else 7.0,
            "carbohydrates": 50.0 if not has_diabetes else 35.0,
            "fat": 6.0 if not has_heart else 3.0,
            "fiber": 5.0,
            "cost": din_cost,
            "selection_reason": din_reason
        })

        # Bedtime
        bt_name = "Warm Milk (Sugar-free, Low-fat)"
        bt_qty = "1 cup (150ml)"
        bt_reason = "Contains tryptophan which helps promote deep sleep and provides nighttime calcium."
        bt_cost = 12.0
        
        if has_kidney:
            bt_name = "Chamomile Tea (Warm)"
            bt_qty = "1 cup"
            bt_reason = "Calming herbal tea. Low in phosphorus and potassium compared to milk."
            bt_cost = 15.0
            
        meals.append({
            "category": "BEDTIME",
            "food_items": [{"name": bt_name, "quantity": bt_qty}],
            "calories": target_calories * 0.05,
            "protein": 4.0 if not has_kidney else 0.5,
            "carbohydrates": 8.0 if not has_diabetes else 4.0,
            "fat": 2.0 if not has_heart else 0.5,
            "fiber": 0.0,
            "cost": bt_cost,
            "selection_reason": bt_reason
        })

        # Filter out anything matching user allergies / strict dislikes
        for meal in meals:
            clean_items = []
            for item in meal["food_items"]:
                name_lower = item["name"].lower()
                is_allergic = any(avoid in name_lower for avoid in avoid_items)
                if not is_allergic:
                    clean_items.append(item)
            if not clean_items:
                # If everything was filtered out, fallback to a basic safe item
                clean_items = [{"name": "Steamed Rice Porridge" if not has_diabetes else "Steamed Vegetable Soup", "quantity": "1 bowl"}]
            meal["food_items"] = clean_items

        # Append disclaimer warning
        for meal in meals:
            meal["selection_reason"] = "This recommendation is AI-generated and should not replace advice from a qualified healthcare professional. " + meal["selection_reason"]

        return {
            "date": date,
            "meals": meals
        }
