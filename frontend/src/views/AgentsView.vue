<template>
  <div class="agents-view h-full flex flex-col p-6 overflow-y-auto">
    <!-- Header -->
    <div class="flex items-center justify-between mb-6 shrink-0 flex-wrap gap-4">
      <div>
        <h1 class="font-sans text-2xl font-bold text-on-surface tracking-tight">Intelligence Fleet</h1>
        <p class="font-mono text-[11px] text-on-surface-variant/60 uppercase tracking-wider mt-1">
          {{ activeNodesCount }} Active Nodes • {{ tabs[0].label }} ({{ tabCount('voice') }} deployed)
        </p>
      </div>
      <button @click="openBuilder(null)"
        class="btn-primary-rect px-5 py-2.5 rounded-xl text-sm font-semibold flex items-center gap-2">
        <span class="material-symbols-outlined text-[18px]">add</span>
        New Node
      </button>
    </div>

    <!-- Category Tabs Navigation -->
    <div class="flex items-center justify-between mb-6 shrink-0 flex-wrap gap-2 border-b border-outline-variant/30 pb-2">
      <div class="flex gap-1">
        <button v-for="tab in tabs" :key="tab.key" @click="activeTab = tab.key"
          :class="[
            'px-4 py-2 rounded-xl font-mono text-[10px] uppercase tracking-wider transition-colors',
            activeTab === tab.key
              ? 'bg-primary/15 text-primary font-bold'
              : 'text-on-surface-variant hover:text-on-surface hover:bg-surface-container-high'
          ]">
          {{ tab.label }} ({{ tabCount(tab.key) }})
        </button>
      </div>
      <div class="flex items-center gap-1.5">
        <button @click="viewMode = 'grid'" :class="['p-1.5 rounded-lg border text-xs', viewMode === 'grid' ? 'border-primary text-primary bg-primary/10' : 'border-outline-variant text-on-surface-variant']">
          <span class="material-symbols-outlined text-sm">grid_view</span>
        </button>
        <button @click="viewMode = 'list'" :class="['p-1.5 rounded-lg border text-xs', viewMode === 'list' ? 'border-primary text-primary bg-primary/10' : 'border-outline-variant text-on-surface-variant']">
          <span class="material-symbols-outlined text-sm">list</span>
        </button>
      </div>
    </div>

    <!-- Agents/Nodes Grid -->
    <div class="flex-1 min-h-[300px]">
      <div v-if="loading" class="flex items-center justify-center h-48">
        <span class="material-symbols-outlined text-4xl text-primary/30 animate-spin">refresh</span>
      </div>
      
      <div v-else-if="filteredAgents.length === 0" class="flex flex-col items-center justify-center h-48 text-on-surface-variant/40 border border-dashed border-outline-variant rounded-2xl">
        <span class="material-symbols-outlined text-5xl mb-3">smart_toy</span>
        <p class="font-mono text-sm uppercase">No agents in this category</p>
      </div>
      
      <div v-else :class="[viewMode === 'grid' ? 'grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4' : 'flex flex-col gap-3']">
        <!-- Node Item Card -->
        <AgentCard v-for="agent in filteredAgents" :key="agent.uuid" :agent="agent"
          @edit="openBuilder(agent)" @clone="cloneAgent(agent)" @delete="deleteAgent(agent)"
          @activate="activateAgent" @deactivate="deactivateAgent" @detail="openDetail" />

        <!-- Deploy New Node Dotted Trigger Card (only in grid mode) -->
        <div 
          v-if="viewMode === 'grid'"
          @click="openBuilder(null)"
          class="border border-dashed border-outline-variant hover:border-primary/50 bg-surface-container/20 hover:bg-primary/5 rounded-2xl p-6 flex flex-col items-center justify-center min-h-[160px] cursor-pointer group transition-all duration-300"
        >
          <div class="w-10 h-10 rounded-full border border-dashed border-outline-variant group-hover:border-primary flex items-center justify-center text-on-surface-variant group-hover:text-primary transition-colors mb-2">
            <span class="material-symbols-outlined text-xl">add</span>
          </div>
          <span class="text-xs font-bold text-on-surface-variant group-hover:text-primary transition-colors">Deploy New Node</span>
          <span class="text-[9px] font-mono text-on-surface-variant/60 mt-1 uppercase tracking-wider">Initialize core engine</span>
        </div>
      </div>
    </div>

    <!-- Modal Builders -->
    <AgentBuilder :open="builderOpen" :agent="editingAgent" @close="builderOpen = false" @saved="onSaved" />
    <AgentDetailPanel :open="detailOpen" :agent="detailAgent" @close="detailOpen = false" @updated="onDetailUpdated" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AgentCard from '@/components/agents/AgentCard.vue'
import AgentBuilder from '@/components/agents/AgentBuilder.vue'
import AgentDetailPanel from '@/components/agents/AgentDetailPanel.vue'
import { apiFetch } from '@/composables/useApi'
import { useToastStore } from '@/stores/toast'

