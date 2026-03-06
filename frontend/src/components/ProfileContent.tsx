import { useState } from 'react'
import type { User } from '../lib/api'
import { authApi } from '../lib/api'
import { useAuth } from '../contexts/AuthContext'

interface ProfileContentProps {
  user: User
}

export function ProfileContent({ user }: ProfileContentProps) {
  const { token, refreshUser, logout } = useAuth()
  const [apiKey, setApiKey] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [copied, setCopied] = useState(false)
  const [name, setName] = useState(user.name)
  const [profileSaving, setProfileSaving] = useState(false)
  const [profileMessage, setProfileMessage] = useState<string | null>(null)

  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [passwordMessage, setPasswordMessage] = useState<string | null>(null)
  const [passwordError, setPasswordError] = useState<string | null>(null)
  const [passwordSaving, setPasswordSaving] = useState(false)

  const [deletePassword, setDeletePassword] = useState('')
  const [deleteConfirm, setDeleteConfirm] = useState('')
  const [deleteError, setDeleteError] = useState<string | null>(null)
  const [deleteSaving, setDeleteSaving] = useState(false)

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

  async function handleSaveProfile(e: React.FormEvent) {
    e.preventDefault()
    if (!token) return
    setProfileSaving(true)
    setProfileMessage(null)
    try {
      await authApi.updateProfile(token, name)
      await refreshUser()
      setProfileMessage('Profile updated')
    } catch (err) {
      setProfileMessage(err instanceof Error ? err.message : 'Failed to update profile')
    } finally {
      setProfileSaving(false)
    }
  }

  async function handleChangePassword(e: React.FormEvent) {
    e.preventDefault()
    if (!token) return
    setPasswordSaving(true)
    setPasswordMessage(null)
    setPasswordError(null)
    try {
      const res = await authApi.changePassword(token, currentPassword, newPassword)
      setPasswordMessage(res.message)
      setCurrentPassword('')
      setNewPassword('')
    } catch (err) {
      setPasswordError(err instanceof Error ? err.message : 'Failed to change password')
    } finally {
      setPasswordSaving(false)
    }
  }

  async function handleDeleteAccount(e: React.FormEvent) {
    e.preventDefault()
    if (!token) return
    setDeleteSaving(true)
    setDeleteError(null)
    try {
      await authApi.deleteAccount(token, deletePassword, deleteConfirm)
      logout()
    } catch (err) {
      setDeleteError(err instanceof Error ? err.message : 'Failed to delete account')
    } finally {
      setDeleteSaving(false)
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
          <h2 className="text-lg font-semibold text-[var(--color-text)] mb-4">Profile</h2>
          <p className="text-sm text-[var(--color-text-secondary)] mb-6">
            Update your basic account information. Email is fixed for security reasons.
          </p>
          <form onSubmit={handleSaveProfile} className="grid lg:grid-cols-2 gap-8 items-start">
            <div className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-widest mb-2">
                  Name
                </label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full px-3 py-2.5 rounded-[var(--radius-md)] bg-[var(--color-bg)] border border-[var(--color-border)]/70 text-sm text-[var(--color-text)] outline-none focus:border-[var(--color-accent)] focus:ring-1 focus:ring-[var(--color-accent)]"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-widest mb-2">
                  Member since
                </label>
                <p className="text-[var(--color-text-secondary)]">{createdDate}</p>
              </div>
              <div>
                <label className="block text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-widest mb-2">
                  Account ID
                </label>
                <p className="text-[var(--color-text-muted)] font-mono text-sm break-all">{user.id}</p>
              </div>
              {profileMessage && (
                <p className="text-xs text-[var(--color-success)]">{profileMessage}</p>
              )}
              <button
                type="submit"
                disabled={profileSaving}
                className="px-4 py-2.5 rounded-[var(--radius-md)] bg-[var(--color-accent)] text-[var(--color-bg)] text-xs font-semibold hover:bg-[var(--color-accent-hover)] disabled:opacity-50 transition-all"
              >
                {profileSaving ? 'Saving…' : 'Save changes'}
              </button>
            </div>
            <div className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-widest mb-2">
                  Email
                </label>
                <div className="flex items-center gap-2 flex-wrap">
                  <p className="text-[var(--color-text)] font-medium">{user.email}</p>
                  <span
                    className={`px-2.5 py-1 rounded-[var(--radius-md)] text-xs font-semibold ${
                      user.email_verified
                        ? 'bg-[var(--color-success-muted)] text-[var(--color-success)]'
                        : 'bg-[var(--color-warning-muted)] text-[var(--color-warning)]'
                    }`}
                  >
                    {user.email_verified ? 'Verified' : 'Unverified'}
                  </span>
                </div>
                <p className="text-xs text-[var(--color-text-muted)] mt-2">
                  To change your email, contact support so we can verify ownership and migrate your account.
                </p>
              </div>
            </div>
          </form>
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
          <h2 className="text-lg font-semibold text-[var(--color-text)] mb-4">Security</h2>
          <div className="grid lg:grid-cols-2 gap-8 items-start">
            <form onSubmit={handleChangePassword} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-widest mb-2">
                  Current password
                </label>
                <input
                  type="password"
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  className="w-full px-3 py-2.5 rounded-[var(--radius-md)] bg-[var(--color-bg)] border border-[var(--color-border)]/70 text-sm text-[var(--color-text)] outline-none focus:border-[var(--color-accent)] focus:ring-1 focus:ring-[var(--color-accent)]"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-widest mb-2">
                  New password
                </label>
                <input
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  className="w-full px-3 py-2.5 rounded-[var(--radius-md)] bg-[var(--color-bg)] border border-[var(--color-border)]/70 text-sm text-[var(--color-text)] outline-none focus:border-[var(--color-accent)] focus:ring-1 focus:ring-[var(--color-accent)]"
                />
              </div>
              {passwordError && (
                <p className="text-xs text-[var(--color-error)]">{passwordError}</p>
              )}
              {passwordMessage && !passwordError && (
                <p className="text-xs text-[var(--color-success)]">{passwordMessage}</p>
              )}
              <button
                type="submit"
                disabled={passwordSaving}
                className="px-4 py-2.5 rounded-[var(--radius-md)] bg-[var(--color-surface)] text-[var(--color-text)] text-xs font-semibold border border-[var(--color-border)] hover:bg-[var(--color-surface-hover)] disabled:opacity-50 transition-all"
              >
                {passwordSaving ? 'Updating…' : 'Update password'}
              </button>
              <p className="text-xs text-[var(--color-text-muted)]">
                Forgot your password? Use the “Forgot password” link on the sign-in page.
              </p>
            </form>
            <form onSubmit={handleDeleteAccount} className="space-y-4 border border-[var(--color-border)]/60 rounded-[var(--radius-lg)] p-4 bg-[var(--color-error-muted)]/10">
              <h3 className="text-sm font-semibold text-[var(--color-error)]">Danger zone</h3>
              <p className="text-xs text-[var(--color-text-secondary)]">
                Deleting your account is permanent and cannot be undone. You must confirm with your password and the phrase{' '}
                <span className="font-mono text-[var(--color-error)]">delete my account</span>.
              </p>
              <div>
                <label className="block text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-widest mb-2">
                  Current password
                </label>
                <input
                  type="password"
                  value={deletePassword}
                  onChange={(e) => setDeletePassword(e.target.value)}
                  className="w-full px-3 py-2.5 rounded-[var(--radius-md)] bg-[var(--color-bg)] border border-[var(--color-border)]/70 text-sm text-[var(--color-text)] outline-none focus:border-[var(--color-error)] focus:ring-1 focus:ring-[var(--color-error)]"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-widest mb-2">
                  Type “delete my account”
                </label>
                <input
                  type="text"
                  value={deleteConfirm}
                  onChange={(e) => setDeleteConfirm(e.target.value)}
                  className="w-full px-3 py-2.5 rounded-[var(--radius-md)] bg-[var(--color-bg)] border border-[var(--color-border)]/70 text-sm text-[var(--color-text)] outline-none focus:border-[var(--color-error)] focus:ring-1 focus:ring-[var(--color-error)]"
                />
              </div>
              {deleteError && (
                <p className="text-xs text-[var(--color-error)]">{deleteError}</p>
              )}
              <button
                type="submit"
                disabled={deleteSaving}
                className="px-4 py-2.5 rounded-[var(--radius-md)] bg-[var(--color-error)] text-white text-xs font-semibold hover:bg-red-600 disabled:opacity-50 transition-all"
              >
                {deleteSaving ? 'Deleting…' : 'Delete account'}
              </button>
            </form>
          </div>
        </section>
      </div>
    </main>
  )
}
