import { CodeBlock } from './CodeBlock'

interface LandingProps {
  onNavigate: (section: 'dashboard' | 'docs') => void
}

export function Landing({ onNavigate }: LandingProps) {
  return (
    <>
      {/* Hero */}
      <section className="relative overflow-hidden min-h-[90vh] flex items-center">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_80%_50%_at_50%_-20%,rgba(0,212,170,0.15),transparent)]" />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_60%_40%_at_80%_50%,rgba(0,212,170,0.06),transparent)]" />
        <div className="absolute inset-0 bg-[linear-gradient(to_bottom,transparent_0%,var(--color-bg)_70%)]" />
        <div className="relative max-w-6xl mx-auto px-6 py-24 md:py-32">
          <div className="text-center">
            <div
              className="inline-flex items-center gap-2.5 px-5 py-2.5 rounded-full bg-[var(--color-surface)]/80 border border-[var(--color-border)]/50 backdrop-blur-sm mb-10 animate-fade-in"
              style={{ animationDelay: '0.1s', animationFillMode: 'both' }}
            >
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[var(--color-accent)] opacity-75" />
                <span className="relative inline-flex rounded-full h-2 w-2 bg-[var(--color-accent)]" />
              </span>
              <span className="text-sm font-medium text-[var(--color-text-secondary)]">Environment drift detection for modern teams</span>
            </div>
            <h1
              className="text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-bold text-[var(--color-text)] tracking-tight leading-[1.05] animate-fade-in-up"
              style={{ animationDelay: '0.2s', animationFillMode: 'both' }}
            >
              Ship with confidence.
              <br />
              <span
                className="bg-[linear-gradient(135deg,var(--color-accent)_0%,var(--color-accent-hover)_50%,var(--color-accent)_100%)] bg-[length:200%_auto] bg-clip-text text-transparent animate-gradient-text"
              >
                Know when environments drift.
              </span>
            </h1>
            <p
              className="mt-8 text-lg md:text-xl text-[var(--color-text-secondary)] max-w-2xl mx-auto leading-relaxed animate-fade-in-up"
              style={{ animationDelay: '0.3s', animationFillMode: 'both' }}
            >
              ParityCheck detects differences across dev, staging, and production—dependencies, env vars, and schema. Get alerts before drift becomes a problem.
            </p>
            <div
              className="mt-12 flex flex-wrap items-center justify-center gap-4 animate-fade-in-up"
              style={{ animationDelay: '0.4s', animationFillMode: 'both' }}
            >
              <button
                onClick={() => onNavigate('dashboard')}
                className="group px-8 py-4 rounded-[var(--radius-lg)] bg-[var(--color-accent)] text-[var(--color-bg)] font-semibold hover:bg-[var(--color-accent-hover)] transition-all duration-300 shadow-[0_0_30px_rgba(0,212,170,0.3)] hover:shadow-[0_0_40px_rgba(0,212,170,0.4)] hover:scale-[1.02] active:scale-[0.98]"
              >
                Open Dashboard
              </button>
              <button
                onClick={() => onNavigate('docs')}
                className="px-8 py-4 rounded-[var(--radius-lg)] bg-[var(--color-surface)]/60 border border-[var(--color-border)] text-[var(--color-text)] font-semibold hover:bg-[var(--color-surface)] hover:border-[var(--color-accent)]/40 transition-all duration-300 hover:scale-[1.02] active:scale-[0.98]"
              >
                Read Documentation
              </button>
            </div>
            <div
              className="mt-10 flex items-center justify-center gap-8 text-sm text-[var(--color-text-muted)] animate-fade-in"
              style={{ animationDelay: '0.5s', animationFillMode: 'both' }}
            >
              {['Free tier', 'CLI + SaaS', 'CI/CD ready'].map((item) => (
                <span key={item} className="flex items-center gap-2">
                  <svg className="w-4 h-4 text-[var(--color-accent)] shrink-0" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  {item}
                </span>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Problem */}
      <section className="border-t border-[var(--color-border)]/50">
        <div className="max-w-4xl mx-auto px-6 py-24 md:py-32">
          <h2 className="text-3xl md:text-4xl font-bold text-[var(--color-text)] text-center mb-6">
            "It works on my machine"
          </h2>
          <p className="text-[var(--color-text-secondary)] text-center max-w-2xl mx-auto text-lg md:text-xl leading-relaxed">
            Dev and prod drift apart over time. Different dependency versions, missing env vars, schema changes—small differences that cause big outages. ParityCheck surfaces them before they do.
          </p>
        </div>
      </section>

      {/* How it works */}
      <section className="border-t border-[var(--color-border)]/50 bg-[var(--color-bg-elevated)]">
        <div className="max-w-6xl mx-auto px-6 py-24 md:py-32">
          <h2 className="text-3xl md:text-4xl font-bold text-[var(--color-text)] text-center mb-4">
            How it works
          </h2>
          <p className="text-[var(--color-text-secondary)] text-center max-w-xl mx-auto mb-20 text-lg">
            Three steps to environment parity visibility
          </p>
          <div className="grid md:grid-cols-3 gap-8">
            {[
              { step: '1', title: 'Collect', desc: 'Run envguard in each environment. It gathers OS, runtime, deps, env vars, and DB schema hash.', icon: 'CollectIcon' },
              { step: '2', title: 'Compare', desc: 'Compare locally or push to the SaaS. See added, removed, and changed keys at a glance.', icon: 'CompareIcon' },
              { step: '3', title: 'Alert', desc: 'Get notified when drift is detected. Slack, email, or webhook—before it hits production.', icon: 'AlertIcon' },
            ].map((item, i) => (
              <div
                key={item.step}
                className="group relative p-8 rounded-[var(--radius-2xl)] bg-[var(--color-surface)]/50 border border-[var(--color-border)]/50 hover:border-[var(--color-accent)]/30 hover:bg-[var(--color-surface)]/80 transition-all duration-300 hover:shadow-[0_0_40px_rgba(0,212,170,0.08)]"
                style={{ animationDelay: `${0.1 * i}s` }}
              >
                <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-[var(--color-accent)]/20 to-[var(--color-accent)]/5 flex items-center justify-center mb-6 group-hover:from-[var(--color-accent)]/30 group-hover:to-[var(--color-accent)]/10 transition-colors">
                  {item.icon === 'CollectIcon' && <CollectIcon />}
                  {item.icon === 'CompareIcon' && <CompareIcon />}
                  {item.icon === 'AlertIcon' && <AlertIcon />}
                </div>
                <span className="text-xs font-semibold text-[var(--color-accent)] uppercase tracking-widest">Step {item.step}</span>
                <h3 className="text-xl font-semibold text-[var(--color-text)] mt-3">{item.title}</h3>
                <p className="text-[var(--color-text-secondary)] mt-3 leading-relaxed">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="border-t border-[var(--color-border)]/50">
        <div className="max-w-6xl mx-auto px-6 py-24 md:py-32">
          <h2 className="text-3xl md:text-4xl font-bold text-[var(--color-text)] text-center mb-4">
            Built for developers
          </h2>
          <p className="text-[var(--color-text-secondary)] text-center max-w-xl mx-auto mb-20 text-lg">
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
              <div
                key={f.title}
                className="group p-6 rounded-[var(--radius-xl)] bg-[var(--color-surface)]/40 border border-[var(--color-border)]/50 hover:border-[var(--color-accent)]/25 hover:bg-[var(--color-surface)]/60 transition-all duration-300"
              >
                <div className="w-12 h-12 rounded-xl bg-[var(--color-accent)]/10 flex items-center justify-center mb-5 group-hover:bg-[var(--color-accent)]/20 transition-colors">
                  <FeatureIcon name={f.icon} />
                </div>
                <h3 className="text-lg font-semibold text-[var(--color-text)]">{f.title}</h3>
                <p className="text-[var(--color-text-secondary)] mt-2 leading-relaxed">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Quick start */}
      <section className="border-t border-[var(--color-border)]/50 bg-[var(--color-bg-elevated)]">
        <div className="max-w-3xl mx-auto px-6 py-24 md:py-32">
          <h2 className="text-3xl md:text-4xl font-bold text-[var(--color-text)] text-center mb-4">
            Get started in 60 seconds
          </h2>
          <p className="text-[var(--color-text-secondary)] text-center max-w-xl mx-auto mb-12 text-lg">
            Install the CLI, collect from your environments, and compare.
          </p>
          <div className="rounded-[var(--radius-xl)] overflow-hidden border border-[var(--color-border)]/50">
            <CodeBlock language="bash">{`# Install
pip install envguard

# Collect from dev (baseline)
envguard collect --env=dev

# Collect from prod
envguard collect --env=prod

# Compare dev vs prod
envguard compare --env=prod --baseline=dev`}</CodeBlock>
          </div>
          <p className="text-sm text-[var(--color-text-muted)] mt-6 text-center">
            Push reports to the dashboard with <code className="font-mono bg-[var(--color-surface)] px-2 py-1 rounded-[var(--radius-sm)] text-[var(--color-accent)]">envguard report --api-key=YOUR_KEY</code>
          </p>
        </div>
      </section>

      {/* CTA */}
      <section className="border-t border-[var(--color-border)]/50">
        <div className="max-w-3xl mx-auto px-6 py-28 md:py-36 text-center">
          <h2 className="text-3xl md:text-4xl font-bold text-[var(--color-text)] mb-4">
            Ready to eliminate drift?
          </h2>
          <p className="text-[var(--color-text-secondary)] mb-10 text-lg">
            Sign up for free. No credit card required.
          </p>
          <div className="flex flex-wrap items-center justify-center gap-4">
            <button
              onClick={() => onNavigate('dashboard')}
              className="px-10 py-4 rounded-[var(--radius-lg)] bg-[var(--color-accent)] text-[var(--color-bg)] font-semibold hover:bg-[var(--color-accent-hover)] transition-all shadow-[0_0_30px_rgba(0,212,170,0.25)] hover:shadow-[0_0_50px_rgba(0,212,170,0.35)] hover:scale-[1.02] active:scale-[0.98]"
            >
              Get started free
            </button>
            <button
              onClick={() => onNavigate('docs')}
              className="px-10 py-4 rounded-[var(--radius-lg)] border border-[var(--color-border)] text-[var(--color-text)] font-semibold hover:bg-[var(--color-surface)] hover:border-[var(--color-accent)]/40 transition-all hover:scale-[1.02] active:scale-[0.98]"
            >
              View documentation
            </button>
          </div>
        </div>
      </section>
    </>
  )
}

function CollectIcon() {
  return (
    <svg className="w-7 h-7 text-[var(--color-accent)]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
    </svg>
  )
}
function CompareIcon() {
  return (
    <svg className="w-7 h-7 text-[var(--color-accent)]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M3 6l3 1m0 0l-3 9a5.002 5.002 0 006.001 0M6 7l3 9M6 7l6-2m6 2l3-1m-3 1l-3 9a5.002 5.002 0 006.001 0M18 7l3 9m-3-9l-6-2m0-2v2m0 16V5m0 16H9m3 0h3" />
    </svg>
  )
}
function AlertIcon() {
  return (
    <svg className="w-7 h-7 text-[var(--color-accent)]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
    </svg>
  )
}

function FeatureIcon({ name }: { name: string }) {
  const className = "w-6 h-6 text-[var(--color-accent)]"
  switch (name) {
    case 'Terminal':
      return <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
    case 'Package':
      return <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" /></svg>
    case 'Settings':
      return <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" /><path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /></svg>
    case 'Database':
      return <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" /></svg>
    case 'Layout':
      return <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 13a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1v-6zM16 13a1 1 0 011-1h2a1 1 0 011 1v6a1 1 0 01-1 1h-2a1 1 0 01-1-1v-6z" /></svg>
    case 'Zap':
      return <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
    default:
      return null
  }
}
