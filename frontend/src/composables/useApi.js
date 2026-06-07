import { useAuthStore } from '@/stores/auth'

const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export async function apiFetch(path, options = {}) {
  const auth = useAuthStore()
  const res = await fetch(`${BASE}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...auth.authHeaders(),
      ...(options.headers || {}),
    },
  })

  if (res.status === 401) {
    const isAuthEndpoint = path.includes('/auth/me') || path.includes('/auth/login')
    if (isAuthEndpoint) {
      auth.logout()
      window.location.href = '/login'
    }
    throw new Error('Unauthorized')
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || `Request failed: ${res.status}`)
  }

  if (res.status === 204) return null
  return res.json()
}

export async function apiFetchBlob(path, options = {}) {
  const auth = useAuthStore()
  const res = await fetch(`${BASE}${path}`, {
    ...options,
    headers: {
      ...auth.authHeaders(),
      ...(options.headers || {}),
    },
  })
  if (res.status === 401) {
    const isAuthEndpoint = path.includes('/auth/me') || path.includes('/auth/login')
    if (isAuthEndpoint) {
      auth.logout()
      window.location.href = '/login'
    }
    throw new Error('Unauthorized')
  }
  if (!res.ok) throw new Error('Audio fetch failed')
  return res.blob()
}
