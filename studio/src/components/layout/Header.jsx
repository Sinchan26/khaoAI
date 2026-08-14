import React from 'react'
import { MapPin, User, LogOut, Settings, Sparkles, UtensilsCrossed } from 'lucide-react'
import { useAuth } from '../../contexts/AuthContext'

export function Header({ onToggleSidebar, isSidebarOpen }) {
  const { user, logout, setIsAuthModalOpen, setIsSettingsModalOpen, settings } = useAuth()

  return (
    <header className="h-16 border-b border-surfaceBorder bg-surface/80 backdrop-blur-xl px-4 lg:px-6 flex items-center justify-between z-30 select-none">
      {/* Left: Brand & Sidebar Toggle */}
      <div className="flex items-center gap-3">
        <button
          onClick={onToggleSidebar}
          className="p-2 rounded-xl bg-surfaceLight hover:bg-surfaceBorder text-slate-300 hover:text-white transition-all duration-200 lg:hidden"
          aria-label="Toggle Navigation"
        >
          <UtensilsCrossed className="w-5 h-5 text-brand-500" />
        </button>

        <div className="flex items-center gap-2.5 cursor-pointer">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-brand-500 via-amber-500 to-tomato flex items-center justify-center shadow-glow text-lg font-bold text-white">
            🍲
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="font-display font-bold text-xl tracking-tight bg-gradient-to-r from-white via-slate-100 to-brand-300 bg-clip-text text-transparent">
                khaoAI
              </span>
              <span className="text-[10px] uppercase font-extrabold px-1.5 py-0.5 rounded-full bg-brand-500/20 text-brand-400 border border-brand-500/30">
                Agentic
              </span>
            </div>
          </div>
        </div>

        {/* Live Multi-Platform Badge */}
        <div className="hidden md:flex items-center gap-2 ml-4 pl-4 border-l border-surfaceBorder/80 text-xs">
          <span className="text-slate-400 font-medium">Scanning:</span>
          <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-tomato/15 border border-tomato/30 text-tomato-light font-semibold">
            <span>🍅</span>
            <span>Tomato</span>
          </div>
          <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-twiggy/15 border border-twiggy/30 text-twiggy-light font-semibold">
            <span>🌿</span>
            <span>Twiggy</span>
          </div>
        </div>
      </div>

      {/* Right: Location Pill, Settings & User Auth */}
      <div className="flex items-center gap-2.5">
        {/* Location Quick Pill */}
        <button
          onClick={() => setIsSettingsModalOpen(true)}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-surfaceLight/80 hover:bg-surfaceBorder border border-white/5 text-xs text-slate-300 transition-all duration-200 group"
          title="Click to change location or dietary preferences"
        >
          <MapPin className="w-3.5 h-3.5 text-brand-400 group-hover:scale-110 transition-transform" />
          <span className="font-medium max-w-[140px] truncate">
            {settings?.default_location || 'Salt Lake, Sector V'}
          </span>
        </button>

        {/* Settings button */}
        <button
          onClick={() => setIsSettingsModalOpen(true)}
          className="p-2 rounded-xl bg-surfaceLight/80 hover:bg-surfaceBorder text-slate-400 hover:text-slate-200 transition-colors"
          title="Preferences & Settings"
        >
          <Settings className="w-4 h-4" />
        </button>

        {/* Auth profile / Login Button */}
        {user ? (
          <div className="flex items-center gap-2 pl-1">
            <div className="hidden sm:flex flex-col items-end">
              <span className="text-xs font-semibold text-slate-200 leading-tight">
                {user.display_name}
              </span>
              <span className="text-[10px] text-slate-400 leading-none">
                {user.email}
              </span>
            </div>
            <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-brand-600 to-amber-500 flex items-center justify-center text-xs font-bold text-white shadow-sm ring-2 ring-brand-500/20">
              {user.display_name?.charAt(0).toUpperCase() || 'U'}
            </div>
            <button
              onClick={logout}
              className="p-2 rounded-xl hover:bg-red-500/20 text-slate-400 hover:text-red-400 transition-colors"
              title="Sign Out"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        ) : (
          <button
            onClick={() => setIsAuthModalOpen(true)}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-gradient-to-r from-brand-500 to-amber-500 hover:from-brand-600 hover:to-amber-600 text-xs font-bold text-white shadow-glow transition-all active:scale-95"
          >
            <User className="w-3.5 h-3.5" />
            <span>Sign In</span>
          </button>
        )}
      </div>
    </header>
  )
}
