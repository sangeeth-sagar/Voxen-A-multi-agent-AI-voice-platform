<template>
  <div class="telegram-bots-view p-6 space-y-6 overflow-y-auto h-full">
    <!-- Header -->
    <header class="flex items-center justify-between shrink-0">
      <div>
        <h1 class="font-sans text-2xl font-bold text-on-surface tracking-tight">Telegram Bot Gateways</h1>
        <p class="font-mono text-[11px] text-on-surface-variant/60 uppercase tracking-wider mt-1">
          Centralized Telegram channel managers and agent linkages
        </p>
      </div>
    </header>

    <!-- Localhost Webhook Warning Banner -->
    <div v-if="isLocalhost" class="p-4 bg-amber-500/10 border border-amber-500/30 rounded-2xl flex items-start gap-3 text-xs text-on-surface">
      <span class="material-symbols-outlined text-amber-500 mt-0.5">warning</span>
      <div>
        <div class="font-bold text-amber-500">Local Development Webhook Warning</div>
        <p class="text-on-surface-variant mt-1 leading-relaxed">
          You are running the platform locally (localhost). Telegram's cloud servers cannot deliver webhook messages to <code>localhost</code> and require a secure public <strong>HTTPS</strong> URL.<br />
          <span class="block mt-1">
            <strong>To activate Telegram messages:</strong> 
            Start an HTTPS tunnel (e.g. run <code>ngrok http 8000</code>), copy the tunnel URL (e.g. <code>https://xxxx.ngrok-free.app</code>), 
            and set it as the <code>WEBHOOK_BASE_URL</code> in your backend <code>.env</code> file.
          </span>
        </p>
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- Register Bot Form -->
      <div class="glass-panel rounded-2xl p-6 border border-outline-variant/50 space-y-5 lg:col-span-1 h-fit">
        <div>
          <h3 class="text-sm font-bold text-on-surface flex items-center gap-1.5">
            <span class="material-symbols-outlined text-base">smart_toy</span>
            Register New Bot
          </h3>
          <p class="text-[10px] text-on-surface-variant/60 leading-normal mt-1">
            Connect a Telegram Bot token to an active Chat Agent to handle automated message replies.
          </p>
        </div>

        <form @submit.prevent="connectTelegram" class="space-y-4">
          <!-- Bot Token -->
          <div class="form-group space-y-1.5">
            <label class="field-label text-[10px] uppercase font-bold tracking-wider">Bot API Token</label>
            <div class="flex gap-2">
              <input 
                v-model="tgToken" 
                type="text" 
                placeholder="123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ" 
                class="field-input text-xs py-2.5 input-glow-focus flex-1" 
                required
              />
              <button 
                type="button" 
                @click="verifyToken" 
                :disabled="verifyingToken || !tgToken.trim()" 
                class="px-4 py-2.5 bg-surface-container-high hover:bg-surface-container-highest border border-outline-variant rounded-xl text-xs font-semibold text-on-surface transition-colors flex items-center gap-1.5 shrink-0 disabled:opacity-50"
              >
                <span v-if="verifyingToken" class="material-symbols-outlined text-sm animate-spin">refresh</span>
                Verify
              </button>
            </div>
            <p class="text-[10px] text-on-surface-variant/50 leading-normal">
              To create a bot, search for <a href="https://t.me/BotFather" target="_blank" class="text-primary hover:underline font-bold">@BotFather</a> on Telegram.
            </p>
          </div>

          <!-- Verification result -->
          <Transition name="fade">
            <div v-if="verifiedBot" class="p-3 bg-success/10 border border-success/30 rounded-xl flex items-start gap-2.5 text-xs text-on-surface">
              <span class="material-symbols-outlined text-success text-base mt-0.5">check_circle</span>
              <div class="min-w-0 flex-1">
                <div class="font-bold">Bot Verified Successfully!</div>
                <div class="text-[11px] text-on-surface-variant mt-0.5">
                  Name: <strong class="text-on-surface">{{ verifiedBot.first_name }}</strong><br />
                  Username: <strong class="text-primary">@{{ verifiedBot.username }}</strong>
                </div>
              </div>
            </div>
            <div v-else-if="verificationError" class="p-3 bg-error/10 border border-error/30 rounded-xl flex items-start gap-2.5 text-xs text-error">
              <span class="material-symbols-outlined text-base mt-0.5">error</span>
              <div class="min-w-0 flex-1">
                <div class="font-bold">Verification Failed</div>
                <div class="text-[10px] opacity-80 mt-0.5">{{ verificationError }}</div>
              </div>
            </div>
          </Transition>

          <!-- Select Chat Agent -->
          <div class="form-group space-y-1.5">
            <label class="field-label text-[10px] uppercase font-bold tracking-wider">Link Chat Agent</label>
            <select v-model="selectedAgentId" class="field-input text-xs py-2.5" required>
              <option :value="null" disabled>— Select Chat Agent —</option>
              <option v-for="agent in chatAgents" :key="agent.id" :value="agent.id">
                {{ agent.name }}
              </option>
            </select>
          </div>

          <!-- Select Voxen API Key (Optional) -->
          <div v-if="selectedAgentId && selectedAgentKeys.length > 0" class="form-group space-y-1.5">
            <label class="field-label text-[10px] uppercase font-bold tracking-wider text-primary">Voxen API Key Security</label>
            <select v-model="selectedVoxenApiKeyId" class="field-input text-xs py-2.5 border-primary/30 focus:border-primary">
              <option :value="null">— No API Key Security —</option>
              <option v-for="key in selectedAgentKeys" :key="key.id" :value="key.id">
                {{ key.label }} ({{ key.key_preview }})
              </option>
            </select>
            <p class="text-[9px] text-on-surface-variant/60 leading-normal">
              Select an API key to secure incoming Telegram messages. If the key is revoked, the bot gateway will instantly stop responding.
            </p>
          </div>

          <button 
            type="submit" 
            :disabled="tgLoading || !tgToken.trim() || !selectedAgentId" 
            class="w-full py-2.5 btn-primary rounded-xl text-xs font-semibold transition-colors flex items-center justify-center gap-1.5 disabled:opacity-50"
          >
            <span v-if="tgLoading" class="material-symbols-outlined text-sm animate-spin">refresh</span>
            <span v-else class="material-symbols-outlined text-sm">link</span>
            Link Telegram Bot
          </button>
        </form>
      </div>

      <!-- Configured Bots Registry Table/List -->
      <div class="glass-panel rounded-2xl p-6 border border-outline-variant/50 space-y-4 lg:col-span-2">
        <div>
          <h3 class="text-sm font-bold text-on-surface flex items-center gap-1.5">
            <span class="material-symbols-outlined text-base text-primary">send</span>
            Configured Gateways
          </h3>
          <p class="text-[10px] text-on-surface-variant/60 leading-normal mt-1">
            Active Telegram bots receiving message updates and callback redirects.
          </p>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mt-2">
          <div 
            v-for="bot in telegramBots" :key="bot.id" 
            class="glass-card rounded-xl p-4 border border-outline-variant/40 hover:border-primary/20 transition-all duration-300 flex flex-col justify-between space-y-4"
          >
            <div class="flex items-start justify-between">
              <div class="flex items-center gap-2.5 min-w-0">
                <div class="w-9 h-9 rounded-xl bg-primary/10 text-primary flex items-center justify-center shrink-0">
                  <span class="material-symbols-outlined">smart_toy</span>
                </div>
                <div class="min-w-0">
                  <h4 class="font-sans font-bold text-sm text-on-surface truncate" :title="'@' + bot.bot_username">@{{ bot.bot_username }}</h4>
                  <span class="text-[9px] font-mono text-on-surface-variant/60 uppercase tracking-wider">Gateway Bot</span>
                </div>
              </div>
              <span class="px-2 py-0.5 bg-success/15 text-success rounded text-[9px] font-bold tracking-wider font-mono shrink-0">ACTIVE</span>
            </div>

            <div class="space-y-2 border-t border-outline-variant/30 pt-3 text-[11px]">
              <div class="flex justify-between items-center gap-2">
                <span class="text-on-surface-variant/60">Linked Agent:</span>
                <span class="font-bold text-on-surface truncate">{{ getLinkedAgentName(bot.agent_id) }}</span>
              </div>
              <div class="flex justify-between items-center gap-2">
                <span class="text-on-surface-variant/60">Voxen API Key:</span>
                <span :class="['font-mono font-bold text-[10px]', bot.voxen_api_key_id ? 'text-primary' : 'text-on-surface-variant/50']">
                  {{ bot.voxen_api_key_id ? 'Secured (Key ID: ' + bot.voxen_api_key_id + ')' : 'None (Unsecured)' }}
                </span>
              </div>
              <div class="flex flex-col space-y-1">
                <span class="text-on-surface-variant/60">Webhook URL:</span>
                <div class="flex items-center gap-1.5 bg-surface-container/40 border border-outline-variant/30 rounded px-2 py-1 font-mono text-[9px] text-on-surface-variant select-all truncate" :title="bot.webhook_url">
                  {{ bot.webhook_url || 'Generating...' }}
                </div>
              </div>
            </div>

            <div class="flex justify-end pt-1">
              <button 
                @click="disconnectTelegram(bot.id)" 
                class="py-1.5 px-3 border border-error/20 hover:bg-error/5 text-error rounded-lg text-[10px] font-bold transition-colors inline-flex items-center gap-1"
              >
                <span class="material-symbols-outlined text-[12px]">link_off</span>
                Disconnect
              </button>
            </div>
          </div>

          <div v-if="telegramBots.length === 0" class="col-span-full text-center py-12 text-on-surface-variant/50 italic border border-dashed border-outline-variant/40 rounded-xl">
            <span class="material-symbols-outlined text-2xl mb-1 text-on-surface-variant/30">forum</span>
            <div class="text-xs">No Telegram bot gateways configured. Use the registration card to link one.</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, computed } from 'vue'
