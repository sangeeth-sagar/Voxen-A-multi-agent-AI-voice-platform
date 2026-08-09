<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="open" class="fixed inset-0 z-[100] flex justify-end">
        <div @click="$emit('close')" class="absolute inset-0 bg-black/40 dark:bg-black/60 backdrop-blur-sm" />

        <Transition name="drawer">
          <div v-if="open" class="relative z-10 w-[460px] h-full glass-panel flex flex-col overflow-hidden">
            <div class="px-7 py-6 border-b border-outline-variant flex items-center justify-between shrink-0">
              <div>
                <h2 class="font-sans font-bold text-lg text-on-surface">Agent Details</h2>
                <p class="font-mono text-[10px] text-on-surface-variant/60 uppercase tracking-widest mt-0.5">
                  {{ agent?.name || '—' }}
                </p>
              </div>
              <button @click="$emit('close')" class="p-2 hover:bg-surface-container-high rounded-xl transition-colors text-on-surface-variant hover:text-on-surface">
                <span class="material-symbols-outlined">close</span>
              </button>
            </div>

            <div class="flex-1 overflow-y-auto p-7 space-y-6">
              <section>
                <h3 class="section-title-sm">Activation</h3>
                <div class="flex items-center gap-3">
                  <span :class="['status-pill', agent?.is_active ? 'active' : 'inactive']">
                    <span class="dot" />
                    {{ agent?.is_active ? 'Active' : 'Inactive' }}
                  </span>
                  <button v-if="!agent?.is_active" @click="generateWebhook" class="btn-secondary-sm">
                    <span class="material-symbols-outlined text-sm">webhook</span>
                    Activate & Generate Webhook
                  </button>
                </div>
              </section>

              <section class="webhook-section">
                <h3 class="section-title-sm">External Webhook</h3>
                <p class="hint">Use this URL to trigger this agent from any external platform or automation suite.</p>

                <div v-if="webhookUrl" class="webhook-display">
                  <code class="webhook-url">{{ webhookUrl }}</code>
                  <button @click="copyWebhook" class="btn-copy" title="Copy URL">
                    <span class="material-symbols-outlined">{{ copied ? 'check' : 'content_copy' }}</span>
                  </button>
                </div>
                <div v-if="webhookUrl" class="webhook-payload-hint">
                  <div class="hint-label">POST JSON payload:</div>
                  <pre class="payload">{ "text": "...", "session_id": "...", "language": "en", "api_key": "your_voxen_api_key_here" }</pre>
                </div>

                <button v-if="!webhookUrl" @click="generateWebhook" class="btn-secondary-sm">
                  <span class="material-symbols-outlined">rocket_launch</span>
                  Activate & Generate Webhook
                </button>
              </section>

              <section>
                <h3 class="section-title-sm">Metadata</h3>
                <dl class="meta-grid">
                  <div><dt>Type</dt><dd>{{ agent?.is_voice_agent ? 'Voice Agent' : 'Chat Agent' }}</dd></div>
                  <div><dt>Uses</dt><dd>{{ agent?.use_count ?? 0 }}</dd></div>
                  <div v-if="agent?.voice_language"><dt>Language</dt><dd>{{ agent.voice_language }}</dd></div>
                  <div v-if="agent?.wake_word"><dt>Wake Word</dt><dd>{{ agent.wake_word }}</dd></div>
                </dl>
              </section>

              <!-- Memory summary card -->
              <section v-if="agent?.is_voice_agent">
                <h3 class="section-title-sm">Conversation Memory</h3>
                <div class="relative bg-surface-container-low border border-outline-variant/60 rounded-xl p-3.5 space-y-2">
                  <div class="flex items-center gap-1.5 mb-1.5">
                    <span class="material-symbols-outlined text-[14px] text-on-surface-variant/70">psychology</span>
                    <span class="text-[11px] uppercase tracking-widest text-on-surface-variant/60 font-mono">Current Memory</span>
                  </div>
                  <p :class="['text-xs leading-relaxed pr-10', memoryText ? 'text-on-surface' : 'text-on-surface-variant/50 italic']">
                    {{ memoryText || 'No memory yet — talk to this agent to build one.' }}
                  </p>
                  <button v-if="memoryText" @click="clearMemory" type="button" class="absolute bottom-3.5 right-3.5 text-error text-xs font-semibold hover:opacity-80 transition-opacity">
                    Clear
                  </button>
                </div>
              </section>

              <!-- Telegram Integration Status (Read-Only) -->
              <section class="border-t border-outline-variant/60 pt-5 space-y-4">
                <h3 class="section-title-sm flex items-center gap-1.5">
                  <span class="material-symbols-outlined text-sm">smart_toy</span>
                  Telegram Channel Link
                </h3>
                <div v-if="tgBot" class="flex items-center justify-between p-3.5 bg-surface-container/30 border border-outline-variant/50 rounded-xl">
                  <div class="flex items-center gap-2 text-xs">
                    <span class="material-symbols-outlined text-primary text-base">smart_toy</span>
                    <span class="font-bold">@{{ tgBot.bot_username }}</span>
                  </div>
                  <span class="status-pill active !py-1 !px-2.5 !text-[9px]">Active</span>
                </div>
                <div v-else class="p-3.5 bg-surface-container/20 border border-outline-variant/40 rounded-xl flex items-center justify-between text-xs">
                  <span class="text-on-surface-variant/70 italic text-[11px]">No Telegram Bot linked</span>
                  <RouterLink to="/telegram-bots" class="text-primary hover:underline text-[10px] font-bold uppercase tracking-wider flex items-center gap-1">
                    Manage link
                    <span class="material-symbols-outlined text-xs">arrow_forward</span>
                  </RouterLink>
                </div>
              </section>

              <!-- Chat Sandbox Panel (Web Chat widget preview) -->
              <section class="border-t border-outline-variant/60 pt-5 space-y-4">
                <h3 class="section-title-sm flex items-center gap-1.5">
                  <span class="material-symbols-outlined text-sm">chat_bubble</span>
                  Chatbot Sandbox
                </h3>
                <p class="hint">Interact with the agent's text chatbot engine and view citations from its pgvector index.</p>

                <div class="border border-outline-variant/60 rounded-xl bg-surface-container/10 flex flex-col h-[280px] overflow-hidden">
                  <!-- Messages Container -->
                  <div class="flex-1 p-3 overflow-y-auto space-y-2.5" ref="chatMessagesBox">
                    <div v-if="chatMessages.length === 0" class="flex flex-col items-center justify-center h-full text-on-surface-variant/40 text-xs italic">
                      <span class="material-symbols-outlined text-2xl mb-1 text-on-surface-variant/30">forum</span>
                      Send a message to start sandbox chat
                    </div>
                    
                    <div v-for="(msg, idx) in chatMessages" :key="idx" :class="['flex flex-col max-w-[85%] rounded-2xl p-3 text-xs', msg.role === 'user' ? 'ml-auto bg-primary/10 text-on-surface border border-primary/20' : 'bg-surface-container-high text-on-surface border border-outline-variant/40']">
                      <span class="font-mono text-[9px] uppercase tracking-wider text-on-surface-variant/50 mb-1">
                        {{ msg.role === 'user' ? 'You' : (msg.agent_name || 'Agent') }}
                      </span>
                      <div class="whitespace-pre-wrap leading-relaxed">{{ msg.text }}</div>
                      
                      <!-- Document Citation Sources -->
                      <div v-if="msg.sources && msg.sources.length > 0" class="mt-2 pt-2 border-t border-outline-variant/30">
                        <div class="text-[9px] font-mono uppercase tracking-wider text-on-surface-variant/60 mb-1 flex items-center gap-1">
                          <span class="material-symbols-outlined text-[10px]">menu_book</span> Citations:
                        </div>
                        <div class="flex flex-wrap gap-1">
                          <span v-for="src in msg.sources" :key="src" class="px-1.5 py-0.5 bg-surface-container rounded font-mono text-[9px] text-on-surface-variant/80 border border-outline-variant/30 truncate max-w-full">
                            {{ src }}
                          </span>
                        </div>
                      </div>
                    </div>
                    
                    <div v-if="chatLoading" class="flex items-center gap-2 text-on-surface-variant/60 text-xs pl-2">
                      <span class="material-symbols-outlined text-sm animate-spin">refresh</span>
                      Generating response...
                    </div>
                  </div>

                  <!-- Send Form -->
                  <div class="p-2 border-t border-outline-variant/40 bg-surface-container/30 flex items-center gap-2">
                    <input v-model="chatInput" type="text" placeholder="Type sandbox message..." class="field-input text-xs py-1.5 flex-1" @keydown.enter.prevent.stop="sendSandboxMessage" :disabled="chatLoading" />
                    <button @click.prevent.stop="sendSandboxMessage" :disabled="chatLoading || !chatInput.trim()" class="p-2 btn-primary rounded-xl flex items-center justify-center shrink-0 disabled:opacity-50">
                      <span class="material-symbols-outlined text-sm">send</span>
                    </button>
                  </div>
                </div>
              </section>
            </div>
          </div>
        </Transition>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { apiFetch } from '@/composables/useApi'
