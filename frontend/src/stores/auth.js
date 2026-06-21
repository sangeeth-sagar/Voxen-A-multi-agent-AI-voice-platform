import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { apiFetch } from '@/composables/useApi'

// Safe JSON parse — never throws, returns null on any failure
function safeParseUser() {
  try {
    const raw = localStorage.getItem('user')
    if (!raw || raw === 'undefined' || raw === 'null') return null
    return JSON.parse(raw)
  } catch {
    localStorage.removeItem('user')  // remove corrupted value
    return null
  }
}

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || null)
  const refreshToken = ref(localStorage.getItem('refresh_token') || null)
  const user = ref(safeParseUser())

  const isLoggedIn = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.role === 'admin' || user.value?.is_superadmin === true)
  const isSuperadmin = computed(() => user.value?.is_superadmin === true)

  function setAuth(accessToken, userData, newRefreshToken = null) {
    token.value = accessToken
    user.value = userData
    localStorage.setItem('token', accessToken)
    if (newRefreshToken) {
      refreshToken.value = newRefreshToken
      localStorage.setItem('refresh_token', newRefreshToken)
    }
    if (userData && typeof userData === 'object') {
      localStorage.setItem('user', JSON.stringify(userData))
    } else {
      localStorage.removeItem('user')
    }
  }

  function setTokens(accessToken, newRefreshToken) {
    token.value = accessToken
    refreshToken.value = newRefreshToken
    localStorage.setItem('token', accessToken)
    localStorage.setItem('refresh_token', newRefreshToken)
  }

  function logout() {
    token.value = null
    refreshToken.value = null
    user.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user')
  }

  function authHeaders() {
    return token.value ? { Authorization: `Bearer ${token.value}` } : {}
  }

  async function fetchFreshUser() {
    if (!token.value) return
    try {
      const data = await apiFetch('/api/v1/auth/me')
      if (data && typeof data === 'object') {
        user.value = data
        localStorage.setItem('user', JSON.stringify(data))
      }
    } catch {
      // silently fail
    }
  }

  return {
    token, refreshToken, user,
    isLoggedIn, isAdmin, isSuperadmin,
    setAuth, setTokens, logout, authHeaders, fetchFreshUser
  }
})
