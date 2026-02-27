import { useState } from 'react'
import { getGitHubAuthUrl, authApi } from '../lib/api'

interface SignupPageProps {
  onRegister: (email: string, password: string, name: string) => Promise<void>
  onSwitchToLogin: () => void
}

export function SignupPage({ onRegister, onSwitchToLogin }: SignupPageProps) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [name, setName] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState(false)
  const [resending, setResending] = useState(false)
  const [resendMsg, setResendMsg] = useState('')

  const passwordStrength = password.length < 8 ? 0 : password.length < 12 ? 1 : 2
  const passwordsMatch = password === confirmPassword && confirmPassword.length > 0

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    if (password !== confirmPassword) {
      setError('Passwords do not match')
      return
    }
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

  function handleGitHubSignup() {
    window.location.href = getGitHubAuthUrl()
  }

  async function handleResend() {
    setResendMsg('')
    setResending(true)
    try {
      await authApi.resendVerification(email)
      setResendMsg('Verification email sent! Check your inbox and spam folder.')
    } catch (err) {
      setResendMsg(err instanceof Error ? err.message : 'Failed to resend')
    } finally {
      setResending(false)
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
            <p className="text-[var(--color-text-muted)] mt-4 text-xs">
              Didn't receive it? Check your <strong>spam/junk folder</strong>, then try:
            </p>
            <div className="mt-4 flex flex-col gap-2">
              <button
                type="button"
                onClick={handleResend}
                disabled={resending}
                className="px-4 py-2 rounded-[var(--radius-md)] border border-[var(--color-border)] text-[var(--color-text)] text-sm font-medium hover:bg-[var(--color-surface)] disabled:opacity-50"
              >
                {resending ? 'Sending...' : 'Resend verification email'}
              </button>
              {resendMsg && (
                <p className={`text-xs ${resendMsg.includes('sent') ? 'text-[var(--color-success)]' : 'text-[var(--color-error)]'}`}>
                  {resendMsg}
                </p>
              )}
            </div>
            <button
              type="button"
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
            <button type="button" onClick={onSwitchToLogin} className="text-[var(--color-accent)] font-medium hover:underline underline-offset-2">
              Sign in
            </button>
          </p>

          <button
            type="button"
            onClick={handleGitHubSignup}
            className="mt-8 w-full flex items-center justify-center gap-3 py-3.5 rounded-[var(--radius-md)] bg-[var(--color-surface)] border border-[var(--color-border)]/70 text-[var(--color-text)] font-semibold hover:bg-[var(--color-surface-hover)] hover:border-[var(--color-border)] transition-all"
          >
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
              <path fillRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" clipRule="evenodd" />
            </svg>
            Continue with GitHub
          </button>

          <div className="mt-6 flex items-center gap-4">
            <div className="flex-1 h-px bg-[var(--color-border)]/50" />
            <span className="text-xs font-medium text-[var(--color-text-muted)]">or</span>
            <div className="flex-1 h-px bg-[var(--color-border)]/50" />
          </div>

          <form onSubmit={handleSubmit} className="mt-6 space-y-5">
            {error && (
              <div className="p-4 rounded-[var(--radius-md)] bg-[var(--color-error-muted)] text-[var(--color-error)] text-sm font-medium">
                {error}
              </div>
            )}
            <div>
              <label htmlFor="signup-name" className="block text-sm font-semibold text-[var(--color-text-secondary)] mb-2">Name</label>
              <input
                id="signup-name"
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
                autoComplete="name"
                className="w-full px-4 py-3 rounded-[var(--radius-md)] bg-[var(--color-bg)] border border-[var(--color-border)]/70 text-[var(--color-text)] placeholder-[var(--color-text-muted)] focus:border-[var(--color-accent)]/50 focus:ring-1 focus:ring-[var(--color-accent)]/30 outline-none transition-all"
                placeholder="Your name"
              />
            </div>
            <div>
              <label htmlFor="signup-email" className="block text-sm font-semibold text-[var(--color-text-secondary)] mb-2">Email</label>
              <input
                id="signup-email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                autoComplete="email"
                className="w-full px-4 py-3 rounded-[var(--radius-md)] bg-[var(--color-bg)] border border-[var(--color-border)]/70 text-[var(--color-text)] placeholder-[var(--color-text-muted)] focus:border-[var(--color-accent)]/50 focus:ring-1 focus:ring-[var(--color-accent)]/30 outline-none transition-all"
                placeholder="you@example.com"
              />
            </div>
            <div>
              <label htmlFor="signup-password" className="block text-sm font-semibold text-[var(--color-text-secondary)] mb-2">Password</label>
              <div className="relative">
                <input
                  id="signup-password"
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  minLength={8}
                  autoComplete="new-password"
                  className="w-full px-4 py-3 pr-12 rounded-[var(--radius-md)] bg-[var(--color-bg)] border border-[var(--color-border)]/70 text-[var(--color-text)] placeholder-[var(--color-text-muted)] focus:border-[var(--color-accent)]/50 focus:ring-1 focus:ring-[var(--color-accent)]/30 outline-none transition-all"
                  placeholder="Min 8 characters"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 p-1.5 rounded-[var(--radius-sm)] text-[var(--color-text-muted)] hover:text-[var(--color-text)] hover:bg-[var(--color-surface)]/50 transition-all"
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? (
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M3.98 8.223A10.477 10.477 0 001.934 12C3.226 16.338 7.244 19.5 12 19.5c.993 0 1.953-.138 2.863-.395M6.228 6.228A10.45 10.45 0 0112 4.5c4.756 0 8.773 3.162 10.065 7.498a10.523 10.523 0 01-4.293 5.774M6.228 6.228L3 3m3.228 3.228l3.65 3.65m7.894 7.894L21 21m-3.228-3.228l-3.65-3.65m0 0a3 3 0 10-4.243-4.243m4.242 4.242L9.88 9.88" />
                    </svg>
                  ) : (
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z" />
                      <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    </svg>
                  )}
                </button>
              </div>
              {password.length > 0 && (
                <div className="mt-1.5 flex gap-1">
                  {[0, 1, 2].map((i) => (
                    <div
                      key={i}
                      className={`h-1 flex-1 rounded-full transition-colors ${
                        i <= passwordStrength
                          ? passwordStrength === 2
                            ? 'bg-[var(--color-success)]'
                            : passwordStrength === 1
                              ? 'bg-[var(--color-warning)]'
                              : 'bg-[var(--color-error)]'
                          : 'bg-[var(--color-border)]/30'
                      }`}
                    />
                  ))}
                </div>
              )}
            </div>
            <div>
              <label htmlFor="signup-confirm-password" className="block text-sm font-semibold text-[var(--color-text-secondary)] mb-2">Confirm password</label>
              <div className="relative">
                <input
                  id="signup-confirm-password"
                  type={showPassword ? 'text' : 'password'}
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  required
                  minLength={8}
                  autoComplete="new-password"
                  className={`w-full px-4 py-3 pr-12 rounded-[var(--radius-md)] bg-[var(--color-bg)] border text-[var(--color-text)] placeholder-[var(--color-text-muted)] focus:ring-1 outline-none transition-all ${
                    confirmPassword.length > 0
                      ? passwordsMatch
                        ? 'border-[var(--color-success)]/50 focus:border-[var(--color-success)]/70 focus:ring-[var(--color-success)]/30'
                        : 'border-[var(--color-error)]/50 focus:border-[var(--color-error)]/70 focus:ring-[var(--color-error)]/30'
                      : 'border-[var(--color-border)]/70 focus:border-[var(--color-accent)]/50 focus:ring-[var(--color-accent)]/30'
                  }`}
                  placeholder="Re-enter your password"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 p-1.5 rounded-[var(--radius-sm)] text-[var(--color-text-muted)] hover:text-[var(--color-text)] hover:bg-[var(--color-surface)]/50 transition-all"
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? (
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M3.98 8.223A10.477 10.477 0 001.934 12C3.226 16.338 7.244 19.5 12 19.5c.993 0 1.953-.138 2.863-.395M6.228 6.228A10.45 10.45 0 0112 4.5c4.756 0 8.773 3.162 10.065 7.498a10.523 10.523 0 01-4.293 5.774M6.228 6.228L3 3m3.228 3.228l3.65 3.65m7.894 7.894L21 21m-3.228-3.228l-3.65-3.65m0 0a3 3 0 10-4.243-4.243m4.242 4.242L9.88 9.88" />
                    </svg>
                  ) : (
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z" />
                      <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    </svg>
                  )}
                </button>
              </div>
              {confirmPassword.length > 0 && !passwordsMatch && (
                <p className="mt-1.5 text-sm text-[var(--color-error)]">Passwords do not match</p>
              )}
              {confirmPassword.length > 0 && passwordsMatch && (
                <p className="mt-1.5 text-sm text-[var(--color-success)] flex items-center gap-1.5">
                  <svg className="w-4 h-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                  </svg>
                  Passwords match
                </p>
              )}
            </div>
            <button
              type="submit"
              disabled={loading}
              className="w-full py-3.5 rounded-[var(--radius-md)] bg-[var(--color-accent)] text-[var(--color-bg)] font-semibold hover:bg-[var(--color-accent-hover)] disabled:opacity-50 transition-all shadow-[0_0_20px_rgba(0,212,170,0.2)] hover:shadow-[0_0_30px_rgba(0,212,170,0.3)]"
            >
              {loading ? 'Creating account...' : 'Create account'}
            </button>
            <p className="text-xs text-[var(--color-text-muted)] text-center">
              By signing up, you agree to our terms of service and privacy policy.
            </p>
          </form>
        </div>
      </div>
    </div>
  )
}
