import { useState, useEffect } from 'react'
import { Routes, Route, useNavigate, useSearchParams, useLocation, Outlet } from 'react-router-dom'
import { EnvironmentStatus } from './components/EnvironmentStatus'
import { DriftTable } from './components/DriftTable'
import { ReportHistory } from './components/ReportHistory'
import { Header } from './components/Header'
import { Footer } from './components/Footer'
import { ProfileContent } from './components/ProfileContent'
import { Documentation } from './components/Documentation'
import { Landing } from './components/Landing'
import { LoginPage } from './pages/LoginPage'
import { SignupPage } from './pages/SignupPage'
import { ForgotPasswordPage } from './pages/ForgotPasswordPage'
import { ResetPasswordPage } from './pages/ResetPasswordPage'
import { VerifyEmailPage } from './pages/VerifyEmailPage'
import { AuthCallbackPage } from './pages/AuthCallbackPage'
import { SettingsPage } from './pages/SettingsPage'
import { useAuth } from './contexts/AuthContext'
import { useWorkspace } from './contexts/WorkspaceContext'
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
    if ((location.pathname === '/dashboard' || location.pathname === '/profile' || location.pathname === '/settings') && !user) {
      navigate('/login', { replace: true })
    }
  }, [location.pathname, user, loading, navigate])

  return (
    <Routes>
      <Route path="/auth/callback" element={
        <div className="min-h-screen bg-[var(--color-bg)]">
          <AuthCallbackPage />
        </div>
      } />
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
      <Route path="/reset-password" element={
        token ? (
          <div className="min-h-screen bg-[var(--color-bg)] flex flex-col">
            <Header user={user} loading={loading} onLogout={logout} />
            <div className="flex-1">
              <ResetPasswordPage
                token={token}
                onSuccess={() => navigate('/login')}
              />
            </div>
            <Footer />
          </div>
        ) : (
          <div className="min-h-screen flex items-center justify-center bg-[var(--color-bg)]">
            <p className="text-[var(--color-text-muted)]">Invalid or expired reset link</p>
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
              onSwitchToForgotPassword={() => navigate('/forgot-password')}
            />
          </div>
          <Footer />
        </div>
      } />
      <Route path="/forgot-password" element={
        <div className="min-h-screen bg-[var(--color-bg)] flex flex-col">
          <Header user={user} loading={loading} onLogout={logout} />
          <div className="flex-1">
            <ForgotPasswordPage onSwitchToLogin={() => navigate('/login')} />
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
        <Route path="settings" element={
          user ? <SettingsPage /> : null
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
  const { workspaces, currentWorkspace, usage, setCurrentWorkspaceId, refresh } = useWorkspace()

  return (
    <main className="max-w-7xl mx-auto px-6 py-10 md:py-12">
      <div className="mb-10 flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-[var(--color-text)] tracking-tight">
            Dashboard
          </h1>
          <p className="text-[var(--color-text-secondary)] mt-2">
            Monitor environment parity and drift across dev, staging, and production.
          </p>
        </div>
        <div className="flex items-center gap-4">
          {workspaces.length > 1 && (
            <div>
              <label className="block text-xs font-semibold text-[var(--color-text-muted)] mb-1">Workspace</label>
              <select
                value={currentWorkspace?.id ?? ''}
                onChange={(e) => setCurrentWorkspaceId(e.target.value)}
                className="px-4 py-2.5 rounded-[var(--radius-md)] bg-[var(--color-bg)] border border-[var(--color-border)]/70 text-[var(--color-text)]"
              >
                {workspaces.map((w) => (
                  <option key={w.id} value={w.id}>{w.name}</option>
                ))}
              </select>
            </div>
          )}
          {usage && (
            <div className="text-sm text-[var(--color-text-muted)]">
              <span className="font-semibold text-[var(--color-text)]">{usage.environments.used}/{usage.environments.limit}</span> envs · {usage.plan}
            </div>
          )}
        </div>
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
          <EnvironmentStatus onBaselineSet={refresh} />
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
            Report History
          </h2>
          <ReportHistory />
        </section>
      )}
    </main>
  )
}

export default App
