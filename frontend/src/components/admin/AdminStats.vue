<template>
  <div class="space-y-5">
    <!-- Metric cards -->
    <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
      <div v-for="card in metricCards" :key="card.label"
        class="glass-card rounded-2xl p-5">
        <div class="flex items-center justify-between mb-3">
          <div :class="['w-9 h-9 rounded-xl flex items-center justify-center', card.bg]">
            <span :class="['material-symbols-outlined text-lg icon-filled', card.color]">{{ card.icon }}</span>
          </div>
          <span :class="['font-mono text-[10px] uppercase tracking-wider', card.color]">{{ card.trend }}</span>
        </div>
        <div :class="['font-mono text-2xl font-bold', card.color]">{{ card.value }}</div>
        <div class="font-mono text-[10px] text-on-surface-variant/50 uppercase tracking-wider mt-1">{{ card.label }}</div>
      </div>
    </div>

    <!-- Bar chart: Jobs per day (SVG) -->
    <div class="glass-panel rounded-2xl p-6">
      <div class="flex items-center justify-between mb-5">
        <h3 class="font-sans font-semibold text-sm">Jobs — Last 7 Days</h3>
        <span class="font-mono text-[10px] text-on-surface-variant/50 uppercase">Execution frequency</span>
      </div>
      <div class="relative h-32">
        <svg viewBox="0 0 700 128" preserveAspectRatio="none" class="w-full h-full" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <linearGradient id="barGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stop-color="#c0c1ff" stop-opacity="0.8" />
              <stop offset="100%" stop-color="#571bc1" stop-opacity="0.4" />
            </linearGradient>
          </defs>
          <rect
            v-for="(bar, i) in chartBars" :key="i"
            :x="bar.x" :y="bar.y" :width="bar.w" :height="bar.h"
            rx="4" fill="url(#barGrad)"
          />
          <!-- Day labels -->
          <text
            v-for="(bar, i) in chartBars" :key="'l'+i"
            :x="bar.x + bar.w / 2" y="126"
            text-anchor="middle" fill="rgba(199,196,215,0.4)"
            font-size="10" font-family="JetBrains Mono"
          >{{ bar.label }}</text>
        </svg>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  stats: { type: Object, default: () => ({}) }
})

const metricCards = computed(() => [
  {
    label: 'Total Users', value: props.stats.total_users ?? 0,
    icon: 'group', color: 'text-primary', bg: 'bg-primary/10', trend: '↑ Active'
  },
  {
    label: 'Total Jobs', value: props.stats.total_jobs ?? 0,
    icon: 'work', color: 'text-secondary', bg: 'bg-secondary/10', trend: '↑ Running'
  },
  {
    label: 'Total Tokens', value: fmtNum(props.stats.total_tokens ?? 0),
    icon: 'generating_tokens', color: 'text-tertiary', bg: 'bg-tertiary/10', trend: 'Usage'
  },
  {
    label: 'Total Cost', value: `$${(props.stats.total_cost_usd ?? 0).toFixed(2)}`,
    icon: 'payments', color: 'text-tactical-amber', bg: 'bg-tactical-amber/10', trend: 'Billed'
  },
])

// Mock daily jobs bar chart
const rawBars = [12, 28, 19, 42, 35, 51, 38]
const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
const maxVal = Math.max(...rawBars)
const totalW = 700
const barW = 70
const gap = (totalW - rawBars.length * barW) / (rawBars.length + 1)
const chartH = 112

const chartBars = rawBars.map((v, i) => {
  const h = Math.round((v / maxVal) * chartH)
  return { x: gap + i * (barW + gap), y: chartH - h, w: barW, h, label: days[i] }
})

function fmtNum(n) {
  if (n >= 1e6) return (n/1e6).toFixed(1) + 'M'
  if (n >= 1000) return (n/1000).toFixed(1) + 'K'
  return n
}
</script>
