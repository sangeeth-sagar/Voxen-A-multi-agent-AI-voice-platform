import { ref } from 'vue'

const LANGUAGES = [
  { code: 'en', label: 'GB English',   native: 'GB English',  flag: '🇬🇧', stt: 'en-GB', tts: 'en-GB' },
  { code: 'hi', label: 'IN Hindi',     native: 'IN Hindi',    flag: '🇮🇳', stt: 'hi-IN', tts: 'hi-IN' },
  { code: 'mr', label: 'IN Marathi',   native: 'IN Marathi',  flag: '🇮🇳', stt: 'mr-IN', tts: 'mr-IN' },
  { code: 'ml', label: 'IN Malayalam', native: 'IN മലയാളം',   flag: '🇮🇳', stt: 'ml-IN', tts: 'ml-IN' },
]

const selectedLanguage = ref(localStorage.getItem('agentiq_language') || 'en')

// Per-language voice availability: 'native' | 'fallback' | undefined
// Populated by detectVoiceStatus()
const voiceStatus = ref({})

function setLanguage(code) {
  selectedLanguage.value = code
  localStorage.setItem('agentiq_language', code)
}

function getCurrentLanguage() {
  return LANGUAGES.find(l => l.code === selectedLanguage.value) || LANGUAGES[0]
}

function getSttLocale() {
  return getCurrentLanguage().stt
}

function getTtsLocale() {
  return getCurrentLanguage().tts
}

function detectVoiceStatus() {
  if (typeof window === 'undefined' || !('speechSynthesis' in window)) return
  const voices = window.speechSynthesis.getVoices()
  if (!voices || voices.length === 0) return

  const locales = { en: 'en-GB', hi: 'hi-IN', mr: 'mr-IN', ml: 'ml-IN' }
  const next = {}
  Object.entries(locales).forEach(([code, locale]) => {
    const hasVoice = voices.some(v =>
      v.lang === locale || v.lang.startsWith(locale.split('-')[0])
    )
    next[code] = hasVoice ? 'native' : 'fallback'
  })
  voiceStatus.value = next
}

export function useLanguage() {
  return {
    LANGUAGES,
    selectedLanguage,
    setLanguage,
    getCurrentLanguage,
    getSttLocale,
    getTtsLocale,
    voiceStatus,
    detectVoiceStatus
  }
}
