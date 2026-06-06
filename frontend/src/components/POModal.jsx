import { useEffect, useState } from 'react'
import { useForm, useFieldArray, Controller } from 'react-hook-form'
import { createPurchaseOrder, updatePurchaseOrder } from '../api/purchaseOrders'
import { getSuppliers } from '../api/suppliers'
import { getProducts } from '../api/products'
import toast from 'react-hot-toast'

export default function POModal({ po, onClose }) {
  const isEdit = !!po
  const isDraft = !po || po.status === 'Draft'

  const [suppliers, setSuppliers] = useState([])
  const [products, setProducts] = useState([])
  const [loadingData, setLoadingData] = useState(true)

  const {
    register,
    control,
    handleSubmit,
    watch,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm({
    defaultValues: isEdit
      ? {
          supplier_id: String(po.supplier_id),
          notes: po.notes || '',
          line_items: po.line_items.map((li) => ({
            product_id: String(li.product_id),
            quantity: li.quantity,
            unit_price: li.unit_price,
          })),
        }
      : {
          supplier_id: '',
          notes: '',
          line_items: [{ product_id: '', quantity: 1, unit_price: 0 }],
        },
  })

  const { fields, append, remove } = useFieldArray({ control, name: 'line_items' })
  const lineItems = watch('line_items') || []
  const grandTotal = lineItems.reduce(
    (sum, item) =>
      sum + (parseFloat(item.quantity) || 0) * (parseFloat(item.unit_price) || 0),
    0
  )

  useEffect(() => {
    Promise.all([getSuppliers(), getProducts()])
      .then(([s, p]) => {
        setSuppliers(s)
        setProducts(p)
      })
      .catch(() => toast.error('Failed to load form data'))
      .finally(() => setLoadingData(false))
  }, [])

  const handleProductChange = (index, productId) => {
    const product = products.find((p) => p.id === parseInt(productId, 10))
    if (product) setValue(`line_items.${index}.unit_price`, product.unit_price)
  }

  const onSubmit = async (data) => {
    try {
      const payload = {
        supplier_id: parseInt(data.supplier_id, 10),
        notes: data.notes || null,
        line_items: data.line_items.map((li) => ({
          product_id: parseInt(li.product_id, 10),
          quantity: parseInt(li.quantity, 10),
          unit_price: parseFloat(li.unit_price),
        })),
      }
      if (isEdit) {
        await updatePurchaseOrder(po.id, payload)
        toast.success('Purchase order updated')
      } else {
        await createPurchaseOrder(payload)
        toast.success('Purchase order created')
      }
      onClose(true)
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Something went wrong')
    }
  }

  if (loadingData) {
    return (
      <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
        <div className="bg-white rounded-xl p-8 text-gray-400 text-sm">Loading…</div>
      </div>
    )
  }

  return (
    <div className="fixed inset-0 bg-black/40 flex items-start justify-center z-50 py-8 overflow-y-auto">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-2xl mx-4 p-6">
        <div className="flex justify-between items-start mb-4">
          <h2 className="text-lg font-bold text-gray-800">
            {isEdit ? `PO-${String(po.id).padStart(4, '0')}` : 'New Purchase Order'}
          </h2>
          {isEdit && !isDraft && (
            <span className="text-xs bg-amber-50 text-amber-700 px-2 py-1 rounded-full font-medium">
              {po.status} — view only
            </span>
          )}
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
          {/* Supplier + Notes */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Supplier *</label>
              <select
                {...register('supplier_id', { required: 'Required' })}
                disabled={!isDraft}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-50 disabled:text-gray-400"
              >
                <option value="">Select supplier…</option>
                {suppliers.map((s) => (
                  <option key={s.id} value={s.id}>{s.name}</option>
                ))}
              </select>
              {errors.supplier_id && (
                <p className="text-red-500 text-xs mt-1">{errors.supplier_id.message}</p>
              )}
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Notes</label>
              <input
                {...register('notes')}
                disabled={!isDraft}
                placeholder="Optional notes…"
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-50 disabled:text-gray-400"
              />
            </div>
          </div>

          {/* Line Items */}
          <div>
            <div className="flex justify-between items-center mb-2">
              <span className="text-xs font-medium text-gray-600">Line Items</span>
              {isDraft && (
                <button
                  type="button"
                  onClick={() => append({ product_id: '', quantity: 1, unit_price: 0 })}
                  className="text-xs text-blue-600 hover:text-blue-800 font-medium"
                >
                  + Add item
                </button>
              )}
            </div>

            <div className="border border-gray-200 rounded-lg overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-gray-50 border-b border-gray-200 text-gray-500 text-xs font-medium">
                    <th className="text-left px-3 py-2">Product</th>
                    <th className="text-right px-3 py-2 w-20">Qty</th>
                    <th className="text-right px-3 py-2 w-28">Unit Price</th>
                    <th className="text-right px-3 py-2 w-24">Line Total</th>
                    {isDraft && <th className="w-8" />}
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {fields.map((field, index) => {
                    const qty = parseFloat(lineItems[index]?.quantity) || 0
                    const price = parseFloat(lineItems[index]?.unit_price) || 0
                    return (
                      <tr key={field.id}>
                        <td className="px-3 py-2">
                          <Controller
                            control={control}
                            name={`line_items.${index}.product_id`}
                            rules={{ required: true }}
                            render={({ field: f }) => (
                              <select
                                {...f}
                                disabled={!isDraft}
                                onChange={(e) => {
                                  f.onChange(e)
                                  handleProductChange(index, e.target.value)
                                }}
                                className="w-full border border-gray-200 rounded px-2 py-1 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500 disabled:bg-gray-50"
                              >
                                <option value="">Select…</option>
                                {products.map((p) => (
                                  <option key={p.id} value={p.id}>
                                    {p.name} ({p.sku})
                                  </option>
                                ))}
                              </select>
                            )}
                          />
                        </td>
                        <td className="px-3 py-2">
                          <input
                            type="number"
                            min="1"
                            disabled={!isDraft}
                            {...register(`line_items.${index}.quantity`, {
                              required: true,
                              min: 1,
                            })}
                            className="w-full border border-gray-200 rounded px-2 py-1 text-sm text-right focus:outline-none focus:ring-1 focus:ring-blue-500 disabled:bg-gray-50"
                          />
                        </td>
                        <td className="px-3 py-2">
                          <input
                            type="number"
                            step="0.01"
                            min="0"
                            disabled={!isDraft}
                            {...register(`line_items.${index}.unit_price`, {
                              required: true,
                              min: 0,
                            })}
                            className="w-full border border-gray-200 rounded px-2 py-1 text-sm text-right focus:outline-none focus:ring-1 focus:ring-blue-500 disabled:bg-gray-50"
                          />
                        </td>
                        <td className="px-3 py-2 text-right text-gray-600 text-sm font-medium">
                          ₹{(qty * price).toFixed(2)}
                        </td>
                        {isDraft && (
                          <td className="px-2 py-2 text-center">
                            {fields.length > 1 && (
                              <button
                                type="button"
                                onClick={() => remove(index)}
                                className="text-red-400 hover:text-red-600 text-xs font-bold"
                              >
                                ✕
                              </button>
                            )}
                          </td>
                        )}
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>

            <div className="flex justify-end mt-2 pr-1">
              <span className="text-sm font-semibold text-gray-700">
                Grand Total:{' '}
                <span className="text-blue-600">₹{grandTotal.toFixed(2)}</span>
              </span>
            </div>
          </div>

          {/* Actions */}
          <div className="flex gap-3 pt-1">
            <button
              type="button"
              onClick={() => onClose(false)}
              className="flex-1 border border-gray-300 text-gray-700 py-2 rounded-lg text-sm font-medium hover:bg-gray-50 transition"
            >
              {isDraft ? 'Cancel' : 'Close'}
            </button>
            {isDraft && (
              <button
                type="submit"
                disabled={isSubmitting}
                className="flex-1 bg-blue-600 text-white py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50 transition"
              >
                {isSubmitting ? 'Saving…' : isEdit ? 'Save Changes' : 'Create Order'}
              </button>
            )}
          </div>
        </form>
      </div>
    </div>
  )
}
