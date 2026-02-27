import { useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import type { TokenResponse } from '../lib/api'

export function AuthCallbackPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const { setTokens } = useAuth()

  useEffect(() => {
    const hash = location.hash.slice(1)
    const params = new URLSearchParams(hash)
    const accessToken = params.get('access_token')
    const refreshToken = params.get('refresh_token')
    const expiresIn = params.get('expires_in')

    if (accessToken && refreshToken) {
      const data: TokenResponse = {
        access_token: accessToken,
        refresh_token: refreshToken,
        token_type: 'bearer',
        expires_in: expiresIn ? parseInt(expiresIn, 10) : 86400,
      }
      setTokens(data)
      // Replace hash in URL so tokens aren't visible
      window.history.replaceState(null, '', '/auth/callback')
      navigate('/dashboard', { replace: true })
    } else {
      navigate('/login?error=oauth_failed', { replace: true })
    }
  }, [location.hash, setTokens, navigate])

  return (
    <div className="min-h-screen flex items-center justify-center bg-[var(--color-bg)]">
      <div className="text-center">
        <div className="w-12 h-12 border-2 border-[var(--color-accent)] border-t-transparent rounded-full animate-spin mx-auto mb-4" />
        <p className="text-[var(--color-text-secondary)]">Signing you in...</p>
      </div>
    </div>
  )
}
