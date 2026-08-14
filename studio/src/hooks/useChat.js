import { useState, useEffect, useRef, useCallback } from 'react'
import { getSessionHistory } from '../lib/api'

export function useChat(sessionId, userSettings, token) {
  const [messages, setMessages] = useState([])
  const [isStreaming, setIsStreaming] = useState(false)
  const [currentStatus, setCurrentStatus] = useState(null)
  const [streamingContent, setStreamingContent] = useState('')
  const [isConnected, setIsConnected] = useState(false)
  const wsRef = useRef(null)

  // Load existing session history on mount or session change
  useEffect(() => {
    async function loadHistory() {
      if (!sessionId) return
      try {
        const history = await getSessionHistory(sessionId)
        if (history && history.length > 0) {
          setMessages(history)
        }
      } catch (err) {
        console.error('Failed to load history:', err)
      }
    }
    loadHistory()
  }, [sessionId])

  // Establish WebSocket connection
  useEffect(() => {
    if (!sessionId) return

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    const wsUrl = `${protocol}//${host}/api/chat/ws/${sessionId}${token ? `?token=${token}` : ''}`

    const ws = new WebSocket(wsUrl)
    wsRef.current = ws

    ws.onopen = () => {
      setIsConnected(true)
      console.log('WebSocket connected to khaoAI')
    }

    ws.onclose = () => {
      setIsConnected(false)
      console.log('WebSocket disconnected')
    }

    ws.onerror = (err) => {
      console.error('WebSocket error:', err)
      setIsConnected(false)
    }

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)

        if (data.type === 'status') {
          setCurrentStatus(data.content)
        } else if (data.type === 'token') {
          setCurrentStatus(null)
          setStreamingContent((prev) => prev + data.content)
        } else if (data.type === 'complete') {
          setIsStreaming(false)
          setCurrentStatus(null)
          setStreamingContent('')

          // Append completed assistant message
          const newAssistantMsg = {
            id: 'msg-' + Date.now(),
            role: 'assistant',
            content: data.reply,
            recommendations: data.recommendations || [],
            meal_type: data.meal_type,
            location: data.location,
            created_at: new Date().toISOString()
          }

          setMessages((prev) => [...prev, newAssistantMsg])
        }
      } catch (e) {
        console.error('Error handling WebSocket message:', e)
      }
    }

    return () => {
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.close()
      }
    }
  }, [sessionId, token])

  const sendMessage = useCallback(
    (text, filterOverrides = {}) => {
      if (!text.trim() || isStreaming) return

      const userMsg = {
        id: 'msg-' + Date.now(),
        role: 'user',
        content: text.trim(),
        created_at: new Date().toISOString()
      }

      setMessages((prev) => [...prev, userMsg])
      setIsStreaming(true)
      setStreamingContent('')
      setCurrentStatus('Understanding craving & context...')

      const payload = {
        message: text.trim(),
        location: filterOverrides.location || userSettings?.default_location,
        preferences: {
          dietary_preference: filterOverrides.dietary_preference || userSettings?.dietary_preference,
          budget_preference: filterOverrides.budget_preference || userSettings?.budget_preference
        }
      }

      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify(payload))
      } else {
        // HTTP POST fallback if WS not open
        fetch('/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ ...payload, session_id: sessionId })
        })
          .then((res) => res.json())
          .then((data) => {
            setIsStreaming(false)
            setCurrentStatus(null)
            const fallbackMsg = {
              id: 'msg-' + Date.now(),
              role: 'assistant',
              content: data.reply,
              recommendations: data.recommendations || [],
              meal_type: data.meal_type,
              location: data.location,
              created_at: new Date().toISOString()
            }
            setMessages((prev) => [...prev, fallbackMsg])
          })
          .catch((err) => {
            setIsStreaming(false)
            setCurrentStatus(null)
            setMessages((prev) => [
              ...prev,
              {
                id: 'msg-' + Date.now(),
                role: 'assistant',
                content: 'Failed to get recommendation. Please ensure all backend services are running.',
                recommendations: [],
                created_at: new Date().toISOString()
              }
            ])
          })
      }
    },
    [sessionId, isStreaming, userSettings]
  )

  const clearMessages = () => {
    setMessages([])
  }

  return {
    messages,
    sendMessage,
    isStreaming,
    currentStatus,
    streamingContent,
    isConnected,
    clearMessages
  }
}
