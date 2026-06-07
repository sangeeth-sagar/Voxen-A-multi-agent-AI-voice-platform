import { ref } from 'vue'

const apiKeys = ref([])

export function useApiKeys() {
  async function fetchKeys() {
    try {
      const res = await fetch(`${import.meta.env.VITE_API_URL}/api/v1/keys/`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      })
      if (res.status === 401) {
        localStorage.removeItem('token')
        localStorage.removeItem('user')
        window.location.href = '/login'
        return
      }
      if (!res.ok) throw new Error('Failed to fetch API keys')
      apiKeys.value = await res.json()
    } catch (e) {
      apiKeys.value = []
      console.error('fetchKeys:', e)
    }
  }

  async function addApiKey({ provider, label, api_key }) {
    const res = await fetch(`${import.meta.env.VITE_API_URL}/api/v1/keys/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${localStorage.getItem('token')}`
      },
      body: JSON.stringify({ provider, label, api_key })
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to add key' }))
      throw new Error(err.detail || 'Failed to add key')
    }
    return res.json()
  }

  async function deleteApiKey(id) {
    const res = await fetch(`${import.meta.env.VITE_API_URL}/api/v1/keys/${id}`, {
      method: 'DELETE',
      headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
    })
    if (!res.ok && res.status !== 204) {
      const err = await res.json().catch(() => ({ detail: 'Failed to delete key' }))
      throw new Error(err.detail || 'Failed to delete key')
    }
  }

  return { apiKeys, fetchKeys, addApiKey, deleteApiKey }
}
