import React, { createContext, useContext, useState, useEffect } from 'react'
import { loginUser, registerUser, getSettings, updateSettings } from '../lib/api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [token, setToken] = useState(() => localStorage.getItem('khaoai_token') || null)
  const [settings, setSettings] = useState({
    default_location: 'Salt Lake, Sector V',
    dietary_preference: 'all',
    budget_preference: 'medium',
    max_delivery_time: 45
  })
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false)
  const [isSettingsModalOpen, setIsSettingsModalOpen] = useState(false)

  useEffect(() => {
    const savedUser = localStorage.getItem('khaoai_user')
    if (savedUser && token) {
      try {
        setUser(JSON.parse(savedUser))
      } catch (e) {
        console.error('Error parsing stored user:', e)
      }
    }
  }, [token])

  useEffect(() => {
    async function loadSettings() {
      try {
        const remoteSettings = await getSettings(token)
        if (remoteSettings) {
          setSettings(remoteSettings)
        }
      } catch (e) {
        console.error('Failed to load user settings:', e)
      }
    }
    loadSettings()
  }, [token])

  const login = async (email, password) => {
    const data = await loginUser(email, password)
    setToken(data.access_token)
    setUser(data.user)
    localStorage.setItem('khaoai_token', data.access_token)
    localStorage.setItem('khaoai_user', JSON.stringify(data.user))
    setIsAuthModalOpen(false)
    return data
  }

  const register = async (email, password, displayName) => {
    const data = await registerUser(email, password, displayName)
    setToken(data.access_token)
    setUser(data.user)
    localStorage.setItem('khaoai_token', data.access_token)
    localStorage.setItem('khaoai_user', JSON.stringify(data.user))
    setIsAuthModalOpen(false)
    return data
  }

  const logout = () => {
    setUser(null)
    setToken(null)
    localStorage.removeItem('khaoai_token')
    localStorage.removeItem('khaoai_user')
  }

  const saveSettings = async (newSettings) => {
    setSettings(newSettings)
    try {
      await updateSettings(newSettings, token)
    } catch (e) {
      console.error('Error updating settings on server:', e)
    }
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        settings,
        saveSettings,
        login,
        register,
        logout,
        isAuthModalOpen,
        setIsAuthModalOpen,
        isSettingsModalOpen,
        setIsSettingsModalOpen
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth must be used within an AuthProvider')
  return context
}
