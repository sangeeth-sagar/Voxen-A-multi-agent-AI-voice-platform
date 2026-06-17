import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'

const STORAGE_KEY = 'agentiq_theme'

export const useThemeStore = defineStore('theme', () => {
  // 'light' | 'dark' | 'system'
  const themePreference = ref(localStorage.getItem(STORAGE_KEY) || 'dark')

  const systemPrefersDark = ref(
    window.matchMedia?.('(prefers-color-scheme: dark)').matches ?? true
  )

  const isDark = computed(() => {
    if (themePreference.value === 'system') {
      return systemPrefersDark.value
    }
    return themePreference.value === 'dark'
  })

  function applyTheme() {
    const html = document.documentElement
    if (isDark.value) {
      html.classList.add('dark')
    } else {
      html.classList.remove('dark')
    }
  }

  function setTheme(preference) {
    themePreference.value = preference
    localStorage.setItem(STORAGE_KEY, preference)
    applyTheme()
  }

  function toggleTheme() {
    if (isDark.value) {
      setTheme('light')
    } else {
      setTheme('dark')
    }
  }

  // Listen for system preference changes
  if (window.matchMedia) {
    const mq = window.matchMedia('(prefers-color-scheme: dark)')
    mq.addEventListener('change', (e) => {
      systemPrefersDark.value = e.matches
      if (themePreference.value === 'system') {
        applyTheme()
      }
    })
  }

  // Apply on store initialization
  applyTheme()

  return {
    themePreference,
    isDark,
    setTheme,
    toggleTheme,
    applyTheme,
  }
})
