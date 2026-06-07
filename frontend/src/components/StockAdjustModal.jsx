import { useState } from 'react'
import toast from 'react-hot-toast'
import api from '../api/axios'

const TYPES = [
  { value: 'sale',       label: 'Sale',        desc: 'Record a sale — reduces stock', color: 'text-red-600' },
  { value: 'restock',    label: 'Restock',     desc: 'Add incoming stock',            color: 'text-green-600' },
  { value: 'write_off',  label: 'Write-off',   desc: 'Damaged / expired removal',    color: 'text-orange-600' },
  { value: 'adjustment', label: 'Adjustment',  desc: 'Manual correction',             color: 'text-blue-600' },
]

export default function StockAdjustModal({ product, onClose }) {
  const [changeType, setChangeType] = useState('sale')
  const [qty, setQty] = useState(1)
  const [note, setNote] = useState('')
  const [saving, setSaving] = useState(false)

  const isDecrease = changeType === 'sale' || changeType === 'write_off'
  const newQty = isDecrease ? product.stock_qty - qty : product.stock_qty + qty
  const invalid = qty <= 0 || newQty < 0

  async function handleSubmit(e) {
    e.preventDefault()
    if (invalid) return
    setSaving(true)
    try {
      await api.post(`/products/${product.id}/adjust`, { change_type: changeType, qty: Number(qty), note })
      toast.success(`Stock updated — new qty: ${newQty}`)
      onClose(true)
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to adjust stock')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-md">
        <div className="px-6 py-5 border-b border-gray-100">
          <h2 className="text-lg font-semibold text-gray-800">Adjust Stock</h2>
          <p className="text-sm text-gray-500 mt-0.5">{product.name}</p>
        </div>

        <form onSubmit={handleSubmit} className="px-6 py-5 space-y-5">
          {/* Type selector */}
          <div>
            <label className="text-xs text-gray-500 uppercase tracking-wide block mb-2">Adjustment Type</label>
            <div className="grid grid-cols-2 gap-2">
              {TYPES.map((t) => (
                <button
                  key={t.value}
                  type="button"
                  onClick={() => setChangeType(t.value)}
                  className={`text-left px-3 py-3 rounded-xl border-2 transition ${
                    changeType === t.value
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <p className={`text-sm font-semibold ${changeType === t.value ? t.color : 'text-gray-700'}`}>
                    {t.label}
                  </p>
                  <p className="text-xs text-gray-400 mt-0.5">{t.desc}</p>
                </button>
              ))}
            </div>
          </div>

          {/* Quantity */}
          <div>
            <label className="text-xs text-gray-500 uppercase tracking-wide block mb-1">Quantity</label>
            <input
              type="number"
              min="1"
              value={qty}
              onChange={(e) => setQty(Number(e.target.value))}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Note */}
          <div>
            <label className="text-xs text-gray-500 uppercase tracking-wide block mb-1">Note (optional)</label>
            <input
              type="text"
              value={note}
              onChange={(e) => setNote(e.target.value)}
              placeholder="e.g. customer return, inventory count"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Preview */}
          <div className="bg-gray-50 rounded-xl px-4 py-3 flex items-center justify-between text-sm">
            <div>
              <p className="text-gray-500 text-xs">Current stock</p>
              <p className="font-semibold text-gray-800">{product.stock_qty} units</p>
            </div>
            <span className="text-gray-400 text-lg">{isDecrease ? '−' : '+'}{qty}</span>
            <div className="text-right">
              <p className="text-gray-500 text-xs">New stock</p>
              <p className={`font-semibold text-lg ${newQty < 0 ? 'text-red-600' : 'text-gray-800'}`}>
                {newQty} units
              </p>
            </div>
          </div>

          {newQty < 0 && (
            <p className="text-red-500 text-xs">Cannot reduce stock below 0</p>
          )}

          <div className="flex gap-3 pt-1">
            <button
              type="button"
              onClick={() => onClose(false)}
              className="flex-1 border border-gray-300 text-gray-600 py-2 rounded-lg text-sm font-medium hover:bg-gray-50 transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={saving || invalid}
              className="flex-1 bg-blue-600 text-white py-2 rounded-lg text-sm font-medium hover:bg-blue-700 transition disabled:opacity-50"
            >
              {saving ? 'Saving…' : 'Confirm Adjustment'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
