<template>
  <div class="theme-toggle">
    <button
      @click="toggle()"
      :class="['theme-btn', { active: !isDark }]"
      title="Light mode"
    >
      <span class="material-symbols-outlined">light_mode</span>
    </button>
    <button
      @click="toggle()"
      :class="['theme-btn', { active: isDark }]"
      title="Dark mode"
    >
      <span class="material-symbols-outlined">dark_mode</span>
    </button>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useAppTheme } from '@/composables/useTheme'

const { theme, toggle } = useAppTheme()
const isDark = computed(() => theme.value === 'dark')
</script>

<style scoped>
.theme-toggle {
  display: flex;
  align-items: center;
  gap: 2px;
  padding: 3px;
  border-radius: 999px;
  background: var(--color-surface-container-high);
  border: 1px solid var(--color-outline-variant);
}

html.dark .theme-toggle {
  background: rgba(0, 23, 16, 0.5);
  border-color: rgba(255, 255, 255, 0.08);
}

.theme-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 999px;
  border: none;
  background: transparent;
  color: var(--color-on-surface-variant);
  cursor: pointer;
  transition: all 0.2s ease;
}

.theme-btn:hover {
  color: var(--color-on-surface);
  background: var(--color-surface-container-highest);
}

.theme-btn.active {
  background: var(--color-primary);
  color: var(--color-on-primary);
  box-shadow: var(--shadow-level-1);
}

html.dark .theme-btn.active {
  box-shadow: 0 0 12px var(--glow-primary);
}

.theme-btn .material-symbols-outlined {
  font-size: 18px;
}
</style>