import { useToastStore } from '@/stores/toast'

const props = defineProps({ open: Boolean, agent: { type: Object, default: null } })
const emit = defineEmits(['close', 'updated'])
const toast = useToastStore()

const apiUrl = import.meta.env.VITE_API_URL || ''
const localAgent = ref(null)
const copied = ref(false)

const webhookUrl = computed(() => {
  if (!localAgent.value) return ''
  if (localAgent.value.webhook_url) {
    return localAgent.value.webhook_url.startsWith('http') ? localAgent.value.webhook_url : `${apiUrl}${localAgent.value.webhook_url}`
  }
  if (localAgent.value.webhook_token) return `${apiUrl}/api/v1/webhook/agent/${localAgent.value.webhook_token}`
  return ''
})

const memoryText = ref('')

async function fetchMemory() {
  if (!props.agent?.uuid) {
    memoryText.value = ''
    return
  }
  try {
    const data = await apiFetch(`/api/v1/agents/${props.agent.uuid}/memory`)
    memoryText.value = data.summary || ''
  } catch (e) {
    memoryText.value = ''
  }
}

async function clearMemory() {
  if (!confirm("Are you sure you want to clear this agent's conversation memory?")) return
  try {
    await apiFetch(`/api/v1/agents/${props.agent.uuid}/memory`, { method: 'DELETE' })
    memoryText.value = ''
    toast.show('Conversation memory cleared', 'success')
  } catch (e) {
    toast.show(e.message || 'Failed to clear memory', 'error')
  }
}

