import api from './axios'

export const getUsers = (params = {}, signal) =>
  api.get('/admin/users', { params, signal }).then((r) => r.data)

export const getUser = (id, signal) =>
  api.get(`/admin/users/${id}`, { signal }).then((r) => r.data)

export const updateUser = (id, data) =>
  api.patch(`/admin/users/${id}`, data).then((r) => r.data)
