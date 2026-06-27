export interface User {
  id: number;
  email: string;
  is_active: boolean;
  created_at: string;
}

export interface Profile {
  name: string;
  age: number;
  gender: string;
  height: number;
  weight: number;
  native_place?: string;
  country: string;
  state?: string;
  food_preference: string;
  religion?: string;
  occupation?: string;
  activity_level: string;
  sleep_schedule?: string;
  economic_condition: string;
  regional_cuisine: string;
  bmi?: number;
  created_at?: string;
}

export interface MedicalHistory {
  diabetes: boolean;
  hypertension: boolean;
  heart_disease: boolean;
  kidney_disease: boolean;
  liver_disease: boolean;
  thyroid: boolean;
  cholesterol: boolean;
  arthritis: boolean;
  osteoporosis: boolean;
  digestive_disorders: boolean;
  others?: string;
}

export interface Allergy {
  id: number;
  allergy_name: string;
}

export interface Preference {
  id: number;
  like_dislike: 'LIKE' | 'DISLIKE';
  food_item: string;
}

export interface MealItem {
  name: string;
  quantity: string;
}

export interface Meal {
  category: string;
  food_items: MealItem[];
  calories: number;
  protein: number;
  carbohydrates: number;
  fat: number;
  fiber: number;
  cost: number;
  selection_reason?: string;
}

export interface MealPlan {
  id: number;
  user_id: number;
  date: string;
  meals: Meal[];
  created_at: string;
}

export interface MealLog {
  id: number;
  user_id: number;
  date: string;
  meal_category: string;
  status: 'FULL' | 'HALF' | 'SKIPPED';
  extra_foods_consumed: Array<{ name: string; quantity: string }> | null;
  water_intake_ml: number;
  logged_at: string;
}

export interface DailyNutritionSummary {
  target_calories: number;
  logged_calories: number;
  target_protein: number;
  logged_protein: number;
  target_carbs: number;
  logged_carbs: number;
  target_fat: number;
  logged_fat: number;
  target_fiber: number;
  logged_fiber: number;
}

export interface DashboardData {
  bmi: number;
  bmi_status: string;
  calories_today: number;
  protein_today: number;
  meal_completion_rate: number;
  water_intake_ml: number;
  weekly_water: Record<string, number>;
  weekly_completion: Record<string, number>;
  daily_nutrition: DailyNutritionSummary;
  warnings: string[];
}

export interface ChatHistoryEntry {
  id: number;
  message: string;
  response: string;
  sender: string;
  created_at: string;
}

export interface HabitStats {
  favorite_foods: Record<string, number>;
  skipped_foods: Record<string, number>;
  average_meal_completion_rate: number;
  water_intake_avg: number;
}
