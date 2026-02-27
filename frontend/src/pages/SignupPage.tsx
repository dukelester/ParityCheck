import { useState } from 'react'

interface SignupPageProps {
  onRegister: (email: string, password: string, name: string) => Promise<void>
  onSwitchToLogin: () => void
}

export function SignupPage({ onRegister, onSwitchToLogin }: SignupPageProps) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [name, setName] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await onRegister(email, password, name)
      setSuccess(true)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Registration failed')
    } finally {
      setLoading(false)
    }
  }

  if (success) {
    return (
      <div className="min-h-[80vh] flex items-center justify-center px-4 py-16">
        <div className="w-full max-w-md">
          <div className="rounded-[var(--radius-2xl)] border border-[var(--color-border)]/50 bg-[var(--color-surface)]/40 p-8 md:p-10 text-center backdrop-blur-sm">
            <div className="w-16 h-16 rounded-2xl bg-[var(--color-success-muted)] flex items-center justify-center mx-auto mb-6">
              <svg className="w-8 h-8 text-[var(--color-success)]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
            </div>
            <h1 className="text-xl md:text-2xl font-bold text-[var(--color-text)]">Check your email</h1>
            <p className="text-[var(--color-text-secondary)] mt-3 text-sm leading-relaxed">
              We sent a verification link to <strong className="text-[var(--color-text)]">{email}</strong>. Click the link to verify your account.
            </p>
            <p className="text-[var(--color-text-muted)] mt-6 text-xs">
              Didn't receive it? Check spam or{' '}
              <button onClick={() => setSuccess(false)} className="text-[var(--color-accent)] font-medium hover:underline">
                try again
              </button>
            </p>
            <button
              onClick={onSwitchToLogin}
              className="mt-8 w-full py-3.5 rounded-[var(--radius-md)] bg-[var(--color-accent)] text-[var(--color-bg)] font-semibold hover:bg-[var(--color-accent-hover)] transition-all shadow-[0_0_20px_rgba(0,212,170,0.2)]"
            >
              Go to sign in
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-[80vh] flex items-center justify-center px-4 py-16">
      <div className="w-full max-w-md">
        <div className="rounded-[var(--radius-2xl)] border border-[var(--color-border)]/50 bg-[var(--color-surface)]/40 p-8 md:p-10 backdrop-blur-sm">
          <h1 className="text-2xl md:text-3xl font-bold text-[var(--color-text)]">Create account</h1>
          <p className="text-[var(--color-text-secondary)] mt-2 text-sm">
            Already have an account?{' '}
            <button onClick={onSwitchToLogin} className="text-[var(--color-accent)] font-medium hover:underline underline-offset-2">
              Sign in
            </button>
          </p>
          <form onSubmit={handleSubmit} className="mt-8 space-y-5">
            {error && (
              <div className="p-4 rounded-[var(--radius-md)] bg-[var(--color-error-muted)] text-[var(--color-error)] text-sm font-medium">
                {error}
              </div>
            )}
            <div>
              <label className="block text-sm font-semibold text-[var(--color-text-secondary)] mb-2">Name</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
                className="w-full px-4 py-3 rounded-[var(--radius-md)] bg-[var(--color-bg)] border border-[var(--color-border)]/70 text-[var(--color-text)] placeholder-[var(--color-text-muted)]"
                placeholder="Your name"
              />
            </div>
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
                minLength={8}
                className="w-full px-4 py-3 rounded-[var(--radius-md)] bg-[var(--color-bg)] border border-[var(--color-border)]/70 text-[var(--color-text)] placeholder-[var(--color-text-muted)]"
                placeholder="Min 8 characters"
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="w-full py-3.5 rounded-[var(--radius-md)] bg-[var(--color-accent)] text-[var(--color-bg)] font-semibold hover:bg-[var(--color-accent-hover)] disabled:opacity-50 transition-all shadow-[0_0_20px_rgba(0,212,170,0.2)] hover:shadow-[0_0_30px_rgba(0,212,170,0.3)]"
            >
              {loading ? 'Creating account...' : 'Create account'}
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}
