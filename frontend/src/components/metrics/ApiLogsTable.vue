<template>
  <div class="bg-surface rounded-lg p-6 shadow-soft border border-outline-variant">
    <div class="flex justify-between items-center mb-4">
      <h2 class="text-xl font-bold text-on-surface">API Call Logs</h2>
      <div class="flex gap-2">
        <select v-model="statusFilter" class="text-sm border border-outline-variant rounded px-2 py-1 bg-surface text-on-surface">
          <option value="">All Status</option>
          <option value="200">200 OK</option>
          <option value="4xx">4xx Errors</option>
          <option value="5xx">5xx Errors</option>
        </select>
        <input v-model="searchText" placeholder="Search text..." class="text-sm border border-outline-variant rounded px-2 py-1 bg-surface text-on-surface" />
      </div>
    </div>

    <div v-if="loading" class="text-center py-8 text-on-surface-variant">Loading...</div>
    <div v-else-if="filteredLogs.length === 0" class="text-center py-8 text-on-surface-variant">No logs found</div>

    <div v-else class="overflow-x-auto">
      <table class="w-full text-sm">
        <thead>
          <tr class="text-left text-on-surface-variant border-b border-outline-variant">
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
          <tr v-for="log in filteredLogs" :key="log.id" class="border-b border-outline-variant hover:bg-surface-container-high">
            <td class="py-2 text-xs text-on-surface-variant whitespace-nowrap">{{ formatTime(log.created_at) }}</td>
            <td class="py-2 max-w-[200px] truncate text-on-surface">{{ log.user_text }}</td>
            <td class="py-2 max-w-[200px] truncate text-on-surface-variant">{{ log.agent_response }}</td>
            <td class="py-2 text-right font-mono text-xs text-on-surface">{{ log.stt_latency_ms }}ms</td>
            <td class="py-2 text-right font-mono text-xs text-on-surface">{{ log.webhook_latency_ms }}ms</td>
            <td class="py-2 text-right font-mono text-xs text-on-surface">{{ log.tts_latency_ms }}ms</td>
            <td class="py-2 text-right font-mono text-xs font-bold text-on-surface">{{ log.total_latency_ms }}ms</td>
            <td class="py-2 text-right">
              <span class="px-2 py-0.5 rounded text-xs font-bold" :class="statusClass(log.webhook_status)">
                {{ log.webhook_status || 'ERR' }}
              </span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="flex justify-between items-center mt-4 text-sm text-on-surface-variant">
      <span>{{ filteredLogs.length }} of {{ logs.length }} logs</span>
      <div class="flex gap-2">
        <button @click="loadMore" :disabled="logs.length < limit" class="px-3 py-1 border border-outline-variant rounded disabled:opacity-40 bg-surface text-on-surface hover:bg-surface-container-high">
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
  if (statusFilter.value === '200') result = result.filter(l => l.webhook_status === 200)
  else if (statusFilter.value === '4xx') result = result.filter(l => l.webhook_status >= 400 && l.webhook_status < 500)
  else if (statusFilter.value === '5xx') result = result.filter(l => l.webhook_status >= 500)
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
  return new Date(iso).toLocaleString()
}

function statusClass(code) {
  if (!code) return 'bg-surface-container-high text-on-surface-variant'
  if (code === 200) return 'bg-success/15 text-success'
  if (code >= 500) return 'bg-error/15 text-error'
  return 'bg-tactical-amber/15 text-tactical-amber'
}

async function fetchLogs() {
  loading.value = true
  try {
    const res = await fetch(`/api/v1/metrics/${props.agentId}/logs?limit=${limit.value}`)
    if (res.ok) logs.value = await res.json()
  } catch (e) { console.error('Logs fetch error', e) } finally { loading.value = false }
}

function loadMore() { limit.value += 50; fetchLogs() }

watch(() => props.agentId, fetchLogs, { immediate: true })
</script>
