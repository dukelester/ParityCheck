import { useNavigate } from 'react-router-dom'
import type { User } from '../lib/api'

type Section = 'home' | 'dashboard' | 'profile' | 'docs'

interface HeaderProps {
  activeSection?: Section
  onSectionChange?: (section: Section) => void
  user?: User | null
  loading?: boolean
  onLogout?: () => void
}

export function Header({ activeSection = 'home', onSectionChange, user, loading, onLogout }: HeaderProps) {
  const navigate = useNavigate()

  const handleSectionChange = (s: Section) => {
    if (onSectionChange) onSectionChange(s)
    else navigate(s === 'home' ? '/' : `/${s}`)
  }

  return (
    <header className="sticky top-0 z-50 border-b border-[var(--color-border)]/50 bg-[var(--color-bg-elevated)]/80 backdrop-blur-xl">
      <div className="max-w-7xl mx-auto px-6 py-3.5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-10">
            <button
              onClick={() => handleSectionChange('home')}
              className="flex items-center gap-3 group"
            >
              <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-[var(--color-accent)] to-[var(--color-accent-muted)] flex items-center justify-center shadow-[0_0_20px_rgba(0,212,170,0.2)] group-hover:shadow-[0_0_30px_rgba(0,212,170,0.3)] transition-shadow">
                <svg className="w-5 h-5 text-[var(--color-bg)]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div>
                <span className="text-lg font-bold tracking-tight text-[var(--color-text)] group-hover:text-[var(--color-accent)] transition-colors">
                  ParityCheck
                </span>
                <span className="block text-[10px] font-semibold text-[var(--color-text-muted)] uppercase tracking-widest -mt-0.5">
                  ENVGUARD
                </span>
              </div>
            </button>
            <nav className="flex items-center gap-1">
              {[
                { id: 'dashboard' as const, label: 'Dashboard' },
                ...(user ? [{ id: 'profile' as const, label: 'Profile' }] : []),
                { id: 'docs' as const, label: 'Docs' },
              ].map(({ id, label }) => (
                <button
                  key={id}
                  onClick={() => handleSectionChange(id)}
                  className={`px-4 py-2.5 rounded-[var(--radius-md)] text-sm font-medium transition-all ${
                    activeSection === id
                      ? 'bg-[var(--color-surface)] text-[var(--color-accent)]'
                      : 'text-[var(--color-text-secondary)] hover:text-[var(--color-text)] hover:bg-[var(--color-surface)]/50'
                  }`}
                >
                  {label}
                </button>
              ))}
            </nav>
          </div>
          <div className="flex items-center gap-3">
            <a
              href="https://github.com"
              target="_blank"
              rel="noopener noreferrer"
              className="p-2.5 rounded-[var(--radius-md)] text-[var(--color-text-muted)] hover:text-[var(--color-text)] hover:bg-[var(--color-surface)]/50 transition-all"
              aria-label="GitHub"
            >
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path fillRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" clipRule="evenodd" /></svg>
            </a>
            {user ? (
              <div className="flex items-center gap-2">
                <span className="text-sm text-[var(--color-text-secondary)] hidden md:inline truncate max-w-[160px]">{user.email}</span>
                <button
                  onClick={() => handleSectionChange('profile')}
                  className="px-3 py-2 rounded-[var(--radius-md)] text-[var(--color-text-secondary)] text-sm font-medium hover:text-[var(--color-text)] hover:bg-[var(--color-surface)]/50 transition-all hidden sm:block"
                >
                  Account
                </button>
                <button
                  onClick={onLogout}
                  className="px-4 py-2.5 rounded-[var(--radius-md)] border border-[var(--color-border)]/70 text-[var(--color-text)] text-sm font-medium hover:bg-[var(--color-surface)] hover:border-[var(--color-border)] transition-all"
                >
                  Sign out
                </button>
              </div>
            ) : !loading ? (
              <button
                onClick={() => navigate('/login')}
                className="px-5 py-2.5 rounded-[var(--radius-md)] bg-[var(--color-accent)] text-[var(--color-bg)] text-sm font-semibold hover:bg-[var(--color-accent-hover)] transition-all shadow-[0_0_20px_rgba(0,212,170,0.2)] hover:shadow-[0_0_30px_rgba(0,212,170,0.3)]"
              >
                Sign In
              </button>
            ) : null}
          </div>
        </div>
      </div>
    </header>
  )
}
