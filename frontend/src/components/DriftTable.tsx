const drifts: { id: string; type: string; env: string; details: string; resolved: boolean }[] = []

export function DriftTable() {
  return (
    <div className="rounded-[var(--radius-xl)] border border-[var(--color-border)]/50 overflow-hidden bg-[var(--color-surface)]/40">
      <div className="px-6 py-5 border-b border-[var(--color-border)]/50">
        <h3 className="text-base font-semibold text-[var(--color-text)]">Active Drifts</h3>
        <p className="text-sm text-[var(--color-text-muted)] mt-0.5">Dependency, env var, and schema differences across environments</p>
      </div>
      <table className="w-full">
        <thead>
          <tr className="border-b border-[var(--color-border)]/50">
            <th className="text-left px-6 py-4 text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-widest">Type</th>
            <th className="text-left px-6 py-4 text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-widest">Environment</th>
            <th className="text-left px-6 py-4 text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-widest">Details</th>
            <th className="text-left px-6 py-4 text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-widest">Status</th>
          </tr>
        </thead>
        <tbody>
          {drifts.length === 0 ? (
            <tr>
              <td colSpan={4} className="px-6 py-20 text-center">
                <div className="flex flex-col items-center gap-5 max-w-sm mx-auto">
                  <div className="w-16 h-16 rounded-2xl bg-[var(--color-surface)]/80 flex items-center justify-center">
                    <svg className="w-8 h-8 text-[var(--color-text-muted)]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                  </div>
                  <div>
                    <p className="font-semibold text-[var(--color-text)]">No drifts detected</p>
                    <p className="text-sm text-[var(--color-text-muted)] mt-2">
                      Run <code className="font-mono text-xs bg-[var(--color-bg)] px-2 py-1 rounded-[var(--radius-sm)] text-[var(--color-accent)]">envguard report</code> from your environments to start tracking.
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
                <td className="px-6 py-4 text-sm text-[var(--color-text-secondary)] capitalize">{d.env}</td>
                <td className="px-6 py-4 text-sm text-[var(--color-text)]">{d.details}</td>
                <td className="px-6 py-4">
                  <span className={`inline-flex px-3 py-1 rounded-[var(--radius-md)] text-xs font-semibold ${
                    d.resolved ? 'bg-[var(--color-success-muted)] text-[var(--color-success)]' : 'bg-[var(--color-warning-muted)] text-[var(--color-warning)]'
                  }`}>
                    {d.resolved ? 'Resolved' : 'Open'}
                  </span>
                </td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  )
}
