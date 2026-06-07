<template>
  <div class="profile-view">
    <div class="max-w-3xl mx-auto space-y-6">

      <!-- Profile hero -->
      <section class="profile-section glass-panel rounded-3xl p-8 flex flex-col sm:flex-row items-center sm:items-start gap-6">
        <div class="relative">
          <div class="w-24 h-24 rounded-2xl bg-gradient-to-br from-primary/30 to-secondary-container/50 border border-primary/20 flex items-center justify-center">
            <span class="material-symbols-outlined text-primary text-5xl icon-filled">person</span>
          </div>
        </div>

        <div class="flex-1 text-center sm:text-left">
          <h1 class="font-sans text-3xl font-bold text-white tracking-tight">
            {{ user?.username || user?.full_name || '—' }}
          </h1>
          <p class="text-on-surface-variant mt-1">{{ user?.email }}</p>
          <div class="flex items-center gap-2 mt-3 justify-center sm:justify-start flex-wrap">
            <span :class="[
              'px-3 py-1 rounded-full font-mono text-[10px] uppercase tracking-wider font-bold',
              user?.is_superadmin
                ? 'bg-error/15 text-error border border-error/30'
                : 'bg-primary/10 text-primary border border-primary/20'
            ]">
              {{ user?.is_superadmin ? 'superadmin' : (user?.role || 'user') }}
            </span>
            <span :class="['px-3 py-1 rounded-full font-mono text-[10px] uppercase tracking-wider',
              user?.is_active ? 'bg-green-900/30 text-green-400 border border-green-500/20' : 'bg-error/10 text-error border border-error/20'
            ]">
              {{ user?.is_active ? 'Active' : 'Suspended' }}
            </span>
          </div>
          <p class="font-mono text-[11px] text-on-surface-variant/40 mt-2 uppercase tracking-widest">
            Member since {{ joinDate }}
          </p>
        </div>
      </section>

      <!-- Change Username -->
      <section class="glass-panel rounded-2xl p-7">
        <h2 class="font-sans font-semibold text-lg text-white mb-5">Change Username</h2>
        <form @submit.prevent="updateUsername" class="space-y-4">
          <div>
            <label class="field-label">New Username</label>
            <input v-model="usernameForm.username" type="text" placeholder="your_new_handle" class="field-input" />
          </div>
          <p v-if="usernameError" class="text-error text-sm">{{ usernameError }}</p>
          <button type="submit" :disabled="usernameLoading" class="btn-primary px-6 py-2.5 rounded-xl text-sm font-semibold flex items-center gap-2 disabled:opacity-50">
            <span v-if="usernameLoading" class="material-symbols-outlined text-sm animate-spin">refresh</span>
            Save Username
          </button>
        </form>
      </section>

      <!-- Change Password -->
      <section class="glass-panel rounded-2xl p-7">
        <h2 class="font-sans font-semibold text-lg text-white mb-5">Change Password</h2>
        <form @submit.prevent="changePassword" class="space-y-4">
          <div>
            <label class="field-label">Current Password</label>
            <input v-model="pwForm.current_password" type="password" placeholder="••••••••" class="field-input" />
          </div>
          <div>
            <label class="field-label">New Password</label>
            <input v-model="pwForm.new_password" type="password" placeholder="min. 8 characters" class="field-input" />
          </div>
          <div>
            <label class="field-label">Confirm Password</label>
            <input v-model="pwForm.confirm_password" type="password" placeholder="repeat new password" class="field-input" />
          </div>
          <p v-if="pwError" class="text-error text-sm">{{ pwError }}</p>
          <button type="submit" :disabled="pwLoading" class="btn-primary px-6 py-2.5 rounded-xl text-sm font-semibold flex items-center gap-2 disabled:opacity-50">
            <span v-if="pwLoading" class="material-symbols-outlined text-sm animate-spin">refresh</span>
            Update Password
          </button>
        </form>
      </section>

      <!-- API KEYS -->
      <section class="api-keys-section glass-panel rounded-2xl p-7">
        <h2 class="section-title">
          <span class="material-symbols-outlined">key</span>
          API Keys
        </h2>
        <p class="section-desc">
          Add your own API keys. These will be available when creating voice agents.
        </p>

        <!-- Add new key form -->
        <div class="add-key-form">
          <select v-model="newKey.provider" class="input">
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

          <input v-model="newKey.label" placeholder="Label (e.g. My Gemini Key)" class="input" />
          <input v-model="newKey.api_key" type="password" placeholder="Paste API key..." class="input" />
          <button @click="addKey" :disabled="adding" class="btn-primary add-btn">
            <span v-if="adding" class="material-symbols-outlined text-sm animate-spin">refresh</span>
            <span v-else class="material-symbols-outlined text-sm">add</span>
            {{ adding ? 'Adding…' : 'Add Key' }}
          </button>
        </div>

        <p v-if="keyError" class="text-error text-sm mt-3">{{ keyError }}</p>

        <!-- Existing keys list -->
        <div class="keys-list">
          <div v-if="loadingKeys" class="loading-row">
            <span class="material-symbols-outlined text-2xl text-primary/40 animate-spin">refresh</span>
            <span class="font-mono text-xs text-on-surface-variant/50 uppercase">Loading keys…</span>
          </div>
          <template v-else>
            <div v-for="key in apiKeys" :key="key.id" class="key-card">
              <div class="key-info">
                <span class="provider-badge" :class="key.provider">
                  {{ providerLabel(key.provider) }}
                </span>
                <span class="key-label">{{ key.label }}</span>
                <span class="key-preview font-mono">{{ key.key_preview || '••••••••' }}</span>
              </div>
              <button @click="deleteKey(key.id)" class="btn-danger-sm" title="Delete key">
                <span class="material-symbols-outlined">delete</span>
              </button>
            </div>
            <div v-if="apiKeys.length === 0" class="empty-state">
              <span class="material-symbols-outlined text-3xl mb-2 block opacity-40">vpn_key</span>
              No API keys added yet. Add one above to use custom providers.
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

