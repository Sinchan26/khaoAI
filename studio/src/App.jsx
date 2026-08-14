import React, { useState } from 'react'
import { Header } from './components/layout/Header'
import { Sidebar } from './components/layout/Sidebar'
import { ChatWindow } from './components/chat/ChatWindow'
import { ChatInput } from './components/chat/ChatInput'
import { AuthModal } from './components/auth/AuthModal'
import { SettingsModal } from './components/settings/SettingsModal'
import { useAuth } from './contexts/AuthContext'
import { useChat } from './hooks/useChat'

export function App() {
  const [sessionId, setSessionId] = useState(() => 'sess-' + Math.random().toString(36).substring(2, 9))
  const [isSidebarOpen, setIsSidebarOpen] = useState(false)
  const [activeFilter, setActiveFilter] = useState(null)
  const { settings, token } = useAuth()

  const {
    messages,
    sendMessage,
    isStreaming,
    currentStatus,
    streamingContent,
    clearMessages
  } = useChat(sessionId, settings, token)

  const handleNewSession = () => {
    setSessionId('sess-' + Math.random().toString(36).substring(2, 9))
    clearMessages()
  }

  const handleSendMessage = (text) => {
    let filterOverrides = {}
    if (activeFilter === 'veg') {
      filterOverrides.dietary_preference = 'veg'
    } else if (activeFilter === 'budget') {
      filterOverrides.budget_preference = 'budget'
    }
    sendMessage(text, filterOverrides)
  }

  return (
    <div className="flex flex-col h-screen w-screen bg-background text-slate-100 overflow-hidden select-none font-sans">
      {/* Top Navigation Bar */}
      <Header
        onToggleSidebar={() => setIsSidebarOpen(!isSidebarOpen)}
        isSidebarOpen={isSidebarOpen}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex overflow-hidden relative">
        {/* Left Sidebar */}
        <Sidebar
          isOpen={isSidebarOpen}
          onClose={() => setIsSidebarOpen(false)}
          onNewSession={handleNewSession}
          onClearSession={clearMessages}
          onSelectPrompt={handleSendMessage}
          onSelectFilter={setActiveFilter}
          activeFilter={activeFilter}
        />

        {/* Center Chat View */}
        <main className="flex-1 flex flex-col h-full overflow-hidden bg-gradient-to-b from-background via-surface/40 to-background">
          <ChatWindow
            messages={messages}
            isStreaming={isStreaming}
            currentStatus={currentStatus}
            streamingContent={streamingContent}
            onSelectPrompt={handleSendMessage}
          />

          <ChatInput
            onSendMessage={handleSendMessage}
            isStreaming={isStreaming}
            currentFilter={activeFilter}
            onSelectFilter={setActiveFilter}
          />
        </main>
      </div>

      {/* Modals */}
      <AuthModal />
      <SettingsModal />
    </div>
  )
}

export default App
