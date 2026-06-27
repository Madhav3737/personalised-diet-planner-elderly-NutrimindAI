import React, { useEffect, useState } from 'react';
import { dashboardAPI, plannerAPI, trackerAPI } from '../services/api';
import { DashboardData, MealPlan, Meal, MealLog } from '../types';
import { 
  Heart, Flame, Droplet, CheckCircle2, UserCheck, Eye, Mic, MicOff,
  Volume2, VolumeX, AlertTriangle, RefreshCw, Plus, Minus, Download, LogOut
} from 'lucide-react';
import { 
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, 
  LineChart, Line, CartesianGrid 
} from 'recharts';

interface DashboardProps {
  onLogout: () => void;
  onNavigateToChat: () => void;
}

export const Dashboard: React.FC<DashboardProps> = ({ onLogout, onNavigateToChat }) => {
  const [stats, setStats] = useState<DashboardData | null>(null);
  const [plan, setPlan] = useState<MealPlan | null>(null);
  const [logs, setLogs] = useState<MealLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [caregiverMode, setCaregiverMode] = useState(false);
  
  // Voice Input States
  const [activeVoiceField, setActiveVoiceField] = useState<string | null>(null);
  const [extraFoodInputs, setExtraFoodInputs] = useState<Record<string, string>>({});
  const [listening, setListening] = useState(false);
  
  // Speech synthesis speaker state
  const [speakingMeal, setSpeakingMeal] = useState<string | null>(null);

  const fetchDashboardData = async () => {
    try {
      const statsData = await dashboardAPI.getStats();
      const planData = await plannerAPI.getPlan();
      const logsData = await trackerAPI.getLogs();
      setStats(statsData);
      setPlan(planData);
      setLogs(logsData);
    } catch (err) {
      console.error("Error loading dashboard data:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const handleRefreshPlan = async () => {
    setRefreshing(true);
    try {
      await plannerAPI.getPlan(); // API will trigger generation
      await fetchDashboardData();
    } catch (err) {
      console.error(err);
    } finally {
      setRefreshing(false);
    }
  };

  // Water tracking increment
  const handleWaterUpdate = async (amount: number) => {
    try {
      await trackerAPI.logWater(amount);
      await fetchDashboardData();
    } catch (err) {
      console.error(err);
    }
  };

  // Meal Log completion status
  const handleLogMeal = async (category: string, status: 'FULL' | 'HALF' | 'SKIPPED') => {
    try {
      await trackerAPI.logMeal(category, status);
      await fetchDashboardData();
    } catch (err) {
      console.error(err);
    }
  };

  // Log Extra Food
  const handleLogExtraFood = async (category: string) => {
    const input = extraFoodInputs[category] || '';
    if (!input.trim()) return;

    try {
      const existingLog = logs.find(l => l.meal_category === category);
      const currentExtras = existingLog?.extra_foods_consumed || [];
      const updatedExtras = [...currentExtras, { name: input.trim(), quantity: '1 portion' }];
      
      await trackerAPI.logMeal(category, existingLog?.status || 'FULL', updatedExtras);
      setExtraFoodInputs(prev => ({ ...prev, [category]: '' }));
      await fetchDashboardData();
    } catch (err) {
      console.error(err);
    }
  };

  // --- Voice Web Speech API helpers ---
  const startSpeechRecognition = (category: string) => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert("Voice input is not supported in this browser. Please use Chrome or Safari.");
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = 'en-IN';
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    recognition.onstart = () => {
      setListening(true);
      setActiveVoiceField(category);
    };

    recognition.onresult = (event: any) => {
      const transcript = event.results[0][0].transcript;
      setExtraFoodInputs(prev => ({
        ...prev,
        [category]: (prev[category] || '') + transcript
      }));
    };

    recognition.onerror = () => {
      setListening(false);
      setActiveVoiceField(null);
    };

    recognition.onend = () => {
      setListening(false);
      setActiveVoiceField(null);
    };

    recognition.start();
  };

  // Speak meal details aloud
  const speakMealAloud = (meal: Meal) => {
    if ('speechSynthesis' in window) {
      if (speakingMeal === meal.category) {
        window.speechSynthesis.cancel();
        setSpeakingMeal(null);
        return;
      }
      
      window.speechSynthesis.cancel(); // Stop any active speech
      const itemsList = meal.food_items.map(item => `${item.quantity} of ${item.name}`).join(', ');
      const textToSpeak = `For ${meal.category.toLowerCase().replace('_', ' ')}, the dietician recommends: ${itemsList}. Reason: ${meal.selection_reason}`;
      
      const utterance = new SpeechSynthesisUtterance(textToSpeak);
      utterance.rate = 0.9; // Read slightly slower for older ears
      
      utterance.onend = () => setSpeakingMeal(null);
      utterance.onerror = () => setSpeakingMeal(null);
      
      setSpeakingMeal(meal.category);
      window.speechSynthesis.speak(utterance);
    } else {
      alert("Text-to-speech is not supported on this browser.");
    }
  };

  // Generate doctor summary / PDF export helper
  const handleExportPDF = () => {
    if (!plan || !stats) return;
    
    let content = `NUTRIMIND AI - GERIATRIC CLINICAL REPORT\n`;
    content += `Date: ${plan.date}\n`;
    content += `Patient BMI: ${stats.bmi} (${stats.bmi_status})\n`;
    content += `Total Calories Logged: ${stats.calories_today} kcal / Target: ${stats.daily_nutrition.target_calories} kcal\n`;
    content += `Total Protein Logged: ${stats.protein_today} g / Target: ${stats.daily_nutrition.target_protein} g\n`;
    content += `Water Consumption: ${stats.water_intake_ml} ml / Goal: 2000 ml\n\n`;
    
    content += `--- MEAL PLAN DETAILS ---\n`;
    plan.meals.forEach(m => {
      const log = logs.find(l => l.meal_category === m.category);
      content += `[${m.category}] Status: ${log?.status || 'NOT LOGGED'}\n`;
      m.food_items.forEach(item => {
        content += `- ${item.name} (${item.quantity})\n`;
      });
      content += `Reason: ${m.selection_reason}\n\n`;
    });
    
    if (stats.warnings.length > 0) {
      content += `--- SAFETY ALERTS & WARNINGS ---\n`;
      stats.warnings.forEach(w => {
        content += `⚠️ ${w}\n`;
      });
    }

    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `NutriMind_Geriatric_Report_${plan.date}.txt`;
    link.click();
    URL.revokeObjectURL(url);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center text-slate-100">
        <div className="w-12 h-12 border-4 border-emerald-500 border-t-transparent rounded-full animate-spin mb-4" />
        <p className="text-elderly-base font-medium">Analyzing RAG database & generating your clinical plan...</p>
      </div>
    );
  }

  // Map database trends format to Recharts arrays
  const waterChartData = stats 
    ? Object.keys(stats.weekly_water).map(day => ({ name: day, amount: stats.weekly_water[day] }))
    : [];
  
  const completionChartData = stats
    ? Object.keys(stats.weekly_completion).map(day => ({ name: day, rate: stats.weekly_completion[day] }))
    : [];

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 pb-20">
      {/* Top Header bar */}
      <header className="glass-panel sticky top-0 z-40 px-6 py-4 flex items-center justify-between shadow-md">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-emerald-500 rounded-xl flex items-center justify-center">
            <Heart className="w-6 h-6 text-slate-950 fill-slate-950" />
          </div>
          <div>
            <h1 className="text-xl font-bold bg-gradient-to-r from-emerald-400 to-teal-300 bg-clip-text text-transparent">
              NutriMind AI
            </h1>
            <span className="text-xs text-slate-400">Dietician & Geriatric Portal</span>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <button
            onClick={() => setCaregiverMode(!caregiverMode)}
            className={`py-2 px-4 rounded-xl border font-bold flex items-center gap-2 text-sm transition-all ${
              caregiverMode 
                ? 'bg-indigo-600/30 border-indigo-500 text-indigo-200' 
                : 'bg-slate-900 border-slate-700 text-slate-300 hover:bg-slate-800'
            }`}
          >
            <Eye className="w-4 h-4" />
            {caregiverMode ? 'Exit Caregiver Mode' : 'Caregiver Mode'}
          </button>
          
          <button
            onClick={onNavigateToChat}
            className="py-2 px-4 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-sm shadow-md"
          >
            Ask Dietician Chat
          </button>

          <button
            onClick={onLogout}
            className="p-2 rounded-xl bg-slate-900 border border-slate-700 hover:bg-slate-800 text-slate-400"
            title="Log Out"
          >
            <LogOut className="w-5 h-5" />
          </button>
        </div>
      </header>

      {/* Main Body */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        
        {/* WARNINGS & ALERTS */}
        {stats?.warnings && stats.warnings.length > 0 && (
          <div className="mb-8 space-y-3">
            {stats.warnings.map((warn, idx) => (
              <div key={idx} className="p-4 rounded-2xl bg-amber-500/10 border border-amber-500/20 text-amber-300 flex items-start gap-3 shadow-md">
                <AlertTriangle className="w-6 h-6 text-amber-500 shrink-0 mt-0.5" />
                <p className="text-elderly-base font-semibold">{warn}</p>
              </div>
            ))}
          </div>
        )}

        {/* SUMMARY STATS GRID */}
        <section className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-10">
          
          {/* BMI Card */}
          <div className="glass-panel p-6 rounded-3xl shadow-xl flex items-center justify-between border-l-8 border-emerald-500">
            <div>
              <p className="text-slate-400 text-sm font-medium">Body Mass Index (BMI)</p>
              <h3 className="text-3xl font-extrabold text-slate-100 mt-1">{stats?.bmi}</h3>
              <span className="text-xs bg-emerald-500/10 text-emerald-300 px-2 py-0.5 rounded-full font-bold mt-2 inline-block">
                {stats?.bmi_status}
              </span>
            </div>
            <UserCheck className="w-12 h-12 text-emerald-500 opacity-80" />
          </div>

          {/* Calories Card */}
          <div className="glass-panel p-6 rounded-3xl shadow-xl flex flex-col justify-between border-l-8 border-amber-500">
            <div className="flex items-center justify-between mb-2">
              <div>
                <p className="text-slate-400 text-sm font-medium">Calories Today</p>
                <h3 className="text-3xl font-extrabold text-slate-100 mt-1">{stats?.calories_today} kcal</h3>
              </div>
              <Flame className="w-10 h-10 text-amber-500 opacity-80" />
            </div>
            <div>
              <div className="w-full bg-slate-800 h-2.5 rounded-full overflow-hidden">
                <div 
                  className="bg-amber-500 h-full rounded-full transition-all duration-500" 
                  style={{ width: `${Math.min(((stats?.calories_today || 0) / (stats?.daily_nutrition.target_calories || 2000)) * 100, 100)}%` }}
                />
              </div>
              <p className="text-xs text-slate-400 mt-1.5 font-medium">Goal: {stats?.daily_nutrition.target_calories} kcal</p>
            </div>
          </div>

          {/* Protein Card */}
          <div className="glass-panel p-6 rounded-3xl shadow-xl flex flex-col justify-between border-l-8 border-teal-500">
            <div className="flex items-center justify-between mb-2">
              <div>
                <p className="text-slate-400 text-sm font-medium">Protein Consumed</p>
                <h3 className="text-3xl font-extrabold text-slate-100 mt-1">{stats?.protein_today} g</h3>
              </div>
              <CheckCircle2 className="w-10 h-10 text-teal-500 opacity-80" />
            </div>
            <div>
              <div className="w-full bg-slate-800 h-2.5 rounded-full overflow-hidden">
                <div 
                  className="bg-teal-500 h-full rounded-full transition-all duration-500" 
                  style={{ width: `${Math.min(((stats?.protein_today || 0) / (stats?.daily_nutrition.target_protein || 60)) * 100, 100)}%` }}
                />
              </div>
              <p className="text-xs text-slate-400 mt-1.5 font-medium">Goal: {stats?.daily_nutrition.target_protein} g</p>
            </div>
          </div>

          {/* Water Tracker Card */}
          <div className="glass-panel p-6 rounded-3xl shadow-xl flex flex-col justify-between border-l-8 border-indigo-500">
            <div className="flex items-center justify-between mb-2">
              <div>
                <p className="text-slate-400 text-sm font-medium">Water Intake</p>
                <h3 className="text-3xl font-extrabold text-slate-100 mt-1">{stats?.water_intake_ml} ml</h3>
              </div>
              <Droplet className="w-10 h-10 text-indigo-400 opacity-80" />
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={() => handleWaterUpdate(-250)}
                className="p-1.5 bg-slate-900 border border-slate-700 hover:bg-slate-850 rounded-lg text-slate-400"
              >
                <Minus className="w-4 h-4" />
              </button>
              <span className="text-xs font-bold text-slate-300">250ml Cup</span>
              <button
                onClick={() => handleWaterUpdate(250)}
                className="p-1.5 bg-indigo-500/20 border border-indigo-500/40 hover:bg-indigo-500/30 rounded-lg text-indigo-400"
              >
                <Plus className="w-4 h-4" />
              </button>
              <span className="text-xs text-slate-400 ml-auto font-medium">Goal: 2000 ml</span>
            </div>
          </div>

        </section>

        {/* CAREGIVER MODE SUMMARY VIEW */}
        {caregiverMode ? (
          <section className="glass-panel p-8 rounded-3xl shadow-2xl mb-10 border border-indigo-500/30">
            <div className="flex items-center justify-between mb-6 border-b border-slate-800 pb-4">
              <div>
                <h2 className="text-2xl font-extrabold text-indigo-300">Caregiver Clinical Overview</h2>
                <p className="text-slate-400 text-sm">Downloadable summaries and diet compliance reports for doctor consultations.</p>
              </div>
              <button
                onClick={handleExportPDF}
                className="py-3 px-6 bg-indigo-600 hover:bg-indigo-500 text-white font-bold rounded-xl shadow-lg flex items-center gap-2"
              >
                <Download className="w-5 h-5" /> Export Text Report
              </button>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              <div className="space-y-4">
                <h3 className="text-lg font-bold text-slate-200">Patient Nutritional Targets</h3>
                <div className="space-y-3 bg-slate-900/60 p-5 rounded-2xl border border-slate-800">
                  <div className="flex justify-between border-b border-slate-800/80 pb-2 text-elderly-base">
                    <span className="text-slate-400">Target Calories:</span>
                    <span className="font-bold text-slate-200">{stats?.daily_nutrition.target_calories} kcal</span>
                  </div>
                  <div className="flex justify-between border-b border-slate-800/80 pb-2 text-elderly-base">
                    <span className="text-slate-400">Target Protein:</span>
                    <span className="font-bold text-slate-200">{stats?.daily_nutrition.target_protein} g</span>
                  </div>
                  <div className="flex justify-between border-b border-slate-800/80 pb-2 text-elderly-base">
                    <span className="text-slate-400">Target Carbohydrates:</span>
                    <span className="font-bold text-slate-200">{stats?.daily_nutrition.target_carbs} g</span>
                  </div>
                  <div className="flex justify-between border-b border-slate-800/80 pb-2 text-elderly-base">
                    <span className="text-slate-400">Target Fiber:</span>
                    <span className="font-bold text-slate-200">{stats?.daily_nutrition.target_fiber} g</span>
                  </div>
                  <div className="flex justify-between pb-2 text-elderly-base">
                    <span className="text-slate-400">Meal Completion Rate:</span>
                    <span className="font-bold text-emerald-400">{stats?.meal_completion_rate}%</span>
                  </div>
                </div>
              </div>

              <div>
                <h3 className="text-lg font-bold text-slate-200 mb-4">Meal Logging Log Details</h3>
                <div className="space-y-3 max-h-60 overflow-y-auto">
                  {logs.map((log, idx) => (
                    <div key={idx} className="p-4 rounded-xl bg-slate-900 border border-slate-850 flex items-center justify-between">
                      <div>
                        <span className="font-bold text-slate-300 text-sm capitalize">{log.meal_category.replace('_', ' ').toLowerCase()}</span>
                        <p className="text-xs text-slate-500 mt-0.5">Logged: {new Date(log.logged_at).toLocaleTimeString()}</p>
                      </div>
                      <span className={`px-3 py-1 rounded-full text-xs font-bold ${
                        log.status === 'FULL' ? 'bg-emerald-500/10 text-emerald-400' :
                        log.status === 'HALF' ? 'bg-amber-500/10 text-amber-400' : 'bg-rose-500/10 text-rose-400'
                      }`}>
                        {log.status}
                      </span>
                    </div>
                  ))}
                  {logs.length === 0 && <p className="text-slate-500 text-sm italic">No meals logged for today yet.</p>}
                </div>
              </div>
            </div>
          </section>
        ) : null}

        {/* DAILY MEALS & DIETARY RECOMMENDATIONS */}
        <section className="mb-12">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-2xl font-extrabold text-slate-100 tracking-tight">Today's Diet Plans</h2>
              <p className="text-slate-400 text-sm mt-0.5">Clinical meals calculated by the RAG Recommendation Engine.</p>
            </div>
            
            <button
              onClick={handleRefreshPlan}
              disabled={refreshing}
              className="py-2.5 px-4 bg-slate-900 border border-slate-700 text-slate-300 font-bold rounded-xl flex items-center gap-2 hover:bg-slate-850 transition-all text-sm"
            >
              <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
              Re-Calculate Plan
            </button>
          </div>

          <div className="space-y-6">
            {plan?.meals.map((meal) => {
              const log = logs.find(l => l.meal_category === meal.category);
              const isSpeaking = speakingMeal === meal.category;
              
              return (
                <div key={meal.category} className="glass-panel p-6 md:p-8 rounded-3xl shadow-xl border border-slate-800 hover:border-slate-700/80 transition-all">
                  <div className="flex flex-col md:flex-row md:items-start justify-between gap-4 mb-4 border-b border-slate-800 pb-4">
                    <div>
                      <div className="flex items-center gap-3">
                        <h3 className="text-xl font-extrabold text-slate-200 capitalize tracking-wide">
                          {meal.category.replace('_', ' ').toLowerCase()}
                        </h3>
                        <span className="text-xs bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 px-2 py-0.5 rounded-full font-bold">
                          {meal.calories} kcal
                        </span>
                        <span className="text-xs bg-teal-500/10 text-teal-400 border border-teal-500/20 px-2 py-0.5 rounded-full font-bold">
                          Protein: {meal.protein}g
                        </span>
                      </div>
                      
                      {/* Food Items list */}
                      <div className="mt-3 flex flex-wrap gap-2">
                        {meal.food_items.map((item, i) => (
                          <span key={i} className="bg-slate-900 border border-slate-700 px-3 py-1.5 rounded-xl font-bold text-slate-300 text-elderly-base">
                            {item.name} <span className="text-emerald-400 text-sm font-medium">({item.quantity})</span>
                          </span>
                        ))}
                      </div>
                    </div>

                    {/* Text-to-speech speaker button */}
                    <div className="flex items-center gap-2 self-start">
                      <button
                        onClick={() => speakMealAloud(meal)}
                        className={`p-2.5 rounded-xl border flex items-center justify-center transition-all ${
                          isSpeaking 
                            ? 'bg-rose-500/10 border-rose-500 text-rose-400' 
                            : 'bg-slate-900 border-slate-800 text-slate-400 hover:border-slate-700'
                        }`}
                        title="Read plan aloud"
                      >
                        {isSpeaking ? <VolumeX className="w-5 h-5 animate-bounce" /> : <Volume2 className="w-5 h-5" />}
                      </button>

                      {/* Tracker buttons */}
                      <div className="bg-slate-900 p-1.5 rounded-2xl flex gap-1 border border-slate-800">
                        {['SKIPPED', 'HALF', 'FULL'].map((st) => (
                          <button
                            key={st}
                            onClick={() => handleLogMeal(meal.category, st as any)}
                            className={`py-1.5 px-4 rounded-xl text-xs font-extrabold uppercase transition-all ${
                              log?.status === st
                                ? st === 'FULL' ? 'bg-emerald-500 text-slate-950 font-bold' :
                                  st === 'HALF' ? 'bg-amber-500 text-slate-950 font-bold' : 'bg-rose-500 text-white font-bold'
                                : 'text-slate-400 hover:bg-slate-800'
                            }`}
                          >
                            {st}
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>

                  <p className="text-slate-400 italic text-elderly-base mb-4 leading-relaxed">
                    {meal.selection_reason}
                  </p>

                  {/* Extra food logging block with Voice Option */}
                  <div className="flex items-center gap-3 bg-slate-900/30 p-3 rounded-2xl border border-slate-850">
                    <div className="relative flex-1">
                      <input
                        type="text"
                        placeholder="Log extra foods (e.g. 1 samosa, sweets)..."
                        value={extraFoodInputs[meal.category] || ''}
                        onChange={(e) => {
                          const val = e.target.value;
                          setExtraFoodInputs(prev => ({ ...prev, [meal.category]: val }));
                        }}
                        className="w-full bg-slate-900/50 border border-slate-800 rounded-xl py-2 px-4 pr-10 text-slate-100 text-sm focus:outline-none focus:border-emerald-500"
                      />
                      <button
                        onClick={() => startSpeechRecognition(meal.category)}
                        className={`absolute right-2 top-1/2 -translate-y-1/2 p-1.5 rounded-lg transition-colors ${
                          activeVoiceField === meal.category && listening
                            ? 'bg-rose-500 text-white'
                            : 'text-slate-500 hover:text-slate-300'
                        }`}
                        title="Voice dictation"
                      >
                        {activeVoiceField === meal.category && listening ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
                      </button>
                    </div>

                    <button
                      onClick={() => handleLogExtraFood(meal.category)}
                      className="py-2 px-4 bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 font-bold rounded-xl text-xs transition-colors shrink-0"
                    >
                      Save Extra
                    </button>
                  </div>

                  {log?.extra_foods_consumed && log.extra_foods_consumed.length > 0 && (
                    <div className="mt-3 flex flex-wrap gap-2 items-center">
                      <span className="text-xs text-slate-500 font-bold">Extra eaten:</span>
                      {log.extra_foods_consumed.map((extra, idx) => (
                        <span key={idx} className="bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs px-2.5 py-1 rounded-lg font-bold">
                          {extra.name}
                        </span>
                      ))}
                    </div>
                  )}

                </div>
              );
            })}
          </div>
        </section>

        {/* WEEKLY CHARTS AND PROGRESS TRENDS */}
        <section className="grid grid-cols-1 md:grid-cols-2 gap-8 mt-10">
          
          <div className="glass-panel p-6 rounded-3xl shadow-xl">
            <h3 className="text-lg font-extrabold text-slate-200 mb-4">Weekly Hydration (ml)</h3>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={waterChartData}>
                  <XAxis dataKey="name" stroke="#64748b" fontSize={12} tickLine={false} />
                  <YAxis stroke="#64748b" fontSize={12} tickLine={false} />
                  <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155' }} />
                  <Bar dataKey="amount" fill="#6366f1" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="glass-panel p-6 rounded-3xl shadow-xl">
            <h3 className="text-lg font-extrabold text-slate-200 mb-4">Diet Compliance Rate (%)</h3>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={completionChartData}>
                  <XAxis dataKey="name" stroke="#64748b" fontSize={12} tickLine={false} />
                  <YAxis stroke="#64748b" fontSize={12} tickLine={false} domain={[0, 100]} />
                  <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155' }} />
                  <CartesianGrid stroke="#334155" strokeDasharray="3 3" vertical={false} />
                  <Line type="monotone" dataKey="rate" stroke="#10b981" strokeWidth={3} dot={{ fill: '#10b981', r: 4 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

        </section>

      </main>
    </div>
  );
};
