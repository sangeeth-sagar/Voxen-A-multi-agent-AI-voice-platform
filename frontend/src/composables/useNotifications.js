import { ref } from 'vue'
import { apiFetch } from '@/composables/useApi'

const notifications = ref([])
const count = ref(0)
const isPanelOpen = ref(false)

export function useNotifications() {
  async function fetchNotifications() {
    try {
      const data = await apiFetch('/api/v1/notifications')
      notifications.value = data.notifications || []
      count.value = data.count || 0
    } catch {
      notifications.value = []
      count.value = 0
    }
  }

  async function fetchCount() {
    try {
      const data = await apiFetch('/api/v1/notifications/count')
      count.value = data.count || 0
    } catch {
      count.value = 0
    }
  }

  async function openPanel() {
    isPanelOpen.value = true
    await fetchNotifications()
    count.value = 0
    try {
      await apiFetch('/api/v1/notifications/mark-seen', { method: 'POST' })
    } catch {
      // non-critical — badge will resync on next fetchCount() poll anyway
    }
  }

  function closePanel() {
    isPanelOpen.value = false
  }

  function togglePanel() {
    isPanelOpen.value ? closePanel() : openPanel()
  }

  return {
    notifications,
    count,
    isPanelOpen,
    fetchNotifications,
    fetchCount,
    openPanel,
    closePanel,
    togglePanel,
  }
}
