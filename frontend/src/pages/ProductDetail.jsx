import { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts'
import toast from 'react-hot-toast'
import Layout from '../components/Layout'
import ProductModal from '../components/ProductModal'
import StockAdjustModal from '../components/StockAdjustModal'
import { getProduct } from '../api/products'
import api from '../api/axios'

const TYPE_STYLES = {
  restock:    'bg-green-50 text-green-700',
  sale:       'bg-red-50 text-red-700',
  write_off:  'bg-orange-50 text-orange-700',
  adjustment: 'bg-blue-50 text-blue-700',
}

export default function ProductDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [product, setProduct] = useState(null)
  const [forecast, setForecast] = useState([])
  const [history, setHistory] = useState([])
  const [loading, setLoading] = useState(true)
  const [forecastLoading, setForecastLoading] = useState(true)
  const [historyLoading, setHistoryLoading] = useState(true)
  const [tab, setTab] = useState('forecast')
  const [editOpen, setEditOpen] = useState(false)
  const [adjustOpen, setAdjustOpen] = useState(false)

  const fetchProduct = useCallback(async () => {
    try {
      const data = await getProduct(id)
      setProduct(data)
    } catch {
      toast.error('Failed to load product')
    } finally {
      setLoading(false)
    }
  }, [id])

  const fetchForecast = useCallback(async () => {
    try {
      const { data } = await api.get(`/products/${id}/forecast`)
      setForecast(data.forecast || [])
    } catch {
      toast.error('Failed to load forecast')
    } finally {
      setForecastLoading(false)
    }
  }, [id])

  const fetchHistory = useCallback(async () => {
    setHistoryLoading(true)
    try {
      const { data } = await api.get(`/products/${id}/history`)
      setHistory(data)
    } catch {
      toast.error('Failed to load history')
    } finally {
      setHistoryLoading(false)
    }
  }, [id])

  useEffect(() => {
    fetchProduct()
    fetchForecast()
    fetchHistory()
  }, [fetchProduct, fetchForecast, fetchHistory])

  const handleAdjustClose = (refresh) => {
    setAdjustOpen(false)
    if (refresh) {
      fetchProduct()
      fetchHistory()
    }
  }

  if (loading) {
    return <Layout><div className="p-10 text-center text-gray-400 text-sm">Loading…</div></Layout>
  }
  if (!product) {
    return <Layout><div className="p-10 text-center text-gray-400 text-sm">Product not found.</div></Layout>
  }

  const isLow = product.stock_qty <= product.reorder_threshold
  const isExpired = product.expiry_date && new Date(product.expiry_date) < new Date()

  return (
    <Layout>
      <div className="p-6 max-w-4xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <button
            onClick={() => navigate('/products')}
            className="text-sm text-gray-500 hover:text-gray-700 flex items-center gap-1 transition"
          >
            ← Back to Products
          </button>
          <div className="flex gap-2">
            <button
              onClick={() => setAdjustOpen(true)}
              className="border border-gray-300 text-gray-700 px-4 py-2 rounded-lg text-sm font-medium hover:bg-gray-50 transition"
            >
              Adjust Stock
            </button>
            <button
              onClick={() => setEditOpen(true)}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 transition"
            >
              Edit Product
            </button>
          </div>
        </div>

        {/* Product Card */}
        <div className="bg-white rounded-xl border border-gray-200 p-6 mb-6">
          <div className="flex items-start justify-between mb-5">
            <div>
              <h1 className="text-2xl font-bold text-gray-800">{product.name}</h1>
              <p className="text-sm font-mono text-gray-400 mt-1">{product.sku}</p>
            </div>
            {isExpired ? (
              <span className="bg-red-50 text-red-700 px-3 py-1 rounded-full text-sm font-medium">Expired</span>
            ) : isLow ? (
              <span className="bg-amber-50 text-amber-700 px-3 py-1 rounded-full text-sm font-medium">Low Stock</span>
            ) : (
              <span className="bg-green-50 text-green-700 px-3 py-1 rounded-full text-sm font-medium">In Stock</span>
            )}
          </div>

          <div className="grid grid-cols-2 md:grid-cols-3 gap-5">
            {[
              { label: 'Category',          value: product.category },
              { label: 'Stock Quantity',     value: `${product.stock_qty} units`,         cls: isLow ? 'text-amber-600' : '' },
              { label: 'Reorder Threshold',  value: `${product.reorder_threshold} units` },
              { label: 'Unit Price',         value: `₹${product.unit_price.toFixed(2)}` },
              { label: 'Expiry Date',        value: product.expiry_date ? new Date(product.expiry_date).toLocaleDateString() : '—', cls: isExpired ? 'text-red-500' : '' },
              { label: 'Added On',           value: new Date(product.created_at).toLocaleDateString() },
            ].map(({ label, value, cls = '' }) => (
              <div key={label}>
                <p className="text-xs text-gray-500 uppercase tracking-wide">{label}</p>
                <p className={`text-sm font-medium mt-1 ${cls || 'text-gray-800'}`}>{value}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Tabs */}
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <div className="flex border-b border-gray-200">
            {[
              { key: 'forecast', label: '7-Day Forecast' },
              { key: 'history',  label: 'Stock History' },
            ].map((t) => (
              <button
                key={t.key}
                onClick={() => setTab(t.key)}
                className={`px-5 py-3 text-sm font-medium transition border-b-2 ${
                  tab === t.key
                    ? 'border-blue-600 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                {t.label}
              </button>
            ))}
          </div>

          <div className="p-6">
            {tab === 'forecast' && (
              forecastLoading ? (
                <div className="h-56 flex items-center justify-center text-gray-400 text-sm">Loading forecast…</div>
              ) : forecast.length === 0 ? (
                <div className="h-56 flex items-center justify-center text-gray-400 text-sm">No forecast data available.</div>
              ) : (
                <ResponsiveContainer width="100%" height={280}>
                  <LineChart data={forecast} margin={{ top: 10, right: 30, left: 10, bottom: 30 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis
                      dataKey="date"
                      tick={{ fontSize: 11, fill: '#6b7280' }}
                      label={{ value: 'Date', position: 'insideBottom', offset: -20, fill: '#6b7280', fontSize: 12 }}
                    />
                    <YAxis
                      tick={{ fontSize: 11, fill: '#6b7280' }}
                      label={{ value: 'Predicted Qty (units)', angle: -90, position: 'insideLeft', offset: 10, fill: '#6b7280', fontSize: 12 }}
                      width={75}
                    />
                    <Tooltip formatter={(v) => [`${v} units`, 'Predicted Qty']} labelFormatter={(l) => `Date: ${l}`} />
                    <Legend verticalAlign="top" height={36} />
                    <Line
                      type="monotone"
                      dataKey="predicted_qty"
                      name="Predicted Qty"
                      stroke="#3b82f6"
                      strokeWidth={2}
                      dot={{ r: 4, fill: '#3b82f6' }}
                      activeDot={{ r: 6 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              )
            )}

            {tab === 'history' && (
              historyLoading ? (
                <div className="h-40 flex items-center justify-center text-gray-400 text-sm">Loading…</div>
              ) : history.length === 0 ? (
                <div className="h-40 flex items-center justify-center text-gray-400 text-sm">
                  No stock movements yet. Use "Adjust Stock" to record a change.
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="bg-gray-50 text-gray-500 text-xs uppercase tracking-wide">
                        <th className="text-left px-4 py-2">Type</th>
                        <th className="text-right px-4 py-2">Change</th>
                        <th className="text-left px-4 py-2">Date & Time</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                      {history.map((h) => (
                        <tr key={h.id} className="hover:bg-gray-50">
                          <td className="px-4 py-2">
                            <span className={`px-2 py-0.5 rounded-full text-xs font-medium capitalize ${TYPE_STYLES[h.change_type] || 'bg-gray-100 text-gray-600'}`}>
                              {h.change_type.replace('_', ' ')}
                            </span>
                          </td>
                          <td className={`px-4 py-2 text-right font-semibold ${h.change_qty >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                            {h.change_qty >= 0 ? '+' : ''}{h.change_qty}
                          </td>
                          <td className="px-4 py-2 text-gray-500 text-xs">
                            {new Date(h.recorded_at).toLocaleString()}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )
            )}
          </div>
        </div>
      </div>

      {editOpen   && <ProductModal product={product} onClose={(r) => { setEditOpen(false); if (r) fetchProduct() }} />}
      {adjustOpen && <StockAdjustModal product={product} onClose={handleAdjustClose} />}
    </Layout>
  )
}
