import React, { useRef, useEffect } from 'react'
import { MessageBubble } from './MessageBubble'
import { WelcomeScreen } from './WelcomeScreen'
import { Loader2, Sparkles, ChefHat } from 'lucide-react'

export function ChatWindow({
  messages,
  isStreaming,
  currentStatus,
  streamingContent,
  onSelectPrompt
}) {
  const scrollRef = useRef(null)

  const scrollToBottom = () => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, streamingContent, currentStatus])

  return (
    <div
      ref={scrollRef}
      className="flex-1 overflow-y-auto p-4 lg:p-6 space-y-4 relative scroll-smooth flex flex-col"
    >
      {messages.length === 0 && !isStreaming ? (
        <WelcomeScreen onSelectPrompt={onSelectPrompt} />
      ) : (
        <>
          {messages.map((msg, idx) => (
            <MessageBubble key={msg.id || idx} message={msg} />
          ))}

          {/* Active Live Streaming State */}
          {isStreaming && (
            <div className="space-y-3 animate-fade-in">
              {/* Agent Status Notification Pill */}
              {currentStatus && (
                <div className="flex items-center gap-2.5 px-4 py-2 rounded-xl bg-surfaceLight/80 border border-brand-500/30 text-xs font-medium text-brand-300 w-fit shadow-glow animate-pulse">
                  <ChefHat className="w-4 h-4 text-brand-400 animate-spin" />
                  <span>{currentStatus}</span>
                </div>
              )}

              {/* Streaming Tokens Bubble */}
              {streamingContent && (
                <MessageBubble
                  message={{
                    role: 'assistant',
                    content: streamingContent,
                    created_at: new Date().toISOString()
                  }}
                  isStreamingNow={true}
                />
              )}
            </div>
          )}
        </>
      )}
    </div>
  )
}