// Telegram connection state variables
const tgBot = ref(null)
const tgWebhookUrl = ref('')

// Sandbox chatbot variables
const chatInput = ref('')
const chatLoading = ref(false)
const chatMessages = ref([])
const chatSessionId = ref('')
const chatMessagesBox = ref(null)

async function fetchTelegramBot() {
  if (!props.agent?.id) {
    tgBot.value = null
    tgWebhookUrl.value = ''
    return
  }
  try {
    const list = await apiFetch('/api/v1/telegram/bots')
    const match = list.find(b => b.agent_id === props.agent.id)
    if (match) {
      tgBot.value = match
      tgWebhookUrl.value = `${apiUrl}/api/v1/telegram/webhook/${match.telegram_token}`
    } else {
      tgBot.value = null
      tgWebhookUrl.value = ''
    }
  } catch (err) {
    console.error('Failed to fetch Telegram bot:', err)
  }
}

function scrollToBottom() {
  setTimeout(() => {
    if (chatMessagesBox.value) {
      chatMessagesBox.value.scrollTop = chatMessagesBox.value.scrollHeight
    }
  }, 50)
}

async function sendSandboxMessage() {
  const text = chatInput.value.trim()
  if (!text || !props.agent?.id || chatLoading.value) return

  // User message turn
  chatMessages.value.push({ role: 'user', text })
  chatInput.value = ''
  scrollToBottom()

  chatLoading.value = true
  try {
    const res = await apiFetch('/api/v1/chat/message', {
      method: 'POST',
      body: JSON.stringify({
        agent_id: props.agent.id,
        session_id: chatSessionId.value || undefined,
        message_text: text,
        language: 'en'
      })
    })
    
    // Update session_id from response
    chatSessionId.value = res.session_id

    // Agent response turn
    chatMessages.value.push({
      role: 'agent',
      text: res.response,
      agent_name: res.agent_name,
      sources: res.sources
    })
  } catch (err) {
    chatMessages.value.push({
      role: 'agent',
      text: `⚠️ Error: ${err.message || 'Failed to get response.'}`,
      agent_name: 'System'
    })
  } finally {
    chatLoading.value = false
    scrollToBottom()
  }
}

watch(() => props.agent, (a) => {
  localAgent.value = a ? { ...a } : null
  chatMessages.value = []
  chatSessionId.value = `sandbox_${Math.random().toString(36).substring(7)}`
  chatInput.value = ''
  if (a) {
    fetchTelegramBot()
    if (a.is_voice_agent) {
      fetchMemory()
    } else {
      memoryText.value = ''
    }
  } else {
    tgBot.value = null
    tgWebhookUrl.value = ''
    memoryText.value = ''
  }
}, { immediate: true })

