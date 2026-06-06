<template>
  <div class="glass-panel rounded-2xl p-5">
    <div class="grid grid-cols-3 gap-4">
      <div v-for="stat in stats" :key="stat.label" class="text-center">
        <div :class="['font-mono text-lg font-bold', stat.color]">{{ stat.value }}</div>
        <div class="font-mono text-[10px] text-on-surface-variant/60 uppercase tracking-wider mt-1">{{ stat.label }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const user = computed(() => auth.user)

const stats = computed(() => [
  { label: 'Jobs Run', value: user.value?.total_jobs ?? 0, color: 'text-primary' },
  { label: 'Tokens', value: formatNum(user.value?.total_tokens ?? 0), color: 'text-secondary' },
  { label: 'Cost USD', value: `$${(user.value?.total_cost_usd ?? 0).toFixed(4)}`, color: 'text-tertiary' },
])

function formatNum(n) {
  if (n >= 1000000) return (n / 1000000).toFixed(1) + 'M'
  if (n >= 1000) return (n / 1000).toFixed(1) + 'K'
  return n
}
</script>
