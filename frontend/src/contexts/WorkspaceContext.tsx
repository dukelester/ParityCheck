import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from 'react'
import { useAuth } from './AuthContext'
import {
  workspacesApi,
  type Workspace,
  type PlanUsage,
} from '../lib/api'

interface WorkspaceContextValue {
  workspaces: Workspace[]
  currentWorkspace: Workspace | null
  usage: PlanUsage | null
  setCurrentWorkspaceId: (id: string) => void
  refresh: () => Promise<void>
  loading: boolean
}

const WorkspaceContext = createContext<WorkspaceContextValue | null>(null)

const STORAGE_KEY = 'paritycheck_workspace_id'

export function WorkspaceProvider({ children }: { children: React.ReactNode }) {
  const { token } = useAuth()
  const [workspaces, setWorkspaces] = useState<Workspace[]>([])
  const [currentWorkspace, setCurrentWorkspace] = useState<Workspace | null>(null)
  const [usage, setUsage] = useState<PlanUsage | null>(null)
  const [loading, setLoading] = useState(true)

  const refresh = useCallback(async () => {
    if (!token) {
      setWorkspaces([])
      setCurrentWorkspace(null)
      setUsage(null)
      setLoading(false)
      return
    }
    try {
      let list = await workspacesApi.list(token)
      if (list.length === 0) {
        await workspacesApi.getDefault(token)
        list = await workspacesApi.list(token)
      }
      setWorkspaces(list)
      const stored = localStorage.getItem(STORAGE_KEY)
      const defaultWs = list[0]
      const current =
        list.find((w: Workspace) => w.id === stored) || defaultWs || null
      setCurrentWorkspace(current)
      if (current) {
        localStorage.setItem(STORAGE_KEY, current.id)
        const u = await workspacesApi.getUsage(token, current.id)
        setUsage(u)
      } else {
        setUsage(null)
      }
    } catch {
      setWorkspaces([])
      setCurrentWorkspace(null)
      setUsage(null)
    } finally {
      setLoading(false)
    }
  }, [token])

  useEffect(() => {
    refresh()
  }, [refresh])

  const setCurrentWorkspaceId = useCallback(
    (id: string) => {
      const ws = workspaces.find((w) => w.id === id)
      if (ws) {
        setCurrentWorkspace(ws)
        localStorage.setItem(STORAGE_KEY, id)
        if (token) {
          workspacesApi.getUsage(token, id).then(setUsage).catch(() => setUsage(null))
        }
      }
    },
    [workspaces, token]
  )

  return (
    <WorkspaceContext.Provider
      value={{
        workspaces,
        currentWorkspace,
        usage,
        setCurrentWorkspaceId,
        refresh,
        loading,
      }}
    >
      {children}
    </WorkspaceContext.Provider>
  )
}

export function useWorkspace() {
  const ctx = useContext(WorkspaceContext)
  if (!ctx) throw new Error('useWorkspace must be used within WorkspaceProvider')
  return ctx
}