const route = useRoute()
const router = useRouter()
const toast = useToastStore()

// State
const agents = ref([])
const loading = ref(false)
const activeTab = ref('voice')
const builderOpen = ref(false)
const editingAgent = ref(null)
const detailOpen = ref(false)
const detailAgent = ref(null)
const viewMode = ref('grid')

const tabs = [
  { key: 'voice', label: 'Voice Agents' },
  { key: 'bi', label: 'BI Agents' },
  { key: 'templates', label: 'Templates' },
]

const activeNodesCount = computed(() => {
  return agents.value.filter(a => a.is_active).length
})

const filteredAgents = computed(() => {
  if (activeTab.value === 'voice') return agents.value.filter(a => a.is_voice_agent)
  if (activeTab.value === 'bi') return agents.value.filter(a => !a.is_voice_agent && !a.is_template)
  return agents.value.filter(a => a.is_template)
})

function tabCount(key) {
  if (key === 'voice') return agents.value.filter(a => a.is_voice_agent).length
  if (key === 'bi') return agents.value.filter(a => !a.is_voice_agent && !a.is_template).length
  return agents.value.filter(a => a.is_template).length
}

async function fetchAgents() {
  loading.value = true
  try {
    agents.value = await apiFetch('/api/v1/agents')
  } catch (e) {
    toast.show(e.message, 'error')
  } finally {
    loading.value = false
  }
}

async function activateAgent(agent) {
  try {
    const data = await apiFetch(`/api/v1/agents/${agent.uuid}/activate`, { method: 'POST' })
    const idx = agents.value.findIndex(a => a.uuid === agent.uuid)
    if (idx > -1) {
      agents.value[idx] = {
        ...agents.value[idx],
        ...data,
        is_active: true,
      }
      if (detailAgent.value?.uuid === agent.uuid) detailAgent.value = agents.value[idx]
    }
    toast.show(`${agent.name} activated successfully`, 'success')
  } catch(e) {
    toast.show(e.message, 'error')
  }
}

async function deactivateAgent(agent) {
  try {
    await apiFetch(`/api/v1/agents/${agent.uuid}/deactivate`, { method: 'POST' })
    const idx = agents.value.findIndex(a => a.uuid === agent.uuid)
    if (idx > -1) {
      agents.value[idx].is_active = false
      if (detailAgent.value?.uuid === agent.uuid) detailAgent.value.is_active = false
    }
    toast.show(`${agent.name} deactivated`, 'info')
  } catch(e) {
    toast.show(e.message, 'error')
  }
}

function openBuilder(agent) {
  editingAgent.value = agent
  builderOpen.value = true
}

function openDetail(agent) {
  detailAgent.value = agent
  detailOpen.value = true
}

function onDetailUpdated(updated) {
  const idx = agents.value.findIndex(a => a.uuid === updated.uuid)
  if (idx > -1) agents.value[idx] = { ...agents.value[idx], ...updated }
  detailAgent.value = agents.value[idx] || updated
}

async function onSaved(updatedAgent) {
  builderOpen.value = false
  editingAgent.value = null
  await fetchAgents()
  const activeUuid = localStorage.getItem('active_agent')
  if (updatedAgent?.uuid === activeUuid) localStorage.setItem('agent_updated', Date.now().toString())
  toast.show('Agent node configured successfully', 'success')
}

async function cloneAgent(agent) {
  try {
    const cloned = await apiFetch(`/api/v1/agents/${agent.uuid}/clone`, { method: 'POST' })
    agents.value.unshift(cloned)
    toast.show('Agent node duplicated successfully', 'success')
  } catch (e) {
    toast.show(e.message, 'error')
  }
}

async function deleteAgent(agent) {
  if (!confirm(`Are you sure you want to delete agent "${agent.name}"?`)) return
  try {
    await apiFetch(`/api/v1/agents/${agent.uuid}`, { method: 'DELETE' })
    agents.value = agents.value.filter(a => a.uuid !== agent.uuid)
    toast.show('Agent deleted from intelligence fleet', 'success')
  } catch (e) {
    toast.show(e.message, 'error')
  }
}

// Watch for topbar query actions to automatically trigger modal builder
watch(() => route.query.new, (val) => {
  if (val === 'true') {
    openBuilder(null)
    router.replace({ path: '/agents', query: {} })
  }
}, { immediate: true })

onMounted(() => {
  fetchAgents()
})
</script>

<style scoped>
.btn-primary-rect {
  background: var(--color-primary);
  color: var(--color-on-primary);
  font-weight: 600;
  border-radius: 10px;
  border: none;
  padding: 10px 18px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-primary-rect:hover {
  filter: brightness(1.15);
}

html.dark .btn-primary-rect {
  background: #0d3c2f;
  color: #a5d1aa;
  border: 1px solid rgba(165, 209, 170, 0.2);
}

html.dark .btn-primary-rect:hover {
  background: #134e3e;
  box-shadow: 0 0 10px rgba(165, 209, 170, 0.25);
}
</style>
