const token = () => localStorage.getItem('um_token')

const headers = () => ({
  'Content-Type': 'application/json',
  ...(token() ? { Authorization: `Bearer ${token()}` } : {}),
})

async function req(method, path, body) {
  const r = await fetch(path, { method, headers: headers(), body: body ? JSON.stringify(body) : undefined })
  if (r.status === 204) return null
  const data = await r.json()
  if (!r.ok) throw new Error(data.detail || r.statusText)
  return data
}

export const login    = (username, password) => req('POST', '/auth/login', { username, password })
export const getMe    = () => req('GET', '/auth/me')
export const listUsers   = () => req('GET', '/users')
export const createUser  = (body) => req('POST', '/users', body)
export const updateUser  = (id, body) => req('PUT', `/users/${id}`, body)
export const deleteUser  = (id) => req('DELETE', `/users/${id}`)
