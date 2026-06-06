import { useForm } from 'react-hook-form'
import { createProduct, updateProduct } from '../api/products'
import toast from 'react-hot-toast'

export default function ProductModal({ product, onClose }) {
  const isEdit = !!product

  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm({
    defaultValues: isEdit
      ? {
          sku: product.sku,
          name: product.name,
          category: product.category,
          stock_qty: product.stock_qty,
          unit_price: product.unit_price,
          reorder_threshold: product.reorder_threshold,
          expiry_date: product.expiry_date
            ? new Date(product.expiry_date).toISOString().split('T')[0]
            : '',
        }
      : { stock_qty: 0, reorder_threshold: 10 },
  })

  const onSubmit = async (data) => {
    try {
      const payload = {
        ...data,
        stock_qty: parseInt(data.stock_qty, 10),
        unit_price: parseFloat(data.unit_price),
        reorder_threshold: parseInt(data.reorder_threshold, 10),
        expiry_date: data.expiry_date || null,
      }
      if (isEdit) {
        const { sku, ...updatePayload } = payload
        await updateProduct(product.id, updatePayload)
        toast.success('Product updated')
      } else {
        await createProduct(payload)
        toast.success('Product created')
      }
      onClose(true)
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Something went wrong')
    }
  }

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-lg p-6">
        <h2 className="text-lg font-bold text-gray-800 mb-4">
          {isEdit ? 'Edit Product' : 'Add Product'}
        </h2>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">SKU *</label>
              <input
                {...register('sku', { required: 'Required' })}
                disabled={isEdit}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-50 disabled:text-gray-400"
              />
              {errors.sku && <p className="text-red-500 text-xs mt-1">{errors.sku.message}</p>}
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Name *</label>
              <input
                {...register('name', { required: 'Required' })}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              {errors.name && <p className="text-red-500 text-xs mt-1">{errors.name.message}</p>}
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Category *</label>
              <input
                {...register('category', { required: 'Required' })}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              {errors.category && <p className="text-red-500 text-xs mt-1">{errors.category.message}</p>}
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Unit Price (₹) *</label>
              <input
                type="number"
                step="0.01"
                min="0"
                {...register('unit_price', { required: 'Required', min: { value: 0, message: 'Must be ≥ 0' } })}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              {errors.unit_price && <p className="text-red-500 text-xs mt-1">{errors.unit_price.message}</p>}
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Stock Qty</label>
              <input
                type="number"
                min="0"
                {...register('stock_qty', { min: 0 })}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Reorder Threshold</label>
              <input
                type="number"
                min="0"
                {...register('reorder_threshold', { min: 0 })}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div className="col-span-2">
              <label className="block text-xs font-medium text-gray-600 mb-1">Expiry Date</label>
              <input
                type="date"
                {...register('expiry_date')}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={() => onClose(false)}
              className="flex-1 border border-gray-300 text-gray-700 py-2 rounded-lg text-sm font-medium hover:bg-gray-50 transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="flex-1 bg-blue-600 text-white py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50 transition"
            >
              {isSubmitting ? 'Saving...' : isEdit ? 'Save Changes' : 'Create Product'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
