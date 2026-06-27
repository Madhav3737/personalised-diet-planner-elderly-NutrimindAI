import axios from 'axios';
import { 
  Profile, MedicalHistory, MealPlan, MealLog, DashboardData, 
  ChatHistoryEntry, HabitStats 
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to automatically attach authorization tokens
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('nutrimind_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
}, (error) => {
  return Promise.reject(error);
});

export const authAPI = {
  register: async (email: string, password: string) => {
    // Fix typo str -> string
    const response = await apiClient.post('/auth/register', { email, password });
    return response.data;
  },
  login: async (email: string, password: string) => {
    // OAuth2 password form data needs x-www-form-urlencoded
    const formData = new URLSearchParams();
    formData.append('username', email);
    formData.append('password', password);
    
    const response = await apiClient.post('/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      }
    });
    
    if (response.data.access_token) {
      localStorage.setItem('nutrimind_token', response.data.access_token);
    }
    return response.data;
  },
  logout: () => {
    localStorage.removeItem('nutrimind_token');
  },
  isAuthenticated: () => {
    return !!localStorage.getItem('nutrimind_token');
  }
};

export const profileAPI = {
  getProfile: async (): Promise<Profile> => {
    const response = await apiClient.get('/profile/me');
    return response.data;
  },
  updateProfile: async (profile: Profile): Promise<Profile> => {
    const response = await apiClient.post('/profile/me', profile);
    return response.data;
  },
  getMedicalHistory: async (): Promise<MedicalHistory> => {
    const response = await apiClient.get('/profile/medical-history');
    return response.data;
  },
  updateMedicalHistory: async (med: MedicalHistory): Promise<MedicalHistory> => {
    const response = await apiClient.post('/profile/medical-history', med);
    return response.data;
  },
  getAllergies: async (): Promise<string[]> => {
    const response = await apiClient.get('/profile/allergies');
    return response.data.map((a: any) => a.allergy_name);
  },
  updateAllergies: async (allergies: string[]): Promise<any> => {
    const response = await apiClient.post('/profile/allergies', allergies);
    return response.data;
  },
  getPreferences: async (): Promise<{ likes: string[]; dislikes: string[] }> => {
    const response = await apiClient.get('/profile/preferences');
    const likes = response.data.filter((p: any) => p.like_dislike === 'LIKE').map((p: any) => p.food_item);
    const dislikes = response.data.filter((p: any) => p.like_dislike === 'DISLIKE').map((p: any) => p.food_item);
    return { likes, dislikes };
  },
  updatePreferences: async (likes: string[], dislikes: string[]): Promise<any> => {
    const response = await apiClient.post('/profile/preferences', null, {
      params: { likes, dislikes }
    });
    return response.data;
  }
};

export const plannerAPI = {
  getPlan: async (date?: string): Promise<MealPlan> => {
    const response = await apiClient.get('/planner/generate-plan', {
      params: date ? { date } : {}
    });
    return response.data;
  },
  getRecommendation: async (): Promise<MealPlan> => {
    const response = await apiClient.get('/planner/recommendation');
    return response.data;
  }
};

export const trackerAPI = {
  logMeal: async (
    category: string, 
    status: 'FULL' | 'HALF' | 'SKIPPED', 
    extraFoods: Array<{ name: string; quantity: string }> | null = null,
    waterMl: number = 0,
    date?: string
  ): Promise<MealLog> => {
    const response = await apiClient.post('/tracker/log-meal', {
      meal_category: category,
      status,
      extra_foods_consumed: extraFoods,
      water_intake_ml: waterMl
    }, {
      params: date ? { date } : {}
    });
    return response.data;
  },
  logWater: async (waterMl: number, date?: string): Promise<MealLog> => {
    const response = await apiClient.post('/tracker/water', {
      water_intake_ml: waterMl
    }, {
      params: date ? { date } : {}
    });
    return response.data;
  },
  getLogs: async (date?: string): Promise<MealLog[]> => {
    const response = await apiClient.get('/tracker/history', {
      params: date ? { date } : {}
    });
    return response.data;
  }
};

export const chatAPI = {
  send: async (message: string): Promise<{ response: string; created_at: string }> => {
    const response = await apiClient.post('/chat', { message });
    return response.data;
  },
  getHistory: async (): Promise<ChatHistoryEntry[]> => {
    const response = await apiClient.get('/chat/history');
    return response.data;
  }
};

export const dashboardAPI = {
  getStats: async (date?: string): Promise<DashboardData> => {
    const response = await apiClient.get('/dashboard', {
      params: date ? { date } : {}
    });
    return response.data;
  },
  getHabits: async (): Promise<HabitStats> => {
    const response = await apiClient.get('/dashboard/habits');
    return response.data;
  }
};
