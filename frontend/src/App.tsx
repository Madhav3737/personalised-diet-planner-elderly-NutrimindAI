import React, { useEffect, useState } from 'react';
import { Login } from './pages/Login';
import { IntakeWizard } from './pages/IntakeWizard';
import { Dashboard } from './pages/Dashboard';
import { Chat } from './pages/Chat';
import { profileAPI, authAPI } from './services/api';
import { NavBar } from './components/NavBar';

type PageView = 'DASHBOARD' | 'CHAT' | 'WIZARD';

export const App: React.FC = () => {
  const [authenticated, setAuthenticated] = useState(authAPI.isAuthenticated());
  const [profileComplete, setProfileComplete] = useState<boolean | null>(null);
  const [currentView, setCurrentView] = useState<PageView>('DASHBOARD');
  const [checking, setChecking] = useState(true);

  const checkProfileState = async () => {
    if (!authenticated) {
      setChecking(false);
      return;
    }
    
    try {
      await profileAPI.getProfile();
      setProfileComplete(true);
      setCurrentView('DASHBOARD');
    } catch (err: any) {
      // 404 profile not found means onboarding is required
      if (err.response?.status === 404 || err.response?.status === 444) {
        setProfileComplete(false);
        setCurrentView('WIZARD');
      } else {
        // Token expired or invalid
        authAPI.logout();
        setAuthenticated(false);
      }
    } finally {
      setChecking(false);
    }
  };

  useEffect(() => {
    checkProfileState();
  }, [authenticated]);

  const handleLoginSuccess = () => {
    setAuthenticated(true);
    setChecking(true);
  };

  const handleLogout = () => {
    authAPI.logout();
    setAuthenticated(false);
    setProfileComplete(null);
    setCurrentView('DASHBOARD');
  };

  if (checking) {
    return (
      <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center text-slate-100">
        <div className="w-12 h-12 border-4 border-emerald-500 border-t-transparent rounded-full animate-spin mb-4" />
        <p className="text-elderly-base font-semibold">Synchronizing healthcare profile...</p>
      </div>
    );
  }

  if (!authenticated) {
    return <Login onLoginSuccess={handleLoginSuccess} />;
  }

  if (profileComplete === false) {
    return (
      <IntakeWizard 
        onComplete={() => {
          setProfileComplete(true);
          setCurrentView('DASHBOARD');
        }} 
      />
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      <NavBar 
        currentView={currentView}
        onNavigate={setCurrentView}
        onLogout={handleLogout}
      />
      <div className="flex-1">
        {currentView === 'DASHBOARD' && (
          <Dashboard />
        )}
        {currentView === 'CHAT' && (
          <Chat />
        )}
        {currentView === 'WIZARD' && (
          <IntakeWizard 
            onComplete={() => {
              setProfileComplete(true);
              setCurrentView('DASHBOARD');
            }} 
          />
        )}
      </div>
    </div>
  );
};

export default App;
