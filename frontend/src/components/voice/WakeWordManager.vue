<template>
  <div aria-hidden="true"></div>
</template>

<script setup>
import { onMounted, onUnmounted, watch } from 'vue'
import { useWakeWord } from '@/composables/useWakeWord'
import { useVoiceAgentStore } from '@/stores/voiceAgent'
import { useAuthStore } from '@/stores/auth'
import { apiFetch } from '@/composables/useApi'

const { startDetection, stopDetection } = useWakeWord()
const voiceAgentStore = useVoiceAgentStore()
const authStore = useAuthStore()

let cleanupFunction = null

const startWakeWordDetection = async () => {
  if (!authStore.isLoggedIn) return
  
  try {
    // Fetch user's active agents
    const response = await apiFetch('/api/v1/agents')
    const activeAgents = response.filter(agent => agent.is_active === true)
    
    if (activeAgents.length > 0) {
      startDetection(activeAgents)
      cleanupFunction = () => stopDetection()
    }
  } catch (error) {
    console.error('Failed to fetch agents for wake word detection:', error)
  }
}

const stopWakeWordDetection = () => {
  if (cleanupFunction) {
    cleanupFunction()
    cleanupFunction = null
  }
}

const handleAuthChange = (isLoggedIn) => {
  if (isLoggedIn) {
    startWakeWordDetection()
  } else {
    stopWakeWordDetection()
  }
}

onMounted(() => {
  // Start detection if already logged in
  if (authStore.isLoggedIn) {
    startWakeWordDetection()
  }
  
  // Watch for auth changes
  watch(() => authStore.isLoggedIn, handleAuthChange)
})

onUnmounted(() => {
  stopWakeWordDetection()
})
</script>

<style scoped>
/* No visible UI */
</style>