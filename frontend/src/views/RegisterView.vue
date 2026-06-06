<template>
  <div class="min-h-screen bg-background tactical-grid flex items-center justify-center relative overflow-hidden">
    <div class="neural-sphere-bg" />
    <div class="absolute top-1/4 right-1/3 w-80 h-80 rounded-full bg-secondary-container/10 blur-3xl pointer-events-none" />

    <div class="relative z-10 w-full max-w-sm px-4">
      <div class="flex flex-col items-center mb-10">
        <div class="w-16 h-16 rounded-2xl bg-primary flex items-center justify-center shadow-[0_0_40px_rgba(192,193,255,0.3)] mb-4">
          <span class="material-symbols-outlined text-on-primary text-4xl icon-filled">neurology</span>
        </div>
        <h1 class="font-sans text-3xl font-bold tracking-tight text-white">AgentIQ</h1>
        <p class="font-mono text-[11px] text-primary/60 uppercase tracking-[0.25em] mt-1">Register New Operator</p>
      </div>

      <div class="glass-panel rounded-3xl p-8">
        <h2 class="text-xl font-semibold text-white mb-1">Create account</h2>
        <p class="text-sm text-on-surface-variant mb-8">Join the neural intelligence network</p>

        <form @submit.prevent="handleRegister" class="space-y-5">
          <div>
            <label class="block font-mono text-[11px] uppercase tracking-widest text-on-surface-variant mb-2">Username</label>
            <input v-model="form.username" type="text" required placeholder="your_handle"
              class="w-full tactical-input rounded-lg px-4 py-3 text-sm" />
          </div>
          <div>
            <label class="block font-mono text-[11px] uppercase tracking-widest text-on-surface-variant mb-2">Email</label>
            <input v-model="form.email" type="email" required placeholder="operator@agentiq.ai"
              class="w-full tactical-input rounded-lg px-4 py-3 text-sm" />
          </div>
          <div>
            <label class="block font-mono text-[11px] uppercase tracking-widest text-on-surface-variant mb-2">Password</label>
            <input v-model="form.password" type="password" required placeholder="min. 8 characters"
              class="w-full tactical-input rounded-lg px-4 py-3 text-sm" />
          </div>

          <p v-if="error" class="text-error text-sm">{{ error }}</p>

          <button type="submit" :disabled="loading"
            class="w-full btn-primary py-3 rounded-xl font-semibold text-sm flex items-center justify-center gap-2 disabled:opacity-50">
            <span v-if="loading" class="material-symbols-outlined text-sm animate-spin">refresh</span>
            <span v-else class="material-symbols-outlined text-sm icon-filled">person_add</span>
            {{ loading ? 'Initializing...' : 'Initialize Operator' }}
          </button>
        </form>

        <p class="text-center text-sm text-on-surface-variant mt-6">
          Already have access?
          <RouterLink to="/login" class="text-primary hover:text-primary/80 font-medium ml-1">Sign in</RouterLink>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { apiFetch } from '@/composables/useApi'

const router = useRouter()
const auth = useAuthStore()
const form = ref({ username: '', email: '', password: '' })
const loading = ref(false)
const error = ref('')

async function handleRegister() {
  loading.value = true
  error.value = ''
  try {
    const data = await apiFetch('/api/v1/auth/register', {
      method: 'POST',
      body: JSON.stringify(form.value),
    })
    auth.setAuth(data.access_token, data.user)
    router.push('/workspace')
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}
</script>
