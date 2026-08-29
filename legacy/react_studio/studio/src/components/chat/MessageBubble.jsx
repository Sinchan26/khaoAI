import React from 'react'
import { FoodCard } from './FoodCard'
import { getMealEmoji } from '../../lib/utils'
import { MapPin, Sparkles } from 'lucide-react'

export function MessageBubble({ message, isStreamingNow }) {
  const isUser = message.role === 'user'

  if (isUser) {
    return (
      <div className="flex justify-end gap-2.5 my-4 animate-slide-up">
        <div className="max-w-xl rounded-2xl rounded-tr-sm bg-gradient-to-r from-brand-600 to-amber-600 text-white px-4 py-3 shadow-lg shadow-brand-500/10">
          <p className="text-sm font-medium leading-relaxed whitespace-pre-wrap">
            {message.content}
          </p>
        </div>
      </div>
    )
  }

  const recommendations = message.recommendations || []

  return (
    <div className="flex items-start gap-3 my-4 animate-slide-up">
      {/* AI Bot Avatar */}
      <div className="flex-shrink-0 w-8 h-8 rounded-xl bg-gradient-to-br from-brand-500 via-amber-500 to-tomato flex items-center justify-center shadow-glow text-sm font-bold text-white mt-1">
        🍲
      </div>

      <div className="flex-1 max-w-4xl space-y-4">
        {/* Assistant Chat Bubble */}
        <div className="glass-panel rounded-2xl rounded-tl-sm p-4 text-slate-200">
          {/* Header metadata pill if meal_type exists */}
          {message.meal_type && (
            <div className="flex items-center gap-2 mb-2 pb-2 border-b border-white/5 text-xs text-slate-400">
              <span className="flex items-center gap-1 font-semibold text-brand-400">
                <span>{getMealEmoji(message.meal_type)}</span>
                <span className="capitalize">{message.meal_type} Options</span>
              </span>
              {message.location && (
                <span className="flex items-center gap-1 text-slate-400">
                  <MapPin className="w-3 h-3 text-slate-400" />
                  <span>{message.location}</span>
                </span>
              )}
            </div>
          )}

          {/* Message Text */}
          <div className="text-sm leading-relaxed text-slate-200 whitespace-pre-wrap">
            {message.content}
            {isStreamingNow && (
              <span className="inline-block w-1.5 h-4 ml-1 bg-brand-400 animate-pulse align-middle" />
            )}
          </div>
        </div>

        {/* Food Recommendations Cards Grid */}
        {recommendations.length > 0 && (
          <div className="space-y-2">
            <div className="flex items-center justify-between px-1">
              <div className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-slate-400">
                <Sparkles className="w-3.5 h-3.5 text-amber-400" />
                <span>Top Ranked Recommendations (Cheapest + Top Rated + Fastest)</span>
              </div>
              <span className="text-xs text-slate-400">
                {recommendations.length} picks
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {recommendations.map((item, idx) => (
                <FoodCard key={item.id || idx} item={item} />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