import { apiFetch } from '@/composables/useApi'
import { useToastStore } from '@/stores/toast'

const toast = useToastStore()

// State
const chatAgents = ref([])
const telegramBots = ref([])
const selectedAgentId = ref(null)
const tgToken = ref('')
const tgLoading = ref(false)

const selectedAgentKeys = ref([])
const selectedVoxenApiKeyId = ref(null)

watch(selectedAgentId, async (newVal) => {
  selectedVoxenApiKeyId.value = null
  selectedAgentKeys.value = []
  if (newVal) {
    try {
      selectedAgentKeys.value = await apiFetch(`/api/v1/voxen-keys/agent/${newVal}`)
    } catch (err) {
      console.error("Failed to load agent API keys:", err)
    }
  }
})

const verifyingToken = ref(false)
const verifiedBot = ref(null)
const verificationError = ref('')

const isLocalhost = computed(() => {
  const hostname = window.location.hostname
  return hostname === 'localhost' || hostname === '127.0.0.1'
})

watch(tgToken, () => {
  verifiedBot.value = null
  verificationError.value = ''
})

async function fetchInitialData() {
  try {
    // 1. Get all chat agents
    const list = await apiFetch('/api/v1/agents?my=true')
    chatAgents.value = list.filter(a => !a.is_voice_agent)
    if (chatAgents.value.length > 0) {
      selectedAgentId.value = chatAgents.value[0].id
    }

    // 2. Get all linked bots
    telegramBots.value = await apiFetch('/api/v1/telegram/bots')
  } catch (err) {
    console.error('Failed to load Telegram bot data:', err)
  }
}

