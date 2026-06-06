<template>
  <div class="language-selector">
    <div class="lang-label">
      <span class="material-symbols-outlined">language</span>
      <span>Language</span>
    </div>

    <div class="lang-options">
      <button
        v-for="lang in LANGUAGES"
        :key="lang.code"
        :class="['lang-btn', { active: selectedLanguage === lang.code }]"
        @click="handleSelect(lang.code)"
        :title="lang.label"
      >
        <span class="flag">{{ lang.flag }}</span>
        <span class="native">{{ lang.native }}</span>
        <span
          v-if="voiceStatus[lang.code] === 'fallback'"
          class="voice-badge fallback"
          title="Native voice not available — using fallback voice"
        >
          ↩ fallback
        </span>
      </button>
    </div>
  </div>
</template>

<script setup>
import { useLanguage } from '@/composables/useLanguage'

const emit = defineEmits(['change'])

const { LANGUAGES, selectedLanguage, setLanguage, voiceStatus } = useLanguage()

function handleSelect(code) {
  setLanguage(code)
  emit('change', code)
}
</script>

<style scoped>
.language-selector {
  display: flex;
  align-items: center;
  gap: 12px;
}

.lang-label {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  font-family: monospace;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  opacity: 0.5;
}

.lang-options {
  display: flex;
  gap: 6px;
}

.lang-btn {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 5px 12px;
  border-radius: 999px;
  border: 1px solid rgba(255,255,255,0.1);
  background: rgba(255,255,255,0.04);
  color: rgba(255,255,255,0.5);
  font-size: 11px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.lang-btn:hover {
  border-color: rgba(196,166,113,0.4);
  color: rgba(255,255,255,0.8);
}

.lang-btn.active {
  border-color: #C4A671;
  background: rgba(196,166,113,0.12);
  color: #C4A671;
  font-weight: 600;
}

.flag { font-size: 14px; }
.native { font-size: 11px; }

.voice-badge {
  font-size: 9px;
  padding: 1px 5px;
  border-radius: 4px;
  font-family: monospace;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.voice-badge.native {
  background: rgba(74, 222, 128, 0.15);
  color: #4ade80;
  border: 1px solid rgba(74, 222, 128, 0.3);
}
.voice-badge.fallback {
  background: rgba(251, 191, 36, 0.15);
  color: #fbbf24;
  border: 1px solid rgba(251, 191, 36, 0.3);
}
</style>
