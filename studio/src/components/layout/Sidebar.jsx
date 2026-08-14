import React from 'react'
import { Plus, Trash2, Clock, Sparkles, Filter, Leaf, Zap, DollarSign, X } from 'lucide-react'
import { useAuth } from '../../contexts/AuthContext'

export function Sidebar({
  isOpen,
  onClose,
  onNewSession,
  onClearSession,
  onSelectPrompt,
  onSelectFilter,
  activeFilter
}) {
  const { settings } = useAuth()

  const mealPrompts = [
    { label: "What's for breakfast?", emoji: "🥞", time: "6 AM - 11 AM" },
    { label: "Find best lunch options", emoji: "🍛", time: "11 AM - 4 PM" },
    { label: "Evening tea & snacks", emoji: "☕", time: "4 PM - 7:30 PM" },
    { label: "Suggest dinner near me", emoji: "🍲", time: "7:30 PM - 11:30 PM" },
    { label: "Late night cravings", emoji: "🌙", time: "11:30 PM - 6 AM" }
  ]

  const filterChips = [
    { id: 'veg', label: 'Pure Veg Only', icon: Leaf, color: 'text-green-400' },
    { id: 'budget', label: 'Under ₹200', icon: DollarSign, color: 'text-amber-400' },
    { id: 'fast', label: 'Fast (≤25 min)', icon: Zap, color: 'text-blue-400' }
  ]

  return (
    <>
      {/* Mobile backdrop overlay */}
      {isOpen && (
        <div
          onClick={onClose}
          className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 lg:hidden animate-fade-in"
        />
      )}

      <aside
        className={`
          fixed lg:static top-0 left-0 bottom-0 w-72 bg-surface/95 lg:bg-surface/50 border-r border-surfaceBorder
          p-4 flex flex-col justify-between z-40 transition-transform duration-300 ease-in-out
          ${isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
        `}
      >
        {/* Top Section */}
        <div className="space-y-5 overflow-y-auto pr-1">
          {/* Mobile close button */}
          <div className="flex items-center justify-between lg:hidden pb-2 border-b border-surfaceBorder">
            <span className="text-sm font-bold text-slate-200">Navigation</span>
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg bg-surfaceLight text-slate-400 hover:text-white"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* New Chat Button */}
          <button
            onClick={() => {
              onNewSession()
              if (window.innerWidth < 1024) onClose()
            }}
            className="w-full flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl bg-gradient-to-r from-brand-500 to-amber-500 hover:from-brand-600 hover:to-amber-600 text-white font-semibold text-sm shadow-glow transition-all active:scale-[0.98]"
          >
            <Plus className="w-4 h-4 stroke-[2.5]" />
            <span>New Food Search</span>
          </button>

          {/* Quick Meal Times */}
          <div className="space-y-2">
            <div className="flex items-center gap-1.5 px-1 text-[11px] font-bold uppercase tracking-wider text-slate-400">
              <Clock className="w-3.5 h-3.5 text-brand-400" />
              <span>Explore by Meal Time</span>
            </div>
            <div className="space-y-1">
              {mealPrompts.map((m, idx) => (
                <button
                  key={idx}
                  onClick={() => {
                    onSelectPrompt(m.label)
                    if (window.innerWidth < 1024) onClose()
                  }}
                  className="w-full flex items-center justify-between p-2.5 rounded-xl bg-surfaceLight/40 hover:bg-surfaceLight border border-white/5 hover:border-brand-500/30 text-left text-xs text-slate-200 transition-all duration-200 group"
                >
                  <div className="flex items-center gap-2.5">
                    <span className="text-base group-hover:scale-125 transition-transform">{m.emoji}</span>
                    <span className="font-medium group-hover:text-brand-300 transition-colors">{m.label}</span>
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Smart Filter Toggles */}
          <div className="space-y-2 pt-2">
            <div className="flex items-center gap-1.5 px-1 text-[11px] font-bold uppercase tracking-wider text-slate-400">
              <Filter className="w-3.5 h-3.5 text-brand-400" />
              <span>Instant Filters</span>
            </div>
            <div className="space-y-1.5">
              {filterChips.map((chip) => {
                const Icon = chip.icon
                const isActive = activeFilter === chip.id
                return (
                  <button
                    key={chip.id}
                    onClick={() => onSelectFilter(isActive ? null : chip.id)}
                    className={`w-full flex items-center justify-between p-2.5 rounded-xl text-xs font-medium transition-all ${
                      isActive
                        ? 'bg-brand-500/20 border border-brand-500 text-white shadow-glow'
                        : 'bg-surfaceLight/40 hover:bg-surfaceLight border border-white/5 text-slate-300'
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      <Icon className={`w-3.5 h-3.5 ${chip.color}`} />
                      <span>{chip.label}</span>
                    </div>
                    {isActive && (
                      <span className="w-2 h-2 rounded-full bg-brand-400 animate-pulse" />
                    )}
                  </button>
                )
              })}
            </div>
          </div>
        </div>

        {/* Bottom Actions */}
        <div className="pt-4 border-t border-surfaceBorder">
          <button
            onClick={() => {
              if (window.confirm('Clear current food search history?')) {
                onClearSession()
              }
            }}
            className="w-full flex items-center justify-center gap-2 p-2.5 rounded-xl hover:bg-red-500/15 border border-transparent hover:border-red-500/30 text-xs font-semibold text-slate-400 hover:text-red-400 transition-all"
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span>Clear Conversation</span>
          </button>
        </div>
      </aside>
    </>
  )
}
