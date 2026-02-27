import { useState } from 'react'
import { authApi } from '../lib/api'

interface ResetPasswordPageProps {
  token: string
  onSuccess: () => void
}

export function ResetPasswordPage({ token, onSuccess }: ResetPasswordPageProps) {
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>(
    'idle'
  )
  const [message, setMessage] = useState('')

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (password !== confirm) {
      setMessage('Passwords do not match')
      setStatus('error')
      return
    }
    if (password.length < 8) {
      setMessage('Password must be at least 8 characters')
      setStatus('error')
      return
    }
    setStatus('loading')
    setMessage('')
    try {
      await authApi.resetPassword(token, password)
      setStatus('success')
      setMessage('Your password has been reset. You can now sign in.')
    } catch (err) {
      setStatus('error')
      setMessage(err instanceof Error ? err.message : 'Reset failed')
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-16">
      <div className="w-full max-w-md">
        <div className="rounded-[var(--radius-2xl)] border border-[var(--color-border)]/50 bg-[var(--color-surface)]/40 p-8 md:p-10 backdrop-blur-sm">
          {status === 'success' ? (
            <>
              <div className="w-16 h-16 rounded-2xl bg-[var(--color-success-muted)] flex items-center justify-center mx-auto mb-6">
                <svg
                  className="w-8 h-8 text-[var(--color-success)]"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth={2}
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M5 13l4 4L19 7"
                  />
                </svg>
              </div>
              <h1 className="text-xl md:text-2xl font-bold text-[var(--color-text)] text-center">
                Password reset
              </h1>
              <p className="text-[var(--color-text-secondary)] mt-3 text-sm text-center leading-relaxed">
                {message}
              </p>
              <button
                onClick={onSuccess}
                className="mt-8 w-full py-3.5 rounded-[var(--radius-md)] bg-[var(--color-accent)] text-[var(--color-bg)] font-semibold hover:bg-[var(--color-accent-hover)] transition-all shadow-[0_0_20px_rgba(0,212,170,0.2)]"
              >
                Sign in
              </button>
            </>
          ) : (
            <>
              <h1 className="text-2xl md:text-3xl font-bold text-[var(--color-text)]">
                Set new password
              </h1>
              <p className="text-[var(--color-text-secondary)] mt-2 text-sm">
                Enter your new password below.
              </p>

              {status === 'error' && (
                <div className="mt-6 p-4 rounded-[var(--radius-md)] bg-[var(--color-error-muted)] text-[var(--color-error)] text-sm font-medium">
                  {message}
                </div>
              )}

              <form onSubmit={handleSubmit} className="mt-6 space-y-5">
                <div>
                  <label
                    htmlFor="reset-password"
                    className="block text-sm font-semibold text-[var(--color-text-secondary)] mb-2"
                  >
                    New password
                  </label>
                  <div className="relative">
                    <input
                      id="reset-password"
                      type={showPassword ? 'text' : 'password'}
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      required
                      minLength={8}
                      autoComplete="new-password"
                      className="w-full px-4 py-3 pr-12 rounded-[var(--radius-md)] bg-[var(--color-bg)] border border-[var(--color-border)]/70 text-[var(--color-text)] placeholder-[var(--color-text-muted)] focus:border-[var(--color-accent)]/50 focus:ring-1 focus:ring-[var(--color-accent)]/30 outline-none transition-all"
                      placeholder="••••••••"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 p-1.5 rounded-[var(--radius-sm)] text-[var(--color-text-muted)] hover:text-[var(--color-text)] hover:bg-[var(--color-surface)]/50 transition-all"
                      aria-label={showPassword ? 'Hide password' : 'Show password'}
                    >
                      {showPassword ? (
                        <svg
                          className="w-5 h-5"
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                          strokeWidth={1.5}
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            d="M3.98 8.223A10.477 10.477 0 001.934 12C3.226 16.338 7.244 19.5 12 19.5c.993 0 1.953-.138 2.863-.395M6.228 6.228A10.45 10.45 0 0112 4.5c4.756 0 8.773 3.162 10.065 7.498a10.523 10.523 0 01-4.293 5.774M6.228 6.228L3 3m3.228 3.228l3.65 3.65m7.894 7.894L21 21m-3.228-3.228l-3.65-3.65m0 0a3 3 0 10-4.243-4.243m4.242 4.242L9.88 9.88"
                          />
                        </svg>
                      ) : (
                        <svg
                          className="w-5 h-5"
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                          strokeWidth={1.5}
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z"
                          />
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                          />
                        </svg>
                      )}
                    </button>
                  </div>
                  <p className="mt-1.5 text-xs text-[var(--color-text-muted)]">
                    At least 8 characters
                  </p>
                </div>
                <div>
                  <label
                    htmlFor="reset-confirm"
                    className="block text-sm font-semibold text-[var(--color-text-secondary)] mb-2"
                  >
                    Confirm password
                  </label>
                  <input
                    id="reset-confirm"
                    type={showPassword ? 'text' : 'password'}
                    value={confirm}
                    onChange={(e) => setConfirm(e.target.value)}
                    required
                    minLength={8}
                    autoComplete="new-password"
                    className="w-full px-4 py-3 rounded-[var(--radius-md)] bg-[var(--color-bg)] border border-[var(--color-border)]/70 text-[var(--color-text)] placeholder-[var(--color-text-muted)] focus:border-[var(--color-accent)]/50 focus:ring-1 focus:ring-[var(--color-accent)]/30 outline-none transition-all"
                    placeholder="••••••••"
                  />
                </div>
                <button
                  type="submit"
                  disabled={status === 'loading'}
                  className="w-full py-3.5 rounded-[var(--radius-md)] bg-[var(--color-accent)] text-[var(--color-bg)] font-semibold hover:bg-[var(--color-accent-hover)] disabled:opacity-50 transition-all shadow-[0_0_20px_rgba(0,212,170,0.2)]"
                >
                  {status === 'loading' ? 'Resetting...' : 'Reset password'}
                </button>
              </form>

              <button
                type="button"
                onClick={onSuccess}
                className="mt-6 w-full py-3 rounded-[var(--radius-md)] border border-[var(--color-border)]/70 text-[var(--color-text-secondary)] font-medium hover:bg-[var(--color-surface)] hover:text-[var(--color-text)] transition-all"
              >
                Back to sign in
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
