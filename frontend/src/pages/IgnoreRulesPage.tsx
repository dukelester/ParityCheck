import { useEffect, useState } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { useWorkspace } from '../contexts/WorkspaceContext'
import { ignoreRulesApi, type IgnoreRule } from '../lib/api'

const RULE_TYPES = [
  { value: 'env_var', label: 'Environment variable' },
  { value: 'config', label: 'Config / Security' },
  { value: 'secret_drift', label: 'Secret drift' },
  { value: 'dependency', label: 'Dependency' },
  { value: 'runtime', label: 'Runtime' },
]

export function IgnoreRulesPage() {
  const { token } = useAuth()
  const { currentWorkspace } = useWorkspace()
  const [rules, setRules] = useState<IgnoreRule[]>([])
  const [loading, setLoading] = useState(true)
  const [adding, setAdding] = useState(false)
  const [newType, setNewType] = useState('env_var')
  const [newPattern, setNewPattern] = useState('')
  const [error, setError] = useState('')

  const load = () => {
    if (!token || !currentWorkspace) return
    ignoreRulesApi.list(token, currentWorkspace.id)
      .then(setRules)
      .catch(() => setRules([]))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    if (!currentWorkspace) {
      setLoading(false)
      return
    }
    setLoading(true)
    load()
  }, [token, currentWorkspace?.id])

  async function handleAdd(e: React.FormEvent) {
    e.preventDefault()
    if (!token || !currentWorkspace || !newPattern.trim()) return
    setError('')
    setAdding(true)
    try {
      await ignoreRulesApi.create(token, currentWorkspace.id, newType, newPattern.trim())
      setNewPattern('')
      load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to add rule')
    } finally {
      setAdding(false)
    }
  }

  async function handleDelete(id: string) {
    if (!token) return
    try {
      await ignoreRulesApi.delete(token, id)
      load()
    } catch {
      // ignore
    }
  }

  if (!currentWorkspace) {
    return (
      <div className="rounded-[var(--radius-xl)] border border-[var(--color-border)]/50 bg-[var(--color-surface)]/40 p-12 text-center">
        <p className="text-[var(--color-text-muted)]">Select a workspace first</p>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-lg font-semibold text-[var(--color-text)] mb-2">
          Ignore Rules
        </h2>
        <p className="text-sm text-[var(--color-text-muted)]">
          Skip these keys during drift comparison. Use exact match or wildcard (*).
        </p>
      </div>

      <form onSubmit={handleAdd} className="flex flex-wrap gap-4 items-end">
        <div>
          <label className="block text-xs font-semibold text-[var(--color-text-muted)] mb-1.5">Type</label>
          <select
            value={newType}
            onChange={(e) => setNewType(e.target.value)}
            className="px-4 py-2.5 rounded-[var(--radius-md)] bg-[var(--color-bg)] border border-[var(--color-border)]/70 text-[var(--color-text)]"
          >
            {RULE_TYPES.map((t) => (
              <option key={t.value} value={t.value}>{t.label}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-xs font-semibold text-[var(--color-text-muted)] mb-1.5">Key pattern</label>
          <input
            type="text"
            value={newPattern}
            onChange={(e) => setNewPattern(e.target.value)}
            placeholder="e.g. DEBUG or DATABASE_*"
            className="px-4 py-2.5 rounded-[var(--radius-md)] bg-[var(--color-bg)] border border-[var(--color-border)]/70 text-[var(--color-text)] w-48"
          />
        </div>
        <button
          type="submit"
          disabled={adding || !newPattern.trim()}
          className="px-4 py-2.5 rounded-[var(--radius-md)] bg-[var(--color-accent)] text-[var(--color-bg)] font-semibold text-sm disabled:opacity-50"
        >
          {adding ? 'Adding…' : 'Add rule'}
        </button>
      </form>
      {error && (
        <p className="text-sm text-[var(--color-error)]">{error}</p>
      )}

      <div className="rounded-[var(--radius-xl)] border border-[var(--color-border)]/50 bg-[var(--color-surface)]/40 overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-[var(--color-text-muted)]">Loading…</div>
        ) : rules.length === 0 ? (
          <div className="p-12 text-center text-[var(--color-text-muted)]">
            No ignore rules. Add one above to exclude keys from drift detection.
          </div>
        ) : (
          <table className="w-full">
            <thead>
              <tr className="border-b border-[var(--color-border)]/50">
                <th className="text-left px-6 py-4 text-xs font-semibold text-[var(--color-text-muted)] uppercase">Type</th>
                <th className="text-left px-6 py-4 text-xs font-semibold text-[var(--color-text-muted)] uppercase">Pattern</th>
                <th className="w-20" />
              </tr>
            </thead>
            <tbody>
              {rules.map((r) => (
                <tr key={r.id} className="border-b border-[var(--color-border)]/30 last:border-0">
                  <td className="px-6 py-4 text-sm text-[var(--color-text)]">{r.type}</td>
                  <td className="px-6 py-4 font-mono text-sm text-[var(--color-text-secondary)]">{r.key_pattern}</td>
                  <td className="px-6 py-4">
                    <button
                      type="button"
                      onClick={() => handleDelete(r.id)}
                      className="text-[var(--color-error)] hover:underline text-sm"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
