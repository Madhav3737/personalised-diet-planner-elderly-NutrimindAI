import React, { useState } from 'react';
import { Heart, Bot, User, LogOut, Menu, X } from 'lucide-react';

interface NavBarProps {
  currentView: 'DASHBOARD' | 'CHAT' | 'WIZARD';
  onNavigate: (view: 'DASHBOARD' | 'CHAT' | 'WIZARD') => void;
  onLogout: () => void;
}

export const NavBar: React.FC<NavBarProps> = ({ currentView, onNavigate, onLogout }) => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navItems = [
    { view: 'DASHBOARD' as const, label: 'Dashboard', icon: Heart },
    { view: 'CHAT' as const, label: 'Dietician Chat', icon: Bot },
    { view: 'WIZARD' as const, label: 'Update Profile', icon: User },
  ];

  const handleNavClick = (view: 'DASHBOARD' | 'CHAT' | 'WIZARD') => {
    onNavigate(view);
    setMobileMenuOpen(false);
  };

  return (
    <nav className="glass-panel sticky top-0 z-50 w-full px-6 py-4 shadow-md">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        {/* Brand Logo */}
        <div 
          className="flex items-center gap-3 cursor-pointer select-none active:scale-[0.98] transition-transform"
          onClick={() => handleNavClick('DASHBOARD')}
        >
          <div className="w-10 h-10 bg-emerald-500 rounded-xl flex items-center justify-center shadow-lg shadow-emerald-500/10">
            <Heart className="w-6 h-6 text-slate-950 fill-slate-950 animate-pulse" />
          </div>
          <div>
            <h1 className="text-xl font-bold bg-gradient-to-r from-emerald-400 to-teal-300 bg-clip-text text-transparent">
              NutriMind AI
            </h1>
            <span className="text-xs text-slate-400 block -mt-1">Dietician & Geriatric Portal</span>
          </div>
        </div>

        {/* Desktop Navigation */}
        <div className="hidden md:flex items-center gap-6">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = currentView === item.view;
            return (
              <button
                key={item.view}
                onClick={() => handleNavClick(item.view)}
                className={`flex items-center gap-2 py-2 px-4 rounded-xl font-bold text-elderly-base transition-all duration-200 border ${
                  isActive
                    ? 'bg-emerald-500/15 border-emerald-500/35 text-emerald-300'
                    : 'bg-transparent border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-900/40'
                }`}
              >
                <Icon className={`w-5 h-5 ${isActive ? 'text-emerald-400' : 'text-slate-400'}`} />
                {item.label}
              </button>
            );
          })}
        </div>

        {/* Logout Button */}
        <div className="hidden md:flex items-center gap-4">
          <button
            onClick={onLogout}
            className="flex items-center gap-2 py-2 px-4 rounded-xl bg-slate-900 border border-slate-700 text-slate-400 hover:text-rose-450 hover:border-rose-500/30 hover:bg-rose-500/5 transition-all text-elderly-base font-bold cursor-pointer"
            title="Log Out"
          >
            <LogOut className="w-5 h-5" />
            <span>Log Out</span>
          </button>
        </div>

        {/* Mobile menu button */}
        <div className="md:hidden flex items-center">
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="p-2.5 rounded-xl bg-slate-900 border border-slate-700 text-slate-400 hover:text-slate-200 cursor-pointer"
            aria-label="Toggle menu"
          >
            {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>
      </div>

      {/* Mobile Menu Dropdown */}
      {mobileMenuOpen && (
        <div className="md:hidden mt-4 pt-4 border-t border-slate-800/80 flex flex-col gap-3">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = currentView === item.view;
            return (
              <button
                key={item.view}
                onClick={() => handleNavClick(item.view)}
                className={`flex items-center gap-3 py-3 px-5 rounded-xl font-bold text-elderly-base text-left transition-all border cursor-pointer ${
                  isActive
                    ? 'bg-emerald-500/15 border-emerald-500/35 text-emerald-300'
                    : 'bg-slate-900/40 border-transparent text-slate-400'
                }`}
              >
                <Icon className={`w-6 h-6 ${isActive ? 'text-emerald-400' : 'text-slate-400'}`} />
                <span>{item.label}</span>
              </button>
            );
          })}
          
          <button
            onClick={() => {
              setMobileMenuOpen(false);
              onLogout();
            }}
            className="flex items-center gap-3 py-3 px-5 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 font-bold text-elderly-base text-left transition-all cursor-pointer"
          >
            <LogOut className="w-6 h-6" />
            <span>Log Out</span>
          </button>
        </div>
      )}
    </nav>
  );
};
