import { useState, useEffect, useCallback } from 'react'
import toast from 'react-hot-toast'
import Layout from '../components/Layout'
import POModal from '../components/POModal'
import { getPurchaseOrders, advanceStatus, deletePurchaseOrder } from '../api/purchaseOrders'

const STATUS_STYLES = {
  Draft:        'bg-gray-100 text-gray-600',
  Sent:         'bg-blue-50 text-blue-700',
  Acknowledged: 'bg-purple-50 text-purple-700',
  Received:     'bg-green-50 text-green-700',
}

const NEXT_STATUS = {
  Draft:        'Sent',
  Sent:         'Acknowledged',
  Acknowledged: 'Received',
}

const ALL_STATUSES = ['Draft', 'Sent', 'Acknowledged', 'Received']

export default function PurchaseOrders() {
  const [orders, setOrders] = useState([])
  const [loading, setLoading] = useState(true)
  const [statusFilter, setStatusFilter] = useState('')
  const [advancing, setAdvancing] = useState(null)
  // undefined = modal closed, null = new PO, object = edit PO
  const [modalPO, setModalPO] = useState(undefined)

  const fetchOrders = useCallback(async () => {
    setLoading(true)
    try {
      const params = {}
      if (statusFilter) params.status = statusFilter
      setOrders(await getPurchaseOrders(params))
    } catch {
      toast.error('Failed to load purchase orders')
    } finally {
      setLoading(false)
    }
  }, [statusFilter])

  useEffect(() => { fetchOrders() }, [fetchOrders])

  const handleAdvance = async (po) => {
    setAdvancing(po.id)
    try {
      await advanceStatus(po.id)
      const next = NEXT_STATUS[po.status]
      toast.success(
        next === 'Received'
          ? `PO-${String(po.id).padStart(4, '0')} received — stock updated`
          : `PO-${String(po.id).padStart(4, '0')} → ${next}`
      )
      fetchOrders()
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to advance status')
    } finally {
      setAdvancing(null)
    }
  }

  const handleDelete = async (po) => {
    if (!window.confirm(`Delete PO-${String(po.id).padStart(4, '0')}?`)) return
    try {
      await deletePurchaseOrder(po.id)
      toast.success('Purchase order deleted')
      fetchOrders()
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to delete')
    }
  }

  const closeModal = (refresh) => {
    setModalPO(undefined)
    if (refresh) fetchOrders()
  }

  const draftCount = orders.filter((o) => o.status === 'Draft').length

  return (
    <Layout>
      <div className="p-6">
        {/* Header */}
        <div className="flex justify-between items-start mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-800">Purchase Orders</h1>
            <p className="text-sm text-gray-500 mt-1">
              {orders.length} total
              {draftCount > 0 && (
                <span className="ml-2 text-gray-500">· {draftCount} draft</span>
              )}
            </p>
          </div>
          <button
            onClick={() => setModalPO(null)}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 transition"
          >
            + New Order
          </button>
        </div>

        {/* Status filter tabs */}
        <div className="flex gap-2 mb-4 flex-wrap">
          <button
            onClick={() => setStatusFilter('')}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition ${
              statusFilter === ''
                ? 'bg-gray-800 text-white'
                : 'bg-white border border-gray-300 text-gray-600 hover:bg-gray-50'
            }`}
          >
            All
          </button>
          {ALL_STATUSES.map((s) => (
            <button
              key={s}
              onClick={() => setStatusFilter(s)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition ${
                statusFilter === s
                  ? 'bg-gray-800 text-white'
                  : 'bg-white border border-gray-300 text-gray-600 hover:bg-gray-50'
              }`}
            >
              {s}
            </button>
          ))}
        </div>

        {/* Table */}
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          {loading ? (
            <div className="p-10 text-center text-gray-400 text-sm">Loading…</div>
          ) : orders.length === 0 ? (
            <div className="p-10 text-center text-gray-400 text-sm">No purchase orders found.</div>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 border-b border-gray-200 text-gray-500 font-medium">
                  <th className="text-left px-4 py-3">PO #</th>
                  <th className="text-left px-4 py-3">Supplier</th>
                  <th className="text-left px-4 py-3">Status</th>
                  <th className="text-right px-4 py-3">Items</th>
                  <th className="text-right px-4 py-3">Total Value</th>
                  <th className="text-left px-4 py-3">Created</th>
                  <th className="px-4 py-3" />
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {orders.map((po) => (
                  <tr key={po.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 font-mono text-xs text-gray-500">
                      PO-{String(po.id).padStart(4, '0')}
                    </td>
                    <td className="px-4 py-3 font-medium text-gray-800">{po.supplier?.name ?? '—'}</td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_STYLES[po.status]}`}>
                        {po.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right text-gray-600">{(po.line_items || []).length}</td>
                    <td className="px-4 py-3 text-right font-medium text-gray-800">
                      ₹{(po.total_value ?? 0).toFixed(2)}
                    </td>
                    <td className="px-4 py-3 text-xs text-gray-500">
                      {new Date(po.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-4 py-3 text-right whitespace-nowrap">
                      <button
                        onClick={() => setModalPO(po)}
                        className="text-blue-500 hover:text-blue-700 text-xs font-medium mr-2"
                      >
                        {po.status === 'Draft' ? 'Edit' : 'View'}
                      </button>
                      {NEXT_STATUS[po.status] && (
                        <button
                          onClick={() => handleAdvance(po)}
                          disabled={advancing === po.id}
                          className="text-indigo-500 hover:text-indigo-700 text-xs font-medium mr-2 disabled:opacity-40"
                        >
                          → {NEXT_STATUS[po.status]}
                        </button>
                      )}
                      {po.status === 'Draft' && (
                        <button
                          onClick={() => handleDelete(po)}
                          className="text-red-400 hover:text-red-600 text-xs font-medium"
                        >
                          Delete
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {modalPO !== undefined && (
        <POModal po={modalPO} onClose={closeModal} />
      )}
    </Layout>
  )
}
