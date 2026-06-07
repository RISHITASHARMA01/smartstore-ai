import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'
import toast from 'react-hot-toast'
import Layout from '../components/Layout'
import ProductModal from '../components/ProductModal'
import { getProduct } from '../api/products'
import api from '../api/axios'

export default function ProductDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [product, setProduct] = useState(null)
  const [forecast, setForecast] = useState([])
  const [loading, setLoading] = useState(true)
  const [forecastLoading, setForecastLoading] = useState(true)
  const [modalOpen, setModalOpen] = useState(false)

  const fetchProduct = async () => {
    try {
      const data = await getProduct(id)
      setProduct(data)
    } catch {
      toast.error('Failed to load product')
    } finally {
      setLoading(false)
    }
  }

  const fetchForecast = async () => {
    try {
      const { data } = await api.get(`/products/${id}/forecast`)
      setForecast(data.forecast || [])
    } catch {
      toast.error('Failed to load forecast')
    } finally {
      setForecastLoading(false)
    }
  }

  useEffect(() => {
    fetchProduct()
    fetchForecast()
  }, [id])

  const closeModal = (refresh) => {
    setModalOpen(false)
    if (refresh) fetchProduct()
  }

  if (loading) {
    return (
      <Layout>
        <div className="p-10 text-center text-gray-400 text-sm">Loading…</div>
      </Layout>
    )
  }
  if (!product) {
    return (
      <Layout>
        <div className="p-10 text-center text-gray-400 text-sm">Product not found.</div>
      </Layout>
    )
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
          <button
            onClick={() => setModalOpen(true)}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 transition"
          >
            Edit Product
          </button>
        </div>

        {/* Product Card */}
        <div className="bg-white rounded-xl border border-gray-200 p-6 mb-6">
          <div className="flex items-start justify-between mb-5">
            <div>
              <h1 className="text-2xl font-bold text-gray-800">{product.name}</h1>
              <p className="text-sm font-mono text-gray-400 mt-1">{product.sku}</p>
            </div>
            {isExpired ? (
              <span className="bg-red-50 text-red-700 px-3 py-1 rounded-full text-sm font-medium">
                Expired
              </span>
            ) : isLow ? (
              <span className="bg-amber-50 text-amber-700 px-3 py-1 rounded-full text-sm font-medium">
                Low Stock
              </span>
            ) : (
              <span className="bg-green-50 text-green-700 px-3 py-1 rounded-full text-sm font-medium">
                In Stock
              </span>
            )}
          </div>

          <div className="grid grid-cols-2 md:grid-cols-3 gap-5">
            <div>
              <p className="text-xs text-gray-500 uppercase tracking-wide">Category</p>
              <p className="text-sm font-medium text-gray-800 mt-1">{product.category}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500 uppercase tracking-wide">Stock Quantity</p>
              <p className={`text-sm font-medium mt-1 ${isLow ? 'text-amber-600' : 'text-gray-800'}`}>
                {product.stock_qty} units
              </p>
            </div>
            <div>
              <p className="text-xs text-gray-500 uppercase tracking-wide">Reorder Threshold</p>
              <p className="text-sm font-medium text-gray-800 mt-1">{product.reorder_threshold} units</p>
            </div>
            <div>
              <p className="text-xs text-gray-500 uppercase tracking-wide">Unit Price</p>
              <p className="text-sm font-medium text-gray-800 mt-1">₹{product.unit_price.toFixed(2)}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500 uppercase tracking-wide">Expiry Date</p>
              <p className={`text-sm font-medium mt-1 ${isExpired ? 'text-red-500' : 'text-gray-800'}`}>
                {product.expiry_date ? new Date(product.expiry_date).toLocaleDateString() : '—'}
              </p>
            </div>
            <div>
              <p className="text-xs text-gray-500 uppercase tracking-wide">Added On</p>
              <p className="text-sm font-medium text-gray-800 mt-1">
                {new Date(product.created_at).toLocaleDateString()}
              </p>
            </div>
          </div>
        </div>

        {/* Forecast Chart */}
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-800 mb-4">7-Day Demand Forecast</h2>
          {forecastLoading ? (
            <div className="h-56 flex items-center justify-center text-gray-400 text-sm">
              Loading forecast…
            </div>
          ) : forecast.length === 0 ? (
            <div className="h-56 flex items-center justify-center text-gray-400 text-sm">
              No forecast data available.
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={280}>
              <LineChart data={forecast} margin={{ top: 10, right: 30, left: 10, bottom: 30 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis
                  dataKey="date"
                  tick={{ fontSize: 11, fill: '#6b7280' }}
                  label={{
                    value: 'Date',
                    position: 'insideBottom',
                    offset: -20,
                    fill: '#6b7280',
                    fontSize: 12,
                  }}
                />
                <YAxis
                  tick={{ fontSize: 11, fill: '#6b7280' }}
                  label={{
                    value: 'Predicted Qty (units)',
                    angle: -90,
                    position: 'insideLeft',
                    offset: 10,
                    fill: '#6b7280',
                    fontSize: 12,
                  }}
                  width={75}
                />
                <Tooltip
                  formatter={(value) => [`${value} units`, 'Predicted Qty']}
                  labelFormatter={(label) => `Date: ${label}`}
                />
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
          )}
        </div>
      </div>

      {modalOpen && <ProductModal product={product} onClose={closeModal} />}
    </Layout>
  )
}
