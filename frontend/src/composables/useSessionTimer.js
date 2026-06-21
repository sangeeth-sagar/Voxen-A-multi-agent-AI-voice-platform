import { ref } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'

const IDLE_TIMEOUT_MS = 10 * 60 * 1000        // 10 minutes
const REFRESH_BEFORE_EXPIRY_MS = 60 * 1000     // refresh 1 min before token expires
const TOKEN_LIFETIME_MS = 10 * 60 * 1000       // matches backend jwt_expire_minutes

let idleTimer = null
let refreshTimer = null
let lastActivityTime = Date.now()

const isSessionActive = ref(true)

export function useSessionTimer() {
  const auth = useAuthStore()
  const router = useRouter()

  function resetIdleTimer() {
    lastActivityTime = Date.now()
    clearTimeout(idleTimer)
    if (!auth.isLoggedIn) return

    idleTimer = setTimeout(() => {
      handleIdleLogout()
    }, IDLE_TIMEOUT_MS)
  }

  function handleIdleLogout() {
    isSessionActive.value = false
    auth.logout()
    clearTimeout(refreshTimer)
    router.push('/login?reason=idle_timeout')
  }

  async function scheduleTokenRefresh() {
    clearTimeout(refreshTimer)
    if (!auth.isLoggedIn) return

    refreshTimer = setTimeout(async () => {
      const idleDuration = Date.now() - lastActivityTime
      if (idleDuration >= IDLE_TIMEOUT_MS) {
        handleIdleLogout()
        return
      }

      try {
        const refreshToken = localStorage.getItem('refresh_token')
        if (!refreshToken) {
          handleIdleLogout()
          return
        }
        const res = await fetch('/api/v1/auth/refresh', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ refresh_token: refreshToken }),
        })
        if (!res.ok) throw new Error('Refresh failed')
        const data = await res.json()
        auth.setTokens(data.access_token, data.refresh_token)
        scheduleTokenRefresh()
      } catch {
        handleIdleLogout()
      }
    }, TOKEN_LIFETIME_MS - REFRESH_BEFORE_EXPIRY_MS)
  }

  function startSessionTracking() {
    resetIdleTimer()
    scheduleTokenRefresh()

    const activityEvents = ['mousedown', 'keydown', 'scroll', 'touchstart']
    activityEvents.forEach(evt =>
      window.addEventListener(evt, resetIdleTimer, { passive: true })
    )
  }

  function stopSessionTracking() {
    clearTimeout(idleTimer)
    clearTimeout(refreshTimer)
    const activityEvents = ['mousedown', 'keydown', 'scroll', 'touchstart']
    activityEvents.forEach(evt =>
      window.removeEventListener(evt, resetIdleTimer)
    )
  }

  return {
    isSessionActive,
    startSessionTracking,
    stopSessionTracking,
    resetIdleTimer,
  }
}
