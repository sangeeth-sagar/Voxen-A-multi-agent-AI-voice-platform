<template>
  <div class="admin-dashboard p-6 space-y-6">
    <header class="flex items-center justify-between">
      <div>
        <h1 class="font-sans text-2xl font-bold text-white tracking-tight">Dashboard</h1>
        <p class="font-mono text-[11px] text-on-surface-variant/60 uppercase tracking-wider mt-1">
          {{ currentTime }}
        </p>
      </div>
      <div class="flex items-center gap-2 px-3 py-1.5 bg-green-900/20 border border-green-500/20 rounded-full">
        <span class="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
        <span class="font-mono text-[10px] text-green-400 uppercase tracking-wider">All Systems Nominal</span>
      </div>
    </header>

    <!-- Stat cards -->
    <section class="grid grid-cols-2 lg:grid-cols-4 gap-4">
      <div v-for="card in metricCards" :key="card.label"
        class="glass-panel rounded-2xl p-5">
        <div class="flex items-center justify-between mb-3">
          <div :class="['w-9 h-9 rounded-xl flex items-center justify-center', card.bg]">
            <span :class="['material-symbols-outlined text-lg icon-filled', card.color]">{{ card.icon }}</span>
          </div>
          <span :class="['font-mono text-[10px] uppercase tracking-wider', card.color]">{{ card.trend }}</span>
        </div>
        <div :class="['font-mono text-2xl font-bold', card.color]">{{ card.value }}</div>
        <div class="font-mono text-[10px] text-on-surface-variant/50 uppercase tracking-wider mt-1">{{ card.label }}</div>
      </div>
    </section>

    <!-- Quick panels -->
    <section class="grid grid-cols-1 lg:grid-cols-2 gap-5">
      <div class="glass-panel rounded-2xl p-6">
        <h3 class="font-sans font-semibold text-sm text-white mb-4">Top Users (by agents)</h3>
        <ul v-if="topUsers.length" class="space-y-2">
          <li v-for="u in topUsers" :key="u.id" class="flex items-center justify-between text-sm">
            <span class="text-white truncate">{{ u.full_name || u.email }}</span>
            <span class="font-mono text-[11px] text-primary">{{ u.agent_count || 0 }} agents</span>
          </li>
        </ul>
        <p v-else class="text-on-surface-variant/40 text-xs font-mono">No data yet.</p>
      </div>

      <div class="glass-panel rounded-2xl p-6">
        <h3 class="font-sans font-semibold text-sm text-white mb-4">Recent Activity</h3>
        <ul v-if="recentJobs.length" class="space-y-2">
          <li v-for="j in recentJobs" :key="j.job_id" class="flex items-center justify-between text-xs">
            <span class="font-mono text-on-surface-variant truncate flex-1">{{ j.user_prompt || '—' }}</span>
            <span :class="['font-mono text-[10px] uppercase px-2 py-0.5 rounded-full ml-3', statusStyle(j.status)]">{{ j.status }}</span>
          </li>
        </ul>
        <p v-else class="text-on-surface-variant/40 text-xs font-mono">No recent jobs.</p>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { apiFetch } from '@/composables/useApi'
import { useToastStore } from '@/stores/toast'

const toast = useToastStore()

const stats = ref({})
const topUsers = ref([])
const recentJobs = ref([])

const currentTime = ref('')
let clockInterval = null
function updateClock() {
  currentTime.value = new Date().toLocaleString('en-US', {
    year: 'numeric', month: 'short', day: '2-digit',
    hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false
  })
}

function fmtNum(n) {
  if (n >= 1e6) return (n/1e6).toFixed(1) + 'M'
  if (n >= 1000) return (n/1000).toFixed(1) + 'K'
  return n
}

const metricCards = computed(() => [
  { label: 'Total Users',  value: stats.value.total_users ?? 0,
    icon: 'group',           color: 'text-primary',         bg: 'bg-primary/10', trend: '↑ Active' },
  { label: 'Total Agents', value: stats.value.total_agents ?? 0,
    icon: 'smart_toy',       color: 'text-secondary',       bg: 'bg-secondary/10', trend: '↑ Deployed' },
  { label: 'Total Jobs',   value: stats.value.total_jobs ?? 0,
    icon: 'work',            color: 'text-tertiary',        bg: 'bg-tertiary/10', trend: 'All-time' },
  { label: 'Total Cost',   value: `$${(stats.value.total_cost_usd ?? 0).toFixed(2)}`,
    icon: 'payments',        color: 'text-tactical-amber',  bg: 'bg-tactical-amber/10', trend: 'Billed' },
])

function statusStyle(status) {
  return {
    pending:    'bg-tactical-amber/10 text-tactical-amber',
    processing: 'bg-secondary/10 text-secondary',
    completed:  'bg-green-900/30 text-green-400',
    failed:     'bg-error/10 text-error',
  }[status] ?? 'bg-white/5 text-on-surface-variant'
}

onMounted(async () => {
  try {
    stats.value = await apiFetch('/api/v1/admin/stats')
  } catch (e) { toast.show('Failed to load stats', 'error') }
  try {
    const users = await apiFetch('/api/v1/admin/users')
    topUsers.value = [...users].sort((a, b) => (b.agent_count || 0) - (a.agent_count || 0)).slice(0, 5)
  } catch (e) { /* non-fatal */ }
  try {
    const jobs = await apiFetch('/api/v1/admin/jobs')
    recentJobs.value = (jobs || []).slice(0, 5)
  } catch (e) { /* non-fatal */ }
  updateClock()
  clockInterval = setInterval(updateClock, 1000)
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
