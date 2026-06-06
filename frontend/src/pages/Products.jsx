import { useState, useEffect } from 'react'
import toast from 'react-hot-toast'
import Layout from '../components/Layout'
import ProductModal from '../components/ProductModal'
import { getProducts, deleteProduct } from '../api/products'

export default function Products() {
  const [products, setProducts] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [categoryFilter, setCategoryFilter] = useState('')
  const [modalOpen, setModalOpen] = useState(false)
  const [editProduct, setEditProduct] = useState(null)

  const fetchProducts = async () => {
    setLoading(true)
    try {
      const params = {}
      if (search) params.search = search
      if (categoryFilter) params.category = categoryFilter
      const data = await getProducts(params)
      setProducts(data)
    } catch {
      toast.error('Failed to load products')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    const timer = setTimeout(fetchProducts, 300)
    return () => clearTimeout(timer)
  }, [search, categoryFilter])

  const handleDelete = async (id, name) => {
    if (!window.confirm(`Delete "${name}"?`)) return
    try {
      await deleteProduct(id)
      toast.success('Product deleted')
      fetchProducts()
    } catch {
      toast.error('Failed to delete product')
    }
  }

  const openAdd = () => { setEditProduct(null); setModalOpen(true) }
  const openEdit = (p) => { setEditProduct(p); setModalOpen(true) }
  const closeModal = (refresh) => {
    setModalOpen(false)
    setEditProduct(null)
    if (refresh) fetchProducts()
  }

  const categories = [...new Set(products.map((p) => p.category))].sort()
  const lowStockCount = products.filter((p) => p.stock_qty <= p.reorder_threshold).length

  return (
    <Layout>
      <div className="p-6">
        {/* Header */}
        <div className="flex justify-between items-start mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-800">Products</h1>
            <p className="text-sm text-gray-500 mt-1">
              {products.length} total
              {lowStockCount > 0 && (
                <span className="ml-2 text-amber-600 font-medium">· {lowStockCount} low stock</span>
              )}
            </p>
          </div>
          <button
            onClick={openAdd}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 transition"
          >
            + Add Product
          </button>
        </div>

        {/* Filters */}
        <div className="flex gap-3 mb-4">
          <input
            type="text"
            placeholder="Search name or SKU…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm w-64 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Categories</option>
            {categories.map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
        </div>

        {/* Table */}
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          {loading ? (
            <div className="p-10 text-center text-gray-400 text-sm">Loading…</div>
          ) : products.length === 0 ? (
            <div className="p-10 text-center text-gray-400 text-sm">No products found.</div>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 border-b border-gray-200 text-gray-500 font-medium">
                  <th className="text-left px-4 py-3">SKU</th>
                  <th className="text-left px-4 py-3">Name</th>
                  <th className="text-left px-4 py-3">Category</th>
                  <th className="text-right px-4 py-3">Stock</th>
                  <th className="text-right px-4 py-3">Unit Price</th>
                  <th className="text-left px-4 py-3">Expiry</th>
                  <th className="text-left px-4 py-3">Status</th>
                  <th className="px-4 py-3" />
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {products.map((p) => {
                  const isLow = p.stock_qty <= p.reorder_threshold
                  const isExpired =
                    p.expiry_date && new Date(p.expiry_date) < new Date()
                  return (
                    <tr key={p.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3 font-mono text-gray-500 text-xs">{p.sku}</td>
                      <td className="px-4 py-3 font-medium text-gray-800">{p.name}</td>
                      <td className="px-4 py-3 text-gray-600">{p.category}</td>
                      <td className={`px-4 py-3 text-right font-semibold ${isLow ? 'text-amber-600' : 'text-gray-800'}`}>
                        {p.stock_qty}
                      </td>
                      <td className="px-4 py-3 text-right text-gray-600">
                        ₹{p.unit_price.toFixed(2)}
                      </td>
                      <td className={`px-4 py-3 text-sm ${isExpired ? 'text-red-500 font-medium' : 'text-gray-500'}`}>
                        {p.expiry_date ? new Date(p.expiry_date).toLocaleDateString() : '—'}
                      </td>
                      <td className="px-4 py-3">
                        {isExpired ? (
                          <span className="bg-red-50 text-red-700 px-2 py-0.5 rounded-full text-xs font-medium">Expired</span>
                        ) : isLow ? (
                          <span className="bg-amber-50 text-amber-700 px-2 py-0.5 rounded-full text-xs font-medium">Low Stock</span>
                        ) : (
                          <span className="bg-green-50 text-green-700 px-2 py-0.5 rounded-full text-xs font-medium">OK</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-right whitespace-nowrap">
                        <button
                          onClick={() => openEdit(p)}
                          className="text-blue-500 hover:text-blue-700 text-xs font-medium mr-3"
                        >
                          Edit
                        </button>
                        <button
                          onClick={() => handleDelete(p.id, p.name)}
                          className="text-red-400 hover:text-red-600 text-xs font-medium"
                        >
                          Delete
                        </button>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {modalOpen && <ProductModal product={editProduct} onClose={closeModal} />}
    </Layout>
  )
}
