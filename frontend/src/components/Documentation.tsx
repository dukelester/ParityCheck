import { useRef, useState, useEffect } from 'react'
import { CodeBlock } from './CodeBlock'

const sections = [
  { id: 'overview', title: 'Overview' },
  { id: 'installation', title: 'Installation' },
  { id: 'quick-start', title: 'Quick Start' },
  { id: 'collect', title: 'collect' },
  { id: 'compare', title: 'compare' },
  { id: 'report', title: 'report' },
  { id: 'schedule', title: 'schedule' },
  { id: 'history', title: 'history' },
  { id: 'workflow', title: 'Workflow & CI' },
]

export function Documentation() {
  const [activeSection, setActiveSection] = useState('overview')
  const sectionRefs = useRef<Record<string, HTMLElement | null>>({}) as React.MutableRefObject<Record<string, HTMLElement | null>>

  useEffect(() => {
    const el = sectionRefs.current[activeSection]
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }, [activeSection])

  return (
    <div className="flex gap-12 max-w-7xl mx-auto px-6 py-10">
      {/* Sidebar */}
      <aside className="w-56 shrink-0 hidden lg:block">
        <nav className="sticky top-24 space-y-1">
          {sections.map((s) => (
            <button
              key={s.id}
              onClick={() => setActiveSection(s.id)}
              className={`block w-full text-left px-3 py-2 rounded-[var(--radius-md)] text-sm font-medium transition-colors ${
                activeSection === s.id
                  ? 'bg-[var(--color-surface)] text-[var(--color-accent)]'
                  : 'text-[var(--color-text-secondary)] hover:text-[var(--color-text)] hover:bg-[var(--color-surface)]/50'
              }`}
            >
              {s.title}
            </button>
          ))}
        </nav>
      </aside>

      {/* Content */}
      <article className="flex-1 min-w-0 max-w-3xl">
        <div className="prose prose-invert prose-sm max-w-none">
          {/* Overview */}
          <DocSection id="overview" title="Overview" innerRef={sectionRefs}>
            <p className="text-[var(--color-text-secondary)] leading-relaxed">
              ParityCheck detects environment drift across dev, staging, and production. The <strong className="text-[var(--color-text)]">envguard</strong> CLI collects metadata from your environments and uploads it to the SaaS dashboard for comparison and alerting.
            </p>
            <ul className="mt-4 space-y-2 text-[var(--color-text-secondary)]">
              <li><strong className="text-[var(--color-text)]">OS & runtime</strong> — System info, Python version</li>
              <li><strong className="text-[var(--color-text)]">Dependencies</strong> — pip packages and versions</li>
              <li><strong className="text-[var(--color-text)]">Environment variables</strong> — Config differences (secrets redacted by default)</li>
              <li><strong className="text-[var(--color-text)]">DB schema hash</strong> — Schema drift detection</li>
            </ul>
          </DocSection>

          {/* Installation */}
          <DocSection id="installation" title="Installation" innerRef={sectionRefs}>
            <p className="text-[var(--color-text-secondary)]">Install from PyPI (when published) or from source:</p>
            <CodeBlock language="bash">{`# From PyPI
pip install envguard

# From source (development)
cd cli && pip install -e .`}</CodeBlock>
          </DocSection>

          {/* Quick Start */}
          <DocSection id="quick-start" title="Quick Start" innerRef={sectionRefs}>
            <p className="text-[var(--color-text-secondary)]">Three steps to get started:</p>
            <CodeBlock language="bash">{`# 1. Collect from dev (baseline)
envguard collect --env=dev

# 2. Collect from prod
envguard collect --env=prod

# 3. Compare dev vs prod
envguard compare --env=prod --baseline=dev`}</CodeBlock>
            <p className="text-[var(--color-text-secondary)] mt-4">
              To push reports to the SaaS dashboard, use <code className="font-mono text-xs bg-[var(--color-bg)] px-1.5 py-0.5 rounded">envguard report --api-key=YOUR_KEY</code>.
            </p>
          </DocSection>

          {/* collect */}
          <DocSection id="collect" title="collect" innerRef={sectionRefs}>
            <p className="text-[var(--color-text-secondary)]">
              Gathers OS, runtime, dependencies, env vars, and DB schema hash from the current environment. Results are cached locally for <code className="font-mono text-xs">compare</code> and <code className="font-mono text-xs">report</code>.
            </p>
            <CodeBlock language="bash">{`envguard collect [OPTIONS]

Options:
  --env, -e TEXT     Environment name (dev/staging/prod) [default: dev]
  --output, -o TEXT  Write report to file instead of cache
  --include-secrets  Include secret env vars (default: redacted)`}</CodeBlock>
            <CodeBlock language="bash">{`# Examples
envguard collect --env=dev
envguard collect --env=staging -o report.json
envguard collect --env=prod --include-secrets`}</CodeBlock>
          </DocSection>

          {/* compare */}
          <DocSection id="compare" title="compare" innerRef={sectionRefs}>
            <p className="text-[var(--color-text-secondary)]">
              Compares two locally cached reports. Shows added, removed, and changed keys for dependencies and env vars.
            </p>
            <CodeBlock language="bash">{`envguard compare [OPTIONS]

Options:
  --env, -e TEXT       Environment to compare (e.g. prod)
  --baseline, -b TEXT  Baseline env to compare against [default: dev]`}</CodeBlock>
            <CodeBlock language="bash">{`# Compare prod against dev baseline
envguard compare --env=prod

# Compare staging against prod
envguard compare --env=staging --baseline=prod`}</CodeBlock>
          </DocSection>

          {/* report */}
          <DocSection id="report" title="report" innerRef={sectionRefs}>
            <p className="text-[var(--color-text-secondary)]">
              Uploads the cached report to the ParityCheck SaaS API. Requires an API key from the dashboard.
            </p>
            <CodeBlock language="bash">{`envguard report [OPTIONS]

Options:
  --api-key, -k TEXT  [Required] API key for authentication
  --env, -e TEXT      Environment name [default: dev]
  --api-url, -u TEXT  API base URL [default: https://api.paritycheck.io]
  --file, -f TEXT     Report file (default: use cached)`}</CodeBlock>
            <CodeBlock language="bash">{`# Upload dev report
envguard report --api-key=pc_xxxxx --env=dev

# Upload from custom file
envguard report --api-key=pc_xxxxx -f ./report.json --env=prod

# Use self-hosted API
envguard report --api-key=pc_xxxxx --api-url=https://parity.internal/api`}</CodeBlock>
          </DocSection>

          {/* schedule */}
          <DocSection id="schedule" title="schedule" innerRef={sectionRefs}>
            <p className="text-[var(--color-text-secondary)]">
              Configures scheduled drift checks. For full automation, use a CI cron job or the SaaS dashboard (Pro/Enterprise).
            </p>
            <CodeBlock language="bash">{`envguard schedule [OPTIONS]

Options:
  --interval, -i TEXT  hourly | daily | weekly [default: daily]
  --notify, -n        Enable Slack/email alerts
  --api-key, -k TEXT  API key (required when --notify)`}</CodeBlock>
          </DocSection>

          {/* history */}
          <DocSection id="history" title="history" innerRef={sectionRefs}>
            <p className="text-[var(--color-text-secondary)]">
              Lists locally cached reports in <code className="font-mono text-xs">~/.envguard/</code>.
            </p>
            <CodeBlock language="bash">{`envguard history [OPTIONS]

Options:
  --env, -e TEXT  Filter by environment`}</CodeBlock>
          </DocSection>

          {/* Workflow */}
          <DocSection id="workflow" title="Workflow & CI" innerRef={sectionRefs}>
            <p className="text-[var(--color-text-secondary)]">
              Recommended workflow for CI/CD pipelines:
            </p>
            <CodeBlock language="yaml">{`# .github/workflows/parity-check.yml
name: Parity Check
on:
  schedule:
    - cron: '0 2 * * *'  # 2 AM daily
  workflow_dispatch:
jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install envguard
      - run: envguard collect --env=prod
      - run: envguard report --api-key=\${{ secrets.PARITYCHECK_API_KEY }} --env=prod`}</CodeBlock>
          </DocSection>
        </div>
      </article>
    </div>
  )
}

function DocSection({
  id,
  title,
  children,
  innerRef,
}: {
  id: string
  title: string
  children: React.ReactNode
  innerRef: React.MutableRefObject<Record<string, HTMLElement | null>>
}) {
  return (
    <section
      id={id}
      ref={(el) => { innerRef.current[id] = el }}
      className="scroll-mt-24 mb-16"
    >
      <h2 className="text-2xl font-semibold text-[var(--color-text)] mb-4 pb-2 border-b border-[var(--color-border)]">
        {title}
      </h2>
      <div className="space-y-4">{children}</div>
    </section>
  )
}
