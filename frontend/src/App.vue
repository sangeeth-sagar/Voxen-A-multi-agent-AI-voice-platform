<template>
  <RouterView />
  <ToastContainer />
</template>

<script setup>
import { RouterView } from 'vue-router'
import { onMounted } from 'vue'
import { useLanguage } from '@/composables/useLanguage'
import ToastContainer from '@/components/ui/ToastContainer.vue'

const { setLanguage, detectVoiceStatus } = useLanguage()

onMounted(() => {
  const saved = localStorage.getItem('agentiq_language')
  if (saved) setLanguage(saved)

  if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
    detectVoiceStatus()
    window.speechSynthesis.addEventListener?.('voiceschanged', detectVoiceStatus)
  }
})
</script>
