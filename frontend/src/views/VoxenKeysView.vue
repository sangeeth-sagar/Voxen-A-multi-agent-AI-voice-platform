<template>
  <div class="voxen-keys-view p-6 space-y-6 overflow-y-auto h-full">
    <!-- Header -->
    <header class="flex items-center justify-between shrink-0">
      <div>
        <h1 class="font-sans text-2xl font-bold text-on-surface tracking-tight">Voxen API Keys</h1>
        <p class="font-mono text-[11px] text-on-surface-variant/60 uppercase tracking-wider mt-1">
          Secure external webhooks, website widgets, and chatbot integrations
        </p>
      </div>
    </header>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- Agent Selection Panel -->
      <div class="glass-panel rounded-2xl p-5 border border-outline-variant/50 lg:col-span-1 space-y-4">
        <div>
          <h3 class="text-sm font-bold text-on-surface">Select Agent Node</h3>
          <p class="text-[11px] text-on-surface-variant">Choose an agent to manage its secure API keys</p>
        </div>

        <div class="space-y-2 max-h-[500px] overflow-y-auto pr-1">
          <button 
            v-for="agent in agents" 
            :key="agent.id"
            @click="selectAgent(agent)"
            :class="[
              'w-full flex items-center justify-between p-3 rounded-xl border text-left transition-all duration-200',
              selectedAgent?.id === agent.id 
                ? 'bg-primary/10 border-primary shadow-[0_0_12px_rgba(14,108,74,0.15)]' 
                : 'bg-surface-container/30 border-outline-variant/40 hover:bg-surface-container-high/40'
            ]"
          >
            <div class="flex items-center gap-3 min-w-0">
              <div :class="['w-8 h-8 rounded-lg flex items-center justify-center shrink-0', selectedAgent?.id === agent.id ? 'bg-primary/20 text-primary' : 'bg-surface-container-highest text-on-surface-variant']">
                <span class="material-symbols-outlined text-sm">
                  {{ agent.is_voice_agent ? 'mic' : 'chat_bubble' }}
                </span>
              </div>
              <div class="min-w-0">
                <div class="text-xs font-semibold text-on-surface truncate">{{ agent.name }}</div>
                <div class="text-[10px] text-on-surface-variant/60 uppercase tracking-wider font-mono mt-0.5">
                  {{ agent.is_voice_agent ? 'Voice Agent' : 'Chat Agent' }}
                </div>
              </div>
            </div>
            <span class="material-symbols-outlined text-sm text-on-surface-variant/60">chevron_right</span>
          </button>
          
          <div v-if="agents.length === 0" class="text-center py-12 text-on-surface-variant/50 italic text-xs">
            No agent nodes deployed.
          </div>
        </div>
      </div>

      <!-- Keys Management Panel -->
      <div class="lg:col-span-2 space-y-6">
        <div v-if="selectedAgent" class="glass-panel rounded-2xl p-6 border border-outline-variant/50 space-y-6">
          <div class="flex items-center justify-between border-b border-outline-variant/20 pb-4">
            <div>
              <h2 class="font-sans text-base font-bold text-on-surface">{{ selectedAgent.name }} Keys</h2>
              <p class="text-xs text-on-surface-variant">Manage secure webhook access tokens for this node</p>
            </div>
            <button 
              @click="showCreateModal = true" 
              class="px-4 py-2 bg-primary hover:bg-primary-hover text-white text-xs font-semibold rounded-xl transition-all flex items-center gap-1.5 shadow-sm"
            >
              <span class="material-symbols-outlined text-sm">add</span>
              Generate Key
            </button>
          </div>

          <!-- Alert for newly generated key (only shown once) -->
          <div v-if="newlyGeneratedKey" class="p-4 bg-primary/10 border border-primary/30 rounded-2xl space-y-3">
            <div class="flex items-start gap-2.5">
              <span class="material-symbols-outlined text-primary text-base mt-0.5">verified_user</span>
              <div>
                <h4 class="text-xs font-bold text-primary">New API Key Generated Successfully</h4>
                <p class="text-[11px] text-on-surface-variant mt-0.5 leading-relaxed">
                  For security, we only display this full key once. Copy it now and save it in a safe place. You will not be able to retrieve it again.
                </p>
              </div>
            </div>
            
            <div class="flex items-center gap-2 bg-surface-container/60 border border-outline-variant/40 rounded-xl p-3 font-mono text-xs text-on-surface select-all">
              <span class="truncate flex-1">{{ newlyGeneratedKey.full_key }}</span>
              <button 
                @click="copyToClipboard(newlyGeneratedKey.full_key)"
                class="p-1.5 hover:bg-surface-container-highest rounded-lg text-primary transition-colors flex items-center justify-center shrink-0"
                title="Copy Key"
              >
                <span class="material-symbols-outlined text-sm">{{ copyIcon }}</span>
              </button>
            </div>
          </div>

          <!-- Key Listing Table -->
          <div class="space-y-4">
            <h3 class="text-xs font-bold uppercase tracking-wider text-on-surface-variant/70 font-mono">Active Keys</h3>
            
            <div class="overflow-x-auto">
              <table class="w-full text-left border-collapse">
                <thead>
                  <tr class="border-b border-outline-variant/40 font-mono text-[10px] text-on-surface-variant/50 uppercase tracking-wider">
                    <th class="py-2.5 px-2">Label</th>
                    <th class="py-2.5 px-2">API Key Preview</th>
                    <th class="py-2.5 px-2">Created</th>
                    <th class="py-2.5 px-2 text-right">Action</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-outline-variant/20 text-xs">
                  <tr v-for="key in activeKeys" :key="key.id" class="hover:bg-surface-container/10">
                    <td class="py-3 px-2 font-semibold text-on-surface">{{ key.label }}</td>
                    <td class="py-3 px-2 font-mono text-[11px] text-on-surface-variant">{{ key.key_preview }}</td>
                    <td class="py-3 px-2 text-on-surface-variant/70 font-mono text-[10px]">{{ formatDate(key.created_at) }}</td>
                    <td class="py-3 px-2 text-right">
                      <button 
                        @click="revokeKey(key.id)"
                        class="px-2.5 py-1 text-[11px] font-semibold text-error hover:bg-error-container rounded-lg transition-colors border border-error/20"
                      >
                        Revoke
                      </button>
                    </td>
                  </tr>
                  
                  <tr v-if="activeKeys.length === 0">
                    <td colspan="4" class="text-center py-12 text-on-surface-variant/50 italic">
                      No active API keys configured for this node. Click Generate Key to create one.
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <div v-else class="glass-panel rounded-2xl p-12 border border-outline-variant/50 text-center flex flex-col items-center justify-center space-y-3 h-full min-h-[300px]">
          <div class="w-12 h-12 rounded-full bg-surface-container-highest text-on-surface-variant/60 flex items-center justify-center">
            <span class="material-symbols-outlined text-2xl">key</span>
          </div>
          <div>
            <h3 class="text-sm font-bold text-on-surface">No Node Selected</h3>
            <p class="text-xs text-on-surface-variant mt-1 max-w-[280px]">
              Select an agent node from the left panel to inspect and manage its secure external access keys.
            </p>
          </div>
        </div>
      </div>
    </div>

    <!-- Create Key Modal -->
    <div v-if="showCreateModal" class="modal-backdrop">
      <div class="modal-card">
        <h3 class="text-sm font-bold text-on-surface mb-2">Generate Voxen API Key</h3>
        <p class="text-xs text-on-surface-variant mb-4">
          Provide a descriptive label to identify this key (e.g. "Corporate Website Chat Widget").
        </p>
        
        <input 
          v-model="newKeyLabel" 
          type="text" 
          placeholder="Key Label..." 
          class="field-input text-xs py-2.5 input-glow-focus mb-5 w-full"
          @keyup.enter="generateKey"
        />

        <div class="flex items-center justify-end gap-2">
          <button @click="closeModal" class="px-4 py-2 hover:bg-surface-container rounded-xl text-xs font-semibold text-on-surface-variant transition-colors border border-outline-variant/20">
            Cancel
          </button>
          <button 
            @click="generateKey" 
            :disabled="!newKeyLabel.trim() || modalLoading" 
            class="px-4 py-2 bg-primary hover:bg-primary-hover text-white text-xs font-semibold rounded-xl transition-all disabled:opacity-50 flex items-center gap-1.5"
          >
            <span v-if="modalLoading" class="material-symbols-outlined text-xs animate-spin">refresh</span>
            Generate
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { apiFetch } from '@/composables/useApi'
import { useToastStore } from '@/stores/toast'

