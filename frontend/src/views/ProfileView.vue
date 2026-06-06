<template>
  <AppLayout>
    <div class="h-full overflow-y-auto p-6">
      <div class="max-w-3xl mx-auto space-y-6">

        <!-- Profile hero -->
        <div class="glass-panel rounded-3xl p-8 flex flex-col sm:flex-row items-center sm:items-start gap-6">
          <div class="relative">
            <div class="w-24 h-24 rounded-2xl bg-gradient-to-br from-primary/30 to-secondary-container/50 border border-primary/20 flex items-center justify-center shadow-[0_0_40px_rgba(192,193,255,0.15)]">
              <span class="material-symbols-outlined text-primary text-5xl icon-filled">person</span>
            </div>
            <div class="absolute -bottom-2 -right-2 w-7 h-7 rounded-full bg-primary flex items-center justify-center shadow-[0_0_12px_rgba(192,193,255,0.4)]">
              <span class="material-symbols-outlined text-on-primary text-xs icon-filled">verified</span>
            </div>
          </div>

          <div class="flex-1 text-center sm:text-left">
            <h1 class="font-sans text-3xl font-bold text-white tracking-tight">{{ user?.username || '—' }}</h1>
            <p class="text-on-surface-variant mt-1">{{ user?.email }}</p>
            <div class="flex items-center gap-2 mt-3 justify-center sm:justify-start">
              <span :class="[
                'px-3 py-1 rounded-full font-mono text-[10px] uppercase tracking-wider font-bold',
                user?.role === 'admin'
                  ? 'bg-error/15 text-error border border-error/30'
                  : 'bg-primary/10 text-primary border border-primary/20'
              ]">
                {{ user?.role || 'user' }}
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

          <!-- Quick stats -->
          <div class="grid grid-cols-3 gap-4 shrink-0">
            <div v-for="s in quickStats" :key="s.label" class="text-center">
              <div :class="['font-mono text-xl font-bold', s.color]">{{ s.value }}</div>
              <div class="font-mono text-[9px] text-on-surface-variant/50 uppercase tracking-wider mt-1">{{ s.label }}</div>
            </div>
          </div>
        </div>

        <!-- Tab bar -->
        <div class="flex gap-1">
          <button
            v-for="tab in tabs" :key="tab.key"
            @click="activeTab = tab.key"
            :class="[
              'px-5 py-2.5 rounded-xl font-mono text-[11px] uppercase tracking-wider transition-colors',
              activeTab === tab.key
                ? 'bg-primary/15 text-primary'
                : 'text-on-surface-variant hover:text-white hover:bg-white/5'
            ]"
          >{{ tab.label }}</button>
        </div>

        <!-- Tab: Username -->
        <div v-if="activeTab === 'username'" class="glass-panel rounded-2xl p-7">
          <h2 class="font-sans font-semibold text-lg text-white mb-5">Change Username</h2>
          <form @submit.prevent="updateUsername" class="space-y-5">
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
        </div>

        <!-- Tab: Password -->
        <div v-if="activeTab === 'password'" class="glass-panel rounded-2xl p-7">
          <h2 class="font-sans font-semibold text-lg text-white mb-5">Change Password</h2>
          <form @submit.prevent="changePassword" class="space-y-5">
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
        </div>

        <!-- Tab: My Agents compact grid -->
        <div v-if="activeTab === 'agents'" class="space-y-4">
          <div v-if="agentsLoading" class="flex justify-center py-10">
            <span class="material-symbols-outlined text-4xl text-primary/30 animate-spin">refresh</span>
          </div>
          <div v-else-if="myAgents.length === 0" class="glass-panel rounded-2xl p-10 text-center text-on-surface-variant/40">
            <span class="material-symbols-outlined text-5xl mb-3 block">smart_toy</span>
            <p class="font-mono text-sm uppercase">No agents deployed yet</p>
          </div>
          <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            <div
              v-for="agent in myAgents" :key="agent.uuid"
              class="glass-card rounded-xl p-4"
              :class="agent.is_voice_agent ? 'card-voice' : 'card-bi'"
            >
              <div class="flex items-center gap-3">
                <div :class="['w-8 h-8 rounded-lg flex items-center justify-center shrink-0', agent.is_voice_agent ? 'bg-secondary/10' : 'bg-primary/10']">
                  <span :class="['material-symbols-outlined text-[16px] icon-filled', agent.is_voice_agent ? 'text-secondary' : 'text-primary']">
                    {{ agent.is_voice_agent ? 'mic' : 'smart_toy' }}
                  </span>
                </div>
                <div class="min-w-0">
                  <p class="text-sm font-semibold text-white truncate">{{ agent.name }}</p>
                  <p class="font-mono text-[10px] text-on-surface-variant/50 uppercase">{{ agent.agent_type }}</p>
                </div>
              </div>
            </div>
          </div>
        </div>

      </div>
    </div>
  </AppLayout>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import AppLayout from '@/components/layout/AppLayout.vue'
import { useAuthStore } from '@/stores/auth'
import { apiFetch } from '@/composables/useApi'
import { useToastStore } from '@/stores/toast'

const auth = useAuthStore()
const toast = useToastStore()
const user = computed(() => auth.user)

const activeTab = ref('username')
const tabs = [
  { key: 'username', label: 'Username' },
  { key: 'password', label: 'Password' },
  { key: 'agents', label: 'My Agents' },
]

const joinDate = computed(() => {
  if (!user.value?.created_at) return '—'
  return new Date(user.value.created_at).toLocaleDateString('en-US', { year: 'numeric', month: 'long' })
})

const quickStats = computed(() => [
  { label: 'Jobs', value: user.value?.total_jobs ?? 0, color: 'text-primary' },
  { label: 'Tokens', value: fmtNum(user.value?.total_tokens ?? 0), color: 'text-secondary' },
  { label: 'Cost', value: `$${(user.value?.total_cost_usd ?? 0).toFixed(3)}`, color: 'text-tertiary' },
])

function fmtNum(n) {
  if (n >= 1e6) return (n/1e6).toFixed(1) + 'M'
  if (n >= 1000) return (n/1000).toFixed(1) + 'K'
  return n
}

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

// Agents
const myAgents = ref([])
const agentsLoading = ref(false)

async function fetchAgents() {
  agentsLoading.value = true
  try { myAgents.value = await apiFetch('/api/v1/agents') }
  catch (e) { toast.show(e.message, 'error') }
  finally { agentsLoading.value = false }
}

onMounted(fetchAgents)
</script>

<style scoped>
.field-label { @apply block font-mono text-[10px] uppercase tracking-widest text-on-surface-variant mb-1.5; }
.field-input { @apply w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-on-surface placeholder:text-on-surface-variant/40 outline-none focus:border-primary/30 transition-colors; }
</style>
