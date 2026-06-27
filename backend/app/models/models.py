import datetime
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text, JSON, Enum
from sqlalchemy.orm import relationship
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    profile = relationship("Profile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    medical_history = relationship("MedicalHistory", back_populates="user", uselist=False, cascade="all, delete-orphan")
    allergies = relationship("Allergy", back_populates="user", cascade="all, delete-orphan")
    preferences = relationship("Preference", back_populates="user", cascade="all, delete-orphan")
    meal_plans = relationship("MealPlan", back_populates="user", cascade="all, delete-orphan")
    meal_logs = relationship("MealLog", back_populates="user", cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="user", cascade="all, delete-orphan")
    habit_history = relationship("HabitHistory", back_populates="user", uselist=False, cascade="all, delete-orphan")
    chat_histories = relationship("ChatHistory", back_populates="user", cascade="all, delete-orphan")


class Profile(Base):
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    name = Column(String, nullable=False)
    age = Column(Integer, nullable=False)
    gender = Column(String, nullable=False)
    height = Column(Float, nullable=False) # in cm
    weight = Column(Float, nullable=False) # in kg
    bmi = Column(Float, nullable=False)
    native_place = Column(String, nullable=True)
    country = Column(String, nullable=False, default="India")
    state = Column(String, nullable=True)
    food_preference = Column(String, nullable=False) # e.g. Vegetarian, Veg (with Egg), Non-Vegetarian, Vegan
    is_vegetarian = Column(Boolean, default=True)
    religion = Column(String, nullable=True)
    occupation = Column(String, nullable=True)
    activity_level = Column(String, nullable=False) # Sedentary, Lightly Active, Moderately Active, Very Active
    sleep_schedule = Column(String, nullable=True) # e.g. "22:00 - 06:00"
    economic_condition = Column(String, nullable=False) # Low, Medium, High
    regional_cuisine = Column(String, nullable=False) # South Indian, North Indian, Andhra, Tamil, Kerala, Bengali, Punjabi, etc.
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="profile")


class MedicalHistory(Base):
    __tablename__ = "medical_histories"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    diabetes = Column(Boolean, default=False)
    hypertension = Column(Boolean, default=False)
    heart_disease = Column(Boolean, default=False)
    kidney_disease = Column(Boolean, default=False)
    liver_disease = Column(Boolean, default=False)
    thyroid = Column(Boolean, default=False)
    cholesterol = Column(Boolean, default=False)
    arthritis = Column(Boolean, default=False)
    osteoporosis = Column(Boolean, default=False)
    digestive_disorders = Column(Boolean, default=False)
    others = Column(Text, nullable=True) # JSON or text list of other diseases

    # Relationships
    user = relationship("User", back_populates="medical_history")


class Allergy(Base):
    __tablename__ = "allergies"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    allergy_name = Column(String, nullable=False, index=True)

    # Relationships
    user = relationship("User", back_populates="allergies")


class Preference(Base):
    __tablename__ = "preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    like_dislike = Column(String, nullable=False) # "LIKE" or "DISLIKE"
    food_item = Column(String, nullable=False)

    # Relationships
    user = relationship("User", back_populates="preferences")


class MealPlan(Base):
    __tablename__ = "meal_plans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    date = Column(String, nullable=False, index=True) # Format: YYYY-MM-DD
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="meal_plans")
    meals = relationship("Meal", back_populates="meal_plan", cascade="all, delete-orphan")


class Meal(Base):
    __tablename__ = "meals"

    id = Column(Integer, primary_key=True, index=True)
    meal_plan_id = Column(Integer, ForeignKey("meal_plans.id", ondelete="CASCADE"), nullable=False)
    category = Column(String, nullable=False) # BREAKFAST, MORNING_SNACK, LUNCH, EVENING_SNACK, DINNER, BEDTIME
    food_items = Column(JSON, nullable=False) # List of food item dicts: [{"name": "Idli", "quantity": "2 pcs"}, ...]
    calories = Column(Float, nullable=False)
    protein = Column(Float, nullable=False) # grams
    carbohydrates = Column(Float, nullable=False) # grams
    fat = Column(Float, nullable=False) # grams
    fiber = Column(Float, nullable=False) # grams
    cost = Column(Float, default=0.0) # approximate cost
    selection_reason = Column(Text, nullable=True)

    # Relationships
    meal_plan = relationship("MealPlan", back_populates="meals")


class MealLog(Base):
    __tablename__ = "meal_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    date = Column(String, nullable=False, index=True) # Format: YYYY-MM-DD
    meal_category = Column(String, nullable=False) # BREAKFAST, MORNING_SNACK, etc.
    status = Column(String, nullable=False) # FULL, HALF, SKIPPED
    extra_foods_consumed = Column(JSON, nullable=True) # List of extra food items
    water_intake_ml = Column(Integer, default=0)
    logged_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="meal_logs")


class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    type = Column(String, nullable=False) # MEAL_PLAN, ADJUSTMENT, CHAT
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="recommendations")


class HabitHistory(Base):
    __tablename__ = "habit_histories"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    favorite_foods = Column(JSON, default=dict) # e.g. {"Idli": 15, "Oats": 10}
    skipped_foods = Column(JSON, default=dict) # e.g. {"Upma": 5}
    average_meal_completion_rate = Column(Float, default=1.0) # percentage 0 to 1
    water_intake_avg = Column(Float, default=0.0) # average ml per day
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="habit_history")


class ChatHistory(Base):
    __tablename__ = "chat_histories"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    message = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    sender = Column(String, nullable=False, default="USER") # USER or AI
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="chat_histories")
