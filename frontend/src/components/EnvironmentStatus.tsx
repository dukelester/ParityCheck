const envs = [
  { name: 'dev', type: 'dev', status: 'ok' as const, lastReport: '2 min ago' },
  { name: 'staging', type: 'staging', status: 'drift' as const, lastReport: '1 hour ago' },
  { name: 'prod', type: 'prod', status: 'ok' as const, lastReport: '5 min ago' },
]

export function EnvironmentStatus() {
  return (
    <div className="grid gap-6 md:grid-cols-3">
      {envs.map((env) => (
        <div
          key={env.name}
          className="group p-6 rounded-[var(--radius-xl)] bg-[var(--color-surface)]/50 border border-[var(--color-border)]/50 hover:border-[var(--color-accent)]/20 hover:bg-[var(--color-surface)]/70 transition-all duration-300"
        >
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-center gap-4">
              <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${
                env.status === 'ok' ? 'bg-[var(--color-success-muted)]' : 'bg-[var(--color-warning-muted)]'
              }`}>
                {env.status === 'ok' ? (
                  <svg className="w-6 h-6 text-[var(--color-success)]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                  </svg>
                ) : (
                  <svg className="w-6 h-6 text-[var(--color-warning)]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                )}
              </div>
              <div>
                <span className="font-semibold text-[var(--color-text)] capitalize block text-lg">{env.name}</span>
                <span className="text-xs text-[var(--color-text-muted)] font-medium uppercase tracking-wider">{env.type}</span>
              </div>
            </div>
            <span className={`px-3 py-1.5 rounded-[var(--radius-md)] text-xs font-semibold ${
              env.status === 'ok'
                ? 'bg-[var(--color-success-muted)] text-[var(--color-success)]'
                : 'bg-[var(--color-warning-muted)] text-[var(--color-warning)]'
            }`}>
              {env.status === 'ok' ? 'In sync' : 'Drift'}
            </span>
          </div>
          <p className="text-sm text-[var(--color-text-secondary)] mb-4">Last report: {env.lastReport}</p>
          <div className="pt-4 border-t border-[var(--color-border)]/50">
            <code className="text-xs font-mono text-[var(--color-text-muted)] bg-[var(--color-bg)] px-3 py-2 rounded-[var(--radius-md)] block overflow-x-auto">
              envguard collect --env={env.name}
            </code>
          </div>
        </div>
      ))}
    </div>
  )
}
