const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

export async function apiRequest(path, options = {}) {
  const token = localStorage.getItem('litnexus_token')
  const headers = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options.headers,
  }

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  })

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || 'API request failed')
  }
  return res.json()
}
