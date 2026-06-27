import React, { useState } from 'react';
import { profileAPI } from '../services/api';
import { Profile, MedicalHistory } from '../types';
import { UserRound, Activity, Stethoscope, AlertTriangle, ShieldCheck, Banknote, MapPin, ArrowRight, ArrowLeft } from 'lucide-react';

interface WizardProps {
  onComplete: () => void;
}

export const IntakeWizard: React.FC<WizardProps> = ({ onComplete }) => {
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Step 1: Profile
  const [profile, setProfile] = useState<Profile>({
    name: '',
    age: 65,
    gender: 'Male',
    height: 165,
    weight: 65,
    native_place: '',
    country: 'India',
    state: '',
    food_preference: 'Vegetarian',
    activity_level: 'Sedentary',
    sleep_schedule: '22:00 - 06:00',
    economic_condition: 'Medium',
    regional_cuisine: 'South Indian',
  });

  // Step 2: Medical Conditions
  const [medical, setMedical] = useState<MedicalHistory>({
    diabetes: false,
    hypertension: false,
    heart_disease: false,
    kidney_disease: false,
    liver_disease: false,
    thyroid: false,
    cholesterol: false,
    arthritis: false,
    osteoporosis: false,
    digestive_disorders: false,
    others: '',
  });

  // Step 3: Allergies & Preferences
  const [allergyInput, setAllergyInput] = useState('');
  const [allergies, setAllergies] = useState<string[]>([]);
  const [likeInput, setLikeInput] = useState('');
  const [likes, setLikes] = useState<string[]>([]);
  const [dislikeInput, setDislikeInput] = useState('');
  const [dislikes, setDislikes] = useState<string[]>([]);

  // Form handlers
  const handleProfileChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setProfile(prev => {
      const updated = { ...prev };
      const key = name as keyof Profile;
      if (key === 'age' || key === 'height' || key === 'weight') {
        (updated as any)[key] = Number(value);
      } else {
        (updated as any)[key] = value;
      }
      return updated;
    });
  };

  const handleMedicalToggle = (key: keyof Omit<MedicalHistory, 'others'>) => {
    setMedical(prev => ({
      ...prev,
      [key]: !prev[key]
    }));
  };

  const addAllergy = () => {
    if (allergyInput.trim() && !allergies.includes(allergyInput.trim())) {
      setAllergies([...allergies, allergyInput.trim()]);
      setAllergyInput('');
    }
  };

  const removeAllergy = (idx: number) => {
    setAllergies(allergies.filter((_, i) => i !== idx));
  };

  const addLike = () => {
    if (likeInput.trim() && !likes.includes(likeInput.trim())) {
      setLikes([...likes, likeInput.trim()]);
      setLikeInput('');
    }
  };

  const removeLike = (idx: number) => {
    setLikes(likes.filter((_, i) => i !== idx));
  };

  const addDislike = () => {
    if (dislikeInput.trim() && !dislikes.includes(dislikeInput.trim())) {
      setDislikes([...dislikes, dislikeInput.trim()]);
      setDislikeInput('');
    }
  };

  const removeDislike = (idx: number) => {
    setDislikes(dislikes.filter((_, i) => i !== idx));
  };

  const handleSave = async () => {
    setLoading(true);
    setError('');
    try {
      // 1. Save Profile (automatically calculates BMI on server)
      await profileAPI.updateProfile(profile);
      // 2. Save Medical History
      await profileAPI.updateMedicalHistory(medical);
      // 3. Save Allergies
      await profileAPI.updateAllergies(allergies);
      // 4. Save Likes / Dislikes
      await profileAPI.updatePreferences(likes, dislikes);
      
      onComplete();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to save health profile. Please check the fields.');
      setLoading(false);
    }
  };

  const stepsList = [
    { title: 'Personal Info', icon: UserRound },
    { title: 'Medical Conditions', icon: Stethoscope },
    { title: 'Allergies & Preferences', icon: AlertTriangle },
    { title: 'Socio-Economic & Region', icon: Banknote },
  ];

  return (
    <div className="min-h-screen bg-slate-950 py-12 px-4 relative overflow-hidden flex items-center justify-center">
      {/* Background decor */}
      <div className="absolute top-10 left-10 w-80 h-80 bg-teal-500/5 rounded-full blur-3xl" />
      <div className="absolute bottom-10 right-10 w-80 h-80 bg-indigo-500/5 rounded-full blur-3xl" />

      <div className="w-full max-w-3xl glass-panel rounded-3xl p-6 md:p-10 shadow-2xl relative z-10 my-4">
        {/* Progress header */}
        <div className="mb-8">
          <h1 className="text-3xl font-extrabold text-slate-100 text-center tracking-tight mb-2">
            Elderly Health Intake Wizard
          </h1>
          <p className="text-center text-slate-400 text-elderly-base mb-6">
            Help us understand your health profile to customize a clinical meal plan.
          </p>
          
          <div className="grid grid-cols-4 gap-2 border-b border-slate-800 pb-6">
            {stepsList.map((s, idx) => {
              const StepIcon = s.icon;
              const isActive = step === idx + 1;
              const isPast = step > idx + 1;
              return (
                <div key={idx} className="flex flex-col items-center text-center">
                  <div className={`w-12 h-12 rounded-xl flex items-center justify-center mb-2 transition-all ${
                    isActive 
                      ? 'bg-emerald-500 text-slate-950 font-bold scale-110 shadow-lg shadow-emerald-500/10' 
                      : isPast 
                        ? 'bg-emerald-500/20 text-emerald-400' 
                        : 'bg-slate-900 text-slate-500'
                  }`}>
                    <StepIcon className="w-6 h-6" />
                  </div>
                  <span className={`text-xs hidden md:inline font-medium ${
                    isActive ? 'text-emerald-400' : isPast ? 'text-slate-300' : 'text-slate-500'
                  }`}>
                    {s.title}
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        {error && (
          <div className="mb-6 p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-200 text-sm">
            {error}
          </div>
        )}

        {/* STEP 1: Personal Info */}
        {step === 1 && (
          <div className="space-y-6">
            <h2 className="text-xl font-bold text-emerald-400 border-l-4 border-emerald-500 pl-3 mb-4">
              Step 1: Personal Demographic Details
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-slate-300 font-medium mb-2 text-elderly-base">Full Name</label>
                <input
                  type="text"
                  name="name"
                  required
                  value={profile.name}
                  onChange={handleProfileChange}
                  placeholder="e.g. John Doe"
                  className="w-full bg-slate-900/50 border border-slate-700 rounded-xl py-3 px-4 text-slate-100 focus:outline-none focus:border-emerald-500 text-elderly-base"
                />
              </div>

              <div>
                <label className="block text-slate-300 font-medium mb-2 text-elderly-base">Age (Years)</label>
                <input
                  type="number"
                  name="age"
                  required
                  value={profile.age}
                  onChange={handleProfileChange}
                  className="w-full bg-slate-900/50 border border-slate-700 rounded-xl py-3 px-4 text-slate-100 focus:outline-none focus:border-emerald-500 text-elderly-base"
                />
              </div>

              <div>
                <label className="block text-slate-300 font-medium mb-2 text-elderly-base">Gender</label>
                <select
                  name="gender"
                  value={profile.gender}
                  onChange={handleProfileChange}
                  className="w-full bg-slate-900/50 border border-slate-700 rounded-xl py-3 px-4 text-slate-100 focus:outline-none focus:border-emerald-500 text-elderly-base"
                >
                  <option value="Male">Male</option>
                  <option value="Female">Female</option>
                  <option value="Other">Other</option>
                </select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-slate-300 font-medium mb-2 text-elderly-base">Height (cm)</label>
                  <input
                    type="number"
                    name="height"
                    required
                    value={profile.height}
                    onChange={handleProfileChange}
                    className="w-full bg-slate-900/50 border border-slate-700 rounded-xl py-3 px-4 text-slate-100 focus:outline-none focus:border-emerald-500 text-elderly-base"
                  />
                </div>
                <div>
                  <label className="block text-slate-300 font-medium mb-2 text-elderly-base">Weight (kg)</label>
                  <input
                    type="number"
                    name="weight"
                    required
                    value={profile.weight}
                    onChange={handleProfileChange}
                    className="w-full bg-slate-900/50 border border-slate-700 rounded-xl py-3 px-4 text-slate-100 focus:outline-none focus:border-emerald-500 text-elderly-base"
                  />
                </div>
              </div>

              <div>
                <label className="block text-slate-300 font-medium mb-2 text-elderly-base">Daily Activity Level</label>
                <select
                  name="activity_level"
                  value={profile.activity_level}
                  onChange={handleProfileChange}
                  className="w-full bg-slate-900/50 border border-slate-700 rounded-xl py-3 px-4 text-slate-100 focus:outline-none focus:border-emerald-500 text-elderly-base"
                >
                  <option value="Sedentary">Sedentary (No exercise, mostly sitting)</option>
                  <option value="Lightly Active">Lightly Active (Light walks, housework)</option>
                  <option value="Moderately Active">Moderately Active (Regular walking, gardening)</option>
                  <option value="Very Active">Very Active (Physical work, swimming, sports)</option>
                </select>
              </div>

              <div>
                <label className="block text-slate-300 font-medium mb-2 text-elderly-base">Dietary Preference</label>
                <select
                  name="food_preference"
                  value={profile.food_preference}
                  onChange={handleProfileChange}
                  className="w-full bg-slate-900/50 border border-slate-700 rounded-xl py-3 px-4 text-slate-100 focus:outline-none focus:border-emerald-500 text-elderly-base"
                >
                  <option value="Vegetarian">Vegetarian (Strict Veg)</option>
                  <option value="Veg (with Egg)">Veg (Includes Egg)</option>
                  <option value="Non-Vegetarian">Non-Vegetarian</option>
                  <option value="Vegan">Vegan (No Dairy)</option>
                </select>
              </div>
            </div>
          </div>
        )}

        {/* STEP 2: Medical Profile */}
        {step === 2 && (
          <div className="space-y-6">
            <h2 className="text-xl font-bold text-emerald-400 border-l-4 border-emerald-500 pl-3 mb-4">
              Step 2: Chronic Diseases & Health Disorders
            </h2>
            <p className="text-slate-400 text-sm mb-4">
              Select all diagnosed conditions. This is vital to prevent harmful dietary recommendations.
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {Object.keys(medical).map((key) => {
                if (key === 'others') return null;
                const fieldKey = key as keyof Omit<MedicalHistory, 'others'>;
                return (
                  <button
                    key={key}
                    type="button"
                    onClick={() => handleMedicalToggle(fieldKey)}
                    className={`p-4 rounded-xl border flex items-center justify-between text-left transition-all ${
                      medical[fieldKey]
                        ? 'bg-emerald-500/10 border-emerald-500 text-emerald-300 font-semibold shadow-md shadow-emerald-500/5'
                        : 'bg-slate-900/50 border-slate-800 text-slate-400 hover:border-slate-700'
                    }`}
                  >
                    <span className="capitalize text-elderly-base">{key.replace('_', ' ')}</span>
                    <div className={`w-5 h-5 rounded-full border flex items-center justify-center ${
                      medical[fieldKey] ? 'border-emerald-500 bg-emerald-500 text-slate-950' : 'border-slate-700'
                    }`}>
                      {medical[fieldKey] && <div className="w-2.5 h-2.5 bg-slate-950 rounded-full" />}
                    </div>
                  </button>
                );
              })}
            </div>

            <div>
              <label className="block text-slate-300 font-medium mb-2 text-elderly-base">Other Disorders or Comments</label>
              <textarea
                name="others"
                value={medical.others || ''}
                onChange={(e) => setMedical(prev => ({ ...prev, others: e.target.value }))}
                placeholder="Mention any other conditions, digestive issues, or special doctor's advice..."
                className="w-full bg-slate-900/50 border border-slate-700 rounded-xl py-3 px-4 text-slate-100 focus:outline-none focus:border-emerald-500 text-elderly-base h-24"
              />
            </div>
          </div>
        )}

        {/* STEP 3: Allergies & Food Likes/Dislikes */}
        {step === 3 && (
          <div className="space-y-6">
            <h2 className="text-xl font-bold text-emerald-400 border-l-4 border-emerald-500 pl-3 mb-4">
              Step 3: Food Allergies and Preferences
            </h2>

            {/* Allergies */}
            <div className="bg-slate-900/40 p-5 rounded-2xl border border-slate-800/80">
              <label className="block text-slate-300 font-bold mb-2 text-elderly-base flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-amber-500" /> Food Allergies / Intolerances
              </label>
              <div className="flex gap-2 mb-3">
                <input
                  type="text"
                  value={allergyInput}
                  onChange={(e) => setAllergyInput(e.target.value)}
                  placeholder="e.g. Peanuts, Milk, Gluten"
                  className="flex-1 bg-slate-900/50 border border-slate-700 rounded-xl py-2.5 px-4 text-slate-100 focus:outline-none focus:border-emerald-500 text-elderly-base"
                />
                <button
                  type="button"
                  onClick={addAllergy}
                  className="bg-emerald-500 text-slate-950 px-5 rounded-xl font-bold hover:brightness-110"
                >
                  Add
                </button>
              </div>
              <div className="flex flex-wrap gap-2">
                {allergies.map((alg, idx) => (
                  <span key={idx} className="bg-rose-500/10 border border-rose-500/30 text-rose-300 px-3 py-1.5 rounded-lg text-sm font-medium flex items-center gap-1">
                    {alg}
                    <button type="button" onClick={() => removeAllergy(idx)} className="hover:text-white font-bold ml-1">×</button>
                  </span>
                ))}
                {allergies.length === 0 && <p className="text-slate-500 text-sm">No allergies added yet.</p>}
              </div>
            </div>

            {/* Dislikes */}
            <div className="bg-slate-900/40 p-5 rounded-2xl border border-slate-800/80">
              <label className="block text-slate-300 font-bold mb-2 text-elderly-base">Foods Disliked (Will be excluded)</label>
              <div className="flex gap-2 mb-3">
                <input
                  type="text"
                  value={dislikeInput}
                  onChange={(e) => setDislikeInput(e.target.value)}
                  placeholder="e.g. Bitter gourd, Mushrooms, Papaya"
                  className="flex-1 bg-slate-900/50 border border-slate-700 rounded-xl py-2.5 px-4 text-slate-100 focus:outline-none focus:border-emerald-500 text-elderly-base"
                />
                <button
                  type="button"
                  onClick={addDislike}
                  className="bg-emerald-500 text-slate-950 px-5 rounded-xl font-bold hover:brightness-110"
                >
                  Add
                </button>
              </div>
              <div className="flex flex-wrap gap-2">
                {dislikes.map((dis, idx) => (
                  <span key={idx} className="bg-amber-500/10 border border-amber-500/20 text-amber-300 px-3 py-1.5 rounded-lg text-sm font-medium flex items-center gap-1">
                    {dis}
                    <button type="button" onClick={() => removeDislike(idx)} className="hover:text-white font-bold ml-1">×</button>
                  </span>
                ))}
                {dislikes.length === 0 && <p className="text-slate-500 text-sm">No disliked foods listed.</p>}
              </div>
            </div>

            {/* Likes */}
            <div className="bg-slate-900/40 p-5 rounded-2xl border border-slate-800/80">
              <label className="block text-slate-300 font-bold mb-2 text-elderly-base">Favorite Foods (Preferred if healthy)</label>
              <div className="flex gap-2 mb-3">
                <input
                  type="text"
                  value={likeInput}
                  onChange={(e) => setLikeInput(e.target.value)}
                  placeholder="e.g. Oats upma, Apple, Moong dal"
                  className="flex-1 bg-slate-900/50 border border-slate-700 rounded-xl py-2.5 px-4 text-slate-100 focus:outline-none focus:border-emerald-500 text-elderly-base"
                />
                <button
                  type="button"
                  onClick={addLike}
                  className="bg-emerald-500 text-slate-950 px-5 rounded-xl font-bold hover:brightness-110"
                >
                  Add
                </button>
              </div>
              <div className="flex flex-wrap gap-2">
                {likes.map((lk, idx) => (
                  <span key={idx} className="bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 px-3 py-1.5 rounded-lg text-sm font-medium flex items-center gap-1">
                    {lk}
                    <button type="button" onClick={() => removeLike(idx)} className="hover:text-white font-bold ml-1">×</button>
                  </span>
                ))}
                {likes.length === 0 && <p className="text-slate-500 text-sm">No favorite foods listed.</p>}
              </div>
            </div>
          </div>
        )}

        {/* STEP 4: Budget & Regional Habits */}
        {step === 4 && (
          <div className="space-y-6">
            <h2 className="text-xl font-bold text-emerald-400 border-l-4 border-emerald-500 pl-3 mb-4">
              Step 4: Economic Status and Cuisine Preference
            </h2>

            <div>
              <label className="block text-slate-300 font-bold mb-3 text-elderly-base flex items-center gap-2">
                <Banknote className="w-5 h-5 text-emerald-400" /> Economic Budget Category
              </label>
              <p className="text-slate-400 text-sm mb-4">
                This prevents the planner from recommending expensive imported products (e.g. avocados, salmon) for budget constraints, substituting affordable local items instead.
              </p>
              
              <div className="grid grid-cols-3 gap-4">
                {['Low', 'Medium', 'High'].map((budgetOpt) => (
                  <button
                    key={budgetOpt}
                    type="button"
                    onClick={() => setProfile(prev => ({ ...prev, economic_condition: budgetOpt }))}
                    className={`p-4 rounded-xl border font-bold text-center transition-all text-elderly-base ${
                      profile.economic_condition === budgetOpt
                        ? 'bg-emerald-500 text-slate-950 border-emerald-500 shadow-md shadow-emerald-500/10'
                        : 'bg-slate-900/50 border-slate-800 text-slate-400 hover:border-slate-700'
                    }`}
                  >
                    {budgetOpt} Cost
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-slate-300 font-bold mb-3 text-elderly-base flex items-center gap-2">
                <MapPin className="w-5 h-5 text-emerald-400" /> Regional Cuisine Style
              </label>
              <p className="text-slate-400 text-sm mb-4">
                Select the food culture you are accustomed to, so that the meal plan compiles familiar ingredients.
              </p>
              
              <select
                name="regional_cuisine"
                value={profile.regional_cuisine}
                onChange={handleProfileChange}
                className="w-full bg-slate-900/50 border border-slate-700 rounded-xl py-3 px-4 text-slate-100 focus:outline-none focus:border-emerald-500 text-elderly-base"
              >
                <option value="South Indian">South Indian (Idli, Dosa, Rice-Sambar, Avial)</option>
                <option value="North Indian">North Indian (Phulka, Dalia, Dal Tadka, Khichdi)</option>
                <option value="Bengali">Bengali (Macher Jhol, Rice, Alu Posto)</option>
                <option value="Punjabi">Punjabi (Chilla, Roti, Dal Fry, Curd)</option>
                <option value="Andhra">Andhra (Spiced Lentils, Rice, Vegetable Stew)</option>
                <option value="Tamil">Tamil (Steamed grains, Sambar, Rasam, Sundal)</option>
                <option value="Kerala">Kerala (Puttu, Brown Rice, Fish curry, Coconut gravies)</option>
              </select>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-slate-300 font-medium mb-2 text-elderly-base">Native Place</label>
                <input
                  type="text"
                  name="native_place"
                  value={profile.native_place || ''}
                  onChange={handleProfileChange}
                  placeholder="e.g. Nellore, Ludhiana"
                  className="w-full bg-slate-900/50 border border-slate-700 rounded-xl py-3 px-4 text-slate-100 focus:outline-none focus:border-emerald-500 text-elderly-base"
                />
              </div>
              <div>
                <label className="block text-slate-300 font-medium mb-2 text-elderly-base">State</label>
                <input
                  type="text"
                  name="state"
                  value={profile.state || ''}
                  onChange={handleProfileChange}
                  placeholder="e.g. Andhra Pradesh"
                  className="w-full bg-slate-900/50 border border-slate-700 rounded-xl py-3 px-4 text-slate-100 focus:outline-none focus:border-emerald-500 text-elderly-base"
                />
              </div>
            </div>
          </div>
        )}

        {/* Wizard Navigation */}
        <div className="flex items-center justify-between border-t border-slate-800 pt-8 mt-8">
          {step > 1 ? (
            <button
              type="button"
              onClick={() => setStep(step - 1)}
              className="py-3 px-6 rounded-xl border border-slate-700 text-slate-300 font-semibold hover:bg-slate-900 active:scale-[0.98] transition-all flex items-center gap-2 text-elderly-base"
            >
              <ArrowLeft className="w-5 h-5" /> Back
            </button>
          ) : (
            <div />
          )}

          {step < 4 ? (
            <button
              type="button"
              onClick={() => setStep(step + 1)}
              className="py-3 px-6 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-400 text-slate-950 font-bold hover:brightness-110 active:scale-[0.98] transition-all flex items-center gap-2 shadow-lg shadow-emerald-500/10 text-elderly-base"
            >
              Next Step <ArrowRight className="w-5 h-5" />
            </button>
          ) : (
            <button
              type="button"
              onClick={handleSave}
              disabled={loading}
              className="py-3 px-8 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-400 text-slate-950 font-extrabold hover:brightness-110 active:scale-[0.98] transition-all flex items-center gap-2 shadow-lg shadow-emerald-500/15 text-elderly-lg disabled:opacity-50"
            >
              {loading ? (
                <span className="w-6 h-6 border-2 border-slate-950 border-t-transparent rounded-full animate-spin" />
              ) : (
                <>
                  Complete & Save Profile <ShieldCheck className="w-6 h-6" />
                </>
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
