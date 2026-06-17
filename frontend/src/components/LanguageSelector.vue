<template>
  <div class="language-selector">
    <div class="lang-label">
      <span class="material-symbols-outlined">language</span>
      <span>Language</span>
    </div>

    <div class="lang-options">
      <button
        v-for="lang in LANGUAGES" :key="lang.code"
        :class="['lang-btn', { active: selectedLanguage === lang.code }]"
        @click="handleSelect(lang.code)" :title="lang.label"
      >
        <span class="flag">{{ lang.flag }}</span>
        <span class="native">{{ lang.native }}</span>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useLanguage } from '@/composables/useLanguage'

const emit = defineEmits(['change'])
const { LANGUAGES, selectedLanguage, setLanguage, voiceStatus } = useLanguage()
const sttStatus = ref({})

onMounted(async () => {
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition
  if (!SR) { sttStatus.value = { en: 'unsupported', hi: 'unsupported', mr: 'unsupported', ml: 'unsupported' }; return }
  const KNOWN_UNSUPPORTED_WINDOWS = ['mr-IN', 'ml-IN']
  const localeMap = { en: 'en-GB', hi: 'hi-IN', mr: 'mr-IN', ml: 'ml-IN' }
  const next = {}
  for (const [code, locale] of Object.entries(localeMap)) {
    next[code] = KNOWN_UNSUPPORTED_WINDOWS.includes(locale) ? 'unsupported' : 'supported'
  }
  sttStatus.value = next
})

function handleSelect(code) { setLanguage(code); emit('change', code) }
</script>

<style scoped>
.language-selector { display: flex; align-items: center; gap: 12px; }

.lang-label {
  display: flex; align-items: center; gap: 4px; font-size: 11px;
  font-family: monospace; text-transform: uppercase; letter-spacing: 0.1em;
  color: var(--color-on-surface-variant); opacity: 0.7;
}

.lang-options { display: flex; gap: 6px; }

.lang-btn {
  display: flex; align-items: center; gap: 5px; padding: 5px 12px;
  border-radius: 999px; border: 1px solid var(--color-outline-variant);
  background: var(--color-surface-container); color: #012d1d;
  font-size: 11px; cursor: pointer; transition: all 0.2s ease;
}

html.dark .lang-btn { background: rgba(255, 255, 255, 0.04); border-color: rgba(255, 255, 255, 0.1); color: #beedd9; }

.lang-btn:hover { border-color: var(--color-primary); color: var(--color-on-surface); }
html.dark .lang-btn:hover { border-color: rgba(165, 209, 170, 0.4); color: rgba(255, 255, 255, 0.8); }

.lang-btn.active { border-color: #0e6c4a; background: #0e6c4a; color: #ffffff !important; font-weight: 600; }
html.dark .lang-btn.active { border-color: #a5d1aa; background: rgba(165, 209, 170, 0.25); color: #ffffff !important; }

.flag { font-size: 14px; }
.native { font-size: 11px; }

.voice-badge { font-size: 9px; padding: 1px 5px; border-radius: 4px; font-family: monospace; text-transform: uppercase; letter-spacing: 0.04em; }
.voice-badge.native { background: var(--color-success-container, rgba(14, 108, 74, 0.15)); color: var(--color-success); border: 1px solid var(--color-success); }
.voice-badge.fallback { background: rgba(251, 191, 36, 0.15); color: #fbbf24; border: 1px solid rgba(251, 191, 36, 0.3); }
.voice-badge.unsupported { background: var(--color-error-container); color: var(--color-error); border: 1px solid var(--color-error); }
</style>
