import { useEffect, useState } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { observabilityApi, type ObservabilityStatus } from '../lib/api'

export function SystemStatus() {
  const { token } = useAuth()
  const [status, setStatus] = useState<ObservabilityStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!token) return
    setLoading(true)
    observabilityApi
      .status(token)
      .then(setStatus)
      .catch((err) => {
        setError(err instanceof Error ? err.message : 'Failed to load system status')
      })
      .finally(() => setLoading(false))
  }, [token])

  const badge = (ok: boolean) => (
    <span
      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-[var(--radius-md)] text-[10px] font-semibold uppercase tracking-widest ${
        ok
          ? 'bg-[var(--color-success-muted)] text-[var(--color-success)]'
          : 'bg-[var(--color-error-muted)] text-[var(--color-error)]'
      }`}
    >
      <span
        className={`w-1.5 h-1.5 rounded-full ${
          ok ? 'bg-[var(--color-success)]' : 'bg-[var(--color-error)]'
        }`}
      />
      {ok ? 'Healthy' : 'Issue'}
    </span>
  )

  return (
    <div className="rounded-[var(--radius-xl)] border border-[var(--color-border)]/50 bg-[var(--color-surface)]/40 p-6 md:p-8 space-y-6">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-semibold text-[var(--color-text)]">
            System status
          </h2>
          <p className="text-sm text-[var(--color-text-secondary)]">
            High-level health of the ParityCheck backend used by your workspace.
          </p>
        </div>
        {status && (
          <span
            className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-[var(--radius-full)] text-xs font-semibold ${
              status.status === 'ok'
                ? 'bg-[var(--color-success-muted)] text-[var(--color-success)]'
                : 'bg-[var(--color-warning-muted)] text-[var(--color-warning)]'
            }`}
          >
            <span
              className={`w-2 h-2 rounded-full ${
                status.status === 'ok'
                  ? 'bg-[var(--color-success)]'
                  : 'bg-[var(--color-warning)]'
              }`}
            />
            {status.status === 'ok' ? 'All systems operational' : 'Degraded'}
          </span>
        )}
      </div>

      {loading ? (
        <p className="text-sm text-[var(--color-text-muted)]">Checking status…</p>
      ) : error ? (
        <p className="text-sm text-[var(--color-error)]">{error}</p>
      ) : status ? (
        <div className="grid gap-4 sm:grid-cols-3">
          <div className="rounded-[var(--radius-lg)] bg-[var(--color-bg)]/60 border border-[var(--color-border)]/50 p-4">
            <div className="flex items-center justify-between mb-2">
              <p className="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-widest">
                Database
              </p>
              {badge(status.components.database.status === 'ok')}
            </div>
            {status.components.database.error && (
              <p className="text-xs text-[var(--color-text-secondary)]">
                {status.components.database.error}
              </p>
            )}
          </div>
          <div className="rounded-[var(--radius-lg)] bg-[var(--color-bg)]/60 border border-[var(--color-border)]/50 p-4">
            <div className="flex items-center justify-between mb-2">
              <p className="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-widest">
                Redis
              </p>
              {badge(status.components.redis.status === 'ok')}
            </div>
            {status.components.redis.error && (
              <p className="text-xs text-[var(--color-text-secondary)]">
                {status.components.redis.error}
              </p>
            )}
          </div>
          <div className="rounded-[var(--radius-lg)] bg-[var(--color-bg)]/60 border border-[var(--color-border)]/50 p-4">
            <p className="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-widest mb-2">
              Rate limits
            </p>
            <p className="text-xs text-[var(--color-text-secondary)] mb-1">
              Plan: <span className="font-semibold">{status.rate_limits.plan}</span>
            </p>
            <p className="text-xs text-[var(--color-text-secondary)]">
              {status.rate_limits.note}
            </p>
          </div>
        </div>
      ) : null}
    </div>
  )
}

