<template>
  <div class="bg-white rounded-lg p-6 shadow-lg">
    <h2 class="text-xl font-bold mb-4">Financial Metrics</h2>

    <div class="grid grid-cols-3 gap-4 mb-6">
      <div class="bg-gray-50 p-4 rounded-lg">
        <p class="text-sm text-gray-600">Today</p>
        <p class="text-2xl font-bold">${{ data?.estimated_cost_today?.toFixed(4) ?? '0.00' }}</p>
        <p class="text-xs text-gray-500">Current usage</p>
      </div>
      <div class="bg-gray-50 p-4 rounded-lg">
        <p class="text-sm text-gray-600">Period Total</p>
        <p class="text-2xl font-bold">${{ data?.estimated_cost_period?.toFixed(4) ?? '0.00' }}</p>
        <p class="text-xs text-gray-500">{{ timeRange }}</p>
      </div>
      <div class="bg-gray-50 p-4 rounded-lg">
        <p class="text-sm text-gray-600">Monthly Projection</p>
        <p class="text-2xl font-bold">${{ data?.estimated_cost_monthly?.toFixed(2) ?? '0.00' }}</p>
        <p class="text-xs text-gray-500">Forecast</p>
      </div>
    </div>

    <div v-if="data?.costs_by_service">
      <h3 class="font-semibold mb-3 text-sm">Cost Breakdown</h3>
      <div class="space-y-3">
        <div class="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
          <div>
            <p class="text-sm font-medium">STT (Groq Whisper)</p>
            <p class="text-xs text-gray-600">{{ data.costs_by_service.stt?.duration_minutes ?? 0 }} min</p>
          </div>
          <p class="font-mono font-bold">${{ data.costs_by_service.stt?.cost?.toFixed(4) ?? '0' }}</p>
        </div>
        <div class="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
          <div>
            <p class="text-sm font-medium">TTS (Edge TTS)</p>
            <p class="text-xs text-gray-600">{{ data.costs_by_service.tts?.characters?.toLocaleString() ?? 0 }} chars</p>
          </div>
          <p class="font-mono font-bold">${{ data.costs_by_service.tts?.cost?.toFixed(4) ?? '0' }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({ agentId: String, timeRange: String })
const data = ref(null)

async function fetchMetrics() {
  try {
    const res = await fetch(`/api/v1/metrics/${props.agentId}/financial?range=${props.timeRange}`)
    if (res.ok) data.value = await res.json()
  } catch (e) { console.error('Financial metrics error', e) }
}

watch(() => [props.agentId, props.timeRange], fetchMetrics, { immediate: true })
</script>
