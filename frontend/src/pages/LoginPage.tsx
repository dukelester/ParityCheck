import { useState } from 'react'

interface LoginPageProps {
  onLogin: (email: string, password: string) => Promise<void>
  onSwitchToSignup: () => void
}

export function LoginPage({ onLogin, onSwitchToSignup }: LoginPageProps) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await onLogin(email, password)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-[80vh] flex items-center justify-center px-4 py-16">
      <div className="w-full max-w-md">
        <div className="rounded-[var(--radius-2xl)] border border-[var(--color-border)]/50 bg-[var(--color-surface)]/40 p-8 md:p-10 backdrop-blur-sm">
          <h1 className="text-2xl md:text-3xl font-bold text-[var(--color-text)]">Sign in</h1>
          <p className="text-[var(--color-text-secondary)] mt-2 text-sm">
            Don't have an account?{' '}
            <button onClick={onSwitchToSignup} className="text-[var(--color-accent)] font-medium hover:underline underline-offset-2">
              Sign up
            </button>
          </p>
          <form onSubmit={handleSubmit} className="mt-8 space-y-5">
            {error && (
              <div className="p-4 rounded-[var(--radius-md)] bg-[var(--color-error-muted)] text-[var(--color-error)] text-sm font-medium">
                {error}
              </div>
            )}
            <div>
              <label className="block text-sm font-semibold text-[var(--color-text-secondary)] mb-2">Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="w-full px-4 py-3 rounded-[var(--radius-md)] bg-[var(--color-bg)] border border-[var(--color-border)]/70 text-[var(--color-text)] placeholder-[var(--color-text-muted)]"
                placeholder="you@example.com"
              />
            </div>
            <div>
              <label className="block text-sm font-semibold text-[var(--color-text-secondary)] mb-2">Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="w-full px-4 py-3 rounded-[var(--radius-md)] bg-[var(--color-bg)] border border-[var(--color-border)]/70 text-[var(--color-text)] placeholder-[var(--color-text-muted)]"
                placeholder="••••••••"
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="w-full py-3.5 rounded-[var(--radius-md)] bg-[var(--color-accent)] text-[var(--color-bg)] font-semibold hover:bg-[var(--color-accent-hover)] disabled:opacity-50 transition-all shadow-[0_0_20px_rgba(0,212,170,0.2)] hover:shadow-[0_0_30px_rgba(0,212,170,0.3)]"
            >
              {loading ? 'Signing in...' : 'Sign in'}
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}
