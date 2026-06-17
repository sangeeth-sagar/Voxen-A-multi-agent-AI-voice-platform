<template>
  <div class="profile-view-container h-full overflow-y-auto">
    <!-- Header Actions -->
    <header class="settings-header">
      <div>
        <h1 class="font-sans text-2xl font-bold text-on-surface tracking-tight">Profile Settings</h1>
        <p class="text-xs text-on-surface-variant mt-1">Manage your identity, credentials, and API connections.</p>
      </div>
      <div class="flex items-center gap-3">
        <button @click="discardChanges" class="btn-secondary">Discard Changes</button>
        <button @click="saveConfiguration" :disabled="usernameLoading || pwLoading" class="btn-primary-rect">
          Save Configuration
        </button>
      </div>
    </header>

    <div class="settings-grid max-w-4xl">
      <!-- Main Settings Card -->
      <section class="glass-panel rounded-2xl p-6 space-y-6">
        <div class="profile-meta-row w-full">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label class="field-label">Full Identity Label</label>
              <input v-model="usernameForm.username" type="text" placeholder="e.g. Alexander Vance" class="field-input" />
            </div>
            <div>
              <label class="field-label">System Email</label>
              <input :value="user?.email" type="email" class="field-input disabled-input" disabled />
            </div>
          </div>
        </div>
      </section>

      <!-- Credentials change card -->
      <section class="glass-panel rounded-2xl p-6 space-y-4">
        <h2 class="section-title">
          <span class="material-symbols-outlined text-primary">security</span>
          Update Credentials
        </h2>
        
        <form @submit.prevent="changePassword" class="grid grid-cols-1 md:grid-cols-3 gap-4 items-end">
          <div>
            <label class="field-label">Current Password</label>
            <input v-model="pwForm.current_password" type="password" placeholder="••••••••" class="field-input text-xs" />
          </div>
          <div>
            <label class="field-label">New Password</label>
            <input v-model="pwForm.new_password" type="password" placeholder="min. 8 chars" class="field-input text-xs" />
          </div>
          <div class="flex gap-2">
            <div class="flex-1">
              <label class="field-label">Confirm Password</label>
              <input v-model="pwForm.confirm_password" type="password" placeholder="repeat password" class="field-input text-xs" />
            </div>
            <button type="submit" :disabled="pwLoading" class="btn-primary-rect h-[38px] px-4 font-semibold text-xs whitespace-nowrap flex items-center gap-1">
              <span v-if="pwLoading" class="material-symbols-outlined text-xs animate-spin">refresh</span>
              Update
            </button>
          </div>
        </form>
        <p v-if="pwError" class="text-error text-xs mt-2 font-mono">{{ pwError }}</p>
      </section>

      <!-- External Provider API Keys Section (Functional App Logic) -->
      <section class="glass-panel rounded-2xl p-6 space-y-6">
        <div>
          <h2 class="section-title">
            <span class="material-symbols-outlined text-primary">key</span>
            Provider Integration Keys
          </h2>
          <p class="text-[11px] text-on-surface-variant mt-1">Configure individual API keys to enable LLM providers and voice synthesis engines.</p>
        </div>

        <!-- Add Key Form -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-2 bg-surface-container/60 p-3 rounded-xl border border-outline-variant/40">
          <select v-model="newKey.provider" class="field-input text-xs">
            <optgroup label="LLM Providers">
              <option value="gemini">Google Gemini</option>
              <option value="openai">OpenAI</option>
              <option value="claude">Anthropic Claude</option>
            </optgroup>
            <optgroup label="Voice / TTS">
              <option value="elevenlabs">ElevenLabs</option>
              <option value="groq">Groq (STT + TTS)</option>
              <option value="deepgram">Deepgram</option>
              <option value="azure_tts">Azure TTS</option>
            </optgroup>
          </select>
          <input v-model="newKey.label" placeholder="Label (e.g. Gemini Key)" class="field-input text-xs" />
          <input v-model="newKey.api_key" type="password" placeholder="Paste API key..." class="field-input text-xs" />
          <button @click="addKey" :disabled="adding" class="btn-primary-rect h-[38px] w-full flex items-center justify-center gap-1 font-semibold text-xs">
            <span v-if="adding" class="material-symbols-outlined text-xs animate-spin">refresh</span>
            <span v-else class="material-symbols-outlined text-xs">add</span>
            {{ adding ? 'Adding…' : 'Add Key' }}
          </button>
        </div>
        <p v-if="keyError" class="text-error text-xs font-mono">{{ keyError }}</p>

        <!-- Keys List -->
        <div class="keys-list space-y-2">
          <div v-if="loadingKeys" class="flex items-center justify-center py-6 gap-2">
            <span class="material-symbols-outlined text-primary animate-spin">refresh</span>
            <span class="font-mono text-xs text-on-surface-variant">Syncing provider keys…</span>
          </div>
          <template v-else>
            <div v-for="key in apiKeys" :key="key.id" class="key-item flex items-center justify-between p-3 bg-surface-container rounded-xl border border-outline-variant/50">
              <div class="flex items-center gap-3">
                <span class="provider-badge" :class="key.provider">{{ providerLabel(key.provider) }}</span>
                <span class="text-xs font-semibold">{{ key.label }}</span>
                <span class="text-[10px] font-mono text-on-surface-variant/70">{{ key.key_preview || '••••••••' }}</span>
              </div>
              <div class="flex items-center gap-3">
                <span class="text-[9px] font-mono text-on-surface-variant bg-surface-container-high px-2 py-0.5 rounded border border-outline-variant">
                  {{ agentCountForKey(key.id) }} active agent(s)
                </span>
                <button @click="deleteKey(key.id)" class="text-error hover:text-red-400 p-1 flex items-center" title="Delete key">
                  <span class="material-symbols-outlined text-base">delete</span>
                </button>
              </div>
            </div>
            <div v-if="apiKeys.length === 0" class="text-center py-6 text-on-surface-variant text-xs italic">
              No custom keys configured. Add keys above to use custom integrations.
            </div>
          </template>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useApiKeys } from '@/composables/useApiKeys'
