<template>
  <RouterView />
</template>

<script setup>
import { RouterView } from 'vue-router'
import { onMounted } from 'vue'
import { useLanguage } from '@/composables/useLanguage'

const { setLanguage, detectVoiceStatus } = useLanguage()

onMounted(() => {
  const saved = localStorage.getItem('agentiq_language')
  if (saved) setLanguage(saved)

  // Detect which languages have native TTS voices installed.
  // Voices may load asynchronously on some browsers, so listen for the event.
  if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
    detectVoiceStatus()
    window.speechSynthesis.addEventListener?.('voiceschanged', detectVoiceStatus)
  }
})
</script>
