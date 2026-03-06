const API_BASE = import.meta.env.VITE_API_URL || '/api/v1'

/** URL to start GitHub OAuth flow. Redirects to backend which redirects to GitHub. */
export const getGitHubAuthUrl = () => `${API_BASE}/auth/github`

export interface User {
  id: string
  email: string
  name: string
  email_verified: boolean
  created_at: string
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

async function request<T>(
  path: string,
  options: RequestInit & { token?: string } = {}
): Promise<T> {
  const { token, ...init } = options
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(init.headers as Record<string, string>),
  }
  if (token) headers['Authorization'] = `Bearer ${token}`

  const res = await fetch(`${API_BASE}${path}`, { ...init, headers })
  const data = await res.json().catch(() => ({}))
  if (!res.ok) throw new Error(data.detail || res.statusText || 'Request failed')
  return data as T
}

export const authApi = {
  register: (email: string, password: string, name: string) =>
    request<User>('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password, name }),
    }),

  login: (email: string, password: string) =>
    request<TokenResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),

  verifyEmail: (token: string) =>
    request<{ message: string }>('/auth/verify-email', {
      method: 'POST',
      body: JSON.stringify({ token }),
    }),

  resendVerification: (email: string) =>
    request<{ message: string }>('/auth/resend-verification', {
      method: 'POST',
      body: JSON.stringify({ email }),
    }),

  forgotPassword: (email: string) =>
    request<{ message: string }>('/auth/forgot-password', {
      method: 'POST',
      body: JSON.stringify({ email }),
    }),

  resetPassword: (token: string, newPassword: string) =>
    request<{ message: string }>('/auth/reset-password', {
      method: 'POST',
      body: JSON.stringify({ token, new_password: newPassword }),
    }),

  refresh: (refreshToken: string) =>
    request<TokenResponse>('/auth/refresh', {
      method: 'POST',
      body: JSON.stringify({ refresh_token: refreshToken }),
    }),

  me: (token: string) =>
    request<User>('/auth/me', { method: 'GET', token }),

  createApiKey: (token: string) =>
    request<{ api_key: string }>('/auth/api-keys', { method: 'POST', token }),

  updateProfile: (token: string, name: string) =>
    request<User>('/auth/me', {
      method: 'PUT',
      token,
      body: JSON.stringify({ name }),
    }),

  changeEmail: (token: string, newEmail: string, currentPassword: string) =>
    request<{ message: string }>('/auth/change-email', {
      method: 'POST',
      token,
      body: JSON.stringify({ new_email: newEmail, current_password: currentPassword }),
    }),

  changePassword: (token: string, currentPassword: string, newPassword: string) =>
    request<{ message: string }>('/auth/change-password', {
      method: 'POST',
      token,
      body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
    }),

  deleteAccount: (token: string, currentPassword: string, confirm: string) =>
    request<{ message: string }>('/auth/me', {
      method: 'DELETE',
      token,
      body: JSON.stringify({ current_password: currentPassword, confirm }),
    }),
}

export interface Environment {
  id: string
  name: string
  type: string
  workspace_id?: string | null
  is_baseline?: boolean
  last_report: string | null
  health_score?: number | null
}

export interface Workspace {
  id: string
  name: string
  plan: string
  role?: string
}

export interface WorkspaceMember {
  id: string
  user_id: string
  email: string
  name: string
  role: string
  joined_at: string
}

export interface Drift {
  id: string
  report_id: string
  env: string
  type: string
  severity: string
  key: string | null
  value_a: string | null
  value_b: string | null
  details?: { category?: string; reason?: string; likely_caused_by?: string }
  created_at: string
  introduced_at?: string
  introduced_by_report_id?: string
}

export interface ReportSummary {
  id: string
  env: string
  timestamp: string
  status: string
  health_score?: number | null
  summary?: {
    os: string | null
    python_version: string | null
    deps_count: number
    env_vars_count: number
    db_schema_hash: string | null
  }
}

export interface DriftDetail {
  id?: string
  type: string
  severity: string
  key: string | null
  value_a: string | null
  value_b: string | null
  details?: { category?: string; reason?: string; likely_caused_by?: string }
  introduced_at?: string
  introduced_by_report_id?: string
}

export interface ReportDetail {
  id: string
  env: string
  timestamp: string
  health_score?: number | null
  os: Record<string, unknown> | null
  python_version: string | null
  deps: Record<string, string> | Record<string, unknown>
  env_vars: Record<string, string>
  db_schema_hash: string | null
  docker?: {
    image_tag?: string | null
    image_digest?: string | null
    base_image?: string | null
    container_os?: { id?: string; name?: string; version_id?: string } | null
  } | null
  k8s?: {
    namespace?: string
    deployments?: Record<string, unknown>
    configmaps?: Record<string, { data_hash?: string; keys?: string[] }>
    secrets?: Record<string, { data_hash?: string; keys?: string[] }>
  } | null
  drifts?: DriftDetail[]
  summary?: { critical: number; high: number; medium: number; low: number }
}

export const environmentsApi = {
  list: (token: string, workspaceId?: string) => {
    const q = workspaceId ? `?workspace_id=${encodeURIComponent(workspaceId)}` : ''
    return request<Environment[]>(`/environments/${q}`, { method: 'GET', token })
  },
  setBaseline: (token: string, envId: string, workspaceId: string) =>
    request<{ message: string }>(
      `/environments/${envId}/set-baseline?workspace_id=${encodeURIComponent(workspaceId)}`,
      { method: 'POST', token }
    ),
}