import { apiFetch } from '@/composables/useApi'
import { useToastStore } from '@/stores/toast'
const auth = useAuthStore()
const toast = useToastStore()
const user = computed(() => auth.user)
const { apiKeys, fetchKeys, addApiKey, deleteApiKey } = useApiKeys()

// Form references
const usernameForm = ref({ username: user.value?.username || '' })
const usernameLoading = ref(false)

const pwForm = ref({ current_password: '', new_password: '', confirm_password: '' })
const pwLoading = ref(false)
const pwError = ref('')

// Discard changes resets forms back to state
function discardChanges() {
  usernameForm.value.username = user.value?.username || ''
  pwForm.value = { current_password: '', new_password: '', confirm_password: '' }
  toast.show('Changes discarded', 'info')
}

// Save config saves local items and updates username on API
async function saveConfiguration() {
  usernameLoading.value = true
  try {
    const data = await apiFetch('/api/v1/auth/me', {
      method: 'PUT',
      body: JSON.stringify(usernameForm.value)
    })
    auth.setAuth(auth.token, data)
    toast.show('Configuration saved successfully', 'success')
  } catch (e) {
    toast.show(e.message || 'Failed to update username', 'error')
  } finally {
    usernameLoading.value = false
  }
}

async function changePassword() {
  if (pwForm.value.new_password !== pwForm.value.confirm_password) {
    pwError.value = 'Passwords do not match'
    return
  }
  pwLoading.value = true
  pwError.value = ''
  try {
    await apiFetch('/api/v1/auth/change-password', {
      method: 'POST',
      body: JSON.stringify({
        current_password: pwForm.value.current_password,
        new_password: pwForm.value.new_password
      })
    })
    toast.show('Password updated successfully', 'success')
    pwForm.value = { current_password: '', new_password: '', confirm_password: '' }
  } catch (e) {
    pwError.value = e.message
  } finally {
    pwLoading.value = false
  }
}

// Keys management
const newKey = ref({ provider: 'gemini', label: '', api_key: '' })
const adding = ref(false)
const keyError = ref('')
const loadingKeys = ref(false)
const agents = ref([])

function agentCountForKey(keyId) {
  return agents.value.filter(a => a.llm_key_id === keyId || a.tts_key_id === keyId).length
}

async function addKey() {
  keyError.value = ''
  if (!newKey.value.api_key || !newKey.value.label) {
    keyError.value = 'Label and API key are required.'
    return
  }
  adding.value = true
  try {
    await addApiKey(newKey.value)
    toast.show('API key added', 'success')
    newKey.value = { provider: 'gemini', label: '', api_key: '' }
    await fetchKeys()
  } catch (e) {
    keyError.value = e.message
  } finally {
    adding.value = false
  }
}

async function deleteKey(id) {
  if (!confirm('Delete this API key? This cannot be undone.')) return
  try {
    await deleteApiKey(id)
    toast.show('API key deleted', 'success')
    await fetchKeys()
  } catch (e) {
    toast.show(e.message, 'error')
  }
}

const PROVIDER_LABELS = {
  gemini: 'Gemini',
  openai: 'OpenAI',
  claude: 'Claude',
  elevenlabs: 'ElevenLabs',
  groq: 'Groq',
  deepgram: 'Deepgram',
  azure_tts: 'Azure TTS'
}
function providerLabel(p) {
  return PROVIDER_LABELS[p] || p
}



onMounted(async () => {
  loadingKeys.value = true
  await fetchKeys()
  loadingKeys.value = false
  try {
    const data = await apiFetch('/api/v1/agents')
    agents.value = Array.isArray(data) ? data : (data?.agents || data?.items || [])
  } catch {
    agents.value = []
  }
})
</script>

<style scoped>
.profile-view-container {
  padding: 24px;
}

.settings-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  gap: 16px;
  flex-wrap: wrap;
}

