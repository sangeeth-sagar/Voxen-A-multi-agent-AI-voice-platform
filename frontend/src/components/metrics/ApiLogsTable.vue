<template>
  <div class="bg-white rounded-lg p-6 shadow-lg">
    <div class="flex justify-between items-center mb-4">
      <h2 class="text-xl font-bold">API Call Logs</h2>
      <div class="flex gap-2">
        <select v-model="statusFilter" class="text-sm border rounded px-2 py-1">
          <option value="">All Status</option>
          <option value="200">200 OK</option>
          <option value="4xx">4xx Errors</option>
          <option value="5xx">5xx Errors</option>
        </select>
        <input v-model="searchText" placeholder="Search text..." class="text-sm border rounded px-2 py-1" />
      </div>
    </div>

    <div v-if="loading" class="text-center py-8 text-gray-400">Loading...</div>

    <div v-else-if="filteredLogs.length === 0" class="text-center py-8 text-gray-400">No logs found</div>

    <div v-else class="overflow-x-auto">
      <table class="w-full text-sm">
        <thead>
          <tr class="text-left text-gray-500 border-b">
            <th class="py-2">Time</th>
            <th class="py-2">User Text</th>
            <th class="py-2">Response</th>
            <th class="py-2 text-right">STT</th>
            <th class="py-2 text-right">Webhook</th>
            <th class="py-2 text-right">TTS</th>
            <th class="py-2 text-right">Total</th>
            <th class="py-2 text-right">Status</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="log in filteredLogs" :key="log.id" class="border-b border-gray-50 hover:bg-gray-50">
            <td class="py-2 text-xs text-gray-500 whitespace-nowrap">{{ formatTime(log.created_at) }}</td>
            <td class="py-2 max-w-[200px] truncate">{{ log.user_text }}</td>
            <td class="py-2 max-w-[200px] truncate text-gray-600">{{ log.agent_response }}</td>
            <td class="py-2 text-right font-mono text-xs">{{ log.stt_latency_ms }}ms</td>
            <td class="py-2 text-right font-mono text-xs">{{ log.webhook_latency_ms }}ms</td>
            <td class="py-2 text-right font-mono text-xs">{{ log.tts_latency_ms }}ms</td>
            <td class="py-2 text-right font-mono text-xs font-bold">{{ log.total_latency_ms }}ms</td>
            <td class="py-2 text-right">
              <span class="px-2 py-0.5 rounded text-xs font-bold"
                    :class="statusClass(log.webhook_status)">
                {{ log.webhook_status || 'ERR' }}
              </span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="flex justify-between items-center mt-4 text-sm text-gray-500">
      <span>{{ filteredLogs.length }} of {{ logs.length }} logs</span>
      <div class="flex gap-2">
        <button @click="loadMore" :disabled="logs.length < limit" class="px-3 py-1 border rounded disabled:opacity-40">
          Load More
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'

const props = defineProps({ agentId: String })

const logs = ref([])
const loading = ref(false)
const statusFilter = ref('')
const searchText = ref('')
const limit = ref(50)

const filteredLogs = computed(() => {
  let result = logs.value
  if (statusFilter.value === '200') {
    result = result.filter(l => l.webhook_status === 200)
  } else if (statusFilter.value === '4xx') {
    result = result.filter(l => l.webhook_status >= 400 && l.webhook_status < 500)
  } else if (statusFilter.value === '5xx') {
    result = result.filter(l => l.webhook_status >= 500)
  }
  if (searchText.value) {
    const q = searchText.value.toLowerCase()
    result = result.filter(l =>
      (l.user_text || '').toLowerCase().includes(q) ||
      (l.agent_response || '').toLowerCase().includes(q)
    )
  }
  return result
})

function formatTime(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  return d.toLocaleString()
}

function statusClass(code) {
  if (!code) return 'bg-gray-100 text-gray-500'
  if (code === 200) return 'bg-green-100 text-green-700'
  if (code >= 500) return 'bg-red-100 text-red-700'
  return 'bg-yellow-100 text-yellow-700'
}

async function fetchLogs() {
  loading.value = true
  try {
    const res = await fetch(`/api/v1/metrics/${props.agentId}/logs?limit=${limit.value}`)
    if (res.ok) logs.value = await res.json()
  } catch (e) {
    console.error('Logs fetch error', e)
  } finally {
    loading.value = false
  }
}

function loadMore() {
  limit.value += 50
  fetchLogs()
}

watch(() => props.agentId, fetchLogs, { immediate: true })
</script>
