import { Link } from 'react-router-dom'
import { useEffect, useState } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { useWorkspace } from '../contexts/WorkspaceContext'
import { driftsApi, type Drift } from '../lib/api'

const SEVERITY_COLORS: Record<string, string> = {
  critical: 'bg-red-500/20 text-red-400',
  high: 'bg-orange-500/20 text-orange-400',
  medium: 'bg-yellow-500/20 text-yellow-400',
  low: 'bg-blue-500/20 text-blue-400',
}

export function DriftTable() {
  const { token } = useAuth()
  const { currentWorkspace } = useWorkspace()
  const [drifts, setDrifts] = useState<Drift[]>([])
  const [loading, setLoading] = useState(true)
  const [severityFilter, setSeverityFilter] = useState<string>('')

  useEffect(() => {
    if (!token) return
    driftsApi.list(token, currentWorkspace?.id, undefined, severityFilter || undefined)
      .then(setDrifts)
      .catch(() => setDrifts([]))
      .finally(() => setLoading(false))
  }, [token, currentWorkspace?.id, severityFilter])

  return (
    <div className="rounded-[var(--radius-xl)] border border-[var(--color-border)]/50 overflow-hidden bg-[var(--color-surface)]/40">
      <div className="px-6 py-5 border-b border-[var(--color-border)]/50 flex flex-wrap items-center justify-between gap-4">
        <div>
          <h3 className="text-base font-semibold text-[var(--color-text)]">Active Drifts</h3>
          <p className="text-sm text-[var(--color-text-muted)] mt-0.5">Dependency, env var, and schema differences across environments</p>
        </div>
        <select
          value={severityFilter}
          onChange={(e) => setSeverityFilter(e.target.value)}
          className="px-3 py-2 rounded-[var(--radius-md)] bg-[var(--color-bg)] border border-[var(--color-border)]/70 text-[var(--color-text)] text-sm"
        >
          <option value="">All severities</option>
          <option value="critical">Critical</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>
      </div>
      <table className="w-full">
        <thead>
          <tr className="border-b border-[var(--color-border)]/50">
            <th className="text-left px-6 py-4 text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-widest">Type</th>
            <th className="text-left px-6 py-4 text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-widest">Severity</th>
            <th className="text-left px-6 py-4 text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-widest">Environment</th>
            <th className="text-left px-6 py-4 text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-widest">Details</th>
            <th className="text-left px-6 py-4 text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-widest">Root cause</th>
          </tr>
        </thead>
        <tbody>
          {loading ? (
            <tr>
              <td colSpan={5} className="px-6 py-12 text-center text-[var(--color-text-muted)]">Loading…</td>
            </tr>
          ) : drifts.length === 0 ? (
            <tr>
              <td colSpan={5} className="px-6 py-20 text-center">
                <div className="flex flex-col items-center gap-5 max-w-sm mx-auto">
                  <div className="w-16 h-16 rounded-2xl bg-[var(--color-surface)]/80 flex items-center justify-center">
                    <svg className="w-8 h-8 text-[var(--color-text-muted)]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                  </div>
                  <div>
                    <p className="font-semibold text-[var(--color-text)]">No drifts detected</p>
                    <p className="text-sm text-[var(--color-text-muted)] mt-2">
                      {severityFilter ? (
                        <>No drifts match &quot;{severityFilter}&quot;. Try <strong>All severities</strong> to see medium/low drifts (e.g. OS differences).</>
                      ) : (
                        <>
                          Drifts appear when environments differ from the baseline. Run{' '}
                          <code className="font-mono text-xs bg-[var(--color-bg)] px-2 py-1 rounded-[var(--radius-sm)] text-[var(--color-accent)]">envguard report</code>{' '}
                          from at least two environments (e.g. dev and staging) to compare.
                        </>
                      )}
                    </p>
                  </div>
                </div>
              </td>
            </tr>
          ) : (
            drifts.map((d) => (
              <tr key={d.id} className="border-b border-[var(--color-border)]/30 hover:bg-[var(--color-surface)]/30 transition-colors">
                <td className="px-6 py-4">
                  <code className="text-sm font-mono text-[var(--color-accent)]">{d.type}</code>
                </td>
                <td className="px-6 py-4">
                  <span className={`inline-flex px-2 py-0.5 rounded text-xs font-semibold capitalize ${SEVERITY_COLORS[d.severity] || ''}`}>
                    {d.severity}
                  </span>
                </td>
                <td className="px-6 py-4 text-sm text-[var(--color-text-secondary)] capitalize">{d.env}</td>
                <td className="px-6 py-4 text-sm text-[var(--color-text)]">
                  {d.details?.category === 'direct' && (
                    <span className="mr-1.5 px-1.5 py-0.5 rounded text-xs font-medium bg-red-500/20 text-red-400">Direct</span>
                  )}
                  {d.details?.category === 'transitive' && (
                    <span className="mr-1.5 px-1.5 py-0.5 rounded text-xs font-medium bg-yellow-500/20 text-yellow-500">Transitive</span>
                  )}
                  {d.key && (
                    <span className="font-mono">{d.key}</span>
                  )}
                  {d.value_a != null && d.value_b != null && (
                    <span className="text-[var(--color-text-muted)] ml-1">
                      {d.value_a} → {d.value_b}
                    </span>
                  )}
                  {d.details?.reason && (
                    <span className="text-[var(--color-text-muted)] ml-1">– {d.details.reason}</span>
                  )}
                </td>
                <td className="px-6 py-4 text-sm text-[var(--color-text-secondary)]">
                  <div className="space-y-1">
                    {d.introduced_at && (
                      <div title="When drift first appeared">
                        Started {new Date(d.introduced_at).toLocaleString()}
                      </div>
                    )}
                    {d.introduced_by_report_id && (
                      <Link
                        to="/dashboard"
                        className="text-[var(--color-accent)] hover:underline"
                        title="Report that introduced this drift"
                      >
                        Report {d.introduced_by_report_id.slice(0, 8)}…
                      </Link>
                    )}
                    {d.details?.likely_caused_by && (
                      <div title="Direct dependency that pulled in this transitive change">
                        Caused by <code className="font-mono text-xs">{d.details.likely_caused_by}</code>
                      </div>
                    )}
                    {!d.introduced_at && !d.details?.likely_caused_by && '—'}
                  </div>
                </td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  )
}
