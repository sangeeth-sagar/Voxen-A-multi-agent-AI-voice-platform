<template>
  <div class="metrics-dashboard p-6 space-y-6 overflow-y-auto h-full">
    <header class="flex items-center justify-between">
      <div>
        <h1 class="font-sans text-2xl font-bold text-white tracking-tight">
          {{ agentName ? agentName + ' Analytics' : 'Platform Analytics' }}
        </h1>
        <p class="font-mono text-[11px] text-on-surface-variant/60 uppercase tracking-wider mt-1">
          {{ currentTime }}
        </p>
      </div>
      <div class="flex items-center gap-2">
        <button
          v-for="r in ranges" :key="r.key"
          @click="timeRange = r.key"
          :class="[
            'px-4 py-2 rounded-xl font-mono text-[11px] uppercase tracking-wider transition-colors',
            timeRange === r.key
              ? 'bg-primary/15 text-primary'
              : 'text-on-surface-variant hover:text-white hover:bg-white/5'
          ]"
        >{{ r.label }}</button>
      </div>
    </header>

    <!-- Agent selector (for platform view) -->
    <div v-if="!agentId" class="flex items-center gap-4">
      <div class="glass-panel rounded-xl px-4 py-2 flex items-center gap-2">
        <span class="material-symbols-outlined text-sm text-on-surface-variant/50">filter_list</span>
        <select v-model="selectedAgentUuid" class="bg-transparent text-sm text-white border-none outline-none font-mono">
          <option value="">All Agents (Platform)</option>
          <option v-for="a in allAgents" :key="a.uuid" :value="a.uuid">{{ a.name }}</option>
        </select>
      </div>
    </div>

    <!-- Metrics grid -->
    <div v-if="activeAgentUuid" class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <VolumeMetricsCard :agentId="activeAgentUuid" :timeRange="timeRange" />
      <PerformanceMetricsCard :agentId="activeAgentUuid" :timeRange="timeRange" />
      <FinancialMetricsCard :agentId="activeAgentUuid" :timeRange="timeRange" />
      <ReliabilityMetricsCard :agentId="activeAgentUuid" :timeRange="timeRange" />
    </div>

    <!-- Platform-wide metrics (no agent selected) -->
    <div v-else>
      <PlatformMetricsCard :timeRange="timeRange" />
    </div>

    <!-- Logs (only when agent selected) -->
    <div v-if="activeAgentUuid">
      <ApiLogsTable :agentId="activeAgentUuid" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import VolumeMetricsCard from '@/components/metrics/VolumeMetricsCard.vue'
import PerformanceMetricsCard from '@/components/metrics/PerformanceMetricsCard.vue'
import FinancialMetricsCard from '@/components/metrics/FinancialMetricsCard.vue'
import ReliabilityMetricsCard from '@/components/metrics/ReliabilityMetricsCard.vue'
import PlatformMetricsCard from '@/components/metrics/PlatformMetricsCard.vue'
import ApiLogsTable from '@/components/metrics/ApiLogsTable.vue'
import { apiFetch } from '@/composables/useApi'

const route = useRoute()

// If navigated via /agents/:uuid/analytics, agentId is from the route
const agentId = computed(() => route.params.uuid || null)

const timeRange = ref('30d')
const ranges = [
  { key: '7d', label: '7 Days' },
  { key: '30d', label: '30 Days' },
  { key: '90d', label: '90 Days' },
]

const allAgents = ref([])
const selectedAgentUuid = ref('')
const activeAgentUuid = computed(() => agentId.value || selectedAgentUuid.value)

const agentName = computed(() => {
  if (agentId.value) {
    const found = allAgents.value.find(a => a.uuid === agentId.value)
    return found?.name || ''
  }
  if (selectedAgentUuid.value) {
    const found = allAgents.value.find(a => a.uuid === selectedAgentUuid.value)
    return found?.name || ''
  }
  return ''
})

const currentTime = ref('')
let clockInterval = null
function updateClock() {
  currentTime.value = new Date().toLocaleString('en-US', {
    year: 'numeric', month: 'short', day: '2-digit',
    hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false
  })
}

onMounted(async () => {
  updateClock()
  clockInterval = setInterval(updateClock, 1000)
  try {
    allAgents.value = await apiFetch('/api/v1/agents?my=true')
  } catch (e) { /* non-fatal */ }
})

onUnmounted(() => clearInterval(clockInterval))
</script>

<style scoped>
.glass-panel {
  background: rgba(17, 19, 25, 0.7);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border: 1px solid rgba(255, 255, 255, 0.08);
}
</style>
