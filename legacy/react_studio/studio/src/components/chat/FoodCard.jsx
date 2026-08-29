import React, { useState } from 'react'
import { Star, Clock, MapPin, ExternalLink, Check, ShoppingBag, Flame, Sparkles } from 'lucide-react'
import { formatCurrency } from '../../lib/utils'

export function FoodCard({ item }) {
  const [isOrdered, setIsOrdered] = useState(false)
  const isTomato = item.platform?.toLowerCase() === 'tomato'

  const handleOrder = () => {
    setIsOrdered(true)
    setTimeout(() => setIsOrdered(false), 3000)
  }

  return (
    <div className="group relative rounded-2xl bg-surfaceLight/80 hover:bg-surfaceLight border border-surfaceBorder hover:border-brand-500/50 p-4 transition-all duration-300 hover:-translate-y-1 hover:shadow-glow flex flex-col justify-between overflow-hidden">
      {/* Top Banner: Badges & Platform Tag */}
      <div>
        <div className="flex items-center justify-between gap-2 mb-3">
          {/* Platform Tag */}
          <div
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold shadow-sm ${
              isTomato
                ? 'bg-tomato/20 border border-tomato/40 text-tomato-light'
                : 'bg-twiggy/20 border border-twiggy/40 text-twiggy-light'
            }`}
          >
            <span>{isTomato ? '🍅' : '🌿'}</span>
            <span>{item.platform}</span>
          </div>

          {/* Special Ranking Badges */}
          <div className="flex items-center gap-1">
            {item.badges && item.badges.length > 0 && (
              <span className="flex items-center gap-1 px-2 py-0.5 rounded-md bg-amber-500/20 border border-amber-500/40 text-amber-300 text-[10px] font-extrabold uppercase tracking-wide">
                <Sparkles className="w-3 h-3 text-amber-400" />
                {item.badges[0]}
              </span>
            )}
          </div>
        </div>

        {/* Dish Title & Veg/Non-Veg */}
        <div className="flex items-start gap-2.5 mb-1.5">
          {/* Veg / Non-veg symbol */}
          <div
            className={`mt-1 flex-shrink-0 w-3.5 h-3.5 rounded-sm border p-0.5 flex items-center justify-center ${
              item.is_veg
                ? 'border-green-500 text-green-500'
                : 'border-red-500 text-red-500'
            }`}
            title={item.is_veg ? 'Pure Vegetarian' : 'Non-Vegetarian'}
          >
            <div
              className={`w-1.5 h-1.5 rounded-full ${
                item.is_veg ? 'bg-green-500' : 'bg-red-500'
              }`}
            />
          </div>

          <div>
            <h4 className="text-sm font-bold text-slate-100 group-hover:text-brand-300 transition-colors line-clamp-1">
              {item.name}
            </h4>
            <p className="text-xs font-medium text-slate-400 line-clamp-1">
              {item.restaurant_name}
            </p>
          </div>
        </div>

        {/* Cuisine & Location */}
        <div className="flex items-center gap-2 text-[11px] text-slate-400 mb-3">
          <span className="px-1.5 py-0.5 rounded bg-surface/80 border border-white/5">
            {item.cuisine}
          </span>
          <span className="flex items-center gap-0.5 truncate max-w-[150px]">
            <MapPin className="w-3 h-3 text-slate-400 flex-shrink-0" />
            {item.location}
          </span>
        </div>
      </div>

      {/* Metrics Row: Price, Rating & Delivery ETA */}
      <div className="pt-3 border-t border-surfaceBorder/60 mt-2">
        <div className="flex items-center justify-between mb-3">
          {/* Price */}
          <div className="flex flex-col">
            <span className="text-[10px] text-slate-400 uppercase font-semibold">Price</span>
            <span className="text-base font-extrabold text-white tracking-tight">
              {formatCurrency(item.price)}
            </span>
          </div>

          {/* Rating */}
          <div className="flex items-center gap-1 px-2 py-1 rounded-lg bg-surface/90 border border-white/5">
            <Star className="w-3.5 h-3.5 fill-amber-400 text-amber-400" />
            <span className="text-xs font-bold text-slate-100">{item.rating}</span>
            <span className="text-[10px] text-slate-400">({item.ratings_count})</span>
          </div>

          {/* Delivery ETA */}
          <div className="flex items-center gap-1 px-2 py-1 rounded-lg bg-surface/90 border border-white/5">
            <Clock className="w-3.5 h-3.5 text-blue-400" />
            <span className="text-xs font-bold text-slate-100">{item.delivery_time_mins}m</span>
          </div>
        </div>

        {/* Action Button: Order on Tomato / Twiggy */}
        <button
          onClick={handleOrder}
          disabled={isOrdered}
          className={`w-full py-2 px-3 rounded-xl text-xs font-bold flex items-center justify-center gap-1.5 transition-all ${
            isOrdered
              ? 'bg-green-600 text-white'
              : isTomato
              ? 'bg-tomato hover:bg-tomato-light text-white shadow-glowTomato'
              : 'bg-twiggy hover:bg-twiggy-light text-white shadow-glowTwiggy'
          }`}
        >
          {isOrdered ? (
            <>
              <Check className="w-3.5 h-3.5" />
              <span>Ordering on {item.platform}...</span>
            </>
          ) : (
            <>
              <ShoppingBag className="w-3.5 h-3.5" />
              <span>Order on {item.platform}</span>
            </>
          )}
        </button>
      </div>
    </div>
  )
}
