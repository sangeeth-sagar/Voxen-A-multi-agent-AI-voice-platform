<template>
  <div class="space-y-6">
    <!-- Platform Channels Summary Cards -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-6">
      <!-- Active Voice Agents -->
      <div class="glass-panel rounded-2xl p-5 flex items-center justify-between border border-outline-variant/50 relative overflow-hidden">
        <div class="space-y-1">
          <span class="text-xs text-on-surface-variant font-medium">Voice Agents</span>
          <h2 class="font-sans text-3xl font-extrabold text-on-surface tracking-tight">
            {{ voiceAgentsCount }}
          </h2>
          <div class="flex items-center gap-1 mt-1">
            <span class="text-[10px] text-on-surface-variant font-mono">Neural voice nodes active</span>
          </div>
        </div>
        <div class="icon-circle bg-primary/10 text-primary">
          <span class="material-symbols-outlined icon-filled">mic</span>
        </div>
      </div>

      <!-- Active Chat Agents -->
      <div class="glass-panel rounded-2xl p-5 flex items-center justify-between border border-outline-variant/50 relative overflow-hidden">
        <div class="space-y-1">
          <span class="text-xs text-on-surface-variant font-medium">Chat Agents</span>
          <h2 class="font-sans text-3xl font-extrabold text-on-surface tracking-tight">
            {{ chatAgentsCount }}
          </h2>
          <div class="flex items-center gap-1 mt-1">
            <span class="text-[10px] text-on-surface-variant font-mono">Text engines active</span>
          </div>
        </div>
        <div class="icon-circle bg-primary/10 text-primary">
          <span class="material-symbols-outlined icon-filled">chat_bubble</span>
        </div>
      </div>

      <!-- Connected Telegram Bots -->
      <div class="glass-panel rounded-2xl p-5 flex items-center justify-between border border-outline-variant/50 relative overflow-hidden">
        <div class="space-y-1">
          <span class="text-xs text-on-surface-variant font-medium">Telegram Integrations</span>
          <h2 class="font-sans text-3xl font-extrabold text-on-surface tracking-tight">
            {{ telegramBotsCount }}
          </h2>
          <div class="flex items-center gap-1 mt-1">
            <span class="text-[10px] text-on-surface-variant font-mono">Connected bot nodes</span>
          </div>
        </div>
        <div class="icon-circle bg-primary/10 text-primary">
          <span class="material-symbols-outlined icon-filled">send</span>
        </div>
      </div>

      <!-- System Calls -->
      <div class="glass-panel rounded-2xl p-5 flex items-center justify-between border border-outline-variant/50 relative overflow-hidden">
        <div class="space-y-1">
          <span class="text-xs text-on-surface-variant font-medium">Total System Calls</span>
          <h2 class="font-sans text-3xl font-extrabold text-on-surface tracking-tight">
            {{ formattedTotalCalls }}
          </h2>
          <div class="flex items-center gap-1 mt-1">
            <span class="text-[10px] text-on-surface-variant font-mono">Combined voice/API turns</span>
          </div>
        </div>
        <div class="icon-circle bg-primary/10 text-success">
          <span class="material-symbols-outlined icon-filled text-success">check_circle</span>
        </div>
      </div>
    </div>

    <!-- Daily Trend Chart & Top Agents List -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- Daily Volume Trend Chart -->
      <div class="glass-panel rounded-2xl p-5 border border-outline-variant/50 lg:col-span-2 space-y-4">
        <div class="flex justify-between items-start">
          <div>
            <h3 class="text-sm font-bold text-on-surface">Daily Session Volume</h3>
            <p class="text-[11px] text-on-surface-variant">Combined daily transaction load history</p>
          </div>
          <span class="text-[10px] text-primary font-mono font-bold">{{ trendCount }} intervalsSynced</span>
        </div>

        <div v-if="data?.daily_trend?.length" class="h-48 flex items-end gap-1.5 pt-4">
          <div 
            v-for="day in data.daily_trend" 
            :key="day.date"
            class="flex-1 bg-primary rounded-t transition-all duration-300 hover:opacity-100"
            :style="{ height: barHeight(day.count) + '%', opacity: '0.8' }"
            :title="day.date + ': ' + day.count + ' transactions'"
          ></div>
        </div>
        
        <div v-else class="h-48 flex items-center justify-center border border-dashed border-outline-variant/30 rounded-xl bg-surface-container/20">
          <span class="text-xs text-on-surface-variant/50 italic">No metrics logs retrieved.</span>
        </div>

        <div v-if="data?.daily_trend?.length" class="flex justify-between text-[9px] font-mono text-on-surface-variant/60 pt-2 border-t border-outline-variant/20">
          <span>{{ data.daily_trend[0]?.date }}</span>
          <span>{{ data.daily_trend[Math.floor(data.daily_trend.length / 2)]?.date }}</span>
          <span>{{ data.daily_trend[data.daily_trend.length - 1]?.date }}</span>
        </div>
      </div>

      <!-- Top Agents List -->
      <div class="glass-panel rounded-2xl p-5 border border-outline-variant/50 lg:col-span-1 space-y-4 flex flex-col justify-between">
        <div class="space-y-4">
          <div>
            <h3 class="text-sm font-bold text-on-surface">Top Nodes</h3>
            <p class="text-[11px] text-on-surface-variant">Ranked by volume shares</p>
          </div>

          <div class="space-y-2 max-h-56 overflow-y-auto pr-1">
            <div 
              v-for="(agent, idx) in sortedTopAgents" 
              :key="agent.id"
              class="flex items-center justify-between p-2.5 bg-surface-container rounded-xl border border-outline-variant/50"
            >
              <div class="flex items-center gap-2.5 min-w-0">
                <span class="font-mono font-bold text-xs text-primary bg-primary/10 w-5 h-5 rounded-lg flex items-center justify-center shrink-0">
                  {{ idx + 1 }}
                </span>
                <span class="material-symbols-outlined text-sm text-on-surface-variant shrink-0">
                  {{ agent.is_voice_agent ? 'mic' : 'chat_bubble' }}
                </span>
                <span class="text-xs font-semibold text-on-surface truncate">{{ agent.name }}</span>
              </div>
              <span class="font-mono text-xs font-bold text-on-surface-variant shrink-0 bg-surface-container-high px-2 py-0.5 rounded border border-outline-variant">
                {{ agent.use_count || 0 }}
              </span>
            </div>
            
            <div v-if="sortedTopAgents.length === 0" class="text-center py-10 text-on-surface-variant text-xs italic">
              Awaiting node metric shares.
            </div>
          </div>
        </div>

        <div class="text-[10px] text-on-surface-variant/40 font-mono text-center pt-3 border-t border-outline-variant/20">
          NEURAL MONITOR PIPELINE
        </div>
      </div>
    </div>

    <!-- Integrations & Active Channels Registry -->
    <div class="glass-panel rounded-2xl p-6 border border-outline-variant/50 space-y-4">
      <div>
        <h3 class="text-sm font-bold text-on-surface">Active Integrations Registry</h3>
        <p class="text-[11px] text-on-surface-variant">Active integration configurations and channel statuses</p>
      </div>

      <div class="overflow-x-auto">
        <table class="w-full text-left border-collapse">
          <thead>
            <tr class="border-b border-outline-variant/60 font-mono text-[10px] text-on-surface-variant/60 uppercase tracking-wider">
              <th class="py-3 px-2">Agent Node</th>
              <th class="py-3 px-2">Type</th>
              <th class="py-3 px-2">Knowledge Base</th>
              <th class="py-3 px-2">Web Chat Sandbox</th>
              <th class="py-3 px-2">Telegram Link</th>
              <th class="py-3 px-2">Webhook Status</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-outline-variant/30 text-xs">
            <tr v-for="agent in agentList" :key="agent.id" class="hover:bg-surface-container/20 transition-colors">
              <td class="py-3.5 px-2 font-semibold text-on-surface">{{ agent.name }}</td>
              <td class="py-3.5 px-2">
                <span class="inline-flex items-center gap-1 font-mono text-[10px] text-on-surface-variant">
                  <span class="material-symbols-outlined text-[12px]">{{ agent.is_voice_agent ? 'mic' : 'chat_bubble' }}</span>
                  {{ agent.is_voice_agent ? 'Voice' : 'Chat' }}
                </span>
              </td>
              <td class="py-3.5 px-2">
                <span :class="['inline-flex items-center gap-1 font-semibold text-[10px]', agent.kb_enabled ? 'text-primary' : 'text-on-surface-variant/50']">
                  <span class="material-symbols-outlined text-[12px]">database</span>
                  {{ agent.kb_enabled ? 'Indexed' : 'Off' }}
                </span>
              </td>
              <td class="py-3.5 px-2">
                <span class="inline-flex items-center gap-1 text-[10px] text-primary font-semibold">
                  <span class="material-symbols-outlined text-[12px]">check_circle</span>
                  Ready
                </span>
              </td>
              <td class="py-3.5 px-2">
                <span v-if="getAgentTgBot(agent.id)" class="inline-flex items-center gap-1 font-mono text-[10px] text-primary font-bold">
                  <span class="material-symbols-outlined text-[12px]">send</span>
                  @{{ getAgentTgBot(agent.id).bot_username }}
                </span>
                <span v-else class="text-on-surface-variant/40 italic text-[10px]">—</span>
              </td>
              <td class="py-3.5 px-2">
                <span :class="['led-circle shrink-0 mt-0.5', agent.is_active ? 'bg-success shadow-[0_0_8px_rgba(74,222,128,0.5)]' : 'bg-outline-variant']" />
              </td>
            </tr>
            <tr v-if="agentList.length === 0">
              <td colspan="6" class="text-center py-10 text-on-surface-variant/50 italic">No agent nodes deployed.</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { apiFetch } from '@/composables/useApi'