async function generateWebhook() {
  if (!localAgent.value) return
  try {
    const data = await apiFetch(`/api/v1/agents/${localAgent.value.uuid}/activate`, { method: 'POST' })
    const baseUrl = apiUrl
    localAgent.value = {
      ...localAgent.value, ...data,
      webhook_token: data.webhook_token || localAgent.value.webhook_token,
      webhook_url: data.webhook_url
        ? (data.webhook_url.startsWith('http') ? data.webhook_url : `${baseUrl}${data.webhook_url}`)
        : (data.webhook_token ? `${baseUrl}/api/v1/webhook/agent/${data.webhook_token}` : localAgent.value.webhook_url),
      is_active: true,
    }
    emit('updated', localAgent.value)
    toast.show('Webhook URL generated', 'success')
  } catch (e) { toast.show(e.message, 'error') }
}

async function copyWebhook() {
  if (!webhookUrl.value) return
  try {
    await navigator.clipboard.writeText(webhookUrl.value)
    copied.value = true
    toast.show('Webhook URL copied!', 'success')
    setTimeout(() => { copied.value = false }, 2000)
  } catch (e) { toast.show('Failed to copy', 'error') }
}
</script>

<style scoped>
.section-title-sm {
  font-size: 11px;
  font-family: 'JetBrains Mono', monospace;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--color-on-surface-variant);
  margin-bottom: 8px;
}

.status-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 600;
  font-family: 'JetBrains Mono', monospace;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.status-pill .dot { width: 6px; height: 6px; border-radius: 50%; }

.status-pill.active {
  background: var(--color-success-container, rgba(74, 222, 128, 0.12));
  color: var(--color-success);
  border: 1px solid var(--color-success);
}
.status-pill.active .dot { background: var(--color-success); animation: pulse 2s infinite; }

.status-pill.inactive {
  background: var(--color-surface-container-high);
  color: var(--color-outline);
  border: 1px solid var(--color-outline-variant);
}
.status-pill.inactive .dot { background: var(--color-outline); }

.btn-secondary-sm {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  border-radius: 10px;
  background: var(--color-primary-container);
  color: var(--color-primary);
  border: 1px solid var(--color-primary);
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.15s ease;
  font-family: inherit;
}
.btn-secondary-sm:hover { filter: brightness(1.1); }

.webhook-section {
  background: var(--color-surface-container-low);
  border: 1px solid var(--color-outline-variant);
  border-radius: 12px;
  padding: 14px;
}

html.dark .webhook-section {
  background: rgba(255, 255, 255, 0.02);
  border-color: rgba(255, 255, 255, 0.06);
}

.hint { font-size: 12px; color: var(--color-outline); margin-bottom: 10px; line-height: 1.5; }

.webhook-display {
  display: flex;
  align-items: center;
  gap: 8px;
  background: var(--color-surface-container);
  border: 1px solid var(--color-outline-variant);
  border-radius: 8px;
  padding: 8px 10px;
  margin-bottom: 12px;
  overflow: hidden;
}

html.dark .webhook-display {
  background: rgba(0, 0, 0, 0.3);
  border-color: rgba(255, 255, 255, 0.08);
}

.webhook-url {
  flex: 1;
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  color: var(--color-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  background: transparent;
}

.btn-copy {
  background: var(--color-primary-container);
  border: 1px solid var(--color-primary);
  color: var(--color-primary);
  border-radius: 6px;
  padding: 4px 6px;
  cursor: pointer;
  flex-shrink: 0;
  transition: background 0.15s ease;
}
.btn-copy:hover { filter: brightness(1.1); }
.btn-copy .material-symbols-outlined { font-size: 16px; }

.webhook-payload-hint {
  background: var(--color-surface-container);
  border-radius: 6px;
  padding: 8px 10px;
  font-size: 11px;
}

html.dark .webhook-payload-hint { background: rgba(0, 0, 0, 0.3); }

.hint-label {
  font-family: 'JetBrains Mono', monospace;
  font-size: 9px;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--color-outline);
  margin-bottom: 4px;
}

.payload {
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  color: var(--color-secondary);
  white-space: pre-wrap;
  word-break: break-all;
  margin: 0;
}

.meta-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  margin: 0;
}

.meta-grid > div {
  background: var(--color-surface-container);
  border-radius: 8px;
  padding: 8px 10px;
  border: 1px solid var(--color-outline-variant);
}

html.dark .meta-grid > div {
  background: rgba(255, 255, 255, 0.03);
  border-color: rgba(255, 255, 255, 0.05);
}

.meta-grid dt {
  font-family: 'JetBrains Mono', monospace;
  font-size: 9px;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--color-outline);
  margin-bottom: 2px;
}

.meta-grid dd {
  font-size: 13px;
  color: var(--color-on-surface);
  margin: 0;
  font-weight: 500;
}

@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }
</style>
