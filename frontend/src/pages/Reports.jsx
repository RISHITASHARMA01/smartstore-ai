import { useState, useEffect } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  LineChart, Line, Legend, PieChart, Pie, Cell,
} from 'recharts'
import Layout from '../components/Layout'
import api from '../api/axios'

const PIE_COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#14b8a6', '#f97316']

function StatCard({ label, value, sub, color = 'text-gray-800' }) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5">
      <p className="text-xs text-gray-500 uppercase tracking-wide mb-1">{label}</p>
      <p className={`text-3xl font-bold ${color}`}>{value}</p>
      {sub && <p className="text-xs text-gray-400 mt-1">{sub}</p>}
    </div>
  )
}

export default function Reports() {
  const [stockByCategory, setStockByCategory] = useState([])
  const [lowStock, setLowStock] = useState([])
  const [expiring, setExpiring] = useState([])
  const [history, setHistory] = useState([])
  const [poSummary, setPoSummary] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    const controller = new AbortController()
    const signal = controller.signal
    Promise.all([
      api.get('/reports/stock-by-category', { signal }),
      api.get('/reports/low-stock', { signal }),
      api.get('/reports/expiring-soon', { signal }),
      api.get('/reports/stock-history', { signal }),
      api.get('/reports/po-summary', { signal }),
    ]).then(([cat, low, exp, hist, po]) => {
      setStockByCategory(cat.data)
      setLowStock(low.data)
      setExpiring(exp.data)
      setHistory(hist.data)
      setPoSummary(po.data)
    }).catch((err) => {
      if (err?.name !== 'CanceledError' && err?.name !== 'AbortError') {
        setError('Failed to load analytics data')
      }
    }).finally(() => setLoading(false))
    return () => controller.abort()
  }, [])

  if (loading) {
    return (
      <Layout>
        <div className="p-6 flex items-center justify-center h-64">
          <p className="text-gray-400 text-sm">Loading analytics…</p>
        </div>
      </Layout>
    )
  }

  if (error) {
    return (
      <Layout>
        <div className="p-6 flex items-center justify-center h-64">
          <p className="text-red-500 text-sm">{error}</p>
        </div>
      </Layout>
    )
  }

  const totalStock = stockByCategory.reduce((s, r) => s + r.total_stock, 0)

  return (
    <Layout>
      <div className="p-6 space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">Reports & Analytics</h1>
          <p className="text-sm text-gray-500 mt-1">Live inventory insights</p>
        </div>

        {/* Summary cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <StatCard label="Total Stock Units" value={totalStock.toLocaleString()} />
          <StatCard
            label="Low Stock Products"
            value={lowStock.length}
            color={lowStock.length > 0 ? 'text-red-600' : 'text-green-600'}
            sub={lowStock.length > 0 ? 'Need reorder' : 'All stocked'}
          />
          <StatCard
            label="Expiring in 30 days"
            value={expiring.length}
            color={expiring.length > 0 ? 'text-orange-600' : 'text-green-600'}
          />
          <StatCard label="PO Statuses" value={poSummary.length} sub="distinct statuses" />
        </div>

        {/* Charts row */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Stock by category bar chart */}
          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <h2 className="text-base font-semibold text-gray-800 mb-4">Stock by Category</h2>
            {stockByCategory.length === 0 ? (
              <p className="text-sm text-gray-400 text-center py-8">No data</p>
            ) : (
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={stockByCategory} margin={{ top: 4, right: 8, left: 0, bottom: 40 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis
                    dataKey="category"
                    tick={{ fontSize: 11, fill: '#6b7280' }}
                    angle={-30}
                    textAnchor="end"
                    interval={0}
                  />
                  <YAxis tick={{ fontSize: 11, fill: '#6b7280' }} />
                  <Tooltip formatter={(v) => [v, 'Units']} />
                  <Bar dataKey="total_stock" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>

          {/* Stock distribution pie */}
          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <h2 className="text-base font-semibold text-gray-800 mb-4">Stock Distribution</h2>
            {stockByCategory.length === 0 ? (
              <p className="text-sm text-gray-400 text-center py-8">No data</p>
            ) : (
              <div className="flex items-center gap-4">
                <ResponsiveContainer width="60%" height={220}>
                  <PieChart>
                    <Pie
                      data={stockByCategory}
                      dataKey="total_stock"
                      nameKey="category"
                      cx="50%"
                      cy="50%"
                      outerRadius={80}
                    >
                      {stockByCategory.map((_, i) => (
                        <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip formatter={(v) => [v, 'Units']} />
                  </PieChart>
                </ResponsiveContainer>
                <div className="space-y-2 flex-1">
                  {stockByCategory.map((r, i) => (
                    <div key={r.category} className="flex items-center gap-2 text-xs">
                      <span
                        className="w-3 h-3 rounded-xs shrink-0"
                        style={{ background: PIE_COLORS[i % PIE_COLORS.length] }}
                      />
                      <span className="text-gray-700 truncate">{r.category}</span>
                      <span className="ml-auto text-gray-500 font-medium">{r.total_stock}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Stock history line chart */}
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <h2 className="text-base font-semibold text-gray-800 mb-4">Stock Movement History</h2>
          {history.length === 0 ? (
            <p className="text-sm text-gray-400 text-center py-8">
              No stock movements recorded yet. Confirm invoices to see restock history here.
            </p>
          ) : (
            <ResponsiveContainer width="100%" height={220}>
              <LineChart data={history} margin={{ top: 4, right: 16, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="date" tick={{ fontSize: 11, fill: '#6b7280' }} />
                <YAxis tick={{ fontSize: 11, fill: '#6b7280' }} />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="restocked" stroke="#10b981" strokeWidth={2} dot={false} name="Restocked" />
                <Line type="monotone" dataKey="sold" stroke="#ef4444" strokeWidth={2} dot={false} name="Sold" />
              </LineChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Bottom tables */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Low stock table */}
          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
            <div className="px-5 py-4 border-b border-gray-100">
              <h2 className="text-base font-semibold text-gray-800">Low Stock Products</h2>
              <p className="text-xs text-gray-500 mt-0.5">Stock ≤ reorder threshold</p>
            </div>
            {lowStock.length === 0 ? (
              <p className="text-sm text-gray-400 text-center py-8">All products are well-stocked</p>
            ) : (
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-gray-50 text-gray-500 text-xs uppercase tracking-wide">
                    <th className="text-left px-4 py-2">Product</th>
                    <th className="text-right px-4 py-2">Stock</th>
                    <th className="text-right px-4 py-2">Threshold</th>
                    <th className="text-right px-4 py-2">Gap</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {lowStock.map((p) => (
                    <tr key={p.id} className="hover:bg-gray-50">
                      <td className="px-4 py-2">
                        <p className="font-medium text-gray-800 truncate max-w-[140px]">{p.name}</p>
                        <p className="text-gray-400 text-xs">{p.sku}</p>
                      </td>
                      <td className="px-4 py-2 text-right font-semibold text-red-600">{p.stock_qty}</td>
                      <td className="px-4 py-2 text-right text-gray-500">{p.reorder_threshold}</td>
                      <td className="px-4 py-2 text-right">
                        <span className="bg-red-50 text-red-700 px-2 py-0.5 rounded-full text-xs font-medium">
                          -{p.gap}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>

          {/* Expiring soon table */}
          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
            <div className="px-5 py-4 border-b border-gray-100">
              <h2 className="text-base font-semibold text-gray-800">Expiring Soon</h2>
              <p className="text-xs text-gray-500 mt-0.5">Products expiring within 30 days</p>
            </div>
            {expiring.length === 0 ? (
              <p className="text-sm text-gray-400 text-center py-8">No products expiring soon</p>
            ) : (
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-gray-50 text-gray-500 text-xs uppercase tracking-wide">
                    <th className="text-left px-4 py-2">Product</th>
                    <th className="text-right px-4 py-2">Stock</th>
                    <th className="text-right px-4 py-2">Expiry</th>
                    <th className="text-right px-4 py-2">Days Left</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {expiring.map((p) => (
                    <tr key={p.id} className="hover:bg-gray-50">
                      <td className="px-4 py-2">
                        <p className="font-medium text-gray-800 truncate max-w-[140px]">{p.name}</p>
                        <p className="text-gray-400 text-xs">{p.sku}</p>
                      </td>
                      <td className="px-4 py-2 text-right text-gray-600">{p.stock_qty}</td>
                      <td className="px-4 py-2 text-right text-gray-600 text-xs">
                        {p.expiry_date ? new Date(p.expiry_date).toLocaleDateString() : '—'}
                      </td>
                      <td className="px-4 py-2 text-right">
                        <span
                          className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                            (p.days_left ?? 0) <= 0
                              ? 'bg-red-100 text-red-700'
                              : (p.days_left ?? 0) <= 7
                              ? 'bg-orange-100 text-orange-700'
                              : 'bg-yellow-50 text-yellow-700'
                          }`}
                        >
                          {(p.days_left ?? 0) <= 0 ? 'Expired' : `${p.days_left}d`}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>

        {/* PO status summary */}
        {poSummary.length > 0 && (
          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <h2 className="text-base font-semibold text-gray-800 mb-4">Purchase Order Status</h2>
            <div className="flex flex-wrap gap-3">
              {poSummary.map((p) => (
                <div key={p.status} className="bg-gray-50 border border-gray-200 rounded-xl px-6 py-4 text-center min-w-[100px]">
                  <p className="text-2xl font-bold text-gray-800">{p.count}</p>
                  <p className="text-xs text-gray-500 mt-1">{p.status}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </Layout>
  )
}
