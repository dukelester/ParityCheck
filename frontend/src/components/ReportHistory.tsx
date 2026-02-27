import React, { useEffect, useState } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { useWorkspace } from '../contexts/WorkspaceContext'
import { reportsApi, type ReportDetail, type ReportSummary } from '../lib/api'

export function ReportHistory() {
  const { token } = useAuth()
  const { currentWorkspace } = useWorkspace()
  const [reports, setReports] = useState<ReportSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const [detail, setDetail] = useState<ReportDetail | null>(null)
  const [detailLoading, setDetailLoading] = useState(false)

  useEffect(() => {
    if (!token) return
    reportsApi.list(token, currentWorkspace?.id)
      .then(setReports)
      .catch(() => setReports([]))
      .finally(() => setLoading(false))
  }, [token, currentWorkspace?.id])

  const fetchDetail = (id: string) => {
    if (expandedId === id) {
      setExpandedId(null)
      setDetail(null)
      return
    }
    if (!token) return
    setExpandedId(id)
    setDetailLoading(true)
    setDetail(null)
    reportsApi.get(token, id)
      .then(setDetail)
      .catch(() => setDetail(null))
      .finally(() => setDetailLoading(false))
  }

  if (loading) {
    return (
      <div className="rounded-[var(--radius-xl)] border border-[var(--color-border)]/50 bg-[var(--color-surface)]/40 p-8 text-center text-[var(--color-text-muted)]">
        Loading reports…
      </div>
    )
  }

  if (reports.length === 0) {
    return (
      <div className="rounded-[var(--radius-xl)] border border-[var(--color-border)]/50 bg-[var(--color-surface)]/40 p-16 text-center">
        <div className="max-w-md mx-auto">
          <div className="w-16 h-16 rounded-2xl bg-[var(--color-surface)]/80 flex items-center justify-center mx-auto mb-5">
            <svg className="w-8 h-8 text-[var(--color-text-muted)]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <p className="font-semibold text-[var(--color-text)]">Report history</p>
          <p className="text-sm text-[var(--color-text-muted)] mt-2 leading-relaxed">
            Connect your CLI and push reports to view historical changes and trends over time.
          </p>
          <code className="mt-5 inline-block text-xs font-mono bg-[var(--color-bg)] px-4 py-2.5 rounded-[var(--radius-md)] text-[var(--color-accent)]">
            envguard report --api-key=YOUR_KEY
          </code>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="rounded-[var(--radius-xl)] border border-[var(--color-border)]/50 bg-[var(--color-surface)]/40 overflow-hidden">
        <table className="w-full text-left">
          <thead>
            <tr className="border-b border-[var(--color-border)]/50">
              <th className="px-6 py-4 text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wider">Environment</th>
              <th className="px-6 py-4 text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wider">Timestamp</th>
              <th className="px-6 py-4 text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wider">Summary</th>
              <th className="px-6 py-4 text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wider">Status</th>
              <th className="px-6 py-4 text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wider"></th>
            </tr>
          </thead>
          <tbody>
            {reports.map((r) => (
              <React.Fragment key={r.id}>
                <tr
                  key={r.id}
                  className="border-b border-[var(--color-border)]/30 last:border-0 hover:bg-[var(--color-surface)]/60 cursor-pointer"
                  onClick={() => fetchDetail(r.id)}
                >
                  <td className="px-6 py-4 font-medium text-[var(--color-text)] capitalize">{r.env}</td>
                  <td className="px-6 py-4 text-sm text-[var(--color-text-secondary)]">
                    {new Date(r.timestamp).toLocaleString()}
                  </td>
                  <td className="px-6 py-4 text-sm text-[var(--color-text-secondary)]">
                    <span className="flex items-center gap-2">
                      {r.health_score != null ? (
                        <>
                          <span
                            className="shrink-0 w-12 h-1.5 rounded-full overflow-hidden bg-[var(--color-bg)]"
                            title={`Health: ${r.health_score}%`}
                          >
                            <span
                              className="block h-full rounded-full transition-all"
                              style={{
                                width: `${r.health_score}%`,
                                backgroundColor:
                                  r.health_score === 100
                                    ? 'var(--color-success)'
                                    : r.health_score >= 80
                                      ? 'var(--color-success)'
                                      : r.health_score >= 50
                                        ? 'var(--color-warning)'
                                        : 'var(--color-error)',
                              }}
                            />
                          </span>
                          <span className="font-semibold text-[var(--color-text)]">
                            Health: {r.health_score}
                          </span>
                        </>
                      ) : (
                        <span className="font-medium text-[var(--color-text-muted)]">Health: —</span>
                      )}
                    </span>
                    {r.summary ? (
                      <span className="text-[var(--color-text-muted)]">
                        {r.summary.os || '—'} · Python {r.summary.python_version || '—'} · {r.summary.deps_count} deps · {r.summary.env_vars_count} env vars
                      </span>
                    ) : (
                      '—'
                    )}
                  </td>
                  <td className="px-6 py-4">
                    <span className="px-2.5 py-1 rounded-[var(--radius-md)] text-xs font-semibold bg-[var(--color-success-muted)] text-[var(--color-success)]">
                      {r.status}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <span className="text-[var(--color-text-muted)]">
                      {expandedId === r.id ? '▼' : '▶'}
                    </span>
                  </td>
                </tr>
                {expandedId === r.id && (
                  <tr>
                    <td colSpan={5} className="px-6 py-6 bg-[var(--color-bg)]/50 border-b border-[var(--color-border)]/30">
                      {detailLoading ? (
                        <div className="text-center text-[var(--color-text-muted)] py-8">Loading details…</div>
                      ) : detail ? (
                        <ReportDetailView report={detail} />
                      ) : (
                        <div className="text-center text-[var(--color-text-muted)] py-4">Failed to load details</div>
                      )}
                    </td>
                  </tr>
                )}
              </React.Fragment>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

const SEVERITY_COLORS: Record<string, string> = {
  critical: 'bg-red-500/20 text-red-400',
  high: 'bg-orange-500/20 text-orange-400',
  medium: 'bg-yellow-500/20 text-yellow-400',
  low: 'bg-blue-500/20 text-blue-400',
}

function ReportDetailView({ report }: { report: ReportDetail }) {
  const [showDeps, setShowDeps] = useState(false)
  const [showEnvVars, setShowEnvVars] = useState(false)
  const [showTransitive, setShowTransitive] = useState(false)

  const os = report.os as Record<string, string> | null
  const osStr = os && typeof os === 'object'
    ? `${os.system || ''} ${os.release || ''} ${os.machine || ''}`.trim()
    : '—'

  const drifts = report.drifts || []
  const directDrifts = drifts.filter((d) => d.type === 'dependency' && d.details?.category === 'direct')
  const transitiveDrifts = drifts.filter((d) => d.type === 'dependency' && d.details?.category === 'transitive')
  const otherDrifts = drifts.filter((d) => d.type !== 'dependency' || (d.details?.category !== 'direct' && d.details?.category !== 'transitive'))

  const summary = report.summary || { critical: 0, high: 0, medium: 0, low: 0 }

  const depsCount = (() => {
    const d = report.deps
    if (!d || typeof d !== 'object') return 0
    const inst = (d as Record<string, unknown>).installed_dependencies
    if (inst && typeof inst === 'object') return Object.keys(inst).length
    return Object.keys(d).filter((k) => !['direct_dependencies', 'installed_dependencies', 'transitive_dependencies'].includes(k)).length || Object.keys(d).length
  })()

  const healthScore = report.health_score ?? null

  return (
    <div className="space-y-6">
        <div className="mb-4 p-4 rounded-[var(--radius-lg)] bg-[var(--color-surface)]/60">
          <p className="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wider mb-1">Health Score</p>
          <div className="flex items-center gap-3">
            <div className="flex-1 h-3 rounded-full bg-[var(--color-bg)] overflow-hidden">
              <div
                className="h-full rounded-full transition-all"
                style={{
                  width: `${healthScore != null ? healthScore : 0}%`,
                  backgroundColor:
                    healthScore == null
                      ? 'var(--color-border)'
                      : healthScore === 100
                        ? 'var(--color-success)'
                        : healthScore >= 80
                          ? 'var(--color-success)'
                          : healthScore >= 50
                            ? 'var(--color-warning)'
                            : 'var(--color-error)',
                }}
              />
            </div>
            <span className="font-bold text-[var(--color-text)]">
              {healthScore != null ? healthScore : '—'}
            </span>
          </div>
          {healthScore === 100 && drifts.length === 0 && (
            <p className="text-xs text-[var(--color-success)] mt-2 font-medium">
              Environment matches baseline
            </p>
          )}
          {healthScore != null && healthScore < 100 && (summary.critical > 0 || summary.high > 0 || summary.medium > 0 || summary.low > 0) && (
            <p className="text-xs text-[var(--color-text-muted)] mt-2">
              Critical: {summary.critical} · High: {summary.high} · Medium: {summary.medium} · Low: {summary.low}
            </p>
          )}
          {healthScore == null && (
            <p className="text-xs text-[var(--color-text-muted)] mt-2">
              Health score unavailable for this report
            </p>
          )}
        </div>
        {drifts.length > 0 && (
          <div className="space-y-3">
            <p className="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wider">Drifts</p>
            <div className="space-y-2">
              {otherDrifts.map((d, i) => (
                <div key={d.id || i} className="flex items-start gap-2 text-sm">
                  <span className={`shrink-0 px-2 py-0.5 rounded text-xs font-semibold capitalize ${SEVERITY_COLORS[d.severity] || ''}`}>
                    {d.severity}
                  </span>
                  <span className="text-[var(--color-text)]">
                    {d.type === 'dependency' ? (
                      <><span className="font-mono">{d.key}</span> {d.value_a != null && d.value_b != null && (
                        <span className="text-[var(--color-text-muted)]">({d.value_a} → {d.value_b})</span>
                      )}</>
                    ) : (
                      <><span className="font-mono">{d.key}</span> {d.value_a != null && d.value_b != null && (
                        <span className="text-[var(--color-text-muted)]">{d.value_a} → {d.value_b}</span>
                      )}</>
                    )}
                  </span>
                </div>
              ))}
              {directDrifts.map((d, i) => (
                <div key={d.id || `direct-${i}`} className="flex items-start gap-2 text-sm">
                  <span className={`shrink-0 px-2 py-0.5 rounded text-xs font-semibold capitalize ${SEVERITY_COLORS[d.severity] || ''}`}>
                    {d.severity}
                  </span>
                  <span className="shrink-0 px-1.5 py-0.5 rounded text-xs font-medium bg-red-500/20 text-red-400">
                    Direct
                  </span>
                  <span className="text-[var(--color-text)]">
                    <span className="font-mono">{d.key}</span>
                    {d.value_a != null && d.value_b != null && (
                      <span className="text-[var(--color-text-muted)] ml-1">({d.value_a} → {d.value_b})</span>
                    )}
                    {d.details?.reason && (
                      <span className="text-[var(--color-text-muted)] ml-1">– {d.details.reason}</span>
                    )}
                  </span>
                </div>
              ))}
              {transitiveDrifts.length > 0 && (
                <div>
                  <button
                    type="button"
                    onClick={() => setShowTransitive(!showTransitive)}
                    className="flex items-center gap-2 text-sm font-semibold text-[var(--color-text)] hover:text-[var(--color-accent)]"
                  >
                    {showTransitive ? '▼' : '▶'} Transitive ({transitiveDrifts.length})
                  </button>
                  {showTransitive && (
                    <div className="mt-2 pl-4 space-y-2 border-l-2 border-[var(--color-border)]/50">
                      {transitiveDrifts.map((d, i) => (
                        <div key={d.id || `trans-${i}`} className="flex items-start gap-2 text-sm">
                          <span className={`shrink-0 px-2 py-0.5 rounded text-xs font-semibold capitalize ${SEVERITY_COLORS[d.severity] || ''}`}>
                            {d.severity}
                          </span>
                          <span className="shrink-0 px-1.5 py-0.5 rounded text-xs font-medium bg-yellow-500/20 text-yellow-500">
                            Transitive
                          </span>
                          <span className="text-[var(--color-text)]">
                            <span className="font-mono">{d.key}</span>
                            {d.value_a != null && d.value_b != null && (
                              <span className="text-[var(--color-text-muted)] ml-1">({d.value_a} → {d.value_b})</span>
                            )}
                            {d.details?.reason && (
                              <span className="text-[var(--color-text-muted)] ml-1">– {d.details.reason}</span>
                            )}
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        )}

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="p-4 rounded-[var(--radius-lg)] bg-[var(--color-surface)]/60">
          <p className="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wider mb-1">OS</p>
          <p className="text-sm text-[var(--color-text)]">{osStr || '—'}</p>
        </div>
        <div className="p-4 rounded-[var(--radius-lg)] bg-[var(--color-surface)]/60">
          <p className="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wider mb-1">Python</p>
          <p className="text-sm text-[var(--color-text)]">{report.python_version || '—'}</p>
        </div>
        <div className="p-4 rounded-[var(--radius-lg)] bg-[var(--color-surface)]/60">
          <p className="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wider mb-1">Dependencies</p>
          <p className="text-sm text-[var(--color-text)]">{depsCount} packages</p>
        </div>
        <div className="p-4 rounded-[var(--radius-lg)] bg-[var(--color-surface)]/60">
          <p className="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wider mb-1">DB schema hash</p>
          <p className="text-sm font-mono text-[var(--color-text)] truncate" title={report.db_schema_hash || undefined}>
            {report.db_schema_hash || '—'}
          </p>
        </div>
      </div>

      {report.k8s && (
        <div className="p-4 rounded-[var(--radius-lg)] bg-[var(--color-surface)]/60 space-y-3">
          <p className="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wider">Kubernetes</p>
          <div className="grid gap-2 sm:grid-cols-2">
            <div>
              <span className="text-xs text-[var(--color-text-muted)]">Namespace</span>
              <p className="text-sm font-mono text-[var(--color-text)]">{report.k8s.namespace || '—'}</p>
            </div>
            <div>
              <span className="text-xs text-[var(--color-text-muted)]">Deployments</span>
              <p className="text-sm text-[var(--color-text)]">
                {Object.keys(report.k8s.deployments || {}).length}
              </p>
            </div>
            <div>
              <span className="text-xs text-[var(--color-text-muted)]">ConfigMaps</span>
              <p className="text-sm text-[var(--color-text)]">
                {Object.keys(report.k8s.configmaps || {}).length}
              </p>
            </div>
            <div>
              <span className="text-xs text-[var(--color-text-muted)]">Secrets</span>
              <p className="text-sm text-[var(--color-text)]">
                {Object.keys(report.k8s.secrets || {}).length}
              </p>
            </div>
          </div>
        </div>
      )}

      {report.docker && (
        <div className="p-4 rounded-[var(--radius-lg)] bg-[var(--color-surface)]/60 space-y-3">
          <p className="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wider">Docker</p>
          <div className="grid gap-2 sm:grid-cols-2">
            <div>
              <span className="text-xs text-[var(--color-text-muted)]">Image</span>
              <p className="text-sm font-mono text-[var(--color-text)] truncate" title={report.docker.image_tag || undefined}>
                {report.docker.image_tag || '—'}
              </p>
            </div>
            <div>
              <span className="text-xs text-[var(--color-text-muted)]">Digest</span>
              <p className="text-sm font-mono text-[var(--color-text)] truncate" title={report.docker.image_digest || undefined}>
                {report.docker.image_digest || '—'}
              </p>
            </div>
            <div>
              <span className="text-xs text-[var(--color-text-muted)]">Base image</span>
              <p className="text-sm font-mono text-[var(--color-text)] truncate" title={report.docker.base_image || undefined}>
                {report.docker.base_image || '—'}
              </p>
            </div>
            <div>
              <span className="text-xs text-[var(--color-text-muted)]">Container OS</span>
              <p className="text-sm text-[var(--color-text)]">
                {report.docker.container_os
                  ? `${report.docker.container_os.name || report.docker.container_os.id || '—'} ${report.docker.container_os.version_id || ''}`.trim()
                  : '—'}
              </p>
            </div>
          </div>
        </div>
      )}

      <div>
        <button
          type="button"
          onClick={() => setShowDeps(!showDeps)}
          className="flex items-center gap-2 text-sm font-semibold text-[var(--color-text)] hover:text-[var(--color-accent)]"
        >
          {showDeps ? '▼' : '▶'} Dependencies ({depsCount})
        </button>
        {showDeps && report.deps && (
          <pre className="mt-2 p-4 rounded-[var(--radius-md)] bg-[var(--color-bg)] text-xs font-mono text-[var(--color-text-secondary)] overflow-x-auto max-h-48 overflow-y-auto">
            {JSON.stringify(report.deps, null, 2)}
          </pre>
        )}
      </div>

      <div>
        <button
          type="button"
          onClick={() => setShowEnvVars(!showEnvVars)}
          className="flex items-center gap-2 text-sm font-semibold text-[var(--color-text)] hover:text-[var(--color-accent)]"
        >
          {showEnvVars ? '▼' : '▶'} Environment variables ({Object.keys(report.env_vars || {}).length})
        </button>
        {showEnvVars && report.env_vars && (
          <pre className="mt-2 p-4 rounded-[var(--radius-md)] bg-[var(--color-bg)] text-xs font-mono text-[var(--color-text-secondary)] overflow-x-auto max-h-48 overflow-y-auto">
            {JSON.stringify(report.env_vars, null, 2)}
          </pre>
        )}
      </div>
    </div>
  )
}