const joinDate = computed(() => {
  if (!user.value?.created_at) return '—'
  return new Date(user.value.created_at).toLocaleDateString('en-US', { year: 'numeric', month: 'long' })
})

// Username form
const usernameForm = ref({ username: user.value?.username || '' })
const usernameLoading = ref(false)
const usernameError = ref('')

async function updateUsername() {
  usernameLoading.value = true; usernameError.value = ''
  try {
    const data = await apiFetch('/api/v1/auth/me', {
      method: 'PUT',
      body: JSON.stringify(usernameForm.value),
    })
    auth.setAuth(auth.token, data)
    toast.show('Username updated', 'success')
  } catch (e) {
    usernameError.value = e.message
  } finally {
    usernameLoading.value = false
  }
}

// Password form
const pwForm = ref({ current_password: '', new_password: '', confirm_password: '' })
const pwLoading = ref(false)
const pwError = ref('')

async function changePassword() {
  if (pwForm.value.new_password !== pwForm.value.confirm_password) {
    pwError.value = 'Passwords do not match'; return
  }
  pwLoading.value = true; pwError.value = ''
  try {
    await apiFetch('/api/v1/auth/change-password', {
      method: 'POST',
      body: JSON.stringify({ current_password: pwForm.value.current_password, new_password: pwForm.value.new_password }),
    })
    toast.show('Password changed successfully', 'success')
    pwForm.value = { current_password: '', new_password: '', confirm_password: '' }
  } catch (e) {
    pwError.value = e.message
  } finally {
    pwLoading.value = false
  }
}

// API Keys
const newKey = ref({ provider: 'gemini', label: '', api_key: '' })
const adding = ref(false)
const keyError = ref('')
const loadingKeys = ref(false)

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
  gemini: 'Gemini', openai: 'OpenAI', claude: 'Claude',
  elevenlabs: 'ElevenLabs', groq: 'Groq', deepgram: 'Deepgram', azure_tts: 'Azure TTS'
}
function providerLabel(p) { return PROVIDER_LABELS[p] || p }

