import { useEffect, useState } from 'react'
import { authApi } from '../lib/api'

interface VerifyEmailPageProps {
  token: string
  onVerified: () => void
}

export function VerifyEmailPage({ token, onVerified }: VerifyEmailPageProps) {
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading')
  const [message, setMessage] = useState('')

  useEffect(() => {
    authApi.verifyEmail(token)
      .then(() => {
        setStatus('success')
        setMessage('Email verified successfully. You can now sign in.')
      })
      .catch((err: unknown) => {
        setStatus('error')
        setMessage(err instanceof Error ? err.message : 'Verification failed')
      })
  }, [token])

  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-16">
      <div className="w-full max-w-md">
        <div className="rounded-[var(--radius-2xl)] border border-[var(--color-border)]/50 bg-[var(--color-surface)]/40 p-8 md:p-10 text-center backdrop-blur-sm">
          {status === 'loading' && (
            <>
              <div className="w-16 h-16 rounded-2xl bg-[var(--color-surface)]/80 flex items-center justify-center mx-auto mb-6 animate-pulse">
                <svg className="w-8 h-8 text-[var(--color-text-muted)]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h1 className="text-xl md:text-2xl font-bold text-[var(--color-text)]">Verifying your email...</h1>
            </>
          )}
          {status === 'success' && (
            <>
              <div className="w-16 h-16 rounded-2xl bg-[var(--color-success-muted)] flex items-center justify-center mx-auto mb-6">
                <svg className="w-8 h-8 text-[var(--color-success)]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <h1 className="text-xl md:text-2xl font-bold text-[var(--color-text)]">Email verified</h1>
              <p className="text-[var(--color-text-secondary)] mt-3 text-sm leading-relaxed">{message}</p>
              <button
                onClick={onVerified}
                className="mt-8 w-full py-3.5 rounded-[var(--radius-md)] bg-[var(--color-accent)] text-[var(--color-bg)] font-semibold hover:bg-[var(--color-accent-hover)] transition-all shadow-[0_0_20px_rgba(0,212,170,0.2)]"
              >
                Sign in
              </button>
            </>
          )}
          {status === 'error' && (
            <>
              <div className="w-16 h-16 rounded-2xl bg-[var(--color-error-muted)] flex items-center justify-center mx-auto mb-6">
                <svg className="w-8 h-8 text-[var(--color-error)]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </div>
              <h1 className="text-xl md:text-2xl font-bold text-[var(--color-text)]">Verification failed</h1>
              <p className="text-[var(--color-text-secondary)] mt-3 text-sm leading-relaxed">{message}</p>
              <button
                onClick={onVerified}
                className="mt-8 w-full py-3.5 rounded-[var(--radius-md)] border border-[var(--color-border)]/70 text-[var(--color-text)] font-semibold hover:bg-[var(--color-surface)] transition-all"
              >
                Go to sign in
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
