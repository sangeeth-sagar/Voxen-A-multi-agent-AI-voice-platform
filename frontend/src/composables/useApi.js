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
    auth.logout()
    window.location.href = '/login'
    return
  }
  if (res.status === 422) {
    throw new Error('422: Request format error: check that all required fields (text, agent_uuid, language) are present in the request body.')
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Unknown error' }))
    throw new Error(err.detail || 'Request failed')
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
    auth.logout()
    window.location.href = '/login'
    return
  }
  if (!res.ok) throw new Error('Audio fetch failed')
  return res.blob()
}
