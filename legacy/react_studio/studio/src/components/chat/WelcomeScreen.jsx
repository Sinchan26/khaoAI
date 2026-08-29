import React from 'react'
import { Sparkles, Utensils, Zap, DollarSign, Star, Compass } from 'lucide-react'
import { useAuth } from '../../contexts/AuthContext'

export function WelcomeScreen({ onSelectPrompt }) {
  const { settings } = useAuth()

  const suggestedPrompts = [
    {
      title: "What should I eat now?",
      description: "Auto-detects meal time & finds cheapest + top-rated options",
      emoji: "🍛",
      category: "Smart Concierge",
      border: "hover:border-brand-500/50"
    },
    {
      title: "Cheapest Biryani deals under ₹300",
      description: "Compares Biryani across Tomato 🍅 and Twiggy 🌿",
      emoji: "🍗",
      category: "Budget Picks",
      border: "hover:border-amber-500/50"
    },
    {
      title: "Fastest delivery healthy lunch",
      description: "Fresh bowls, salads & thalis ready in ≤ 20 mins",
      emoji: "🥗",
      category: "Speed & Nutrition",
      border: "hover:border-green-500/50"
    },
    {
      title: "Late night sweet cravings & rolls",
      description: "Kathi rolls, waffles & desserts open right now",
      emoji: "🌯",
      category: "Night Bites",
      border: "hover:border-purple-500/50"
    }
  ]

  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] max-w-2xl mx-auto px-4 text-center select-none animate-fade-in my-auto">
      {/* Hero Badge */}
      <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-brand-500/15 border border-brand-500/30 text-brand-400 text-xs font-bold mb-4 shadow-glow">
        <Sparkles className="w-3.5 h-3.5 text-amber-400" />
        <span>Multi-Platform AI Food Concierge</span>
      </div>

      {/* Main Headline */}
      <h1 className="font-display text-3xl sm:text-4xl font-extrabold text-white tracking-tight mb-2">
        Hungry? Let's find your <br />
        <span className="bg-gradient-to-r from-brand-400 via-amber-400 to-tomato-light bg-clip-text text-transparent">
          perfect meal in seconds.
        </span>
      </h1>

      {/* Subtitle */}
      <p className="text-sm text-slate-400 max-w-lg mb-8">
        Ask naturally in plain English. I'll scan <span className="text-tomato-light font-semibold">Tomato 🍅</span> and{' '}
        <span className="text-twiggy-light font-semibold">Twiggy 🌿</span> to prioritize the cheapest, top-rated, and fastest delivery options around{' '}
        <span className="text-slate-200 font-medium">{settings?.default_location || 'your location'}</span>.
      </p>

      {/* Suggested Prompt Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full text-left">
        {suggestedPrompts.map((p, idx) => (
          <button
            key={idx}
            onClick={() => onSelectPrompt(p.title)}
            className={`p-4 rounded-2xl bg-surfaceLight/60 hover:bg-surfaceLight border border-surfaceBorder ${p.border} transition-all duration-300 hover:-translate-y-1 hover:shadow-glow text-left group`}
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-2xl group-hover:scale-125 transition-transform">
                {p.emoji}
              </span>
              <span className="text-[10px] uppercase font-bold text-slate-400 bg-surface/80 px-2 py-0.5 rounded-md border border-white/5">
                {p.category}
              </span>
            </div>
            <h3 className="text-sm font-bold text-slate-100 group-hover:text-brand-300 transition-colors mb-1">
              "{p.title}"
            </h3>
            <p className="text-xs text-slate-400">
              {p.description}
            </p>
          </button>
        ))}
      </div>
    </div>
  )
}