const props = defineProps({ timeRange: String })

const data = ref(null)
const agentList = ref([])
const telegramBotsList = ref([])

const voiceAgentsCount = computed(() => {
  return agentList.value.filter(a => a.is_voice_agent).length
})

const chatAgentsCount = computed(() => {
  return agentList.value.filter(a => !a.is_voice_agent).length
})

const telegramBotsCount = computed(() => {
  return telegramBotsList.value.length
})

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

const trendCount = computed(() => {
  return data.value?.daily_trend?.length ?? 0
})

const sortedTopAgents = computed(() => {
  return [...agentList.value]
    .sort((a, b) => (b.use_count || 0) - (a.use_count || 0))
    .slice(0, 5)
})

function getAgentTgBot(agentId) {
  return telegramBotsList.value.find(b => b.agent_id === agentId)
}

async function fetchMetrics() {
  try {
    data.value = await apiFetch(`/api/v1/metrics/platform?range=${props.timeRange}`)
  } catch (e) {
    console.error('Platform metrics error', e)
  }
}

async function fetchBotsAndAgents() {
  try {
    agentList.value = await apiFetch('/api/v1/agents?my=true')
  } catch (e) {
    console.error('Fetch agents error', e)
  }

  try {
    telegramBotsList.value = await apiFetch('/api/v1/telegram/bots')
  } catch (e) {
    console.error('Fetch telegram bots error', e)
  }
}

watch(() => props.timeRange, async () => {
  await fetchMetrics()
  await fetchBotsAndAgents()
}, { immediate: true })
</script>

<style scoped>
.icon-circle {
  width: 42px;
  height: 42px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.led-circle {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
}
</style>
