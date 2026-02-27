import { useState } from 'react'
import { authApi } from '../lib/api'

interface ForgotPasswordPageProps {
  onSwitchToLogin: () => void
}

export function ForgotPasswordPage({ onSwitchToLogin }: ForgotPasswordPageProps) {
  const [email, setEmail] = useState('')
  const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>(
    'idle'
  )
  const [message, setMessage] = useState('')

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setStatus('loading')
    setMessage('')
    try {
      await authApi.forgotPassword(email)
      setStatus('success')
      setMessage(
        'If an account exists for that email, we sent a reset link. Check your inbox.'
      )
    } catch (err) {
      setStatus('error')
      setMessage(err instanceof Error ? err.message : 'Request failed')
    }
  }

  return (
    <div className="min-h-[80vh] flex items-center justify-center px-4 py-16">
      <div className="w-full max-w-md">
        <div className="rounded-[var(--radius-2xl)] border border-[var(--color-border)]/50 bg-[var(--color-surface)]/40 p-8 md:p-10 backdrop-blur-sm">
          <h1 className="text-2xl md:text-3xl font-bold text-[var(--color-text)]">
            Forgot password
          </h1>
          <p className="text-[var(--color-text-secondary)] mt-2 text-sm">
            Enter your email and we'll send you a link to reset your password.
          </p>

          {(status === 'success' || status === 'error') && (
            <div
              className={`mt-6 p-4 rounded-[var(--radius-md)] text-sm font-medium ${
                status === 'success'
                  ? 'bg-[var(--color-success-muted)] text-[var(--color-success)]'
                  : 'bg-[var(--color-error-muted)] text-[var(--color-error)]'
              }`}
            >
              {message}
            </div>
          )}

          {status !== 'success' && (
            <form onSubmit={handleSubmit} className="mt-6 space-y-5">
              <div>
                <label
                  htmlFor="forgot-email"
                  className="block text-sm font-semibold text-[var(--color-text-secondary)] mb-2"
                >
                  Email
                </label>
                <input
                  id="forgot-email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  autoComplete="email"
                  className="w-full px-4 py-3 rounded-[var(--radius-md)] bg-[var(--color-bg)] border border-[var(--color-border)]/70 text-[var(--color-text)] placeholder-[var(--color-text-muted)] focus:border-[var(--color-accent)]/50 focus:ring-1 focus:ring-[var(--color-accent)]/30 outline-none transition-all"
                  placeholder="you@example.com"
                />
              </div>
              <button
                type="submit"
                disabled={status === 'loading'}
                className="w-full py-3.5 rounded-[var(--radius-md)] bg-[var(--color-accent)] text-[var(--color-bg)] font-semibold hover:bg-[var(--color-accent-hover)] disabled:opacity-50 transition-all shadow-[0_0_20px_rgba(0,212,170,0.2)]"
              >
                {status === 'loading' ? 'Sending...' : 'Send reset link'}
              </button>
            </form>
          )}

          {status === 'success' && (
            <button
              onClick={() => {
                setStatus('idle')
                setMessage('')
                setEmail('')
              }}
              className="mt-6 w-full py-3.5 rounded-[var(--radius-md)] bg-[var(--color-accent)] text-[var(--color-bg)] font-semibold hover:bg-[var(--color-accent-hover)] transition-all"
            >
              Send another link
            </button>
          )}

          <button
            type="button"
            onClick={onSwitchToLogin}
            className="mt-6 w-full py-3 rounded-[var(--radius-md)] border border-[var(--color-border)]/70 text-[var(--color-text-secondary)] font-medium hover:bg-[var(--color-surface)] hover:text-[var(--color-text)] transition-all"
          >
            Back to sign in
          </button>
        </div>
      </div>
    </div>
  )
}
