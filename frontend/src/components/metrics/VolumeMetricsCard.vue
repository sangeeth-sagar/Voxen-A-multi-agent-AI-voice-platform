<template>
  <div class="bg-white rounded-lg p-6 shadow-lg">
    <h2 class="text-xl font-bold mb-4">Volume Metrics</h2>

    <div class="grid grid-cols-3 gap-4 mb-6">
      <div class="bg-gray-50 p-4 rounded-lg">
        <p class="text-sm text-gray-600">Total Requests</p>
        <p class="text-2xl font-bold">{{ data?.total_requests?.toLocaleString() ?? 0 }}</p>
      </div>
      <div class="bg-gray-50 p-4 rounded-lg">
        <p class="text-sm text-gray-600">Active Sessions</p>
        <p class="text-2xl font-bold">{{ data?.active_sessions ?? 0 }}</p>
      </div>
      <div class="bg-gray-50 p-4 rounded-lg">
        <p class="text-sm text-gray-600">Time Range</p>
        <p class="text-2xl font-bold">{{ timeRange }}</p>
      </div>
    </div>

    <div v-if="data?.requests_per_day?.length" class="mb-4">
      <h3 class="font-semibold mb-2 text-sm">Requests Over Time</h3>
      <div class="h-48 flex items-end gap-1">
        <div
          v-for="day in data.requests_per_day"
          :key="day.date"
          class="flex-1 bg-blue-500 rounded-t"
          :style="{ height: barHeight(day.count) + '%' }"
          :title="day.date + ': ' + day.count"
        ></div>
      </div>
      <div class="flex justify-between text-xs text-gray-400 mt-1">
        <span v-if="data.requests_per_day.length">{{ data.requests_per_day[0].date }}</span>
        <span v-if="data.requests_per_day.length">{{ data.requests_per_day[data.requests_per_day.length - 1].date }}</span>
      </div>
    </div>

    <div v-if="data?.requests_by_hour?.length">
      <h3 class="font-semibold mb-2 text-sm">Requests by Hour (24h)</h3>
      <div class="h-32 flex items-end gap-px">
        <div
          v-for="h in data.requests_by_hour"
          :key="h.hour"
          class="flex-1 bg-green-500 rounded-t"
          :style="{ height: hourBarHeight(h.count) + '%' }"
          :title="'Hour ' + h.hour + ': ' + h.count"
        ></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue'

const props = defineProps({ agentId: String, timeRange: String })
const data = ref(null)

const maxCount = computed(() => {
  if (!data.value?.requests_per_day?.length) return 1
  return Math.max(...data.value.requests_per_day.map(d => d.count), 1)
})
const maxHour = computed(() => {
  if (!data.value?.requests_by_hour?.length) return 1
  return Math.max(...data.value.requests_by_hour.map(h => h.count), 1)
})

function barHeight(count) { return (count / maxCount.value) * 100 }
function hourBarHeight(count) { return (count / maxHour.value) * 100 }

async function fetchMetrics() {
  try {
    const res = await fetch(`/api/v1/metrics/${props.agentId}/volume?range=${props.timeRange}`)
    if (res.ok) data.value = await res.json()
  } catch (e) { console.error('Volume metrics error', e) }
}

watch(() => [props.agentId, props.timeRange], fetchMetrics, { immediate: true })
</script>
