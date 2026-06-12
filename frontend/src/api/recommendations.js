import api from './axios'

export const getRecommendations = (productId = null) =>
  api.post('/recommendations', { product_id: productId }).then((r) => r.data)
