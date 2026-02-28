import { createContext, useCallback, useContext, useEffect, useState } from 'react'
import { authApi } from '../lib/api'
import type { TokenResponse, User } from '../lib/api'


const TOKEN_KEY = 'paritycheck_access_token'
const REFRESH_KEY = 'paritycheck_refresh_token'

interface AuthContextValue {
  user: User | null
  token: string | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string, name: string) => Promise<void>
  logout: () => void
  setTokens: (data: TokenResponse) => void
  refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(() => localStorage.getItem(TOKEN_KEY))
  const [loading, setLoading] = useState(true)

  const setTokens = useCallback((data: TokenResponse) => {
    localStorage.setItem(TOKEN_KEY, data.access_token)
    localStorage.setItem(REFRESH_KEY, data.refresh_token)
    setToken(data.access_token)
  }, [])

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(REFRESH_KEY)
    setToken(null)
    setUser(null)
  }, [])

  const refreshUser = useCallback(async () => {
    const t = localStorage.getItem(TOKEN_KEY)
    if (!t) return
    try {
      const u = await authApi.me(t)
      setUser(u)
    } catch {
      const refresh = localStorage.getItem(REFRESH_KEY)
      if (refresh) {
        try {
          const data = await authApi.refresh(refresh)
          setTokens(data)
          const u = await authApi.me(data.access_token)
          setUser(u)
        } catch {
          logout()
        }
      } else {
        logout()
      }
    }
  }, [logout, setTokens])

  useEffect(() => {
    if (!token) {
      setUser(null)
      setLoading(false)
      return
    }
    authApi.me(token)
      .then(setUser)
      .catch(() => {
        const refresh = localStorage.getItem(REFRESH_KEY)
        if (refresh) {
          authApi.refresh(refresh)
            .then((data: TokenResponse) => {
              setTokens(data)
              return authApi.me(data.access_token)
            })
            .then(setUser)
            .catch(logout)
        } else {
          logout()
        }
      })
      .finally(() => setLoading(false))
  }, [token, logout, setTokens])

  const login = useCallback(async (email: string, password: string) => {
    const data = await authApi.login(email, password)
    setTokens(data)
    const u = await authApi.me(data.access_token)
    setUser(u)
  }, [setTokens])

  const register = useCallback(async (email: string, password: string, name: string) => {
    await authApi.register(email, password, name)
    // Don't auto-login - user must verify email first
  }, [])

  return (
    <AuthContext.Provider value={{ user, token, loading, login, register, logout, setTokens, refreshUser }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
