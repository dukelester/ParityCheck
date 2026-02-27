import { useState } from 'react'
import { EnvironmentStatus } from './components/EnvironmentStatus'
import { DriftTable } from './components/DriftTable'
import { Header } from './components/Header'
import { Documentation } from './components/Documentation'
import { Landing } from './components/Landing'
import './index.css'

type Section = 'home' | 'dashboard' | 'docs'

function App() {
  const [activeSection, setActiveSection] = useState<Section>('home')
  const [activeTab, setActiveTab] = useState<'overview' | 'drifts' | 'history'>('overview')

  return (
    <div className="min-h-screen bg-[var(--color-bg)]">
      <Header activeSection={activeSection} onSectionChange={setActiveSection} />

      {activeSection === 'home' && (
        <Landing onNavigate={(s) => setActiveSection(s)} />
      )}

      {activeSection === 'dashboard' && (
        <main className="max-w-7xl mx-auto px-6 py-10">
          <div className="mb-8">
            <h1 className="text-2xl font-semibold text-[var(--color-text)] tracking-tight">
              Dashboard
            </h1>
            <p className="text-[var(--color-text-secondary)] mt-1">
              Monitor environment parity and drift across dev, staging, and production.
            </p>
          </div>

          <nav className="flex gap-1 mb-10 p-1 rounded-[var(--radius-lg)] bg-[var(--color-surface)] w-fit border border-[var(--color-border)]">
            {(['overview', 'drifts', 'history'] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-5 py-2.5 rounded-[var(--radius-md)] text-sm font-medium transition-all ${
                  activeTab === tab
                    ? 'bg-[var(--color-accent)] text-white shadow-lg shadow-cyan-500/20'
                    : 'text-[var(--color-text-secondary)] hover:text-[var(--color-text)]'
                }`}
              >
                {tab.charAt(0).toUpperCase() + tab.slice(1)}
              </button>
            ))}
          </nav>

          {activeTab === 'overview' && (
            <section>
              <h2 className="text-lg font-semibold text-[var(--color-text)] mb-5">
                Environment Parity Status
              </h2>
              <EnvironmentStatus />
            </section>
          )}

          {activeTab === 'drifts' && (
            <section>
              <h2 className="text-lg font-semibold text-[var(--color-text)] mb-5">
                Drift Detection
              </h2>
              <DriftTable />
            </section>
          )}

          {activeTab === 'history' && (
            <section>
              <h2 className="text-lg font-semibold text-[var(--color-text)] mb-5">
                Historical Changes
              </h2>
              <div className="rounded-[var(--radius-xl)] border border-[var(--color-border)] bg-[var(--color-surface)] p-12 text-center">
                <div className="max-w-md mx-auto">
                  <div className="w-14 h-14 rounded-full bg-[var(--color-surface-hover)] flex items-center justify-center mx-auto mb-4">
                    <svg className="w-7 h-7 text-[var(--color-text-muted)]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <p className="font-medium text-[var(--color-text)]">Report history</p>
                  <p className="text-sm text-[var(--color-text-muted)] mt-2">
                    Connect your CLI and push reports to view historical changes and trends over time.
                  </p>
                  <code className="mt-4 inline-block text-xs font-mono bg-[var(--color-bg)] px-3 py-2 rounded-[var(--radius-md)] text-[var(--color-text-secondary)]">
                    envguard report --api-key=YOUR_KEY
                  </code>
                </div>
              </div>
            </section>
          )}
        </main>
      )}

      {activeSection === 'docs' && <Documentation />}
    </div>
  )
}

export default App