.settings-grid {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* Form Styles */
.field-label {
  display: block;
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--color-outline);
  margin-bottom: 6px;
  font-weight: 700;
}

.field-input {
  width: 100%;
  background: var(--color-surface-container);
  border: 1px solid var(--color-outline-variant);
  border-radius: 12px;
  padding: 10px 14px;
  font-size: 13px;
  color: var(--color-on-surface);
  outline: none;
  transition: all 0.2s ease;
  font-family: inherit;
}

html.dark .field-input {
  background: rgba(255, 255, 255, 0.04);
  border-color: rgba(255, 255, 255, 0.08);
}

.field-input:focus {
  border-color: var(--color-primary);
  box-shadow: 0 0 8px rgba(14, 108, 74, 0.15);
}

html.dark .field-input:focus {
  border-color: #a5d1aa;
  box-shadow: 0 0 8px rgba(165, 209, 170, 0.15);
}

.disabled-input {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Avatar edit styling */
.avatar-wrapper {
  display: inline-block;
  flex-shrink: 0;
}

.avatar-box {
  background: var(--color-surface-container-high);
}

.camera-btn {
  position: absolute;
  bottom: 0;
  right: 0;
  background: var(--color-primary);
  color: var(--color-on-primary);
  border: 2px solid var(--color-surface);
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: var(--shadow-level-1);
  transition: all 0.15s ease;
}

.camera-btn:hover {
  transform: scale(1.1);
}

/* Badges */
.badge-operator {
  display: inline-flex;
  align-items: center;
  background: rgba(14, 108, 74, 0.12);
  color: var(--color-success);
  border: 1px solid rgba(14, 108, 74, 0.25);
  font-size: 10px;
  font-weight: 700;
  font-family: 'JetBrains Mono', monospace;
  text-transform: uppercase;
  padding: 4px 10px;
  border-radius: 99px;
  letter-spacing: 0.02em;
}

html.dark .badge-operator {
  background: rgba(165, 209, 170, 0.12);
  color: #a5d1aa;
  border-color: rgba(165, 209, 170, 0.25);
}

.badge-access {
  background: var(--color-surface-container-high);
  color: var(--color-on-surface-variant);
  border: 1px solid var(--color-outline-variant);
  font-size: 10px;
  font-weight: 700;
  font-family: 'JetBrains Mono', monospace;
  text-transform: uppercase;
  padding: 4px 10px;
  border-radius: 99px;
}

html.dark .badge-access {
  background: rgba(255, 255, 255, 0.05);
  border-color: rgba(255, 255, 255, 0.08);
}

/* Buttons */
.btn-primary-rect {
  background: var(--color-primary);
  color: var(--color-on-primary);
  font-weight: 600;
  font-size: 13px;
  border-radius: 10px;
  border: none;
  padding: 10px 18px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-primary-rect:hover {
  filter: brightness(1.15);
}

.btn-primary-rect:active {
  transform: scale(0.98);
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

.btn-secondary {
  background: transparent;
  color: var(--color-on-surface-variant);
  border: 1px solid var(--color-outline-variant);
  font-weight: 600;
  font-size: 13px;
  border-radius: 10px;
  padding: 10px 18px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-secondary:hover {
  background: var(--color-surface-container-high);
  color: var(--color-on-surface);
}

html.dark .btn-secondary {
  border-color: rgba(255, 255, 255, 0.12);
}

html.dark .btn-secondary:hover {
  background: rgba(255, 255, 255, 0.04);
}

/* Custom provider integration key badges */
.provider-badge {
  font-family: 'JetBrains Mono', monospace;
  font-size: 8px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  padding: 3px 6px;
  border-radius: 4px;
  background: var(--color-primary-container);
  color: var(--color-primary);
  border: 1px solid var(--color-primary);
}

.provider-badge.gemini { background: rgba(66, 133, 244, 0.12); color: #4d8af0; border-color: rgba(66, 133, 244, 0.3); }
.provider-badge.openai { background: rgba(16, 163, 127, 0.12); color: #10a37f; border-color: rgba(16, 163, 127, 0.3); }
.provider-badge.claude { background: rgba(204, 119, 34, 0.12); color: #cc7722; border-color: rgba(204, 119, 34, 0.3); }
.provider-badge.elevenlabs { background: rgba(109, 151, 115, 0.12); color: var(--color-secondary); border-color: rgba(14, 108, 74, 0.3); }
.provider-badge.groq { background: rgba(251, 146, 60, 0.12); color: #fb923c; border-color: rgba(251, 146, 60, 0.3); }
.provider-badge.deepgram { background: rgba(56, 189, 248, 0.12); color: #38bdf8; border-color: rgba(56, 189, 248, 0.3); }
.provider-badge.azure_tts { background: rgba(99, 102, 241, 0.12); color: #818cf8; border-color: rgba(99, 102, 241, 0.3); }

.section-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 16px;
  font-weight: 700;
  color: var(--color-on-surface);
}
</style>
