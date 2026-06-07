import api from './axios'

export const getProducts = (params = {}, signal) =>
  api.get('/products', { params, signal }).then((r) => r.data)

export const getProduct = (id, signal) =>
  api.get(`/products/${id}`, { signal }).then((r) => r.data)

export const createProduct = (data) =>
  api.post('/products', data).then((r) => r.data)

export const updateProduct = (id, data) =>
  api.put(`/products/${id}`, data).then((r) => r.data)

export const deleteProduct = (id) =>
  api.delete(`/products/${id}`)
