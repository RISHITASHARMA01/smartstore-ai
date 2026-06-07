import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import Layout from '../components/Layout'
import ChatPanel from '../components/ChatPanel'
import api from '../api/axios'
import { useWebSocket } from '../hooks/useWebSocket'

let _updateId = 0

export default function Dashboard() {
  const navigate = useNavigate()
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [recentUpdates, setRecentUpdates] = useState([])

  useEffect(() => {
    const controller = new AbortController()
    setLoading(true)
    setError(null)
    api.get('/dashboard/stats', { signal: controller.signal })
      .then((r) => setStats(r.data))
      .catch((err) => {
        if (err?.name !== 'CanceledError' && err?.name !== 'AbortError') {
          setError('Failed to load dashboard stats')
        }
      })
      .finally(() => setLoading(false))
    return () => controller.abort()
  }, [])

  const handleWebSocketMessage = useCallback((message) => {
    if (message.event === 'stock_updated') {
      toast.success(`Stock updated: ${message.data.product_name} now has ${message.data.new_stock_qty} units`)
      if (message.data.status === 'low') {
        toast.error(`Low stock alert: ${message.data.product_name}`)
      }
      setRecentUpdates((prev) => [{ ...message.data, _id: ++_updateId }, ...prev.slice(0, 4)])
    }
    if (message.event === 'invoice_confirmed') {
      toast.success(`Invoice confirmed — ${message.data.products_updated?.length || 0} products restocked`)
      setRecentUpdates((prev) => [{ ...message.data, _id: ++_updateId }, ...prev.slice(0, 4)])
    }
  }, [])

  useWebSocket(handleWebSocketMessage)

  const dash = loading ? null : stats

  const cards = [
    {
      label: 'Total Products',
      value: loading ? '…' : (dash?.total_products ?? '—'),
      color: 'text-blue-600',
      bg: 'bg-blue-50',
      icon: '📦',
      link: '/products',
    },
    {
      label: 'Low Stock Alerts',
      value: loading ? '…' : (dash?.low_stock_alerts ?? '—'),
      color: dash?.low_stock_alerts > 0 ? 'text-red-600' : 'text-green-600',
      bg: dash?.low_stock_alerts > 0 ? 'bg-red-50' : 'bg-green-50',
      icon: '⚠️',
      link: '/reports',
    },
    {
      label: 'Expired Items',
      value: loading ? '…' : (dash?.expired_items ?? '—'),
      color: dash?.expired_items > 0 ? 'text-orange-600' : 'text-green-600',
      bg: dash?.expired_items > 0 ? 'bg-orange-50' : 'bg-green-50',
      icon: '🕒',
      link: '/reports',
    },
    {
      label: 'Suppliers',
      value: loading ? '…' : (dash?.total_suppliers ?? '—'),
      color: 'text-purple-600',
      bg: 'bg-purple-50',
      icon: '🏭',
      link: '/suppliers',
    },
  ]

  return (
    <Layout>
      <div className="p-6">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-800">Dashboard</h1>
          <p className="text-sm text-gray-500 mt-1">Welcome back — here's your store overview</p>
        </div>

        {error && (
          <div className="mb-4 bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-3 text-sm">
            {error}
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          {cards.map((card) => (
            <button
              key={card.label}
              onClick={() => navigate(card.link)}
              className="bg-white rounded-xl shadow-xs p-5 border border-gray-100 text-left hover:shadow-md transition group"
            >
              <div className={`inline-flex items-center justify-center w-10 h-10 rounded-lg ${card.bg} mb-3`}>
                <span className="text-xl">{card.icon}</span>
              </div>
              <p className="text-sm text-gray-500">{card.label}</p>
              <p className={`text-3xl font-bold mt-1 ${card.color}`}>{card.value}</p>
            </button>
          ))}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <h2 className="text-base font-semibold text-gray-800 mb-3">Quick Actions</h2>
            <div className="space-y-2">
              {[
                { label: 'Add New Product', link: '/products', icon: '➕' },
                { label: 'Upload Invoice (OCR)', link: '/invoices/upload', icon: '📄' },
                { label: 'Create Purchase Order', link: '/purchase-orders', icon: '🛒' },
                { label: 'View Analytics', link: '/reports', icon: '📊' },
              ].map((a) => (
                <button
                  key={a.label}
                  onClick={() => navigate(a.link)}
                  className="w-full flex items-center gap-3 px-4 py-3 rounded-lg hover:bg-gray-50 text-sm text-gray-700 transition"
                >
                  <span>{a.icon}</span>
                  <span>{a.label}</span>
                  <span className="ml-auto text-gray-400">→</span>
                </button>
              ))}
            </div>
          </div>

          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <h2 className="text-base font-semibold text-gray-800 mb-3">AI Assistant</h2>
            <p className="text-sm text-gray-500 mb-4">
              Ask about stock levels, expiring products, supplier history, and more using the chat below.
            </p>
            <div className="space-y-2 text-sm text-gray-600">
              {[
                '"Which products are running low?"',
                '"Show me expiring items in the next 7 days"',
                '"What did we order from Agro Supplies?"',
              ].map((q) => (
                <div key={q} className="flex items-start gap-2 bg-gray-50 rounded-lg px-3 py-2">
                  <span className="text-blue-400">💬</span>
                  <span className="italic">{q}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="mt-6 bg-white rounded-xl shadow-sm p-5 border border-gray-100">
          <div className="flex items-center gap-2 mb-3">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
            <h3 className="font-semibold text-gray-700">Live Updates</h3>
          </div>
          {recentUpdates.length === 0 ? (
            <p className="text-sm text-gray-400">Watching for real-time stock changes...</p>
          ) : (
            <ul className="space-y-2">
              {recentUpdates.map((update) => (
                <li key={update._id} className="text-sm text-gray-600 border-l-2 border-blue-400 pl-3">
                  {update.product_name
                    ? `${update.product_name}: ${update.new_stock_qty} units`
                    : `Invoice confirmed — ${update.products_updated?.length || 0} products restocked`}
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
      <ChatPanel />
    </Layout>
  )
}
