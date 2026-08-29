import React, { useState, useEffect } from 'react'
import { X, MapPin, Leaf, DollarSign, Clock, Check } from 'lucide-react'
import { useAuth } from '../../contexts/AuthContext'

const POPULAR_LOCATIONS = [
  "Salt Lake, Sector V",
  "Salt Lake, Sector I",
  "Park Street, Kolkata",
  "New Town, Action Area 1",
  "Ballygunge, Kolkata",
  "Indiranagar, Bangalore",
  "Koramangala, Bangalore",
  "HSR Layout, Bangalore",
  "Bandra West, Mumbai",
  "Connaught Place, Delhi"
]

export function SettingsModal() {
  const { isSettingsModalOpen, setIsSettingsModalOpen, settings, saveSettings } = useAuth()
  const [formData, setFormData] = useState({
    default_location: 'Salt Lake, Sector V',
    dietary_preference: 'all',
    budget_preference: 'medium',
    max_delivery_time: 45
  })
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    if (settings) {
      setFormData(settings)
    }
  }, [settings])

  if (!isSettingsModalOpen) return null

  const handleSave = (e) => {
    e.preventDefault()
    saveSettings(formData)
    setSaved(true)
    setTimeout(() => {
      setSaved(false)
      setIsSettingsModalOpen(false)
    }, 1000)
  }

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-md flex items-center justify-center p-4 z-50 animate-fade-in select-none">
      <div className="relative w-full max-w-lg bg-surface border border-surfaceBorder rounded-3xl p-6 shadow-2xl space-y-5 animate-slide-up">
        {/* Close Button */}
        <button
          onClick={() => setIsSettingsModalOpen(false)}
          className="absolute top-4 right-4 p-2 rounded-xl bg-surfaceLight text-slate-400 hover:text-white"
        >
          <X className="w-4 h-4" />
        </button>

        {/* Header */}
        <div>
          <h2 className="font-display text-xl font-bold text-white flex items-center gap-2">
            <span>⚙️</span>
            <span>Food Search Preferences</span>
          </h2>
          <p className="text-xs text-slate-400">
            Customize your default location, dietary preference, and budget.
          </p>
        </div>

        <form onSubmit={handleSave} className="space-y-4">
          {/* Location Picker */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1 flex items-center gap-1.5">
              <MapPin className="w-3.5 h-3.5 text-brand-400" />
              <span>Current Delivery Location</span>
            </label>
            <input
              type="text"
              value={formData.default_location}
              onChange={(e) => setFormData({ ...formData, default_location: e.target.value })}
              placeholder="Enter your area..."
              className="w-full bg-surfaceLight border border-surfaceBorder focus:border-brand-500 rounded-xl p-2.5 text-xs text-white placeholder-slate-400 focus:outline-none mb-2"
            />
            {/* Quick Location Chips */}
            <div className="flex flex-wrap gap-1.5">
              {POPULAR_LOCATIONS.map((loc) => (
                <button
                  type="button"
                  key={loc}
                  onClick={() => setFormData({ ...formData, default_location: loc })}
                  className={`px-2 py-1 rounded-lg text-[11px] font-medium transition-all ${
                    formData.default_location === loc
                      ? 'bg-brand-500/20 border border-brand-500 text-brand-300'
                      : 'bg-surfaceLight hover:bg-surfaceBorder text-slate-400'
                  }`}
                >
                  {loc}
                </button>
              ))}
            </div>
          </div>

          {/* Dietary Preference */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5 flex items-center gap-1.5">
              <Leaf className="w-3.5 h-3.5 text-green-400" />
              <span>Dietary Preference</span>
            </label>
            <div className="grid grid-cols-3 gap-2">
              {[
                { id: 'all', label: 'All Cuisines 🍗🥗' },
                { id: 'veg', label: 'Pure Veg 🌱' },
                { id: 'non-veg', label: 'Non-Veg Fav 🍖' }
              ].map((opt) => (
                <button
                  type="button"
                  key={opt.id}
                  onClick={() => setFormData({ ...formData, dietary_preference: opt.id })}
                  className={`p-2.5 rounded-xl text-xs font-semibold border transition-all text-center ${
                    formData.dietary_preference === opt.id
                      ? 'bg-brand-500/20 border-brand-500 text-white shadow-glow'
                      : 'bg-surfaceLight border-surfaceBorder text-slate-400 hover:text-slate-200'
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>

          {/* Budget Preference */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5 flex items-center gap-1.5">
              <DollarSign className="w-3.5 h-3.5 text-amber-400" />
              <span>Budget Preference</span>
            </label>
            <div className="grid grid-cols-3 gap-2">
              {[
                { id: 'budget', label: 'Budget Friendly (₹)' },
                { id: 'medium', label: 'Balanced (₹₹)' },
                { id: 'premium', label: 'Gourmet (₹₹₹)' }
              ].map((opt) => (
                <button
                  type="button"
                  key={opt.id}
                  onClick={() => setFormData({ ...formData, budget_preference: opt.id })}
                  className={`p-2.5 rounded-xl text-xs font-semibold border transition-all text-center ${
                    formData.budget_preference === opt.id
                      ? 'bg-amber-500/20 border-amber-500 text-white shadow-glow'
                      : 'bg-surfaceLight border-surfaceBorder text-slate-400 hover:text-slate-200'
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>

          {/* Save Button */}
          <div className="pt-3 border-t border-surfaceBorder">
            <button
              type="submit"
              className="w-full py-2.5 rounded-xl bg-gradient-to-r from-brand-500 to-amber-500 hover:from-brand-600 hover:to-amber-600 text-white text-xs font-bold shadow-glow transition-all flex items-center justify-center gap-1.5 active:scale-98"
            >
              {saved ? (
                <>
                  <Check className="w-4 h-4" />
                  <span>Preferences Saved!</span>
                </>
              ) : (
                <span>Save Preferences</span>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
