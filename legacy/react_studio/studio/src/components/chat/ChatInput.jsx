import React, { useState, useRef, useEffect } from 'react'
import { Send, Sparkles, Leaf, DollarSign, Zap } from 'lucide-react'

export function ChatInput({ onSendMessage, isStreaming, currentFilter, onSelectFilter }) {
  const [input, setInput] = useState('')
  const inputRef = useRef(null)

  useEffect(() => {
    inputRef.current?.focus()
  }, [])

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!input.trim() || isStreaming) return
    onSendMessage(input.trim())
    setInput('')
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  return (
    <div className="w-full max-w-4xl mx-auto px-4 pb-4 pt-2">
      {/* Quick Filter Pills Row */}
      <div className="flex items-center gap-2 mb-2 px-1 overflow-x-auto text-xs select-none">
        <span className="text-[11px] font-semibold text-slate-400">Quick Filter:</span>
        <button
          type="button"
          onClick={() => onSelectFilter(currentFilter === 'veg' ? null : 'veg')}
          className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full font-medium transition-all ${
            currentFilter === 'veg'
              ? 'bg-green-500/20 border border-green-500 text-green-300'
              : 'bg-surfaceLight/60 hover:bg-surfaceLight border border-white/5 text-slate-300'
          }`}
        >
          <Leaf className="w-3 h-3 text-green-400" />
          <span>Veg Only</span>
        </button>

        <button
          type="button"
          onClick={() => onSelectFilter(currentFilter === 'budget' ? null : 'budget')}
          className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full font-medium transition-all ${
            currentFilter === 'budget'
              ? 'bg-amber-500/20 border border-amber-500 text-amber-300'
              : 'bg-surfaceLight/60 hover:bg-surfaceLight border border-white/5 text-slate-300'
          }`}
        >
          <DollarSign className="w-3 h-3 text-amber-400" />
          <span>Under ₹200</span>
        </button>

        <button
          type="button"
          onClick={() => onSelectFilter(currentFilter === 'fast' ? null : 'fast')}
          className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full font-medium transition-all ${
            currentFilter === 'fast'
              ? 'bg-blue-500/20 border border-blue-500 text-blue-300'
              : 'bg-surfaceLight/60 hover:bg-surfaceLight border border-white/5 text-slate-300'
          }`}
        >
          <Zap className="w-3 h-3 text-blue-400" />
          <span>Fast Delivery (≤25m)</span>
        </button>
      </div>

      {/* Floating Glass Input Container */}
      <form
        onSubmit={handleSubmit}
        className="relative flex items-center rounded-2xl glass-input p-2 pl-4 focus-within:border-brand-500/60 focus-within:shadow-glow transition-all duration-200"
      >
        <textarea
          ref={inputRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask anything... e.g. 'Hey what should I eat now?' or 'Best mutton biryani in Salt Lake'"
          rows={1}
          disabled={isStreaming}
          className="w-full bg-transparent text-sm text-slate-100 placeholder-slate-400 focus:outline-none resize-none max-h-24 py-1.5"
        />

        <button
          type="submit"
          disabled={!input.trim() || isStreaming}
          className={`p-2.5 rounded-xl font-bold transition-all duration-200 flex items-center justify-center ${
            input.trim() && !isStreaming
              ? 'bg-gradient-to-r from-brand-500 to-amber-500 hover:from-brand-600 hover:to-amber-600 text-white shadow-glow active:scale-95'
              : 'bg-surfaceLight text-slate-400 cursor-not-allowed opacity-60'
          }`}
          aria-label="Send message"
        >
          <Send className="w-4 h-4" />
        </button>
      </form>
    </div>
  )
}
