<template>
  <AppLayout>
    <div class="h-full flex flex-col p-6 overflow-hidden">
      <!-- Page header -->
      <div class="flex items-center justify-between mb-6 shrink-0">
        <div>
          <h1 class="font-sans text-2xl font-bold text-white tracking-tight">Intelligence Fleet</h1>
          <p class="font-mono text-[11px] text-on-surface-variant/60 uppercase tracking-wider mt-1">
            {{ agents.length }} agents deployed
          </p>
        </div>
        <button @click="openBuilder(null)"
          class="btn-primary px-5 py-2.5 rounded-xl text-sm font-semibold flex items-center gap-2">
          <span class="material-symbols-outlined text-[18px]">add</span>
          New Agent
        </button>
      </div>

      <!-- Tabs -->
      <div class="flex gap-1 mb-5 shrink-0">
        <button
          v-for="tab in tabs" :key="tab.key"
          @click="activeTab = tab.key"
          :class="[
            'px-4 py-2 rounded-xl font-mono text-[11px] uppercase tracking-wider transition-colors',
            activeTab === tab.key
              ? 'bg-primary/15 text-primary'
              : 'text-on-surface-variant hover:text-white hover:bg-white/5'
          ]"
        >
          {{ tab.label }} ({{ tabCount(tab.key) }})
        </button>
      </div>

      <!-- Agent grid -->
      <div class="flex-1 overflow-y-auto">
        <div v-if="loading" class="flex items-center justify-center h-32">
          <span class="material-symbols-outlined text-4xl text-primary/30 animate-spin">refresh</span>
        </div>
        <div v-else-if="filteredAgents.length === 0" class="flex flex-col items-center justify-center h-48 text-on-surface-variant/40">
          <span class="material-symbols-outlined text-5xl mb-3">smart_toy</span>
          <p class="font-mono text-sm uppercase">No agents in this category</p>
        </div>
        <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          <AgentCard
            v-for="agent in filteredAgents"
            :key="agent.uuid"
            :agent="agent"
            @edit="openBuilder(agent)"
            @clone="cloneAgent(agent)"
            @delete="deleteAgent(agent)"
            @activate="activateAgent"
            @test="openTest"
          />
        </div>
      </div>
    </div>

    <!-- Drawer -->
    <AgentBuilder
      :open="builderOpen"
      :agent="editingAgent"
      @close="builderOpen = false"
      @saved="onSaved"
    />

    <!-- Test Window -->
    <AgentTestWindow
      :open="testOpen"
      :agent="testingAgent"
      @close="testOpen = false; testingAgent = null"
    />
  </AppLayout>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import AppLayout from '@/components/layout/AppLayout.vue'
import AgentCard from '@/components/agents/AgentCard.vue'
import AgentBuilder from '@/components/agents/AgentBuilder.vue'
import AgentTestWindow from '@/components/voice/AgentTestWindow.vue'
import { apiFetch } from '@/composables/useApi'
import { useToastStore } from '@/stores/toast'
import { useAuthStore } from '@/stores/auth'

const toast = useToastStore()
const auth = useAuthStore()
const agents = ref([])
const loading = ref(false)
const activeTab = ref('voice')
const builderOpen = ref(false)
const editingAgent = ref(null)
const testOpen = ref(false)
const testingAgent = ref(null)

const tabs = [
  { key: 'voice', label: 'Voice Agents' },
  { key: 'bi', label: 'BI Agents' },
  { key: 'templates', label: 'Templates' },
]

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
    const updated = await apiFetch(
      `/api/v1/agents/${agent.uuid}/activate`,
      { method: 'POST' }
    )
    // Update agent in agents array
    const idx = agents.value.findIndex(a => a.uuid === agent.uuid)
    if (idx > -1) agents.value[idx] = updated
    toast.show(
      `${agent.name} activated. Webhook ready.`, 
      'success'
    )
  } catch(e) { 
    toast.show(e.message, 'error') 
  }
}

async function deactivateAgent(agent) {
  try {
    const updated = await apiFetch(
      `/api/v1/agents/${agent.uuid}/deactivate`,
      { method: 'POST' }
    )
    const idx = agents.value.findIndex(a => a.uuid === agent.uuid)
    if (idx > -1) agents.value[idx] = updated
    toast.show(`${agent.name} deactivated`, 'success')
  } catch(e) { 
    toast.show(e.message, 'error') 
  }
}

function openTest(agent) {
  testingAgent.value = agent
  testOpen.value = true
}

function openBuilder(agent) {
  editingAgent.value = agent
  builderOpen.value = true
}

function onSaved(agent) {
  const idx = agents.value.findIndex(a => a.uuid === agent.uuid)
  if (idx > -1) agents.value[idx] = agent
  else agents.value.unshift(agent)
}

async function cloneAgent(agent) {
  try {
    const cloned = await apiFetch(`/api/v1/agents/${agent.uuid}/clone`, { method: 'POST' })
    agents.value.unshift(cloned)
    toast.show('Agent cloned successfully', 'success')
  } catch (e) {
    toast.show(e.message, 'error')
  }
}

async function deleteAgent(agent) {
  if (!confirm(`Delete "${agent.name}"?`)) return
  try {
    await apiFetch(`/api/v1/agents/${agent.uuid}`, { method: 'DELETE' })
    agents.value = agents.value.filter(a => a.uuid !== agent.uuid)
    toast.show('Agent deleted', 'success')
  } catch (e) {
    toast.show(e.message, 'error')
  }
}

onMounted(fetchAgents)
</script>
