import api from './axios'

export const getPurchaseOrders = (params = {}) =>
  api.get('/purchase-orders', { params }).then((r) => r.data)

export const getPurchaseOrder = (id) =>
  api.get(`/purchase-orders/${id}`).then((r) => r.data)

export const createPurchaseOrder = (data) =>
  api.post('/purchase-orders', data).then((r) => r.data)

export const updatePurchaseOrder = (id, data) =>
  api.put(`/purchase-orders/${id}`, data).then((r) => r.data)

export const advanceStatus = (id) =>
  api.patch(`/purchase-orders/${id}/status`).then((r) => r.data)

export const deletePurchaseOrder = (id) =>
  api.delete(`/purchase-orders/${id}`)
