import { useState, useEffect } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { useWorkspace } from '../contexts/WorkspaceContext'
import {
  reportsApi,
  environmentsApi,
  type ReportSummary,
  type Environment,
  type AnalyzeResult,
} from '../lib/api'

const SEVERITY_COLORS: Record<string, string> = {
  critical: 'bg-red-500/20 text-red-400',
  high: 'bg-orange-500/20 text-orange-400',
  medium: 'bg-yellow-500/20 text-yellow-400',
  low: 'bg-blue-500/20 text-blue-400',
}

export function AnalyzeView() {
  const { token } = useAuth()
  const { currentWorkspace } = useWorkspace()
  const [reports, setReports] = useState<ReportSummary[]>([])
  const [envs, setEnvs] = useState<Environment[]>([])
  const [loading, setLoading] = useState(true)
  const [reportId, setReportId] = useState('')
  const [against, setAgainst] = useState('prod')
  const [analyzing, setAnalyzing] = useState(false)
  const [result, setResult] = useState<AnalyzeResult | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!token) return
    setLoading(true)
    Promise.all([
      reportsApi.list(token, currentWorkspace?.id),
      environmentsApi.list(token, currentWorkspace?.id),
    ])
      .then(([r, e]) => {
        setReports(r)
        setEnvs(e)
        if (e.length > 0) {
          setAgainst(e.find((x) => x.name === 'prod')?.name || e[0].name)
        }
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [token, currentWorkspace?.id])

  async function runAnalysis() {
    if (!token || !reportId) return
    setAnalyzing(true)
    setError(null)
    setResult(null)
    try {
      const r = await reportsApi.analyze(token, reportId, against)
      setResult(r)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Analysis failed')
    } finally {
      setAnalyzing(false)
    }
  }

  if (loading) {
    return (
      <div className="rounded-[var(--radius-xl)] border border-[var(--color-border)]/50 bg-[var(--color-surface)]/40 p-8 text-center text-[var(--color-text-muted)]">
        Loading…
      </div>
    )
  }

  if (reports.length === 0) {
    return (
      <div className="rounded-[var(--radius-xl)] border border-[var(--color-border)]/50 bg-[var(--color-surface)]/40 p-12 text-center">
        <p className="font-semibold text-[var(--color-text)]">No reports yet</p>
        <p className="text-sm text-[var(--color-text-muted)] mt-2">
          Upload reports from the CLI first, then run analysis.
        </p>
        <code className="mt-4 inline-block text-xs font-mono bg-[var(--color-bg)] px-4 py-2.5 rounded-[var(--radius-md)] text-[var(--color-accent)]">
          envguard report --api-key=YOUR_KEY --env=prod
        </code>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="rounded-[var(--radius-xl)] border border-[var(--color-border)]/50 bg-[var(--color-surface)]/40 p-6">
        <h3 className="text-base font-semibold text-[var(--color-text)] mb-1">
          Deployment Risk Analysis
        </h3>
        <p className="text-sm text-[var(--color-text-muted)] mb-6">
          Compare a report against a target environment (e.g. prod) to predict deployment risk.
        </p>
        <div className="flex flex-wrap gap-4 items-end">
          <div>
            <label className="block text-xs font-semibold text-[var(--color-text-muted)] mb-1.5">
              Report to analyze
            </label>
            <select
              value={reportId}
              onChange={(e) => setReportId(e.target.value)}
              className="px-4 py-2.5 rounded-[var(--radius-md)] bg-[var(--color-bg)] border border-[var(--color-border)]/70 text-[var(--color-text)] min-w-[220px]"
            >
              <option value="">Select report…</option>
              {reports.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.env} · {new Date(r.timestamp).toLocaleString()}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs font-semibold text-[var(--color-text-muted)] mb-1.5">
              Compare against
            </label>
            <select
              value={against}
              onChange={(e) => setAgainst(e.target.value)}
              className="px-4 py-2.5 rounded-[var(--radius-md)] bg-[var(--color-bg)] border border-[var(--color-border)]/70 text-[var(--color-text)]"
            >
              {envs.map((e) => (
                <option key={e.id} value={e.name}>
                  {e.name}
                </option>
              ))}
              {envs.length === 0 && (
                <>
                  <option value="prod">prod</option>
                  <option value="staging">staging</option>
                  <option value="dev">dev</option>
                </>
              )}
            </select>
          </div>
          <button
            type="button"
            onClick={runAnalysis}
            disabled={!reportId || analyzing}
            className="px-5 py-2.5 rounded-[var(--radius-md)] bg-[var(--color-accent)] text-[var(--color-bg)] font-semibold hover:bg-[var(--color-accent-hover)] disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {analyzing ? 'Analyzing…' : 'Analyze'}
          </button>
        </div>
        {error && (
          <p className="mt-4 text-sm text-[var(--color-error)]">{error}</p>
        )}
      </div>

      {result && (
        <div className="rounded-[var(--radius-xl)] border border-[var(--color-border)]/50 bg-[var(--color-surface)]/40 overflow-hidden">
          <div className="px-6 py-5 border-b border-[var(--color-border)]/50">
            <h3 className="text-base font-semibold text-[var(--color-text)]">Results</h3>
            <p className="text-sm text-[var(--color-text-muted)] mt-0.5">
              {result.current_env} → {result.against}
            </p>
          </div>
          <div className="p-6 space-y-6">
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <div className="p-4 rounded-[var(--radius-lg)] bg-[var(--color-bg)]/60">
                <p className="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wider mb-1">
                  Deployment Risk
                </p>
                <p className="text-2xl font-bold text-[var(--color-text)]">
                  {result.deployment_risk_score}/100
                </p>
                <p className="text-xs text-[var(--color-text-muted)] mt-0.5">
                  {result.risk_level}
                </p>
              </div>
              <div className="p-4 rounded-[var(--radius-lg)] bg-[var(--color-bg)]/60">
                <p className="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wider mb-1">
                  Health Score
                </p>
                <p className="text-2xl font-bold text-[var(--color-text)]">
                  {result.health_score}/100
                </p>
              </div>
              <div className="p-4 rounded-[var(--radius-lg)] bg-[var(--color-bg)]/60">
                <p className="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wider mb-1">
                  Safe to deploy
                </p>
                <p
                  className={`text-lg font-bold ${
                    result.safe_to_deploy ? 'text-[var(--color-success)]' : 'text-[var(--color-error)]'
                  }`}
                >
                  {result.safe_to_deploy ? 'Yes' : 'No'}
                </p>
              </div>
              <div className="p-4 rounded-[var(--radius-lg)] bg-[var(--color-bg)]/60">
                <p className="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wider mb-1">
                  Drifts
                </p>
                <p className="text-2xl font-bold text-[var(--color-text)]">
                  {result.drift_count}
                </p>
                {result.summary && (
                  <p className="text-xs text-[var(--color-text-muted)] mt-0.5">
                    C:{result.summary.critical} H:{result.summary.high} M:{result.summary.medium} L:
                    {result.summary.low}
                  </p>
                )}
              </div>
            </div>

            {result.risky_changes.length > 0 && (
              <div>
                <p className="text-sm font-semibold text-[var(--color-text)] mb-3">
                  Risky changes
                </p>
                <div className="space-y-2">
                  {result.risky_changes.map((d, i) => (
                    <div
                      key={i}
                      className="flex items-start gap-2 text-sm py-2 px-3 rounded-[var(--radius-md)] bg-[var(--color-bg)]/40"
                    >
                      <span
                        className={`shrink-0 px-2 py-0.5 rounded text-xs font-semibold capitalize ${SEVERITY_COLORS[d.severity] || ''}`}
                      >
                        {d.severity}
                      </span>
                      {d.category && (
                        <span
                          className={`shrink-0 px-1.5 py-0.5 rounded text-xs ${
                            d.category === 'direct'
                              ? 'bg-red-500/20 text-red-400'
                              : 'bg-yellow-500/20 text-yellow-500'
                          }`}
                        >
                          {d.category}
                        </span>
                      )}
                      <span className="font-mono text-[var(--color-text)]">{d.key}</span>
                      <span className="text-[var(--color-text-muted)]">
                        {d.value_a ?? '?'} → {d.value_b ?? '?'}
                      </span>
                      {d.reason && (
                        <span className="text-[var(--color-text-muted)]">– {d.reason}</span>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {result.safe_to_deploy && (
              <p className="text-sm text-[var(--color-success)] font-medium">
                No drift detected. Safe to deploy.
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