async function verifyToken() {
  const token = tgToken.value.trim()
  if (!token) return
  
  verifyingToken.value = true
  verificationError.value = ''
  verifiedBot.value = null
  try {
    const res = await apiFetch('/api/v1/telegram/verify', {
      method: 'POST',
      body: JSON.stringify({ telegram_token: token })
    })
    if (res.ok) {
      verifiedBot.value = {
        first_name: res.first_name,
        username: res.username
      }
      toast.show(`Bot verified: @${res.username}`, 'success')
    }
  } catch (err) {
    verificationError.value = err.message || 'Verification failed. Please check the token.'
    toast.show('Failed to verify token', 'error')
  } finally {
    verifyingToken.value = false
  }
}

async function connectTelegram() {
  if (!tgToken.value.trim() || !selectedAgentId.value) return
  tgLoading.value = true
  try {
    const res = await apiFetch('/api/v1/telegram/bots', {
      method: 'POST',
      body: JSON.stringify({
        agent_id: selectedAgentId.value,
        telegram_token: tgToken.value.trim(),
        voxen_api_key_id: selectedVoxenApiKeyId.value
      })
    })
    toast.show(res.message || 'Telegram Bot link registered successfully!', 'success')
    tgToken.value = ''
    verifiedBot.value = null
    await fetchInitialData()
  } catch (err) {
    toast.show(err.message || 'Failed to connect Telegram Bot', 'error')
  } finally {
    tgLoading.value = false
  }
}

async function disconnectTelegram(id) {
  if (!confirm('Are you sure you want to disconnect this Telegram Bot?')) return
  try {
    await apiFetch(`/api/v1/telegram/bots/${id}`, {
      method: 'DELETE'
    })
    toast.show('Telegram Bot link removed', 'info')
    await fetchInitialData()
  } catch (err) {
    toast.show(err.message || 'Failed to disconnect bot link', 'error')
  }
}

function getLinkedAgentName(agentId) {
  const match = chatAgents.value.find(a => a.id === agentId)
  return match ? match.name : `Agent ID: ${agentId}`
}

function getWebhookEndpoint(token) {
  const host = window.location.origin.replace('5173', '8000') // backend proxy fallback
  return `${host}/api/v1/telegram/webhook/${token}`
}

onMounted(() => {
  fetchInitialData()
})
</script>

<style scoped>
.field-label {
  display: block;
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--color-on-surface-variant);
  margin-bottom: 6px;
}

.field-input, select {
  background: var(--color-surface-container) !important;
  border: 1px solid var(--color-outline-variant) !important;
  color: var(--color-on-surface) !important;
  outline: none;
}
html.dark .field-input, html.dark select {
  background: rgba(255, 255, 255, 0.05) !important;
  border-color: rgba(255, 255, 255, 0.1) !important;
  color: #E1EFE6 !important;
}

.field-input:focus {
  border-color: var(--color-primary) !important;
}

.fade-enter-active, .fade-leave-active {
  transition: opacity 0.25s ease;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}
</style>
