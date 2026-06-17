<template>
  <div class="bg-surface rounded-lg p-6 shadow-soft border border-outline-variant">
    <h2 class="text-xl font-bold mb-4 text-on-surface">Performance Metrics</h2>

    <div class="mb-6 p-4 latency-highlight-box rounded-lg">
      <p class="text-sm text-on-surface-variant latency-sub">Average Total Latency</p>
      <p class="text-4xl font-bold text-primary latency-val">{{ data?.avg_total_latency_ms ?? 0 }}ms</p>
      <p class="text-xs text-on-surface-variant mt-1 latency-sub">
        {{ (data?.avg_total_latency_ms ?? 0) > 1500 ? 'Slow - Users may perceive lag' : 'Good response time' }}
      </p>
    </div>

    <div class="mb-6">
      <h3 class="font-semibold mb-3 text-sm text-on-surface">Latency Breakdown</h3>
      <div class="space-y-3">
        <LatencyBar label="STT (Whisper)" :value="data?.avg_stt_latency_ms" :total="totalMs" color="bg-error" />
        <LatencyBar label="Webhook" :value="data?.avg_webhook_latency_ms" :total="totalMs" color="bg-tactical-amber" />
        <LatencyBar label="TTS (Edge)" :value="data?.avg_tts_latency_ms" :total="totalMs" color="bg-success" />
      </div>
    </div>

    <div class="mb-6">
      <h3 class="font-semibold mb-3 text-sm text-on-surface">Percentile Distribution</h3>
      <table class="w-full text-sm">
        <tbody>
          <tr v-for="(val, key) in data?.latency_percentiles" :key="key" class="border-b border-outline-variant">
            <td class="py-1 text-on-surface-variant uppercase text-xs">{{ key }}</td>
            <td class="py-1 text-right font-mono text-on-surface">{{ val }}ms</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="data?.latency_trend?.length">
      <h3 class="font-semibold mb-2 text-sm text-on-surface">Latency Trend</h3>
      <div class="h-40 flex items-end gap-1">
        <div v-for="day in data.latency_trend" :key="day.date"
          class="flex-1 rounded-t"
          :style="{ height: trendBarHeight(day.total_ms) + '%', background: trendColor(day.total_ms) }"
          :title="day.date + ': ' + day.total_ms + 'ms'"
        ></div>
      </div>
    </div>

    <div v-if="data?.slowest_component" class="mt-4 p-3 bg-tactical-amber/10 border border-tactical-amber/30 rounded-lg text-sm text-on-surface">
      Bottleneck: <strong>{{ data.slowest_component.toUpperCase() }}</strong> is the slowest step
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'

const props = defineProps({ agentId: String, timeRange: String })
const data = ref(null)

const totalMs = computed(() => {
  if (!data.value) return 1
  return (data.value.avg_stt_latency_ms || 0) + (data.value.avg_webhook_latency_ms || 0) + (data.value.avg_tts_latency_ms || 0) || 1
})

const maxTrend = computed(() => {
  if (!data.value?.latency_trend?.length) return 1
  return Math.max(...data.value.latency_trend.map(d => d.total_ms), 1)
})

function trendBarHeight(ms) { return (ms / maxTrend.value) * 100 }
function trendColor(ms) {
  if (ms > 2000) return '#ba1a1a'
  if (ms > 1500) return '#c48a00'
  return '#0e6c4a'
}

async function fetchMetrics() {
  try {
    const res = await fetch(`/api/v1/metrics/${props.agentId}/performance?range=${props.timeRange}`)
    if (res.ok) data.value = await res.json()
  } catch (e) { console.error('Performance metrics error', e) }
}

watch(() => [props.agentId, props.timeRange], fetchMetrics, { immediate: true })
</script>

<style scoped>
.latency-highlight-box {
  background: var(--color-primary-container);
  color: var(--color-on-primary);
}
html:not(.dark) .latency-highlight-box {
  background: var(--color-surface-container-low) !important;
  color: var(--color-on-surface) !important;
  border: 1px solid var(--color-outline-variant);
}
html:not(.dark) .latency-val {
  color: var(--color-primary) !important;
}
html:not(.dark) .latency-sub {
  color: var(--color-on-surface-variant) !important;
}
</style>
