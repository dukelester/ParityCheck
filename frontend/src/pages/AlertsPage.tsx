import { useEffect, useState } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { useWorkspace } from '../contexts/WorkspaceContext'
import { alertsApi, type Alert } from '../lib/api'

export function AlertsPage() {
  const { token, user } = useAuth()
  const { currentWorkspace, usage } = useWorkspace()
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [loading, setLoading] = useState(true)
  const [adding, setAdding] = useState(false)
  const [alertType, setAlertType] = useState<'slack' | 'email'>('email')
  const [webhookUrl, setWebhookUrl] = useState('')
  const [email, setEmail] = useState('')

  useEffect(() => {
    if (user?.email && !email) setEmail(user.email)
  }, [user?.email])
  const [minSeverity, setMinSeverity] = useState('medium')
  const [error, setError] = useState('')

  const load = () => {
    if (!token || !currentWorkspace) return
    alertsApi.list(token, currentWorkspace.id)
      .then(setAlerts)
      .catch(() => setAlerts([]))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    if (!currentWorkspace) {
      setLoading(false)
      return
    }
    setLoading(true)
    load()
  }, [token, currentWorkspace?.id])

  async function handleAdd(e: React.FormEvent) {
    e.preventDefault()
    if (!token || !currentWorkspace) return
    const valid = alertType === 'slack' ? webhookUrl.trim() : email.trim()
    if (!valid) return
    setError('')
    if (!canAddAlert) {
      setError('Plan limit reached')
      return
    }
    setAdding(true)
    try {
      await alertsApi.create(
        token,
        currentWorkspace.id,
        alertType,
        alertType === 'slack' ? webhookUrl.trim() : undefined,
        alertType === 'email' ? email.trim() : undefined,
        minSeverity
      )
      setWebhookUrl('')
      setEmail('')
      load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to add alert')
    } finally {
      setAdding(false)
    }
  }

  async function handleDelete(id: string) {
    if (!token) return
    try {
      await alertsApi.delete(token, id)
      load()
    } catch {
      // ignore
    }
  }

  if (!currentWorkspace) {
    return (
      <div className="rounded-[var(--radius-xl)] border border-[var(--color-border)]/50 bg-[var(--color-surface)]/40 p-12 text-center">
        <p className="text-[var(--color-text-muted)]">Select a workspace first</p>
      </div>
    )
  }

  const canAddAlert = (usage?.slack_alerts.allowed ?? 0) > 0 && (usage?.slack_alerts.used ?? 0) < (usage?.slack_alerts.allowed ?? 0)

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-lg font-semibold text-[var(--color-text)] mb-2">
          Drift Alerts
        </h2>
        <p className="text-sm text-[var(--color-text-muted)]">
          Get notified when drift is detected. Free plan includes up to 20 alerts (Slack or email).
        </p>
        {!canAddAlert && (usage?.slack_alerts.allowed ?? 0) === 0 && (
          <p className="mt-2 text-sm text-[var(--color-warning)]">
            Upgrade to Pro for more alerts.
          </p>
        )}
      </div>

      <form onSubmit={handleAdd} className="flex flex-wrap gap-4 items-end">
        <div>
          <label className="block text-xs font-semibold text-[var(--color-text-muted)] mb-1.5">Type</label>
          <select
            value={alertType}
            onChange={(e) => setAlertType(e.target.value as 'slack' | 'email')}
            className="px-4 py-2.5 rounded-[var(--radius-md)] bg-[var(--color-bg)] border border-[var(--color-border)]/70 text-[var(--color-text)]"
          >
            <option value="email">Email</option>
            <option value="slack">Slack</option>
          </select>
        </div>
        {alertType === 'slack' ? (
          <div className="flex-1 min-w-[200px]">
            <label className="block text-xs font-semibold text-[var(--color-text-muted)] mb-1.5">Webhook URL</label>
            <input
              type="url"
              value={webhookUrl}
              onChange={(e) => setWebhookUrl(e.target.value)}
              placeholder="https://hooks.slack.com/services/..."
              className="w-full px-4 py-2.5 rounded-[var(--radius-md)] bg-[var(--color-bg)] border border-[var(--color-border)]/70 text-[var(--color-text)]"
            />
          </div>
        ) : (
          <div className="flex-1 min-w-[200px]">
            <label className="block text-xs font-semibold text-[var(--color-text-muted)] mb-1.5">Email address</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              className="w-full px-4 py-2.5 rounded-[var(--radius-md)] bg-[var(--color-bg)] border border-[var(--color-border)]/70 text-[var(--color-text)]"
            />
          </div>
        )}
        <div>
          <label className="block text-xs font-semibold text-[var(--color-text-muted)] mb-1.5">Min severity</label>
          <select
            value={minSeverity}
            onChange={(e) => setMinSeverity(e.target.value)}
            className="px-4 py-2.5 rounded-[var(--radius-md)] bg-[var(--color-bg)] border border-[var(--color-border)]/70 text-[var(--color-text)]"
          >
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
        </div>
        <button
          type="submit"
          disabled={adding || !(alertType === 'slack' ? webhookUrl.trim() : email.trim()) || !canAddAlert}
          className="px-4 py-2.5 rounded-[var(--radius-md)] bg-[var(--color-accent)] text-[var(--color-bg)] font-semibold text-sm disabled:opacity-50"
        >
          {adding ? 'Adding…' : 'Add alert'}
        </button>
      </form>
      {error && (
        <p className="text-sm text-[var(--color-error)]">{error}</p>
      )}

      <div className="rounded-[var(--radius-xl)] border border-[var(--color-border)]/50 bg-[var(--color-surface)]/40 overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-[var(--color-text-muted)]">Loading…</div>
        ) : alerts.length === 0 ? (
          <div className="p-12 text-center text-[var(--color-text-muted)]">
            No alerts configured. Add an email or Slack alert above.
          </div>
        ) : (
          <table className="w-full">
            <thead>
              <tr className="border-b border-[var(--color-border)]/50">
                <th className="text-left px-6 py-4 text-xs font-semibold text-[var(--color-text-muted)] uppercase">Type</th>
                <th className="text-left px-6 py-4 text-xs font-semibold text-[var(--color-text-muted)] uppercase">Min severity</th>
                <th className="text-left px-6 py-4 text-xs font-semibold text-[var(--color-text-muted)] uppercase">Status</th>
                <th className="w-20" />
              </tr>
            </thead>
            <tbody>
              {alerts.map((a) => (
                <tr key={a.id} className="border-b border-[var(--color-border)]/30 last:border-0">
                  <td className="px-6 py-4 text-sm text-[var(--color-text)] capitalize">{a.type}</td>
                  <td className="px-6 py-4 text-sm text-[var(--color-text-secondary)] capitalize">{a.min_severity}</td>
                  <td className="px-6 py-4">
                    <span className={`px-2 py-0.5 rounded text-xs font-semibold ${
                      a.enabled ? 'bg-[var(--color-success-muted)] text-[var(--color-success)]' : 'bg-[var(--color-surface)] text-[var(--color-text-muted)]'
                    }`}>
                      {a.enabled ? 'Enabled' : 'Disabled'}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <button
                      type="button"
                      onClick={() => handleDelete(a.id)}
                      className="text-[var(--color-error)] hover:underline text-sm"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
