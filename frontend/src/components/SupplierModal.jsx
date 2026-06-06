import { useForm } from 'react-hook-form'
import { createSupplier, updateSupplier } from '../api/suppliers'
import toast from 'react-hot-toast'

export default function SupplierModal({ supplier, onClose }) {
  const isEdit = !!supplier

  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm({
    defaultValues: isEdit
      ? {
          name: supplier.name,
          email: supplier.email,
          categories: supplier.categories.join(', '),
          lead_time_days: supplier.lead_time_days,
        }
      : { lead_time_days: 3, categories: '' },
  })

  const onSubmit = async (data) => {
    try {
      const payload = {
        ...data,
        lead_time_days: parseInt(data.lead_time_days, 10),
        categories: data.categories
          ? data.categories.split(',').map((s) => s.trim()).filter(Boolean)
          : [],
      }
      if (isEdit) {
        await updateSupplier(supplier.id, payload)
        toast.success('Supplier updated')
      } else {
        await createSupplier(payload)
        toast.success('Supplier added')
      }
      onClose(true)
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Something went wrong')
    }
  }

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-6">
        <h2 className="text-lg font-bold text-gray-800 mb-4">
          {isEdit ? 'Edit Supplier' : 'Add Supplier'}
        </h2>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Name *</label>
            <input
              {...register('name', { required: 'Required' })}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            {errors.name && <p className="text-red-500 text-xs mt-1">{errors.name.message}</p>}
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Email *</label>
            <input
              type="email"
              {...register('email', {
                required: 'Required',
                pattern: { value: /^\S+@\S+\.\S+$/, message: 'Invalid email' },
              })}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            {errors.email && <p className="text-red-500 text-xs mt-1">{errors.email.message}</p>}
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">
              Categories
              <span className="ml-1 font-normal text-gray-400">(comma-separated)</span>
            </label>
            <input
              {...register('categories')}
              placeholder="e.g. Dairy, Grains, Produce"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Lead Time (days)</label>
            <input
              type="number"
              min="1"
              {...register('lead_time_days', { min: { value: 1, message: 'Must be ≥ 1' } })}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            {errors.lead_time_days && (
              <p className="text-red-500 text-xs mt-1">{errors.lead_time_days.message}</p>
            )}
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
              {isSubmitting ? 'Saving…' : isEdit ? 'Save Changes' : 'Add Supplier'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