const toast = useToastStore()

// State
const agents = ref([])
const selectedAgent = ref(null)
const activeKeys = ref([])

const showCreateModal = ref(false)
const newKeyLabel = ref('')
const modalLoading = ref(false)
const newlyGeneratedKey = ref(null)

const copyIcon = ref('content_copy')

async function fetchAgents() {
  try {
    agents.value = await apiFetch('/api/v1/agents?my=true')
    if (agents.value.length > 0) {
      selectAgent(agents.value[0])
    }
  } catch (err) {
    toast.show('Failed to fetch agent list', 'error')
  }
}

async function selectAgent(agent) {
  selectedAgent.value = agent
  newlyGeneratedKey.value = null
  newKeyLabel.value = ''
  await fetchAgentKeys()
}

async function fetchAgentKeys() {
  if (!selectedAgent.value) return
  try {
    activeKeys.value = await apiFetch(`/api/v1/voxen-keys/agent/${selectedAgent.value.id}`)
  } catch (err) {
    toast.show('Failed to fetch API keys for this agent', 'error')
  }
}

async function generateKey() {
  const label = newKeyLabel.value.trim()
  if (!label || !selectedAgent.value) return
  
  modalLoading.value = true
  try {
    const res = await apiFetch(`/api/v1/voxen-keys/agent/${selectedAgent.value.id}`, {
      method: 'POST',
      body: JSON.stringify({ label })
    })
    newlyGeneratedKey.value = res
    toast.show('Voxen API Key generated successfully!', 'success')
    closeModal()
    await fetchAgentKeys()
  } catch (err) {
    toast.show(err.message || 'Failed to generate API Key', 'error')
  } finally {
    modalLoading.value = false
  }
}

