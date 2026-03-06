import { useEffect, useState } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { useWorkspace } from '../contexts/WorkspaceContext'
import { workspacesApi, type WorkspaceMember } from '../lib/api'

export function WorkspaceTeam() {
  const { token } = useAuth()
  const { currentWorkspace } = useWorkspace()
  const [members, setMembers] = useState<WorkspaceMember[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [inviteEmail, setInviteEmail] = useState('')
  const [inviteRole, setInviteRole] = useState<'member' | 'admin'>('member')
  const [inviting, setInviting] = useState(false)
  const [updatingId, setUpdatingId] = useState<string | null>(null)

  useEffect(() => {
    if (!token || !currentWorkspace) return
    setLoading(true)
    workspacesApi
      .listMembers(token, currentWorkspace.id)
      .then(setMembers)
      .catch((err) => {
        setError(err instanceof Error ? err.message : 'Failed to load members')
        setMembers([])
      })
      .finally(() => setLoading(false))
  }, [token, currentWorkspace?.id])

  async function handleInvite(e: React.FormEvent) {
    e.preventDefault()
    if (!token || !currentWorkspace || !inviteEmail) return
    setInviting(true)
    setError(null)
    try {
      const m = await workspacesApi.inviteMember(token, currentWorkspace.id, inviteEmail, inviteRole)
      setMembers((prev) => [...prev, m])
      setInviteEmail('')
      setInviteRole('member')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to invite member')
    } finally {
      setInviting(false)
    }
  }

  async function handleRoleChange(member: WorkspaceMember, role: 'member' | 'admin') {
    if (!token || !currentWorkspace || member.role === role) return
    setUpdatingId(member.id)
    setError(null)
    try {
      const updated = await workspacesApi.updateMemberRole(token, currentWorkspace.id, member.id, role)
      setMembers((prev) => prev.map((m) => (m.id === updated.id ? updated : m)))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update role')
    } finally {
      setUpdatingId(null)
    }
  }

  async function handleRemove(member: WorkspaceMember) {
    if (!token || !currentWorkspace) return
    setUpdatingId(member.id)
    setError(null)
    try {
      await workspacesApi.removeMember(token, currentWorkspace.id, member.id)
      setMembers((prev) => prev.filter((m) => m.id !== member.id))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to remove member')
    } finally {
      setUpdatingId(null)
    }
  }

  if (!currentWorkspace) {
    return (
      <div className="rounded-[var(--radius-xl)] border border-[var(--color-border)]/50 bg-[var(--color-surface)]/40 p-8 text-center text-[var(--color-text-muted)]">
        Select a workspace to manage team members.
      </div>
    )
  }

  return (
    <div className="space-y-8">
      <div className="rounded-[var(--radius-xl)] border border-[var(--color-border)]/50 bg-[var(--color-surface)]/40 p-6 md:p-8">
        <h2 className="text-lg font-semibold text-[var(--color-text)] mb-2">
          Team members
        </h2>
        <p className="text-sm text-[var(--color-text-secondary)] mb-6">
          Invite teammates to collaborate on <span className="font-semibold">{currentWorkspace.name}</span>. Owners can promote members to admins.
        </p>
        {error && (
          <div className="mb-4 p-3 rounded-[var(--radius-md)] bg-[var(--color-error-muted)] text-[var(--color-error)] text-xs font-medium">
            {error}
          </div>
        )}
        {loading ? (
          <p className="text-sm text-[var(--color-text-muted)]">Loading team…</p>
        ) : members.length === 0 ? (
          <p className="text-sm text-[var(--color-text-muted)]">
            No members yet. Invite your first teammate below.
          </p>
        ) : (
          <div className="overflow-x-auto -mx-2 md:mx-0">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="text-left text-[var(--color-text-muted)] border-b border-[var(--color-border)]/50">
                  <th className="py-2 px-2 font-medium">Name</th>
                  <th className="py-2 px-2 font-medium">Email</th>
                  <th className="py-2 px-2 font-medium">Role</th>
                  <th className="py-2 px-2 font-medium">Joined</th>
                  <th className="py-2 px-2 font-medium text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                {members.map((m) => (
                  <tr key={m.id} className="border-b border-[var(--color-border)]/30 last:border-b-0">
                    <td className="py-2.5 px-2 text-[var(--color-text)]">{m.name}</td>
                    <td className="py-2.5 px-2 text-[var(--color-text-secondary)]">{m.email}</td>
                    <td className="py-2.5 px-2">
                      <span
                        className={`inline-flex items-center gap-1 px-2 py-1 rounded-[var(--radius-md)] text-[10px] font-semibold uppercase tracking-widest ${
                          m.role === 'owner'
                            ? 'bg-[var(--color-accent)]/20 text-[var(--color-accent)]'
                            : m.role === 'admin'
                              ? 'bg-blue-500/15 text-blue-400'
                              : 'bg-[var(--color-surface)]/80 text-[var(--color-text-muted)]'
                        }`}
                      >
                        {m.role}
                      </span>
                    </td>
                    <td className="py-2.5 px-2 text-[var(--color-text-muted)] text-xs">
                      {new Date(m.joined_at).toLocaleDateString()}
                    </td>
                    <td className="py-2.5 px-2 text-right">
                      {m.role !== 'owner' && (
                        <div className="inline-flex items-center gap-2">
                          <select
                            value={m.role === 'owner' ? 'owner' : m.role}
                            disabled={updatingId === m.id}
                            onChange={(e) =>
                              handleRoleChange(m, e.target.value === 'admin' ? 'admin' : 'member')
                            }
                            className="text-xs px-2 py-1 rounded-[var(--radius-md)] bg-[var(--color-bg)] border border-[var(--color-border)]/70 text-[var(--color-text)]"
                          >
                            <option value="member">Member</option>
                            <option value="admin">Admin</option>
                          </select>
                          <button
                            type="button"
                            disabled={updatingId === m.id}
                            onClick={() => handleRemove(m)}
                            className="text-xs text-[var(--color-error)] hover:underline disabled:opacity-50"
                          >
                            Remove
                          </button>
                        </div>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <div className="rounded-[var(--radius-xl)] border border-[var(--color-border)]/50 bg-[var(--color-surface)]/40 p-6 md:p-8">
        <h3 className="text-sm font-semibold text-[var(--color-text)] mb-2">
          Invite a teammate
        </h3>
        <p className="text-xs text-[var(--color-text-secondary)] mb-4">
          Enter the email of an existing ParityCheck user. Owners and admins can manage team members.
        </p>
        <form onSubmit={handleInvite} className="flex flex-col sm:flex-row gap-3">
          <input
            type="email"
            placeholder="teammate@company.com"
            value={inviteEmail}
            onChange={(e) => setInviteEmail(e.target.value)}
            className="flex-1 px-3 py-2.5 rounded-[var(--radius-md)] bg-[var(--color-bg)] border border-[var(--color-border)]/70 text-sm text-[var(--color-text)] outline-none focus:border-[var(--color-accent)] focus:ring-1 focus:ring-[var(--color-accent)]"
          />
          <select
            value={inviteRole}
            onChange={(e) => setInviteRole(e.target.value === 'admin' ? 'admin' : 'member')}
            className="px-3 py-2.5 rounded-[var(--radius-md)] bg-[var(--color-bg)] border border-[var(--color-border)]/70 text-sm text-[var(--color-text)]"
          >
            <option value="member">Member</option>
            <option value="admin">Admin</option>
          </select>
          <button
            type="submit"
            disabled={inviting}
            className="px-5 py-2.5 rounded-[var(--radius-md)] bg-[var(--color-accent)] text-[var(--color-bg)] text-sm font-semibold hover:bg-[var(--color-accent-hover)] disabled:opacity-50 transition-all"
          >
            {inviting ? 'Inviting…' : 'Send invite'}
          </button>
        </form>
      </div>
    </div>
  )
}

