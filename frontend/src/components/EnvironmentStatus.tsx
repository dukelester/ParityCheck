import { useEffect, useState } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { useWorkspace } from '../contexts/WorkspaceContext'
import { environmentsApi, type Environment } from '../lib/api'

function formatTimeAgo(iso: string | null): string {
  if (!iso) return 'Never'
  const d = new Date(iso)
  const s = Math.floor((Date.now() - d.getTime()) / 1000)
  if (s < 60) return 'Just now'
  if (s < 3600) return `${Math.floor(s / 60)} min ago`
  if (s < 86400) return `${Math.floor(s / 3600)} hour(s) ago`
  return `${Math.floor(s / 86400)} day(s) ago`
}

interface EnvironmentStatusProps {
  onBaselineSet?: () => void
}

export function EnvironmentStatus({ onBaselineSet }: EnvironmentStatusProps) {
  const { token } = useAuth()
  const { currentWorkspace, refresh } = useWorkspace()
  const [envs, setEnvs] = useState<Environment[]>([])
  const [loading, setLoading] = useState(true)
  const [settingBaseline, setSettingBaseline] = useState<string | null>(null)

  useEffect(() => {
    if (!token) return
    environmentsApi.list(token, currentWorkspace?.id)
      .then(setEnvs)
      .catch(() => setEnvs([]))
      .finally(() => setLoading(false))
  }, [token, currentWorkspace?.id])

  if (loading) {
    return (
      <div className="rounded-[var(--radius-xl)] border border-[var(--color-border)]/50 bg-[var(--color-surface)]/40 p-8 text-center text-[var(--color-text-muted)]">
        Loading environments…
      </div>
    )
  }

  if (envs.length === 0) {
    return (
      <div className="rounded-[var(--radius-xl)] border border-[var(--color-border)]/50 bg-[var(--color-surface)]/40 p-12 text-center">
        <p className="font-semibold text-[var(--color-text)]">No environments yet</p>
        <p className="text-sm text-[var(--color-text-muted)] mt-2">
          Push a report from the CLI to create your first environment.
        </p>
        <code className="mt-4 inline-block text-xs font-mono bg-[var(--color-bg)] px-4 py-2.5 rounded-[var(--radius-md)] text-[var(--color-accent)]">
          envguard report --api-key=YOUR_KEY --env=dev
        </code>
      </div>
    )
  }

  async function handleSetBaseline(env: Environment) {
    const wsId = env.workspace_id || currentWorkspace?.id
    if (!token || !wsId) return
    setSettingBaseline(env.id)
    try {
      await environmentsApi.setBaseline(token, env.id, wsId)
      refresh()
      onBaselineSet?.()
    } catch {
      // ignore
    } finally {
      setSettingBaseline(null)
    }
  }

  return (
    <div className="grid gap-6 md:grid-cols-3">
      {envs.map((env) => (
        <div
          key={env.id}
          className="group p-6 rounded-[var(--radius-xl)] bg-[var(--color-surface)]/50 border border-[var(--color-border)]/50 hover:border-[var(--color-accent)]/20 hover:bg-[var(--color-surface)]/70 transition-all duration-300"
        >
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-center gap-4">
              <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${
                env.last_report ? 'bg-[var(--color-success-muted)]' : 'bg-[var(--color-surface)]/80'
              }`}>
                {env.last_report ? (
                  <svg className="w-6 h-6 text-[var(--color-success)]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                  </svg>
                ) : (
                  <svg className="w-6 h-6 text-[var(--color-text-muted)]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                )}
              </div>
              <div>
                <span className="font-semibold text-[var(--color-text)] capitalize block text-lg">{env.name}</span>
                <span className="text-xs text-[var(--color-text-muted)] font-medium uppercase tracking-wider">{env.type}</span>
              </div>
            </div>
            <span className="flex items-center gap-2">
              {env.is_baseline && (
                <span className="px-2 py-0.5 rounded-[var(--radius-sm)] text-xs font-semibold bg-[var(--color-accent)]/20 text-[var(--color-accent)]">
                  Baseline
                </span>
              )}
              <span className={`px-3 py-1.5 rounded-[var(--radius-md)] text-xs font-semibold ${
                env.health_score === 100
                  ? 'bg-[var(--color-success-muted)] text-[var(--color-success)]'
                  : env.last_report
                    ? 'bg-[var(--color-warning)]/20 text-[var(--color-warning)]'
                    : 'bg-[var(--color-surface)]/80 text-[var(--color-text-muted)]'
              }`}>
                {env.health_score === 100 ? 'Matches' : env.last_report ? 'Reported' : 'No reports'}
              </span>
            </span>
          </div>
          <p className="text-sm text-[var(--color-text-secondary)] mb-4">
            Last report: {formatTimeAgo(env.last_report)}
          </p>
          {env.last_report && env.health_score != null && (
            <div className="mb-4">
              <div className="flex items-center justify-between text-xs mb-1">
                <span className="text-[var(--color-text-muted)]">Parity</span>
                <span className="font-semibold text-[var(--color-text)]">{env.health_score}%</span>
              </div>
              <div className="h-2 rounded-full bg-[var(--color-bg)] overflow-hidden">
                <div
                  className="h-full rounded-full transition-all"
                  style={{
                    width: `${env.health_score}%`,
                    backgroundColor:
                      env.health_score === 100
                        ? 'var(--color-success)'
                        : env.health_score >= 80
                          ? 'var(--color-success)'
                          : env.health_score >= 50
                            ? 'var(--color-warning)'
                            : 'var(--color-error)',
                  }}
                />
              </div>
            </div>
          )}
          <div className="pt-4 border-t border-[var(--color-border)]/50 space-y-3">
            {!env.is_baseline && (env.workspace_id || currentWorkspace?.id) && (
              <button
                type="button"
                onClick={() => handleSetBaseline(env)}
                disabled={settingBaseline === env.id}
                className="text-xs font-semibold text-[var(--color-accent)] hover:underline disabled:opacity-50"
              >
                {settingBaseline === env.id ? 'Setting…' : 'Set as baseline'}
              </button>
            )}
            <code className="text-xs font-mono text-[var(--color-text-muted)] bg-[var(--color-bg)] px-3 py-2 rounded-[var(--radius-md)] block overflow-x-auto">
              envguard collect --env={env.name}
            </code>
          </div>
        </div>
      ))}
    </div>
  )
}
