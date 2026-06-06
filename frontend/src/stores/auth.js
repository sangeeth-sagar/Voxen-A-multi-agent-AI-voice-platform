import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { apiFetch } from '@/composables/useApi'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || null)
  const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))

  const isLoggedIn = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.role === 'admin')

  function setAuth(accessToken, userData) {
    token.value = accessToken
    user.value = userData
    localStorage.setItem('token', accessToken)
    localStorage.setItem('user', JSON.stringify(userData))
  }

  function logout() {
    token.value = null
    user.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  }

  function authHeaders() {
    return token.value ? { Authorization: `Bearer ${token.value}` } : {}
  }

  async function fetchFreshUser() {
    if (!token.value) return
    try {
      const data = await apiFetch('/api/v1/auth/me')
      user.value = data
      localStorage.setItem('user', JSON.stringify(data))
    } catch(e) {
      // silently fail
    }
  }

  return { token, user, isLoggedIn, isAdmin, setAuth, logout, authHeaders, fetchFreshUser }
})