async function revokeKey(keyId) {
  if (!confirm('Are you sure you want to revoke this API Key? Any external systems using it will lose access immediately.')) return
  try {
    await apiFetch(`/api/v1/voxen-keys/${keyId}`, {
      method: 'DELETE'
    })
    toast.show('API Key revoked successfully', 'success')
    await fetchAgentKeys()
    if (newlyGeneratedKey.value && newlyGeneratedKey.value.id === keyId) {
      newlyGeneratedKey.value = null
    }
  } catch (err) {
    toast.show(err.message || 'Failed to revoke API Key', 'error')
  }
}

function copyToClipboard(text) {
  navigator.clipboard.writeText(text).then(() => {
    copyIcon.value = 'check'
    toast.show('API Key copied to clipboard!', 'success')
    setTimeout(() => {
      copyIcon.value = 'content_copy'
    }, 2000)
  })
}

function closeModal() {
  showCreateModal.value = false
  newKeyLabel.value = ''
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return d.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false
  })
}

onMounted(() => {
  fetchAgents()
})
</script>

<style scoped>
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
  animation: fade-in 0.2s ease-out;
}

.modal-card {
  width: 90%;
  max-width: 400px;
  background: var(--color-surface);
  border: 1px solid var(--color-outline-variant);
  border-radius: 20px;
  padding: 24px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
  animation: scale-up 0.2s cubic-bezier(0.34, 1.56, 0.64, 1);
}

html.dark .modal-card {
  background: rgba(0, 24, 16, 0.95);
  border-color: rgba(255, 255, 255, 0.08);
}

@keyframes fade-in {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes scale-up {
  from { transform: scale(0.9); opacity: 0; }
  to { transform: scale(1); opacity: 1; }
}
</style>
