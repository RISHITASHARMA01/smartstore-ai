import api from './axios'

export const getSuppliers = (params = {}) =>
  api.get('/suppliers', { params }).then((r) => r.data)

export const getSupplier = (id) =>
  api.get(`/suppliers/${id}`).then((r) => r.data)

export const createSupplier = (data) =>
  api.post('/suppliers', data).then((r) => r.data)

export const updateSupplier = (id, data) =>
  api.put(`/suppliers/${id}`, data).then((r) => r.data)

export const deleteSupplier = (id) =>
  api.delete(`/suppliers/${id}`)
