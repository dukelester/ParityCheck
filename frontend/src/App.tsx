import { useState, useEffect } from 'react'
import { Routes, Route, useNavigate, useSearchParams, useLocation, Outlet } from 'react-router-dom'
import { EnvironmentStatus } from './components/EnvironmentStatus'
import { DriftTable } from './components/DriftTable'
import { Header } from './components/Header'
import { Footer } from './components/Footer'
import { ProfileContent } from './components/ProfileContent'
import { Documentation } from './components/Documentation'
import { Landing } from './components/Landing'
import { LoginPage } from './pages/LoginPage'
import { SignupPage } from './pages/SignupPage'
import { VerifyEmailPage } from './pages/VerifyEmailPage'
import { useAuth } from './contexts/AuthContext'
import './index.css'

function App() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const location = useLocation()
  const { user, loading, login, register, logout } = useAuth()
  const [activeTab, setActiveTab] = useState<'overview' | 'drifts' | 'history'>('overview')

  const token = searchParams.get('token')

  useEffect(() => {
    if (loading) return
    if ((location.pathname === '/dashboard' || location.pathname === '/profile') && !user) {
      navigate('/login', { replace: true })
    }
  }, [location.pathname, user, loading, navigate])

  return (
    <Routes>
      <Route path="/verify-email" element={
        token ? (
          <div className="min-h-screen bg-[var(--color-bg)]">
            <VerifyEmailPage
              token={token}
              onVerified={() => navigate('/login')}
            />
          </div>
        ) : (
          <div className="min-h-screen flex items-center justify-center bg-[var(--color-bg)]">
            <p className="text-[var(--color-text-muted)]">Invalid verification link</p>
          </div>
        )
      } />
      <Route path="/login" element={
        <div className="min-h-screen bg-[var(--color-bg)] flex flex-col">
          <Header user={user} loading={loading} onLogout={logout} />
          <div className="flex-1">
            <LoginPage
            onLogin={async (email, password) => {
              await login(email, password)
              navigate('/dashboard')
            }}
            onSwitchToSignup={() => navigate('/signup')}
          />
          </div>
          <Footer />
        </div>
      } />
      <Route path="/signup" element={
        <div className="min-h-screen bg-[var(--color-bg)] flex flex-col">
          <Header user={user} loading={loading} onLogout={logout} />
          <div className="flex-1">
            <SignupPage
            onRegister={register}
            onSwitchToLogin={() => navigate('/login')}
          />
          </div>
          <Footer />
        </div>
      } />
      <Route path="/" element={
        <div className="min-h-screen bg-[var(--color-bg)] flex flex-col">
          <Header user={user} loading={loading} onLogout={logout} />
          <div className="flex-1">
            <Outlet />
          </div>
          <Footer />
        </div>
      }>
        <Route index element={<Landing />} />
        <Route path="dashboard" element={
          user ? <DashboardContent activeTab={activeTab} setActiveTab={setActiveTab} /> : null
        } />
        <Route path="profile" element={
          user ? <ProfileContent user={user} /> : null
        } />
        <Route path="docs" element={<Documentation />} />
      </Route>
    </Routes>
  )
}

function DashboardContent({
  activeTab,
  setActiveTab,
}: {
  activeTab: 'overview' | 'drifts' | 'history'
  setActiveTab: (t: 'overview' | 'drifts' | 'history') => void
}) {
  return (
    <main className="max-w-7xl mx-auto px-6 py-10 md:py-12">
      <div className="mb-10">
        <h1 className="text-2xl md:text-3xl font-bold text-[var(--color-text)] tracking-tight">
          Dashboard
        </h1>
        <p className="text-[var(--color-text-secondary)] mt-2">
          Monitor environment parity and drift across dev, staging, and production.
        </p>
      </div>

      <nav className="flex gap-1 mb-12 p-1.5 rounded-[var(--radius-lg)] bg-[var(--color-surface)]/40 w-fit border border-[var(--color-border)]/50">
        {(['overview', 'drifts', 'history'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-6 py-3 rounded-[var(--radius-md)] text-sm font-semibold transition-all ${
              activeTab === tab
                ? 'bg-[var(--color-accent)] text-[var(--color-bg)] shadow-[0_0_20px_rgba(0,212,170,0.25)]'
                : 'text-[var(--color-text-secondary)] hover:text-[var(--color-text)] hover:bg-[var(--color-surface)]/50'
            }`}
          >
            {tab.charAt(0).toUpperCase() + tab.slice(1)}
          </button>
        ))}
      </nav>

      {activeTab === 'overview' && (
        <section>
          <h2 className="text-lg font-semibold text-[var(--color-text)] mb-6">
            Environment Parity Status
          </h2>
          <EnvironmentStatus />
        </section>
      )}

      {activeTab === 'drifts' && (
        <section>
          <h2 className="text-lg font-semibold text-[var(--color-text)] mb-6">
            Drift Detection
          </h2>
          <DriftTable />
        </section>
      )}

      {activeTab === 'history' && (
        <section>
          <h2 className="text-lg font-semibold text-[var(--color-text)] mb-6">
            Historical Changes
          </h2>
          <div className="rounded-[var(--radius-xl)] border border-[var(--color-border)]/50 bg-[var(--color-surface)]/40 p-16 text-center">
            <div className="max-w-md mx-auto">
              <div className="w-16 h-16 rounded-2xl bg-[var(--color-surface)]/80 flex items-center justify-center mx-auto mb-5">
                <svg className="w-8 h-8 text-[var(--color-text-muted)]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <p className="font-semibold text-[var(--color-text)]">Report history</p>
              <p className="text-sm text-[var(--color-text-muted)] mt-2 leading-relaxed">
                Connect your CLI and push reports to view historical changes and trends over time.
              </p>
              <code className="mt-5 inline-block text-xs font-mono bg-[var(--color-bg)] px-4 py-2.5 rounded-[var(--radius-md)] text-[var(--color-accent)]">
                envguard report --api-key=YOUR_KEY
              </code>
            </div>
          </div>
        </section>
      )}
    </main>
  )
}

export default App
