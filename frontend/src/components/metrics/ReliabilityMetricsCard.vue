<template>
  <div class="bg-surface rounded-lg p-6 shadow-soft border border-outline-variant">
    <h2 class="text-xl font-bold mb-4 text-on-surface">Reliability Metrics</h2>

    <div class="mb-6 p-4 bg-success/10 border border-success/30 rounded-lg">
      <div class="flex items-center justify-between">
        <div>
          <p class="text-sm text-on-surface-variant">Webhook Success Rate</p>
          <p class="text-3xl font-bold" :class="rateColor">
            {{ data?.webhook_success_rate ?? 100 }}%
          </p>
        </div>
        <div class="text-right">
          <p class="text-xs text-on-surface-variant">Target: 99.5%</p>
          <p class="text-xs" :class="rateColor">{{ rateStatus }}</p>
        </div>
      </div>
    </div>

    <div class="mb-6">
      <h3 class="font-semibold mb-3 text-sm text-on-surface">Errors by Code</h3>
      <div class="space-y-2">
        <div v-for="(count, code) in data?.errors_by_code" :key="code"
             class="flex justify-between items-center p-2 rounded"
             :class="codeClass(code)">
          <span class="text-sm">HTTP {{ code }}</span>
          <span class="font-bold">{{ count }}</span>
        </div>
        <div v-if="data?.timeout_count" class="flex justify-between items-center p-2 rounded bg-tactical-amber/10 text-tactical-amber">
          <span class="text-sm">Timeouts (&gt;30s)</span>
          <span class="font-bold">{{ data.timeout_count }}</span>
        </div>
      </div>
    </div>

    <div v-if="data?.reliability_trend?.length">
      <h3 class="font-semibold mb-2 text-sm text-on-surface">Success Rate Trend</h3>
      <div class="h-32 flex items-end gap-1">
        <div v-for="day in data.reliability_trend" :key="day.date"
          class="flex-1 rounded-t"
          :style="{ height: day.success_rate + '%', background: day.success_rate >= 99 ? '#0e6c4a' : day.success_rate >= 95 ? '#c48a00' : '#ba1a1a' }"
          :title="day.date + ': ' + day.success_rate + '% success, ' + day.error_count + ' errors'"
        ></div>
      </div>
      <div class="flex justify-between text-xs text-on-surface-variant mt-1">
        <span>{{ data.reliability_trend[0]?.date }}</span>
        <span>{{ data.reliability_trend[data.reliability_trend.length - 1]?.date }}</span>
      </div>
    </div>

    <div class="mt-4 text-sm text-on-surface-variant">
      Total: {{ data?.total_requests ?? 0 }} requests, {{ data?.total_errors ?? 0 }} errors
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { apiFetch } from '@/composables/useApi'

const props = defineProps({ agentId: String, timeRange: String })
const data = ref(null)

const rateColor = computed(() => {
  const r = data.value?.webhook_success_rate ?? 100
  return r >= 99 ? 'text-success' : r >= 95 ? 'text-tactical-amber' : 'text-error'
})
const rateStatus = computed(() => {
  const r = data.value?.webhook_success_rate ?? 100
  return r >= 99 ? 'Healthy' : r >= 95 ? 'Degraded' : 'Critical'
})

function codeClass(code) {
  if (code.startsWith('5')) return 'bg-error/10 text-error'
  if (code.startsWith('4')) return 'bg-tactical-amber/10 text-tactical-amber'
  return 'bg-surface-container-high text-on-surface-variant'
}

async function fetchMetrics() {
  try {
    data.value = await apiFetch(`/api/v1/metrics/${props.agentId}/reliability?range=${props.timeRange}`)
  } catch (e) { console.error('Reliability metrics error', e) }
}

watch(() => [props.agentId, props.timeRange], fetchMetrics, { immediate: true })
</script>
