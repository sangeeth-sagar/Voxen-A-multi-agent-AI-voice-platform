<template>
  <main>
    <RouterView />
  </main>
  <ToastContainer />
</template>

<script setup>
import { RouterView, useRoute } from 'vue-router'
import { onMounted, watch } from 'vue'
import { useLanguage } from '@/composables/useLanguage'
import { useAuthStore } from '@/stores/auth'
import { useSessionTimer } from '@/composables/useSessionTimer'
import { initThemeOnLoad } from '@/composables/useTheme'
import ToastContainer from '@/components/ui/ToastContainer.vue'

const route = useRoute()
const { setLanguage, detectVoiceStatus } = useLanguage()
const auth = useAuthStore()
const { startSessionTracking } = useSessionTimer()

// Synchronize theme on route changes (auth vs app routes)
watch(
  () => route.path,
  (newPath) => {
    initThemeOnLoad(newPath)
  }
)

onMounted(() => {
  initThemeOnLoad(route.path)

  const saved = localStorage.getItem('agentiq_language')
  if (saved) setLanguage(saved)

  if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
    detectVoiceStatus()
    window.speechSynthesis.addEventListener?.('voiceschanged', detectVoiceStatus)
  }

  if (auth.isLoggedIn) {
    startSessionTracking()
  }
})
</script>
