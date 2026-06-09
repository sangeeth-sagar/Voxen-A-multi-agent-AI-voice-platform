<template>
  <div class="bg-white rounded-lg p-6 shadow-lg">
    <h2 class="text-xl font-bold mb-4">Platform Analytics</h2>

    <div class="grid grid-cols-3 gap-4 mb-6">
      <div class="bg-gray-50 p-4 rounded-lg">
        <p class="text-sm text-gray-600">Total Calls</p>
        <p class="text-2xl font-bold">{{ data?.total_calls?.toLocaleString() ?? 0 }}</p>
      </div>
      <div class="bg-gray-50 p-4 rounded-lg">
        <p class="text-sm text-gray-600">Active Agents</p>
        <p class="text-2xl font-bold">{{ data?.active_agents ?? 0 }}</p>
      </div>
      <div class="bg-gray-50 p-4 rounded-lg">
        <p class="text-sm text-gray-600">Total Cost</p>
        <p class="text-2xl font-bold">${{ data?.total_cost?.toFixed(4) ?? '0' }}</p>
      </div>
    </div>

    <div v-if="data?.daily_trend?.length" class="mb-6">
      <h3 class="font-semibold mb-2 text-sm">Daily Volume</h3>
      <div class="h-40 flex items-end gap-1">
        <div
          v-for="day in data.daily_trend"
          :key="day.date"
          class="flex-1 bg-blue-500 rounded-t"
          :style="{ height: barHeight(day.count) + '%' }"
          :title="day.date + ': ' + day.count"
        ></div>
      </div>
    </div>

    <div v-if="data?.top_agents?.length">
      <h3 class="font-semibold mb-3 text-sm">Top Agents by Usage</h3>
      <table class="w-full text-sm">
        <thead>
          <tr class="text-left text-gray-500 border-b">
            <th class="py-2">Agent</th>
            <th class="py-2 text-right">Calls</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="agent in data.top_agents" :key="agent.agent_id" class="border-b border-gray-50">
            <td class="py-2">{{ agent.agent_name }}</td>
            <td class="py-2 text-right font-mono">{{ agent.call_count.toLocaleString() }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'

const props = defineProps({ timeRange: String })
const data = ref(null)

const maxCount = computed(() => {
  if (!data.value?.daily_trend?.length) return 1
  return Math.max(...data.value.daily_trend.map(d => d.count), 1)
})
function barHeight(count) { return (count / maxCount.value) * 100 }

async function fetchMetrics() {
  try {
    const res = await fetch(`/api/v1/metrics/platform?range=${props.timeRange}`)
    if (res.ok) data.value = await res.json()
  } catch (e) { console.error('Platform metrics error', e) }
}

watch(() => props.timeRange, fetchMetrics, { immediate: true })
</script>
