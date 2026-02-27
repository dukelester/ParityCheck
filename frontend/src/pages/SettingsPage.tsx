import { useState } from 'react'
import { IgnoreRulesPage } from './IgnoreRulesPage'
import { AlertsPage } from './AlertsPage'
import { useWorkspace } from '../contexts/WorkspaceContext'

export function SettingsPage() {
  const [tab, setTab] = useState<'ignore' | 'alerts'>('ignore')
  const { currentWorkspace, usage } = useWorkspace()

  return (
    <main className="max-w-7xl mx-auto px-6 py-10 md:py-12">
      <div className="mb-10">
        <h1 className="text-2xl md:text-3xl font-bold text-[var(--color-text)] tracking-tight">
          Settings
        </h1>
        <p className="text-[var(--color-text-secondary)] mt-2">
          Manage ignore rules and alerts for {currentWorkspace?.name || 'your workspace'}.
        </p>
      </div>

      {usage && (
        <div className="mb-8 p-6 rounded-[var(--radius-xl)] border border-[var(--color-border)]/50 bg-[var(--color-surface)]/40">
          <h2 className="text-base font-semibold text-[var(--color-text)] mb-4">Plan usage</h2>
          <div className="grid gap-4 sm:grid-cols-3">
            <div>
              <p className="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wider">Plan</p>
              <p className="text-lg font-bold text-[var(--color-text)] capitalize mt-1">{usage.plan}</p>
            </div>
            <div>
              <p className="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wider">Environments</p>
              <p className="text-lg font-bold text-[var(--color-text)] mt-1">
                {usage.environments.used} / {usage.environments.limit}
              </p>
            </div>
            <div>
              <p className="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wider">History</p>
              <p className="text-lg font-bold text-[var(--color-text)] mt-1">{usage.history_days} days</p>
            </div>
          </div>
        </div>
      )}

      <nav className="flex gap-1 mb-8 p-1.5 rounded-[var(--radius-lg)] bg-[var(--color-surface)]/40 w-fit border border-[var(--color-border)]/50">
        <button
          onClick={() => setTab('ignore')}
          className={`px-6 py-3 rounded-[var(--radius-md)] text-sm font-semibold transition-all ${
            tab === 'ignore'
              ? 'bg-[var(--color-accent)] text-[var(--color-bg)]'
              : 'text-[var(--color-text-secondary)] hover:text-[var(--color-text)] hover:bg-[var(--color-surface)]/50'
          }`}
        >
          Ignore rules
        </button>
        <button
          onClick={() => setTab('alerts')}
          className={`px-6 py-3 rounded-[var(--radius-md)] text-sm font-semibold transition-all ${
            tab === 'alerts'
              ? 'bg-[var(--color-accent)] text-[var(--color-bg)]'
              : 'text-[var(--color-text-secondary)] hover:text-[var(--color-text)] hover:bg-[var(--color-surface)]/50'
          }`}
        >
          Alerts
        </button>
      </nav>

      {tab === 'ignore' && <IgnoreRulesPage />}
      {tab === 'alerts' && <AlertsPage />}
    </main>
  )
}
