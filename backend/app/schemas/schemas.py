from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

# --- Token & Authentication ---
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

# --- Profile schemas (Step 1 & 4 & 5 of intake) ---
class ProfileCreate(BaseModel):
    name: str
    age: int
    gender: str
    height: float # cm
    weight: float # kg
    native_place: Optional[str] = None
    country: str = "India"
    state: Optional[str] = None
    food_preference: str # Vegetarian, Veg (with Egg), Non-Vegetarian, Vegan
    religion: Optional[str] = None
    occupation: Optional[str] = None
    activity_level: str # Sedentary, Lightly Active, Moderately Active, Very Active
    sleep_schedule: Optional[str] = None
    economic_condition: str # Low, Medium, High
    regional_cuisine: str # South Indian, North Indian, Andhra, Tamil, Kerala, Bengali, Punjabi, etc.

class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    native_place: Optional[str] = None
    country: Optional[str] = None
    state: Optional[str] = None
    food_preference: Optional[str] = None
    religion: Optional[str] = None
    occupation: Optional[str] = None
    activity_level: Optional[str] = None
    sleep_schedule: Optional[str] = None
    economic_condition: Optional[str] = None
    regional_cuisine: Optional[str] = None

class ProfileResponse(ProfileCreate):
    id: int
    user_id: int
    bmi: float
    created_at: datetime

    class Config:
        from_attributes = True

# --- Medical History schemas (Step 2) ---
class MedicalHistoryCreate(BaseModel):
    diabetes: bool = False
    hypertension: bool = False
    heart_disease: bool = False
    kidney_disease: bool = False
    liver_disease: bool = False
    thyroid: bool = False
    cholesterol: bool = False
    arthritis: bool = False
    osteoporosis: bool = False
    digestive_disorders: bool = False
    others: Optional[str] = None

class MedicalHistoryResponse(MedicalHistoryCreate):
    id: int
    user_id: int

    class Config:
        from_attributes = True

# --- Allergies & Preferences schemas (Step 3) ---
class AllergyCreate(BaseModel):
    allergy_name: str

class AllergyResponse(AllergyCreate):
    id: int
    user_id: int

    class Config:
        from_attributes = True

class PreferenceCreate(BaseModel):
    like_dislike: str # LIKE or DISLIKE
    food_item: str

class PreferenceResponse(PreferenceCreate):
    id: int
    user_id: int

    class Config:
        from_attributes = True

# --- Meal and MealPlan schemas ---
class MealItem(BaseModel):
    name: str
    quantity: str

class MealSchema(BaseModel):
    category: str # BREAKFAST, MORNING_SNACK, LUNCH, EVENING_SNACK, DINNER, BEDTIME
    food_items: List[MealItem]
    calories: float
    protein: float
    carbohydrates: float
    fat: float
    fiber: float
    cost: float
    selection_reason: Optional[str] = None

class MealPlanCreate(BaseModel):
    date: str
    meals: List[MealSchema]

class MealPlanResponse(BaseModel):
    id: int
    user_id: int
    date: str
    meals: List[MealSchema]
    created_at: datetime

    class Config:
        from_attributes = True

# --- Meal Logging schemas ---
class MealLogCreate(BaseModel):
    meal_category: str
    status: str # FULL, HALF, SKIPPED
    extra_foods_consumed: Optional[List[Dict[str, Any]]] = None # [{"name": "Samosa", "quantity": "1 pc"}]
    water_intake_ml: int = 0

class MealLogResponse(BaseModel):
    id: int
    user_id: int
    date: str
    meal_category: str
    status: str
    extra_foods_consumed: Optional[List[Dict[str, Any]]] = None
    water_intake_ml: int
    logged_at: datetime

    class Config:
        from_attributes = True

class WaterLogCreate(BaseModel):
    water_intake_ml: int

# --- Chat schemas ---
class ChatCreate(BaseModel):
    message: str

class ChatResponse(BaseModel):
    message: str
    response: str
    created_at: datetime

class ChatHistoryResponse(BaseModel):
    id: int
    message: str
    response: str
    sender: str
    created_at: datetime

    class Config:
        from_attributes = True

# --- Habits schemas ---
class HabitHistoryResponse(BaseModel):
    favorite_foods: Dict[str, int]
    skipped_foods: Dict[str, int]
    average_meal_completion_rate: float
    water_intake_avg: float

    class Config:
        from_attributes = True

# --- Dashboard Summary ---
class DailyNutritionSummary(BaseModel):
    target_calories: float = 2000
    logged_calories: float = 0
    target_protein: float = 60
    logged_protein: float = 0
    target_carbs: float = 250
    logged_carbs: float = 0
    target_fat: float = 65
    logged_fat: float = 0
    target_fiber: float = 25
    logged_fiber: float = 0

class DashboardResponse(BaseModel):
    bmi: float
    bmi_status: str
    calories_today: float
    protein_today: float
    meal_completion_rate: float # 0.0 to 100.0
    water_intake_ml: int
    weekly_water: Dict[str, int] # Day of week to ml
    weekly_completion: Dict[str, float] # Day of week to completion rate
    daily_nutrition: DailyNutritionSummary
    warnings: List[str]
