import { useState } from 'react'
import type { User } from '../lib/api'
import { authApi } from '../lib/api'
import { useAuth } from '../contexts/AuthContext'

interface ProfileContentProps {
  user: User
}

export function ProfileContent({ user }: ProfileContentProps) {
  const { token } = useAuth()
  const [apiKey, setApiKey] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [copied, setCopied] = useState(false)

  const createdDate = user.created_at ? new Date(user.created_at).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  }) : '—'

  async function handleCreateApiKey() {
    if (!token) return
    setLoading(true)
    setError('')
    setApiKey(null)
    try {
      const res = await authApi.createApiKey(token)
      setApiKey(res.api_key)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create API key')
    } finally {
      setLoading(false)
    }
  }

  function handleCopyKey() {
    if (apiKey) {
      navigator.clipboard.writeText(apiKey)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  return (
    <main className="max-w-3xl mx-auto px-6 py-10">
      <div className="mb-10">
        <h1 className="text-2xl md:text-3xl font-bold text-[var(--color-text)] tracking-tight">
          Account
        </h1>
        <p className="text-[var(--color-text-secondary)] mt-2">
          Manage your profile and API keys
        </p>
      </div>

      <div className="space-y-8">
        {/* Profile details */}
        <section className="rounded-[var(--radius-xl)] border border-[var(--color-border)]/50 bg-[var(--color-surface)]/40 p-6 md:p-8">
          <h2 className="text-lg font-semibold text-[var(--color-text)] mb-6">Profile</h2>
          <div className="grid sm:grid-cols-2 gap-6">
            <div>
              <label className="block text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-widest mb-2">Name</label>
              <p className="text-[var(--color-text)] font-medium">{user.name}</p>
            </div>
            <div>
              <label className="block text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-widest mb-2">Email</label>
              <div className="flex items-center gap-2 flex-wrap">
                <p className="text-[var(--color-text)] font-medium">{user.email}</p>
                {user.email_verified ? (
                  <span className="px-2.5 py-1 rounded-[var(--radius-md)] text-xs font-semibold bg-[var(--color-success-muted)] text-[var(--color-success)]">
                    Verified
                  </span>
                ) : (
                  <span className="px-2.5 py-1 rounded-[var(--radius-md)] text-xs font-semibold bg-[var(--color-warning-muted)] text-[var(--color-warning)]">
                    Unverified
                  </span>
                )}
              </div>
            </div>
            <div>
              <label className="block text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-widest mb-2">Member since</label>
              <p className="text-[var(--color-text-secondary)]">{createdDate}</p>
            </div>
            <div>
              <label className="block text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-widest mb-2">Account ID</label>
              <p className="text-[var(--color-text-muted)] font-mono text-sm">{user.id}</p>
            </div>
          </div>
        </section>

        {/* API Keys */}
        <section className="rounded-[var(--radius-xl)] border border-[var(--color-border)]/50 bg-[var(--color-surface)]/40 p-6 md:p-8">
          <h2 className="text-lg font-semibold text-[var(--color-text)] mb-2">API Keys</h2>
          <p className="text-sm text-[var(--color-text-secondary)] mb-6">
            Use API keys to authenticate the envguard CLI. Keys are shown only once when created.
          </p>
          {error && (
            <div className="mb-6 p-4 rounded-[var(--radius-md)] bg-[var(--color-error-muted)] text-[var(--color-error)] text-sm font-medium">
              {error}
            </div>
          )}
          <button
            onClick={handleCreateApiKey}
            disabled={loading}
            className="px-5 py-2.5 rounded-[var(--radius-md)] bg-[var(--color-accent)] text-[var(--color-bg)] text-sm font-semibold hover:bg-[var(--color-accent-hover)] disabled:opacity-50 transition-all shadow-[0_0_20px_rgba(0,212,170,0.2)]"
          >
            {loading ? 'Creating...' : 'Create API key'}
          </button>
          {apiKey && (
            <div className="mt-6 p-5 rounded-[var(--radius-lg)] bg-[var(--color-bg)] border border-[var(--color-border)]/50">
              <p className="text-xs font-semibold text-[var(--color-warning)] mb-3">
                Store this key securely. It won't be shown again.
              </p>
              <div className="flex items-center gap-3">
                <code className="flex-1 font-mono text-sm text-[var(--color-text-secondary)] break-all">
                  {apiKey}
                </code>
                <button
                  onClick={handleCopyKey}
                  className="px-4 py-2 rounded-[var(--radius-md)] bg-[var(--color-surface)] text-[var(--color-text)] text-xs font-semibold hover:bg-[var(--color-surface-hover)] transition-all shrink-0"
                >
                  {copied ? 'Copied!' : 'Copy'}
                </button>
              </div>
              <p className="text-xs text-[var(--color-text-muted)] mt-3">
                Use with CLI: <code className="font-mono text-[var(--color-accent)]">envguard report --api-key=YOUR_KEY</code>
              </p>
            </div>
          )}
        </section>

        {/* Security */}
        <section className="rounded-[var(--radius-xl)] border border-[var(--color-border)]/50 bg-[var(--color-surface)]/40 p-6 md:p-8">
          <h2 className="text-lg font-semibold text-[var(--color-text)] mb-2">Security</h2>
          <p className="text-sm text-[var(--color-text-secondary)] leading-relaxed">
            Your password is securely hashed. To change it, contact support or use the password reset flow when available.
          </p>
        </section>
      </div>
    </main>
  )
}
