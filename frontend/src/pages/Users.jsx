import { useState, useEffect, useCallback } from 'react'
import toast from 'react-hot-toast'
import Layout from '../components/Layout'
import { getUsers, updateUser } from '../api/users'
import useAuthStore from '../store/authStore'

function RoleBadge({ role }) {
  const styles =
    role === 'admin'
      ? 'bg-purple-50 text-purple-700'
      : 'bg-gray-100 text-gray-600'
  return (
    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${styles}`}>
      {role}
    </span>
  )
}

function StatusBadge({ active }) {
  return active ? (
    <span className="bg-green-50 text-green-700 px-2 py-0.5 rounded-full text-xs font-medium">
      Active
    </span>
  ) : (
    <span className="bg-red-50 text-red-500 px-2 py-0.5 rounded-full text-xs font-medium">
      Inactive
    </span>
  )
}

export default function Users() {
  const currentUser = useAuthStore((s) => s.user)
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [updating, setUpdating] = useState(null) // user id being updated

  const fetchUsers = useCallback(async (signal) => {
    setLoading(true)
    try {
      const params = {}
      if (search) params.search = search
      const data = await getUsers(params, signal)
      setUsers(data)
    } catch (err) {
      if (err?.name !== 'CanceledError' && err?.name !== 'AbortError')
        toast.error('Failed to load users')
    } finally {
      setLoading(false)
    }
  }, [search])

  useEffect(() => {
    const controller = new AbortController()
    const timer = setTimeout(() => fetchUsers(controller.signal), 300)
    return () => { clearTimeout(timer); controller.abort() }
  }, [fetchUsers])

  const handleRoleToggle = async (user) => {
    if (user.id === currentUser?.id) {
      toast.error("You can't change your own role")
      return
    }
    const newRole = user.role === 'admin' ? 'staff' : 'admin'
    setUpdating(user.id)
    try {
      const updated = await updateUser(user.id, { role: newRole })
      setUsers((prev) => prev.map((u) => (u.id === updated.id ? updated : u)))
      toast.success(`${updated.email} is now ${updated.role}`)
    } catch {
      toast.error('Failed to update role')
    } finally {
      setUpdating(null)
    }
  }

  const handleStatusToggle = async (user) => {
    if (user.id === currentUser?.id) {
      toast.error("You can't deactivate your own account")
      return
    }
    const newStatus = !user.is_active
    setUpdating(user.id)
    try {
      const updated = await updateUser(user.id, { is_active: newStatus })
      setUsers((prev) => prev.map((u) => (u.id === updated.id ? updated : u)))
      toast.success(`${updated.email} ${updated.is_active ? 'activated' : 'deactivated'}`)
    } catch {
      toast.error('Failed to update status')
    } finally {
      setUpdating(null)
    }
  }

  const isSelf = (user) => user.id === currentUser?.id

  return (
    <Layout>
      <div className="p-6">
        {/* Header */}
        <div className="flex justify-between items-start mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-800">Users</h1>
            <p className="text-sm text-gray-500 mt-1">{users.length} total</p>
          </div>
        </div>

        {/* Search */}
        <div className="mb-4">
          <input
            type="text"
            placeholder="Search by email…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            aria-label="Search users"
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm w-72 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* Table */}
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          {loading ? (
            <div className="p-10 text-center text-gray-400 text-sm">Loading…</div>
          ) : users.length === 0 ? (
            <div className="p-10 text-center text-gray-400 text-sm">No users found.</div>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 border-b border-gray-200 text-gray-500 font-medium">
                  <th className="text-left px-4 py-3">Email</th>
                  <th className="text-left px-4 py-3">Role</th>
                  <th className="text-left px-4 py-3">Status</th>
                  <th className="text-left px-4 py-3">Joined</th>
                  <th className="px-4 py-3" />
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {users.map((u) => (
                  <tr key={u.id} className={`hover:bg-gray-50 ${!u.is_active ? 'opacity-60' : ''}`}>
                    <td className="px-4 py-3 font-medium text-gray-800">
                      {u.email}
                      {isSelf(u) && (
                        <span className="ml-2 text-xs text-gray-400 font-normal">(you)</span>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <RoleBadge role={u.role} />
                    </td>
                    <td className="px-4 py-3">
                      <StatusBadge active={u.is_active} />
                    </td>
                    <td className="px-4 py-3 text-gray-500">
                      {new Date(u.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-4 py-3 text-right whitespace-nowrap">
                      {!isSelf(u) && (
                        <>
                          <button
                            onClick={() => handleRoleToggle(u)}
                            disabled={updating === u.id}
                            className="text-blue-500 hover:text-blue-700 text-xs font-medium mr-3 disabled:opacity-40"
                          >
                            Make {u.role === 'admin' ? 'staff' : 'admin'}
                          </button>
                          <button
                            onClick={() => handleStatusToggle(u)}
                            disabled={updating === u.id}
                            className={`text-xs font-medium disabled:opacity-40 ${
                              u.is_active
                                ? 'text-red-400 hover:text-red-600'
                                : 'text-green-500 hover:text-green-700'
                            }`}
                          >
                            {u.is_active ? 'Deactivate' : 'Activate'}
                          </button>
                        </>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </Layout>
  )
}
