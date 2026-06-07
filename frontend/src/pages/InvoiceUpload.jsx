import { useState, useRef, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import Layout from '../components/Layout'
import api from '../api/axios'

const EMPTY_ITEM = () => ({ name: '', qty: 1, unit_price: 0, total: 0 })

function calcTotal(items) {
  return items.reduce((s, it) => s + (parseFloat(it.qty) || 0) * (parseFloat(it.unit_price) || 0), 0)
}

export default function InvoiceUpload() {
  const navigate = useNavigate()
  const inputRef = useRef(null)

  const [dragging, setDragging] = useState(false)
  const [file, setFile] = useState(null)
  const [parsing, setParsing] = useState(false)
  const [invoiceId, setInvoiceId] = useState(null)
  const [form, setForm] = useState(null)   // { supplier_name, invoice_date, line_items }
  const [confirming, setConfirming] = useState(false)
  const [result, setResult] = useState(null)

  // ── drag & drop ─────────────────────────────────────────────────────────────
  const onDragOver = useCallback((e) => { e.preventDefault(); setDragging(true) }, [])
  const onDragLeave = useCallback(() => setDragging(false), [])
  const onDrop = useCallback((e) => {
    e.preventDefault()
    setDragging(false)
    const f = e.dataTransfer.files[0]
    if (f) acceptFile(f)
  }, [])

  function acceptFile(f) {
    const ok = ['image/jpeg', 'image/jpg', 'image/png', 'application/pdf']
    if (!ok.includes(f.type) && !f.name.match(/\.(jpg|jpeg|png|pdf)$/i)) {
      toast.error('Unsupported file type. Use JPG, PNG, or PDF.')
      return
    }
    setFile(f)
    setForm(null)
    setResult(null)
    setInvoiceId(null)
  }

  // ── parse ────────────────────────────────────────────────────────────────────
  async function handleParse() {
    if (!file) return
    setParsing(true)
    try {
      const fd = new FormData()
      fd.append('file', file)
      const { data } = await api.post('/invoices/parse', fd, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      setInvoiceId(data.id)
      setForm({
        supplier_name: data.supplier_name || '',
        invoice_date: data.invoice_date || '',
        line_items: (data.line_items || []).map((it) => ({
          name: it.name || '',
          qty: it.qty ?? 1,
          unit_price: it.unit_price ?? 0,
          total: it.total ?? (it.qty * it.unit_price),
        })),
      })
      toast.success('Invoice parsed successfully')
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Failed to parse invoice')
    } finally {
      setParsing(false)
    }
  }

  // ── line item helpers ────────────────────────────────────────────────────────
  function updateItem(idx, field, val) {
    setForm((prev) => {
      const items = prev.line_items.map((it, i) => {
        if (i !== idx) return it
        const updated = { ...it, [field]: val }
        updated.total = (parseFloat(updated.qty) || 0) * (parseFloat(updated.unit_price) || 0)
        return updated
      })
      return { ...prev, line_items: items }
    })
  }

  function addRow() {
    setForm((prev) => ({ ...prev, line_items: [...prev.line_items, EMPTY_ITEM()] }))
  }

  function removeRow(idx) {
    setForm((prev) => ({
      ...prev,
      line_items: prev.line_items.filter((_, i) => i !== idx),
    }))
  }

  // ── confirm ──────────────────────────────────────────────────────────────────
  async function handleConfirm() {
    if (!invoiceId || !form) return
    setConfirming(true)
    try {
      const { data } = await api.post(`/invoices/confirm/${invoiceId}`, {
        line_items: form.line_items.map((it) => ({
          product_name: it.name,
          qty: parseInt(it.qty) || 0,
          unit_price: parseFloat(it.unit_price) || 0,
        })),
      })
      setResult(data)
      toast.success('Stock updated successfully!')
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Failed to confirm invoice')
    } finally {
      setConfirming(false)
    }
  }

  const grandTotal = form ? calcTotal(form.line_items) : 0

  return (
    <Layout>
      <div className="p-6 max-w-4xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-800">Invoice OCR Upload</h1>
            <p className="text-sm text-gray-500 mt-1">Upload an invoice image — Gemini AI will extract the data</p>
          </div>
          <button
            onClick={() => navigate('/invoices')}
            className="text-sm text-gray-500 hover:text-gray-700 transition"
          >
            ← All Invoices
          </button>
        </div>

        {/* Upload zone */}
        {!result && (
          <div
            onDragOver={onDragOver}
            onDragLeave={onDragLeave}
            onDrop={onDrop}
            onClick={() => inputRef.current?.click()}
            className={`border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition mb-6 ${
              dragging
                ? 'border-blue-400 bg-blue-50'
                : file
                ? 'border-green-400 bg-green-50'
                : 'border-gray-300 bg-white hover:border-blue-400 hover:bg-blue-50'
            }`}
          >
            <input
              ref={inputRef}
              type="file"
              accept=".jpg,.jpeg,.png,.pdf"
              className="hidden"
              onChange={(e) => e.target.files[0] && acceptFile(e.target.files[0])}
            />
            {file ? (
              <div>
                <p className="text-2xl mb-2">📄</p>
                <p className="text-sm font-medium text-gray-700">{file.name}</p>
                <p className="text-xs text-gray-500 mt-1">{(file.size / 1024).toFixed(1)} KB</p>
                <p className="text-xs text-blue-500 mt-2">Click or drop to replace</p>
              </div>
            ) : (
              <div>
                <p className="text-4xl mb-3">📁</p>
                <p className="text-sm font-medium text-gray-700">Drag & drop your invoice here</p>
                <p className="text-xs text-gray-400 mt-1">JPG, PNG, or PDF accepted</p>
              </div>
            )}
          </div>
        )}

        {/* Parse button */}
        {file && !form && !result && (
          <button
            onClick={handleParse}
            disabled={parsing}
            className="w-full bg-blue-600 text-white py-3 rounded-xl font-medium hover:bg-blue-700 transition disabled:opacity-50 flex items-center justify-center gap-2 mb-6"
          >
            {parsing ? (
              <>
                <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/>
                </svg>
                Gemini is reading your invoice…
              </>
            ) : (
              '🔍 Upload & Parse Invoice'
            )}
          </button>
        )}

        {/* Editable form */}
        {form && !result && (
          <div className="bg-white rounded-xl border border-gray-200 p-6 space-y-5">
            <h2 className="text-lg font-semibold text-gray-800">Parsed Invoice — Review & Edit</h2>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-xs text-gray-500 uppercase tracking-wide block mb-1">Supplier Name</label>
                <input
                  type="text"
                  value={form.supplier_name}
                  onChange={(e) => setForm((p) => ({ ...p, supplier_name: e.target.value }))}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="text-xs text-gray-500 uppercase tracking-wide block mb-1">Invoice Date</label>
                <input
                  type="date"
                  value={form.invoice_date}
                  onChange={(e) => setForm((p) => ({ ...p, invoice_date: e.target.value }))}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            {/* Line items */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="text-xs text-gray-500 uppercase tracking-wide">Line Items</label>
                <button
                  onClick={addRow}
                  className="text-xs text-blue-600 hover:text-blue-800 font-medium"
                >
                  + Add Row
                </button>
              </div>
              <div className="overflow-x-auto rounded-lg border border-gray-200">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="bg-gray-50 border-b border-gray-200 text-gray-500 font-medium text-xs">
                      <th className="text-left px-3 py-2">Product Name</th>
                      <th className="text-right px-3 py-2 w-20">Qty</th>
                      <th className="text-right px-3 py-2 w-28">Unit Price</th>
                      <th className="text-right px-3 py-2 w-28">Total</th>
                      <th className="px-3 py-2 w-8" />
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {form.line_items.map((it, idx) => (
                      <tr key={idx}>
                        <td className="px-3 py-2">
                          <input
                            type="text"
                            value={it.name}
                            onChange={(e) => updateItem(idx, 'name', e.target.value)}
                            className="w-full border-0 bg-transparent focus:outline-none focus:ring-1 focus:ring-blue-400 rounded px-1"
                            placeholder="Product name"
                          />
                        </td>
                        <td className="px-3 py-2">
                          <input
                            type="number"
                            value={it.qty}
                            onChange={(e) => updateItem(idx, 'qty', e.target.value)}
                            className="w-full text-right border-0 bg-transparent focus:outline-none focus:ring-1 focus:ring-blue-400 rounded px-1"
                            min="0"
                          />
                        </td>
                        <td className="px-3 py-2">
                          <input
                            type="number"
                            value={it.unit_price}
                            onChange={(e) => updateItem(idx, 'unit_price', e.target.value)}
                            className="w-full text-right border-0 bg-transparent focus:outline-none focus:ring-1 focus:ring-blue-400 rounded px-1"
                            min="0"
                            step="0.01"
                          />
                        </td>
                        <td className="px-3 py-2 text-right text-gray-600">
                          ₹{(parseFloat(it.qty) * parseFloat(it.unit_price) || 0).toFixed(2)}
                        </td>
                        <td className="px-3 py-2 text-center">
                          <button
                            onClick={() => removeRow(idx)}
                            className="text-red-400 hover:text-red-600 text-xs"
                          >
                            ✕
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Grand total */}
            <div className="flex justify-end">
              <div className="bg-gray-50 rounded-lg px-5 py-3 text-right">
                <p className="text-xs text-gray-500 uppercase tracking-wide">Grand Total</p>
                <p className="text-xl font-bold text-gray-800 mt-0.5">₹{grandTotal.toFixed(2)}</p>
              </div>
            </div>

            {/* Confirm button */}
            <button
              onClick={handleConfirm}
              disabled={confirming}
              className="w-full bg-green-600 text-white py-3 rounded-xl font-medium hover:bg-green-700 transition disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {confirming ? (
                <>
                  <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/>
                  </svg>
                  Updating stock…
                </>
              ) : (
                '✅ Confirm & Update Stock'
              )}
            </button>
          </div>
        )}

        {/* Success result */}
        {result && (
          <div className="bg-white rounded-xl border border-gray-200 p-6 space-y-4">
            <div className="flex items-center gap-3">
              <span className="text-3xl">✅</span>
              <div>
                <h2 className="text-lg font-semibold text-gray-800">Invoice Confirmed</h2>
                <p className="text-sm text-gray-500">Stock has been updated</p>
              </div>
            </div>

            {result.updated_products.length > 0 && (
              <div>
                <p className="text-xs text-gray-500 uppercase tracking-wide mb-2">Updated Products</p>
                <div className="space-y-1">
                  {result.updated_products.map((p, i) => (
                    <div key={i} className="flex items-center justify-between bg-green-50 rounded-lg px-4 py-2 text-sm">
                      <span className="text-gray-800 font-medium">{p.name}</span>
                      <span className="text-green-700 font-semibold">+{p.added_qty} units</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {result.not_found.length > 0 && (
              <div>
                <p className="text-xs text-gray-500 uppercase tracking-wide mb-2">Products Not Found (skipped)</p>
                <div className="space-y-1">
                  {result.not_found.map((name, i) => (
                    <div key={i} className="bg-amber-50 rounded-lg px-4 py-2 text-sm text-amber-700">
                      {name}
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="flex gap-3 pt-2">
              <button
                onClick={() => navigate('/invoices')}
                className="flex-1 bg-blue-600 text-white py-2 rounded-lg text-sm font-medium hover:bg-blue-700 transition"
              >
                View All Invoices
              </button>
              <button
                onClick={() => { setFile(null); setForm(null); setResult(null); setInvoiceId(null) }}
                className="flex-1 border border-gray-300 text-gray-600 py-2 rounded-lg text-sm font-medium hover:bg-gray-50 transition"
              >
                Upload Another
              </button>
            </div>
          </div>
        )}
      </div>
    </Layout>
  )
}