export interface IgnoreRule {
  id: string
  workspace_id: string
  type: string
  key_pattern: string
}

export interface Alert {
  id: string
  type: string
  min_severity: string
  enabled: boolean
  webhook_configured?: boolean
  email_configured?: boolean
}

export interface PlanUsage {
  plan: string
  environments: { used: number; limit: number }
  slack_alerts: { used: number; allowed: number }
  history_days: number
}

export const workspacesApi = {
  list: (token: string) =>
    request<Workspace[]>('/workspaces/', { method: 'GET', token }),
  getDefault: (token: string) =>
    request<Workspace>('/workspaces/default', { method: 'GET', token }),
  getUsage: (token: string, workspaceId: string) =>
    request<PlanUsage>(`/workspaces/${workspaceId}/usage`, { method: 'GET', token }),
  listMembers: (token: string, workspaceId: string) =>
    request<WorkspaceMember[]>(`/workspaces/${workspaceId}/members`, { method: 'GET', token }),
  inviteMember: (token: string, workspaceId: string, email: string, role: 'member' | 'admin') =>
    request<WorkspaceMember>(`/workspaces/${workspaceId}/members`, {
      method: 'POST',
      token,
      body: JSON.stringify({ email, role }),
    }),
  updateMemberRole: (token: string, workspaceId: string, memberId: string, role: 'member' | 'admin') =>
    request<WorkspaceMember>(`/workspaces/${workspaceId}/members/${memberId}`, {
      method: 'PATCH',
      token,
      body: JSON.stringify({ role }),
    }),
  removeMember: (token: string, workspaceId: string, memberId: string) =>
    request<{ message: string }>(`/workspaces/${workspaceId}/members/${memberId}`, {
      method: 'DELETE',
      token,
    }),
}

export const ignoreRulesApi = {
  list: (token: string, workspaceId: string) =>
    request<IgnoreRule[]>(`/ignore-rules/?workspace_id=${encodeURIComponent(workspaceId)}`, { method: 'GET', token }),
  create: (token: string, workspaceId: string, type: string, keyPattern: string) =>
    request<IgnoreRule>('/ignore-rules/', {
      method: 'POST',
      token,
      body: JSON.stringify({ workspace_id: workspaceId, type, key_pattern: keyPattern }),
    }),
  delete: (token: string, ruleId: string) =>
    request<{ message: string }>(`/ignore-rules/${ruleId}`, { method: 'DELETE', token }),
}

export const alertsApi = {
  list: (token: string, workspaceId: string) =>
    request<Alert[]>(`/alerts/?workspace_id=${encodeURIComponent(workspaceId)}`, { method: 'GET', token }),
  create: (token: string, workspaceId: string, type: 'slack' | 'email', webhookUrl?: string, email?: string, minSeverity?: string) =>
    request<Alert>('/alerts/', {
      method: 'POST',
      token,
      body: JSON.stringify({
        workspace_id: workspaceId,
        type,
        webhook_url: type === 'slack' ? webhookUrl : undefined,
        email: type === 'email' ? email : undefined,
        min_severity: minSeverity || 'medium',
      }),
    }),
  delete: (token: string, alertId: string) =>
    request<{ message: string }>(`/alerts/${alertId}`, { method: 'DELETE', token }),
}

export const driftsApi = {
  list: (token: string, workspaceId?: string, env?: string, severity?: string) => {
    const params = new URLSearchParams()
    if (workspaceId) params.set('workspace_id', workspaceId)
    if (env) params.set('env', env)
    if (severity) params.set('severity', severity)
    const q = params.toString() ? `?${params}` : ''
    return request<Drift[]>(`/drifts/${q}`, { method: 'GET', token })
  },
}

export interface ObservabilityStatus {
  status: 'ok' | 'degraded'
  components: {
    database: { status: 'ok' | 'error'; error?: string | null }
    redis: { status: 'ok' | 'error'; error?: string | null }
  }
  rate_limits: {
    plan: string
    enforced: boolean
    note: string
  }
}

export const observabilityApi = {
  status: (token: string) =>
    request<ObservabilityStatus>('/observability/status', { method: 'GET', token }),
}

export interface AnalyzeResult {
  deployment_risk_score: number
  health_score: number
  risk_level: string
  safe_to_deploy: boolean
  current_env: string
  against: string
  drift_count: number
  summary: { critical: number; high: number; medium: number; low: number }
  risky_changes: Array<{
    severity: string
    type: string
    key: string | null
    value_a: string | null
    value_b: string | null
    category?: string
    reason?: string
  }>
}

export const reportsApi = {
  list: (token: string, workspaceId?: string, env?: string) => {
    const params = new URLSearchParams()
    if (workspaceId) params.set('workspace_id', workspaceId)
    if (env) params.set('env', env)
    const q = params.toString() ? `?${params}` : ''
    return request<ReportSummary[]>(`/reports/${q}`, { method: 'GET', token })
  },
  get: (token: string, id: string) =>
    request<ReportDetail>(`/reports/${id}`, { method: 'GET', token }),
  analyze: (token: string, reportId: string, against: string) =>
    request<AnalyzeResult>('/reports/analyze', {
      method: 'POST',
      token,
      body: JSON.stringify({ report_id: reportId, against }),
    }),
}
