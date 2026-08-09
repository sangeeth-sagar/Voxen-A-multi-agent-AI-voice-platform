<template>
  <div class="chat-view-container h-full flex flex-col bg-neural-gradient overflow-hidden">
    <!-- Top Action Bar -->
    <header class="flex justify-between items-center px-6 h-16 shrink-0 border-b border-outline-variant/30 bg-surface/40 relative z-30">
      <div class="agent-switcher">
        <label class="switcher-label">Active Chat Agent</label>
        <select v-model="activeAgentUuid" class="agent-select" @change="resetSession">
          <option :value="null" disabled>— Select an agent —</option>
          <option v-for="agent in chatAgents" :key="agent.uuid" :value="agent.uuid">{{ agent.name }}</option>
        </select>
        <span class="ws-status connected" v-if="activeAgent">
          <span class="ws-dot" />
          Ready
        </span>
      </div>

      <div class="flex items-center gap-3">
        <button @click="resetSession" class="btn-micro">
          New Session
        </button>
      </div>
    </header>

    <!-- Error/Setup banners -->
    <div class="banner-area relative z-30 px-6 pt-3 shrink-0" v-if="activeAgent && !activeAgent.llm_key_id">
      <div class="setup-banner mb-2">
        <span class="material-symbols-outlined">key_off</span>
        <div class="setup-banner-text">
          <strong>No API key attached to this agent.</strong>
          <span> Go to Chat Lab → Edit Agent → select key, then save.</span>
        </div>
        <div class="setup-banner-actions">
          <RouterLink to="/chat-lab" class="setup-btn">Fix in Chat Lab →</RouterLink>
        </div>
      </div>
    </div>

    <!-- Chat Messages Interface -->
    <div class="flex-1 flex flex-col p-6 overflow-hidden min-h-0 relative z-10">
      <div class="flex-1 max-w-4xl w-full mx-auto glass-panel border border-outline-variant/50 rounded-2xl flex flex-col overflow-hidden relative">
        <!-- Messages Area -->
        <div class="flex-1 p-6 overflow-y-auto space-y-4" ref="messageBox">
          <div v-if="!activeAgent" class="flex flex-col items-center justify-center h-full text-on-surface-variant/40 space-y-2">
            <span class="material-symbols-outlined text-5xl">forum</span>
            <p class="font-mono text-sm uppercase tracking-wider">Select a Chat Agent from the switcher above</p>
          </div>

          <div v-else-if="messages.length === 0" class="flex flex-col items-center justify-center h-full text-on-surface-variant/40 space-y-2">
            <span class="material-symbols-outlined text-5xl text-primary/30">smart_toy</span>
            <p class="text-sm font-semibold">Start a conversation with {{ activeAgent.name }}</p>
            <p class="text-xs text-on-surface-variant/60">Type a prompt in the input below to test responses.</p>
          </div>

          <div 
            v-for="(msg, idx) in messages" 
            :key="idx" 
            :class="['flex flex-col max-w-[80%] rounded-2xl p-4 text-xs transition-all duration-200 animate-[fadeIn_0.2s_ease-out]', msg.role === 'user' ? 'ml-auto bg-primary/10 text-on-surface border border-primary/20' : 'bg-surface-container-high text-on-surface border border-outline-variant/40']"
          >
            <span class="font-mono text-[9px] uppercase tracking-wider text-on-surface-variant/50 mb-1.5 flex items-center gap-1">
              <span class="material-symbols-outlined text-[12px]">{{ msg.role === 'user' ? 'person' : 'smart_toy' }}</span>
              {{ msg.role === 'user' ? 'You' : (msg.agent_name || 'Agent') }}
            </span>
            <div class="whitespace-pre-wrap leading-relaxed">{{ msg.text }}</div>
            
            <!-- Sources citations -->
            <div v-if="msg.sources && msg.sources.length > 0" class="mt-3 pt-3 border-t border-outline-variant/30">
              <div class="text-[9px] font-mono uppercase tracking-wider text-on-surface-variant/60 mb-1.5 flex items-center gap-1.5">
                <span class="material-symbols-outlined text-[10px]">menu_book</span>
                Document Citations:
              </div>
              <div class="flex flex-wrap gap-1.5">
                <span v-for="src in msg.sources" :key="src" class="px-2 py-0.5 bg-surface-container rounded font-mono text-[9px] text-on-surface-variant/80 border border-outline-variant/30 truncate max-w-full">
                  {{ src }}
                </span>
              </div>
            </div>
          </div>

          <div v-if="loading" class="flex items-center gap-2 text-on-surface-variant/60 text-xs pl-2">
            <span class="material-symbols-outlined text-sm animate-spin">refresh</span>
            {{ activeAgent.name }} is processing response...
          </div>
        </div>

        <!-- Input Form Area -->
        <div v-if="activeAgent" class="p-4 border-t border-outline-variant/40 bg-surface-container/20 flex items-center gap-3">
          <input 
            v-model="inputMsg" 
            type="text" 
            placeholder="Type a message to chat..." 
            class="field-input py-3 flex-1 text-sm input-glow-focus" 
            @keydown.enter.prevent.stop="sendMessage" 
            :disabled="loading" 
          />
          <button 
            @click.prevent.stop="sendMessage" 
            :disabled="loading || !inputMsg.trim()" 
            class="p-3 btn-primary rounded-xl flex items-center justify-center shrink-0 disabled:opacity-50"
          >
            <span class="material-symbols-outlined">send</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { apiFetch } from '@/composables/useApi'
