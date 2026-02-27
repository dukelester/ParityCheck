import { useRef, useState, useEffect } from 'react'
import { CodeBlock } from './CodeBlock'

const sections = [
  { id: 'overview', title: 'Overview' },
  { id: 'drift-timeline', title: 'Drift Timeline & Root Cause' },
  { id: 'installation', title: 'Installation' },
  { id: 'quick-start', title: 'Quick Start' },
  { id: 'collect', title: 'collect' },
  { id: 'compare', title: 'compare' },
  { id: 'analyze', title: 'analyze' },
  { id: 'check', title: 'check' },
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
    <div className="flex gap-16 max-w-7xl mx-auto px-6 py-12 md:py-16">
      {/* Sidebar */}
      <aside className="w-56 shrink-0 hidden lg:block">
        <nav className="sticky top-28 space-y-1">
          {sections.map((s) => (
            <button
              key={s.id}
              onClick={() => setActiveSection(s.id)}
              className={`block w-full text-left px-4 py-2.5 rounded-[var(--radius-md)] text-sm font-medium transition-all ${
                activeSection === s.id
                  ? 'bg-[var(--color-surface)]/80 text-[var(--color-accent)]'
                  : 'text-[var(--color-text-secondary)] hover:text-[var(--color-text)] hover:bg-[var(--color-surface)]/40'
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
              ParityCheck is a <strong className="text-[var(--color-text)]">Deployment Safety Engine</strong> that detects environment drift across dev, staging, and production. The <strong className="text-[var(--color-text)]">envguard</strong> CLI collects metadata, analyzes deployment risk before you deploy, and uploads reports to the SaaS dashboard for comparison and alerting.
            </p>
            <ul className="mt-4 space-y-2 text-[var(--color-text-secondary)]">
              <li><strong className="text-[var(--color-text)]">OS & runtime</strong> — System info, Python version</li>
              <li><strong className="text-[var(--color-text)]">Dependencies</strong> — pip packages and versions</li>
              <li><strong className="text-[var(--color-text)]">Environment variables</strong> — Config differences (secrets redacted by default)</li>
              <li><strong className="text-[var(--color-text)]">DB schema hash</strong> — Schema drift detection</li>
              <li><strong className="text-[var(--color-text)]">Docker</strong> — Image tag, digest, base image, container OS (with <code className="font-mono text-xs bg-[var(--color-bg)] px-1.5 py-0.5 rounded">--docker</code>)</li>
              <li><strong className="text-[var(--color-text)]">Kubernetes</strong> — ConfigMaps, Secrets, Deployments (image, replicas, resources, env vars) with <code className="font-mono text-xs bg-[var(--color-bg)] px-1.5 py-0.5 rounded">--k8s</code></li>
              <li><strong className="text-[var(--color-text)]">Security</strong> — Secret drift (value changed), weak config, DEBUG in prod, AWS S3 audit advisory</li>
            </ul>
          </DocSection>

          {/* Drift Timeline */}
          <DocSection id="drift-timeline" title="Drift Timeline & Root Cause" innerRef={sectionRefs}>
            <p className="text-[var(--color-text-secondary)]">
              When drift appears, the dashboard shows <strong className="text-[var(--color-text)]">when it started</strong>, <strong className="text-[var(--color-text)]">which report introduced it</strong>, and for transitive dependency changes, <strong className="text-[var(--color-text)]">which direct dependency caused it</strong>.
            </p>
            <ul className="mt-4 space-y-2 text-[var(--color-text-secondary)]">
              <li><strong className="text-[var(--color-text)]">When it started</strong> — Timestamp of the report that first showed the drift</li>
              <li><strong className="text-[var(--color-text)]">Which report introduced it</strong> — Link to the report (deploy) that triggered the drift</li>
              <li><strong className="text-[var(--color-text)]">Which dependency caused transitive change</strong> — For transitive drifts, the direct dependency that pulled in the change (requires <code className="font-mono text-xs bg-[var(--color-bg)] px-1.5 py-0.5 rounded">pip install pipdeptree</code>)</li>
              <li><strong className="text-[var(--color-text)]">Which deploy likely triggered it</strong> — Same as report timestamp; the deploy that introduced the drift</li>
            </ul>
            <p className="text-[var(--color-text-secondary)] mt-4">
              Install <code className="font-mono text-xs">pip install envguard[root-cause]</code> or <code className="font-mono text-xs">pip install pipdeptree</code> for transitive root cause attribution.
            </p>
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
            <p className="text-[var(--color-text-secondary)]">Get started in a few steps:</p>
            <CodeBlock language="bash">{`# 1. Collect from dev (baseline)
envguard collect --env=dev

# 2. Collect from prod (add --docker if running in a container)
envguard collect --env=prod --docker

# 3. Compare dev vs prod
envguard compare --env=prod --baseline=dev

# 4. Deployment risk: compare PR branch vs prod
envguard collect --env=pr-branch
envguard analyze --against=prod --env=pr-branch --api-key=YOUR_KEY`}</CodeBlock>
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
  --include-secrets  Include secret env vars (default: redacted)
  --docker, -d       Collect Docker metadata (image tag, digest, base, OS)
  --container, -c    Container name/ID when running on host (use with --docker)
  --k8s, -k          Collect Kubernetes metadata (deployments, configmaps, secrets)
  --namespace, -n    K8s namespace [default: default]
  --deployment       Specific deployment name (default: all in namespace)`}</CodeBlock>
            <CodeBlock language="bash">{`# Examples
envguard collect --env=dev
envguard collect --env=staging -o report.json
envguard collect --env=prod --include-secrets

# Inside a container: collect Docker image info for drift detection
envguard collect --env=prod --docker

# On host: inspect a specific container
envguard collect --env=prod --docker --container=my-app

# Kubernetes: ConfigMaps, Secrets, Deployments (image, replicas, resources)
envguard collect --env=prod --k8s --namespace=prod
envguard collect --env=staging --k8s -n staging --deployment=my-app`}</CodeBlock>
            <p className="text-[var(--color-text-secondary)] mt-4">
              <strong className="text-[var(--color-text)]">Docker drift</strong> — Base image changes (Alpine → Debian), Python minor version in container, and image digest drift are high-value production risks. Use <code className="font-mono text-xs bg-[var(--color-bg)] px-1.5 py-0.5 rounded">--docker</code> to detect them.
            </p>
            <p className="text-[var(--color-text-secondary)] mt-2">
              <strong className="text-[var(--color-text)]">Kubernetes drift</strong> — ConfigMap mismatch, Secret mismatch, replica count, resource limits, and deployment env vars. Use <code className="font-mono text-xs bg-[var(--color-bg)] px-1.5 py-0.5 rounded">--k8s --namespace=prod</code> to detect them. Requires <code className="font-mono text-xs">kubectl</code> and cluster access.
            </p>
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

          {/* analyze */}
          <DocSection id="analyze" title="analyze" innerRef={sectionRefs}>
            <p className="text-[var(--color-text-secondary)]">
              <strong className="text-[var(--color-text)]">Deployment risk analysis.</strong> Compares your current environment (e.g. PR branch) against a target (e.g. prod) and outputs a deployment risk score. Use before merging or deploying to predict drift impact.
            </p>
            <CodeBlock language="bash">{`envguard analyze [OPTIONS]

Options:
  --against, -a TEXT    Environment to compare against [default: prod]
  --env, -e TEXT       Current env / branch (report from collect) [default: dev]
  --api-key, -k TEXT   [Required] API key for auth
  --file, -F TEXT      Report file (default: use cached for --env)
  --output, -o TEXT   Output format: text | json [default: text]
  --fail-on-risk, -f   Exit 1 if risk score >= threshold
  --risk-threshold, -t INT  Risk threshold for -f (0-100) [default: 50]`}</CodeBlock>
            <CodeBlock language="bash">{`# Analyze PR branch vs prod
envguard collect --env=pr-feature-xyz
envguard analyze --against=prod --env=pr-feature-xyz --api-key=pc_xxxxx

# JSON output for CI
envguard analyze --against=prod --api-key=pc_xxxxx -o json

# Fail CI if risk >= 30
envguard analyze --against=prod --api-key=pc_xxxxx -f --risk-threshold=30`}</CodeBlock>
          </DocSection>

          {/* check */}
          <DocSection id="check" title="check" innerRef={sectionRefs}>
            <p className="text-[var(--color-text-secondary)]">
              Compares current env with the workspace baseline from the API. Use <code className="font-mono text-xs">--fail-on-drift</code> for CI/CD to exit 1 when drift is detected.
            </p>
            <CodeBlock language="bash">{`envguard check [OPTIONS]

Options:
  --api-key, -k TEXT   [Required] API key
  --env, -e TEXT       Environment to check [default: dev]
  --fail-on-drift, -f  Exit 1 if drift severity >= min-severity
  --min-severity, -m TEXT  critical | high | medium | low [default: high]
  --file, -F TEXT      Report file (default: use cached)`}</CodeBlock>
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
              Recommended workflows for CI/CD:
            </p>
            <p className="text-[var(--color-text)] font-medium mt-6">Deployment risk (before merge/deploy)</p>
            <CodeBlock language="yaml">{`# Run before merging PR
- run: envguard collect --env=pr-branch
- run: envguard analyze --against=prod --env=pr-branch --api-key=\${{ secrets.PARITYCHECK_API_KEY }} -f --risk-threshold=50`}</CodeBlock>
            <p className="text-[var(--color-text)] font-medium mt-6">Scheduled drift monitoring</p>
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
      - run: envguard collect --env=prod --docker  # add --docker for container drift
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
      className="scroll-mt-28 mb-20"
    >
      <h2 className="text-2xl md:text-3xl font-bold text-[var(--color-text)] mb-6 pb-3 border-b border-[var(--color-border)]/50">
        {title}
      </h2>
      <div className="space-y-4">{children}</div>
    </section>
  )
}
