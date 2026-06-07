import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import Layout from '../components/Layout'
import api from '../api/axios'

export default function InvoiceList() {
  const navigate = useNavigate()
  const [invoices, setInvoices] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const controller = new AbortController()
    api.get('/invoices/', { signal: controller.signal })
      .then((r) => setInvoices(r.data))
      .catch((err) => {
        if (err?.name !== 'CanceledError' && err?.name !== 'AbortError') {
          toast.error('Failed to load invoices')
        }
      })
      .finally(() => setLoading(false))
    return () => controller.abort()
  }, [])

  return (
    <Layout>
      <div className="p-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-800">Invoices</h1>
            <p className="text-sm text-gray-500 mt-1">{invoices.length} total</p>
          </div>
          <button
            onClick={() => navigate('/invoices/upload')}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 transition"
          >
            + Upload Invoice
          </button>
        </div>

        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          {loading ? (
            <div className="p-10 text-center text-gray-400 text-sm">Loading…</div>
          ) : invoices.length === 0 ? (
            <div className="p-10 text-center">
              <p className="text-gray-400 text-sm mb-3">No invoices yet.</p>
              <button
                onClick={() => navigate('/invoices/upload')}
                className="text-blue-600 text-sm font-medium hover:underline"
              >
                Upload your first invoice →
              </button>
            </div>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 border-b border-gray-200 text-gray-500 font-medium text-xs uppercase tracking-wide">
                  <th className="text-left px-4 py-3">ID</th>
                  <th className="text-left px-4 py-3">Supplier</th>
                  <th className="text-left px-4 py-3">Date</th>
                  <th className="text-right px-4 py-3">Items</th>
                  <th className="text-right px-4 py-3">Total</th>
                  <th className="text-left px-4 py-3">Status</th>
                  <th className="text-left px-4 py-3">Created</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {invoices.map((inv) => (
                  <tr key={inv.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 font-mono text-gray-400 text-xs">#{inv.id}</td>
                    <td className="px-4 py-3 font-medium text-gray-800">
                      {inv.supplier_name || '—'}
                    </td>
                    <td className="px-4 py-3 text-gray-600">{inv.invoice_date || '—'}</td>
                    <td className="px-4 py-3 text-right text-gray-600">{inv.line_items_count}</td>
                    <td className="px-4 py-3 text-right font-medium text-gray-800">
                      {inv.grand_total != null ? `₹${Number(inv.grand_total).toFixed(2)}` : '—'}
                    </td>
                    <td className="px-4 py-3">
                      {inv.confirmed ? (
                        <span className="bg-green-50 text-green-700 px-2 py-0.5 rounded-full text-xs font-medium">
                          Confirmed
                        </span>
                      ) : (
                        <span className="bg-amber-50 text-amber-700 px-2 py-0.5 rounded-full text-xs font-medium">
                          Pending
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-gray-500 text-xs">
                      {inv.created_at ? new Date(inv.created_at).toLocaleDateString() : '—'}
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
