<template>
  <div class="space-y-6">
    <!-- Top Metrics Summary Row (Backend-backed) -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
      <!-- Total System Calls -->
      <div class="glass-panel rounded-2xl p-5 flex items-center justify-between border border-outline-variant/50 relative overflow-hidden">
        <div class="space-y-1">
          <span class="text-xs text-on-surface-variant font-medium">Total System Calls</span>
          <h2 class="font-sans text-3xl font-extrabold text-on-surface tracking-tight">
            {{ formattedTotalCalls }}
          </h2>
          <div class="flex items-center gap-1 mt-1">
            <span class="text-[10px] text-on-surface-variant font-mono">Platform lifetime</span>
          </div>
        </div>
        <div class="icon-circle bg-primary/10 text-primary">
          <span class="material-symbols-outlined icon-filled">call</span>
        </div>
      </div>

      <!-- Active Neural Agents -->
      <div class="glass-panel rounded-2xl p-5 flex items-center justify-between border border-outline-variant/50 relative overflow-hidden">
        <div class="space-y-1">
          <span class="text-xs text-on-surface-variant font-medium">Active Agents</span>
          <h2 class="font-sans text-3xl font-extrabold text-on-surface tracking-tight">
            {{ activeAgentsCount }}
          </h2>
          <div class="flex items-center gap-1 mt-1">
            <span class="text-[10px] text-on-surface-variant font-mono">Currently configured</span>
          </div>
        </div>
        <div class="icon-circle bg-primary/10 text-primary">
          <span class="material-symbols-outlined icon-filled">smart_toy</span>
        </div>
      </div>

      <!-- Platform Status -->
      <div class="glass-panel rounded-2xl p-5 flex items-center justify-between border border-outline-variant/50 relative overflow-hidden">
        <div class="space-y-1 flex-1">
          <span class="text-xs text-on-surface-variant font-medium">Platform Status</span>
          <h2 class="font-sans text-3xl font-extrabold text-success tracking-tight">
            ACTIVE
          </h2>
          <div class="flex items-center gap-1 mt-1">
            <span class="text-[10px] text-on-surface-variant font-mono">System fully operational</span>
          </div>
        </div>
        <div class="icon-circle bg-primary/10 text-success">
          <span class="material-symbols-outlined icon-filled text-success">check_circle</span>
        </div>
      </div>
    </div>

    <!-- Main Graphs Grid (Backend-backed) -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- Daily Volume Chart (Vetted Backend Trend) -->
      <div class="glass-panel rounded-2xl p-5 border border-outline-variant/50 lg:col-span-2 space-y-4">
        <div class="flex justify-between items-start">
          <div>
            <h3 class="text-sm font-bold text-on-surface">Daily Call Volume</h3>
            <p class="text-[11px] text-on-surface-variant">Vocal and API sessions timeline</p>
          </div>
          <span class="text-[10px] text-primary font-mono font-bold">{{ data?.daily_trend?.length || 0 }} intervals synced</span>
        </div>

        <div v-if="data?.daily_trend?.length" class="h-48 flex items-end gap-1.5 pt-4">
          <div 
            v-for="day in data.daily_trend" 
            :key="day.date"
            class="flex-1 bg-primary rounded-t transition-all duration-300 hover:opacity-100"
            :style="{ height: barHeight(day.count) + '%', opacity: '0.8' }"
            :title="day.date + ': ' + day.count + ' calls'"
          ></div>
        </div>
        
        <div v-else class="h-48 flex items-center justify-center border border-dashed border-outline-variant/30 rounded-xl bg-surface-container/20">
          <span class="text-xs text-on-surface-variant/50 italic">No usage logged for this filter duration.</span>
        </div>

        <div v-if="data?.daily_trend?.length" class="flex justify-between text-[9px] font-mono text-on-surface-variant/60 pt-2 border-t border-outline-variant/20">
          <span>{{ data.daily_trend[0]?.date }}</span>
          <span>{{ data.daily_trend[Math.floor(data.daily_trend.length / 2)]?.date }}</span>
          <span>{{ data.daily_trend[data.daily_trend.length - 1]?.date }}</span>
        </div>
      </div>

      <!-- Top Agents By Usage (Backend-backed list) -->
      <div class="glass-panel rounded-2xl p-5 border border-outline-variant/50 lg:col-span-1 space-y-4 flex flex-col justify-between">
        <div class="space-y-4">
          <div>
            <h3 class="text-sm font-bold text-on-surface">Top Agents</h3>
            <p class="text-[11px] text-on-surface-variant">Ranked by session counts</p>
          </div>

          <div class="space-y-2 max-h-56 overflow-y-auto pr-1">
            <div 
              v-for="(agent, idx) in data?.top_agents || []" 
              :key="agent.agent_id"
              class="flex items-center justify-between p-2.5 bg-surface-container rounded-xl border border-outline-variant/50"
            >
              <div class="flex items-center gap-2.5 min-w-0">
                <span class="font-mono font-bold text-xs text-primary bg-primary/10 w-5 h-5 rounded-lg flex items-center justify-center shrink-0">
                  {{ idx + 1 }}
                </span>
                <span class="text-xs font-semibold text-on-surface truncate">{{ agent.agent_name }}</span>
              </div>
              <span class="font-mono text-xs font-bold text-on-surface-variant shrink-0 bg-surface-container-high px-2 py-0.5 rounded border border-outline-variant">
                {{ agent.call_count.toLocaleString() }}
              </span>
            </div>
            
            <div v-if="!data?.top_agents?.length" class="text-center py-10 text-on-surface-variant text-xs italic">
              Awaiting session metrics logs.
            </div>
          </div>
        </div>

        <div class="text-[10px] text-on-surface-variant/40 font-mono text-center pt-3 border-t border-outline-variant/20">
          SECURE METRICS PIPELINE
        </div>
      </div>
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

function barHeight(count) { 
  return (count / maxCount.value) * 100 
}

const formattedTotalCalls = computed(() => {
  const calls = data.value?.total_calls
  if (calls) {
    return calls >= 1000000 
      ? (calls / 1000000).toFixed(2) + 'M' 
      : calls.toLocaleString()
  }
  return '0'
})

const activeAgentsCount = computed(() => {
  return data.value?.active_agents ?? 0
})



async function fetchMetrics() {
  try {
    const res = await fetch(`/api/v1/metrics/platform?range=${props.timeRange}`)
    if (res.ok) data.value = await res.json()
  } catch (e) {
    console.error('Platform metrics error', e)
  }
}

watch(() => props.timeRange, fetchMetrics, { immediate: true })
</script>

<style scoped>
.icon-circle {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
</style>