import { useToastStore } from '@/stores/toast'

const toast = useToastStore()
const chatAgents = ref([])
const activeAgentUuid = ref(null)
const inputMsg = ref('')
const loading = ref(false)
const messages = ref([])
const sessionId = ref('')
const messageBox = ref(null)

const activeAgent = computed(() => {
  return chatAgents.value.find(a => a.uuid === activeAgentUuid.value) || null
})

async function fetchAgents() {
  try {
    const list = await apiFetch('/api/v1/agents?my=true')
    chatAgents.value = list.filter(a => !a.is_voice_agent)
    if (chatAgents.value.length > 0) {
      activeAgentUuid.value = chatAgents.value[0].uuid
      resetSession()
    }
  } catch (err) {
    toast.show(err.message, 'error')
  }
}

function resetSession() {
  messages.value = []
  inputMsg.value = ''
  sessionId.value = `chat_${Math.random().toString(36).substring(7)}`
}

function scrollDown() {
  setTimeout(() => {
    if (messageBox.value) {
      messageBox.value.scrollTop = messageBox.value.scrollHeight
    }
  }, 50)
}

async function sendMessage() {
  const text = inputMsg.value.trim()
  if (!text || !activeAgent.value || loading.value) return

  // 1. Append user bubble
  messages.value.push({ role: 'user', text })
  inputMsg.value = ''
  scrollDown()

  // 2. Fetch agent reply
  loading.value = true
  try {
    const res = await apiFetch('/api/v1/chat/message', {
      method: 'POST',
      body: JSON.stringify({
        agent_id: activeAgent.value.id,
        session_id: sessionId.value || undefined,
        message_text: text,
        language: 'en'
      })
    })

    sessionId.value = res.session_id
    messages.value.push({
      role: 'agent',
      text: res.response,
      agent_name: res.agent_name,
      sources: res.sources
    })
  } catch (err) {
    messages.value.push({
      role: 'agent',
      text: `⚠️ Error: ${err.message || 'Unable to load response.'}`,
      agent_name: 'System'
    })
  } finally {
    loading.value = false
    scrollDown()
  }
}

onMounted(() => {
  fetchAgents()
})
</script>

<style scoped>
.agent-switcher {
  display: flex;
  align-items: center;
  gap: 12px;
}
.switcher-label {
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--color-on-surface-variant);
}
.agent-select {
  background: var(--color-surface-container);
  border: 1px solid var(--color-outline-variant);
  color: var(--color-on-surface);
  font-size: 13px;
  font-weight: 600;
  padding: 6px 12px;
  border-radius: 10px;
  outline: none;
  cursor: pointer;
  transition: all 0.2s ease;
}
html.dark .agent-select {
  background: rgba(255, 255, 255, 0.05);
  border-color: rgba(255, 255, 255, 0.1);
  color: #E1EFE6;
}
.ws-status {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  padding: 4px 8px;
  border-radius: 99px;
  border: 1px solid var(--color-success);
  background: var(--color-success-container, rgba(74, 222, 128, 0.12));
  color: var(--color-success);
}
.ws-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--color-success);
  animation: pulse 2s infinite;
}
.btn-micro {
  padding: 6px 12px;
  font-size: 11px;
  font-family: 'JetBrains Mono', monospace;
  text-transform: uppercase;
  background: var(--color-surface-container-high);
  border: 1px solid var(--color-outline-variant);
  border-radius: 8px;
  color: var(--color-on-surface-variant);
  cursor: pointer;
}
.btn-micro:hover {
  background: var(--color-surface-container-highest);
  color: var(--color-on-surface);
}
.setup-banner {
  background: var(--color-primary-container);
  color: var(--color-on-primary-container);
  border: 1px solid var(--color-primary);
  border-radius: 12px;
  padding: 10px 14px;
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 12px;
}
.setup-btn {
  padding: 4px 10px;
  background: var(--color-primary);
  color: var(--color-on-primary);
  font-weight: 600;
  border-radius: 8px;
  text-decoration: none;
  font-size: 11px;
}
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }
@keyframes fadeIn { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: translateY(0); } }
</style>
