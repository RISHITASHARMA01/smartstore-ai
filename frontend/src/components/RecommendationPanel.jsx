import { useState, useCallback } from 'react'
import { getRecommendations } from '../api/recommendations'

const ACTION_STYLES = {
  restock:    'bg-blue-50 text-blue-700',
  promote:    'bg-green-50 text-green-700',
  monitor:    'bg-yellow-50 text-yellow-700',
  clearance:  'bg-orange-50 text-orange-700',
  'cross-sell': 'bg-purple-50 text-purple-700',
}

const PRIORITY_STYLES = {
  high:   'bg-red-50 text-red-600',
  medium: 'bg-amber-50 text-amber-600',
  low:    'bg-gray-100 text-gray-500',
}

export default function RecommendationPanel({ productId = null }) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const fetch = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const result = await getRecommendations(productId)
      setData(result)
    } catch {
      setError('Failed to get recommendations. Please try again.')
    } finally {
      setLoading(false)
    }
  }, [productId])

  if (!data && !loading) {
    return (
      <div className="flex flex-col items-center justify-center py-12 gap-3">
        <div className="text-4xl">✨</div>
        <p className="text-sm text-gray-500 text-center max-w-xs">
          Get AI-powered recommendations based on your current stock levels and sales velocity.
        </p>
        <button
          onClick={fetch}
          className="mt-2 bg-blue-600 text-white px-5 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 transition"
        >
          Get Recommendations
        </button>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-12 gap-3">
        <div className="w-6 h-6 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
        <p className="text-sm text-gray-400">Analysing your inventory…</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-12 gap-3">
        <p className="text-sm text-red-500">{error}</p>
        <button
          onClick={fetch}
          className="text-sm text-blue-600 hover:underline"
        >
          Retry
        </button>
      </div>
    )
  }

  const { recommendations = [], summary } = data

  return (
    <div className="space-y-4">
      {summary && (
        <div className="bg-blue-50 border border-blue-100 rounded-lg px-4 py-3 text-sm text-blue-800">
          {summary}
        </div>
      )}

      {recommendations.length === 0 ? (
        <p className="text-sm text-gray-400 text-center py-6">No recommendations at this time.</p>
      ) : (
        <div className="space-y-3">
          {recommendations.map((rec, i) => (
            <div key={i} className="border border-gray-200 rounded-lg p-4">
              <div className="flex items-start justify-between gap-3 mb-2">
                <p className="text-sm font-semibold text-gray-800">{rec.product_name}</p>
                <div className="flex gap-2 shrink-0">
                  <span className={`px-2 py-0.5 rounded-full text-xs font-medium capitalize ${ACTION_STYLES[rec.action] || 'bg-gray-100 text-gray-600'}`}>
                    {rec.action}
                  </span>
                  <span className={`px-2 py-0.5 rounded-full text-xs font-medium capitalize ${PRIORITY_STYLES[rec.priority] || 'bg-gray-100 text-gray-500'}`}>
                    {rec.priority}
                  </span>
                </div>
              </div>
              <p className="text-xs text-gray-500 leading-relaxed">{rec.reason}</p>
            </div>
          ))}
        </div>
      )}

      <div className="flex justify-end pt-1">
        <button
          onClick={fetch}
          className="text-xs text-blue-600 hover:underline"
        >
          Refresh recommendations
        </button>
      </div>
    </div>
  )
}
