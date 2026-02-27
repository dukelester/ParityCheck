import { CodeBlock } from './CodeBlock'

interface LandingProps {
  onNavigate: (section: 'dashboard' | 'docs') => void
}

export function Landing({ onNavigate }: LandingProps) {
  return (
    <>
      {/* Hero */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-cyan-500/5 via-transparent to-transparent" />
        <div className="relative max-w-5xl mx-auto px-6 pt-20 pb-24 md:pt-28 md:pb-32">
          <div className="text-center">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-[var(--color-surface)] border border-[var(--color-border)] mb-8">
              <span className="w-2 h-2 rounded-full bg-[var(--color-success)] animate-pulse" />
              <span className="text-sm font-medium text-[var(--color-text-secondary)]">Environment drift detection for modern teams</span>
            </div>
            <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold text-[var(--color-text)] tracking-tight leading-[1.1]">
              Ship with confidence.
              <br />
              <span className="text-[var(--color-accent)]">Know when environments drift.</span>
            </h1>
            <p className="mt-6 text-lg md:text-xl text-[var(--color-text-secondary)] max-w-2xl mx-auto leading-relaxed">
              ParityCheck detects differences across dev, staging, and production—dependencies, env vars, and schema. Get alerts before drift becomes a problem.
            </p>
            <div className="mt-10 flex flex-wrap items-center justify-center gap-4">
              <button
                onClick={() => onNavigate('dashboard')}
                className="px-6 py-3.5 rounded-[var(--radius-lg)] bg-[var(--color-accent)] text-white font-semibold hover:bg-[var(--color-accent-hover)] transition-all shadow-lg shadow-cyan-500/25 hover:shadow-cyan-500/30"
              >
                Open Dashboard
              </button>
              <button
                onClick={() => onNavigate('docs')}
                className="px-6 py-3.5 rounded-[var(--radius-lg)] bg-[var(--color-surface)] border border-[var(--color-border)] text-[var(--color-text)] font-semibold hover:bg-[var(--color-surface-hover)] hover:border-[var(--color-accent)]/30 transition-all"
              >
                Read Documentation
              </button>
            </div>
            <div className="mt-8 flex items-center justify-center gap-6 text-sm text-[var(--color-text-muted)]">
              <span className="flex items-center gap-2">
                <svg className="w-4 h-4 text-[var(--color-success)]" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" /></svg>
                Free tier available
              </span>
              <span className="flex items-center gap-2">
                <svg className="w-4 h-4 text-[var(--color-success)]" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" /></svg>
                CLI + SaaS
              </span>
              <span className="flex items-center gap-2">
                <svg className="w-4 h-4 text-[var(--color-success)]" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" /></svg>
                CI/CD ready
              </span>
            </div>
          </div>
        </div>
      </section>

      {/* Problem */}
      <section className="border-t border-[var(--color-border)]">
        <div className="max-w-5xl mx-auto px-6 py-20">
          <h2 className="text-2xl md:text-3xl font-semibold text-[var(--color-text)] text-center mb-4">
            "It works on my machine"
          </h2>
          <p className="text-[var(--color-text-secondary)] text-center max-w-2xl mx-auto text-lg">
            Dev and prod drift apart over time. Different dependency versions, missing env vars, schema changes—small differences that cause big outages. ParityCheck surfaces them before they do.
          </p>
        </div>
      </section>

      {/* How it works */}
      <section className="border-t border-[var(--color-border)] bg-[var(--color-bg-elevated)]">
        <div className="max-w-5xl mx-auto px-6 py-20">
          <h2 className="text-2xl md:text-3xl font-semibold text-[var(--color-text)] text-center mb-4">
            How it works
          </h2>
          <p className="text-[var(--color-text-secondary)] text-center max-w-xl mx-auto mb-16">
            Three steps to environment parity visibility
          </p>
          <div className="grid md:grid-cols-3 gap-8">
            {[
              { step: '1', title: 'Collect', desc: 'Run envguard in each environment. It gathers OS, runtime, deps, env vars, and DB schema hash.', icon: '📦' },
              { step: '2', title: 'Compare', desc: 'Compare locally or push to the SaaS. See added, removed, and changed keys at a glance.', icon: '⚖️' },
              { step: '3', title: 'Alert', desc: 'Get notified when drift is detected. Slack, email, or webhook—before it hits production.', icon: '🔔' },
            ].map((item) => (
              <div key={item.step} className="relative p-6 rounded-[var(--radius-xl)] bg-[var(--color-surface)] border border-[var(--color-border)]">
                <div className="w-12 h-12 rounded-[var(--radius-lg)] bg-[var(--color-accent)]/10 flex items-center justify-center text-2xl mb-4">
                  {item.icon}
                </div>
                <span className="text-xs font-semibold text-[var(--color-accent)] uppercase tracking-wider">Step {item.step}</span>
                <h3 className="text-lg font-semibold text-[var(--color-text)] mt-2">{item.title}</h3>
                <p className="text-[var(--color-text-secondary)] mt-2 text-sm leading-relaxed">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="border-t border-[var(--color-border)]">
        <div className="max-w-5xl mx-auto px-6 py-20">
          <h2 className="text-2xl md:text-3xl font-semibold text-[var(--color-text)] text-center mb-4">
            Built for developers
          </h2>
          <p className="text-[var(--color-text-secondary)] text-center max-w-xl mx-auto mb-16">
            Everything you need to keep environments in sync
          </p>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {[
              { title: 'CLI-first', desc: 'envguard runs anywhere—local, CI, containers. One command to collect, compare, and report.', icon: 'Terminal' },
              { title: 'Dependency tracking', desc: 'See exactly which packages differ across environments. Version mismatches surfaced instantly.', icon: 'Package' },
              { title: 'Env var diff', desc: 'Config drift is invisible until it breaks. We show added, removed, and changed variables.', icon: 'Settings' },
              { title: 'DB schema hash', desc: 'Track schema changes with a hash. Know when migrations diverge between envs.', icon: 'Database' },
              { title: 'SaaS dashboard', desc: 'Visual parity reports, historical trends, and team collaboration in one place.', icon: 'Layout' },
              { title: 'CI/CD integration', desc: 'GitHub Actions, GitLab CI, cron—run envguard on a schedule and get alerts.', icon: 'Zap' },
            ].map((f) => (
              <div key={f.title} className="p-6 rounded-[var(--radius-xl)] bg-[var(--color-surface)] border border-[var(--color-border)] hover:border-[var(--color-accent)]/30 transition-colors">
                <div className="w-10 h-10 rounded-[var(--radius-md)] bg-[var(--color-accent)]/10 flex items-center justify-center mb-4">
                  <FeatureIcon name={f.icon} />
                </div>
                <h3 className="font-semibold text-[var(--color-text)]">{f.title}</h3>
                <p className="text-sm text-[var(--color-text-secondary)] mt-2 leading-relaxed">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Quick start */}
      <section className="border-t border-[var(--color-border)] bg-[var(--color-bg-elevated)]">
        <div className="max-w-5xl mx-auto px-6 py-20">
          <h2 className="text-2xl md:text-3xl font-semibold text-[var(--color-text)] text-center mb-4">
            Get started in 60 seconds
          </h2>
          <p className="text-[var(--color-text-secondary)] text-center max-w-xl mx-auto mb-10">
            Install the CLI, collect from your environments, and compare.
          </p>
          <div className="max-w-2xl mx-auto">
            <CodeBlock language="bash">{`# Install
pip install envguard

# Collect from dev (baseline)
envguard collect --env=dev

# Collect from prod
envguard collect --env=prod

# Compare dev vs prod
envguard compare --env=prod --baseline=dev`}</CodeBlock>
            <p className="text-sm text-[var(--color-text-muted)] mt-4 text-center">
              Push reports to the dashboard with <code className="font-mono bg-[var(--color-surface)] px-1.5 py-0.5 rounded">envguard report --api-key=YOUR_KEY</code>
            </p>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="border-t border-[var(--color-border)]">
        <div className="max-w-3xl mx-auto px-6 py-24 text-center">
          <h2 className="text-2xl md:text-3xl font-semibold text-[var(--color-text)] mb-4">
            Ready to eliminate drift?
          </h2>
          <p className="text-[var(--color-text-secondary)] mb-8">
            Sign up for free. No credit card required.
          </p>
          <div className="flex flex-wrap items-center justify-center gap-4">
            <button
              onClick={() => onNavigate('dashboard')}
              className="px-8 py-4 rounded-[var(--radius-lg)] bg-[var(--color-accent)] text-white font-semibold hover:bg-[var(--color-accent-hover)] transition-all shadow-lg shadow-cyan-500/25"
            >
              Get started free
            </button>
            <button
              onClick={() => onNavigate('docs')}
              className="px-8 py-4 rounded-[var(--radius-lg)] border border-[var(--color-border)] text-[var(--color-text)] font-semibold hover:bg-[var(--color-surface)] transition-all"
            >
              View documentation
            </button>
          </div>
        </div>
      </section>
    </>
  )
}

function FeatureIcon({ name }: { name: string }) {
  const className = "w-5 h-5 text-[var(--color-accent)]"
  switch (name) {
    case 'Terminal':
      return <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
    case 'Package':
      return <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" /></svg>
    case 'Settings':
      return <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" /><path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /></svg>
    case 'Database':
      return <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" /></svg>
    case 'Layout':
      return <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 13a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1v-6zM16 13a1 1 0 011-1h2a1 1 0 011 1v6a1 1 0 01-1 1h-2a1 1 0 01-1-1v-6z" /></svg>
    case 'Zap':
      return <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
    default:
      return null
  }
}
