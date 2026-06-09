<template>
  <div class="bg-white rounded-lg p-6 shadow-lg">
    <h2 class="text-xl font-bold mb-4">Performance Metrics</h2>

    <div class="mb-6 p-4 bg-blue-50 rounded-lg">
      <p class="text-sm text-gray-600">Average Total Latency</p>
      <p class="text-4xl font-bold text-blue-600">{{ data?.avg_total_latency_ms ?? 0 }}ms</p>
      <p class="text-xs text-gray-500 mt-1">
        {{ (data?.avg_total_latency_ms ?? 0) > 1500 ? 'Slow - Users may perceive lag' : 'Good response time' }}
      </p>
    </div>

    <div class="mb-6">
      <h3 class="font-semibold mb-3 text-sm">Latency Breakdown</h3>
      <div class="space-y-3">
        <LatencyBar label="STT (Whisper)" :value="data?.avg_stt_latency_ms" :total="totalMs" color="bg-red-500" />
        <LatencyBar label="Webhook" :value="data?.avg_webhook_latency_ms" :total="totalMs" color="bg-yellow-500" />
        <LatencyBar label="TTS (Edge)" :value="data?.avg_tts_latency_ms" :total="totalMs" color="bg-green-500" />
      </div>
    </div>

    <div class="mb-6">
      <h3 class="font-semibold mb-3 text-sm">Percentile Distribution</h3>
      <table class="w-full text-sm">
        <tbody>
          <tr v-for="(val, key) in data?.latency_percentiles" :key="key" class="border-b border-gray-100">
            <td class="py-1 text-gray-600 uppercase text-xs">{{ key }}</td>
            <td class="py-1 text-right font-mono">{{ val }}ms</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="data?.latency_trend?.length">
      <h3 class="font-semibold mb-2 text-sm">Latency Trend</h3>
      <div class="h-40 flex items-end gap-1">
        <div
          v-for="day in data.latency_trend"
          :key="day.date"
          class="flex-1 rounded-t"
          :style="{ height: trendBarHeight(day.total_ms) + '%', background: trendColor(day.total_ms) }"
          :title="day.date + ': ' + day.total_ms + 'ms'"
        ></div>
      </div>
    </div>

    <div v-if="data?.slowest_component" class="mt-4 p-3 bg-yellow-50 rounded-lg text-sm">
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
  if (ms > 2000) return '#ef4444'
  if (ms > 1500) return '#f59e0b'
  return '#22c55e'
}

async function fetchMetrics() {
  try {
    const res = await fetch(`/api/v1/metrics/${props.agentId}/performance?range=${props.timeRange}`)
    if (res.ok) data.value = await res.json()
  } catch (e) { console.error('Performance metrics error', e) }
}

watch(() => [props.agentId, props.timeRange], fetchMetrics, { immediate: true })
</script>
