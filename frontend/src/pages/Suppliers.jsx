import { useState, useEffect, useCallback } from 'react'
import toast from 'react-hot-toast'
import Layout from '../components/Layout'
import SupplierModal from '../components/SupplierModal'
import { getSuppliers, deleteSupplier } from '../api/suppliers'

export default function Suppliers() {
  const [suppliers, setSuppliers] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [modalOpen, setModalOpen] = useState(false)
  const [editSupplier, setEditSupplier] = useState(null)

  const fetchSuppliers = useCallback(async () => {
    setLoading(true)
    try {
      const params = {}
      if (search) params.search = search
      const data = await getSuppliers(params)
      setSuppliers(data)
    } catch {
      toast.error('Failed to load suppliers')
    } finally {
      setLoading(false)
    }
  }, [search])

  useEffect(() => {
    const timer = setTimeout(fetchSuppliers, 300)
    return () => clearTimeout(timer)
  }, [fetchSuppliers])

  const handleDelete = async (id, name) => {
    if (!window.confirm(`Delete "${name}"?`)) return
    try {
      await deleteSupplier(id)
      toast.success('Supplier deleted')
      fetchSuppliers()
    } catch {
      toast.error('Failed to delete supplier')
    }
  }

  const openAdd = () => { setEditSupplier(null); setModalOpen(true) }
  const openEdit = (s) => { setEditSupplier(s); setModalOpen(true) }
  const closeModal = (refresh) => {
    setModalOpen(false)
    setEditSupplier(null)
    if (refresh) fetchSuppliers()
  }

  return (
    <Layout>
      <div className="p-6">
        {/* Header */}
        <div className="flex justify-between items-start mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-800">Suppliers</h1>
            <p className="text-sm text-gray-500 mt-1">{suppliers.length} total</p>
          </div>
          <button
            onClick={openAdd}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 transition"
          >
            + Add Supplier
          </button>
        </div>

        {/* Search */}
        <div className="mb-4">
          <input
            type="text"
            placeholder="Search by name or email…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            aria-label="Search suppliers"
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm w-72 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* Table */}
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          {loading ? (
            <div className="p-10 text-center text-gray-400 text-sm">Loading…</div>
          ) : suppliers.length === 0 ? (
            <div className="p-10 text-center text-gray-400 text-sm">No suppliers found.</div>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 border-b border-gray-200 text-gray-500 font-medium">
                  <th className="text-left px-4 py-3">Name</th>
                  <th className="text-left px-4 py-3">Email</th>
                  <th className="text-left px-4 py-3">Categories</th>
                  <th className="text-right px-4 py-3">Lead Time</th>
                  <th className="px-4 py-3" />
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {suppliers.map((s) => (
                  <tr key={s.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 font-medium text-gray-800">{s.name}</td>
                    <td className="px-4 py-3 text-gray-500">{s.email}</td>
                    <td className="px-4 py-3">
                      <div className="flex flex-wrap gap-1">
                        {(s.categories || []).length === 0 ? (
                          <span className="text-gray-400 text-xs">—</span>
                        ) : (
                          (s.categories || []).map((c) => (
                            <span
                              key={c}
                              className="bg-blue-50 text-blue-700 px-2 py-0.5 rounded-full text-xs font-medium"
                            >
                              {c}
                            </span>
                          ))
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-right text-gray-600">
                      {s.lead_time_days} {s.lead_time_days === 1 ? 'day' : 'days'}
                    </td>
                    <td className="px-4 py-3 text-right whitespace-nowrap">
                      <button
                        onClick={() => openEdit(s)}
                        className="text-blue-500 hover:text-blue-700 text-xs font-medium mr-3"
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => handleDelete(s.id, s.name)}
                        className="text-red-400 hover:text-red-600 text-xs font-medium"
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

      {modalOpen && <SupplierModal supplier={editSupplier} onClose={closeModal} />}
    </Layout>
  )
}