onMounted(async () => {
  loadingKeys.value = true
  await fetchKeys()
  loadingKeys.value = false
})
</script>

<style scoped>
.profile-view {
  padding: 24px;
  min-height: 100%;
}

.field-label {
  display: block;
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: #c7c4d7;
  margin-bottom: 6px;
}

.field-input,
.input {
  width: 100%;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 10px 14px;
  font-size: 14px;
  color: #e2e2eb;
  outline: none;
  transition: border-color 0.15s ease;
  font-family: inherit;
}

.field-input:focus,
.input:focus {
  border-color: rgba(192, 193, 255, 0.4);
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 18px;
  font-weight: 600;
  color: #fff;
  margin-bottom: 6px;
}

.section-title .material-symbols-outlined {
  color: #c0c1ff;
  font-size: 22px;
}

.section-desc {
  font-size: 13px;
  color: #c7c4d7;
  margin-bottom: 18px;
}

.add-key-form {
  display: grid;
  grid-template-columns: 1fr 1fr 1.5fr auto;
  gap: 8px;
  margin-bottom: 18px;
}

.add-key-form .input,
.add-key-form .btn-primary {
  min-width: 0;
}

.add-key-form .add-btn {
  white-space: nowrap;
  padding: 0 16px;
  height: 42px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

@media (max-width: 720px) {
  .add-key-form { grid-template-columns: 1fr; }
}

.keys-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.key-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 14px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 12px;
}

.key-info {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
  flex: 1;
}

.provider-badge {
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  padding: 4px 8px;
  border-radius: 6px;
  background: rgba(192, 193, 255, 0.1);
  color: #c0c1ff;
  border: 1px solid rgba(192, 193, 255, 0.2);
  flex-shrink: 0;
}

.provider-badge.gemini      { background: rgba(66, 133, 244, 0.12); color: #4d8af0; border-color: rgba(66, 133, 244, 0.3); }
.provider-badge.openai      { background: rgba(16, 163, 127, 0.12); color: #10a37f; border-color: rgba(16, 163, 127, 0.3); }
.provider-badge.claude      { background: rgba(204, 119, 34, 0.12); color: #cc7722; border-color: rgba(204, 119, 34, 0.3); }
.provider-badge.elevenlabs  { background: rgba(192, 193, 255, 0.12); color: #d0bcff; border-color: rgba(208, 188, 255, 0.3); }
.provider-badge.groq        { background: rgba(251, 146, 60, 0.12); color: #fb923c; border-color: rgba(251, 146, 60, 0.3); }
.provider-badge.deepgram    { background: rgba(56, 189, 248, 0.12); color: #38bdf8; border-color: rgba(56, 189, 248, 0.3); }
.provider-badge.azure_tts   { background: rgba(99, 102, 241, 0.12); color: #818cf8; border-color: rgba(99, 102, 241, 0.3); }

.key-label {
  font-size: 14px;
  font-weight: 500;
  color: #fff;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.key-preview {
  font-size: 11px;
  color: #908fa0;
  margin-left: auto;
  padding-left: 12px;
  flex-shrink: 0;
}

.btn-danger-sm {
  background: rgba(255, 180, 171, 0.1);
  color: #ffb4ab;
  border: 1px solid rgba(255, 180, 171, 0.2);
  border-radius: 8px;
  padding: 6px 8px;
  cursor: pointer;
  transition: background 0.15s ease;
}

.btn-danger-sm:hover {
  background: rgba(255, 180, 171, 0.2);
}

.btn-danger-sm .material-symbols-outlined {
  font-size: 18px;
}

.empty-state {
  padding: 32px 20px;
  text-align: center;
  color: #908fa0;
  font-size: 13px;
  background: rgba(255, 255, 255, 0.02);
  border-radius: 12px;
  border: 1px dashed rgba(255, 255, 255, 0.08);
}

.loading-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 20px;
  justify-content: center;
}
</style>
