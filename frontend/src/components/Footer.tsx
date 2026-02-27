import { Link } from 'react-router-dom'
import { Logo } from './Logo'

export function Footer() {
  return (
    <footer className="border-t border-[var(--color-border)]/50 bg-[var(--color-bg-elevated)]/50">
      <div className="max-w-7xl mx-auto px-6 py-12">
        <div className="flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-2">
            <Logo size={28} />
            <span className="text-sm font-semibold text-[var(--color-text)]">ParityCheck</span>
            <span className="text-[10px] font-medium text-[var(--color-text-muted)] uppercase tracking-wider">ENVGUARD</span>
          </div>
          <nav className="flex flex-wrap items-center justify-center gap-6 text-sm">
            <Link to="/docs" className="text-[var(--color-text-secondary)] hover:text-[var(--color-accent)] transition-colors">
              Documentation
            </Link>
            <Link to="/dashboard" className="text-[var(--color-text-secondary)] hover:text-[var(--color-accent)] transition-colors">
              Dashboard
            </Link>
            <Link to="/login" className="text-[var(--color-text-secondary)] hover:text-[var(--color-accent)] transition-colors">
              Sign In
            </Link>
            <a
              href="https://github.com"
              target="_blank"
              rel="noopener noreferrer"
              className="text-[var(--color-text-secondary)] hover:text-[var(--color-accent)] transition-colors"
            >
              GitHub
            </a>
          </nav>
        </div>
        <div className="mt-8 pt-8 border-t border-[var(--color-border)]/30 flex flex-col sm:flex-row items-center justify-between gap-4 text-sm text-[var(--color-text-muted)]">
          <p>Environment drift detection for dev, staging, and production.</p>
          <p>© {new Date().getFullYear()} ParityCheck. MIT License.</p>
        </div>
      </div>
    </footer>
  )
}
