<template>
  <div :class="theme === 'dark' ? 'auth-theme-dark' : 'auth-theme-light'"
       class="min-h-screen flex items-center justify-center relative overflow-hidden">
    <div class="neural-sphere-bg" />

    <button @click="toggle"
      class="absolute top-5 right-5 z-20 w-10 h-10 rounded-full flex items-center
             justify-center bg-white/10 hover:bg-white/20 transition-colors">
      <span class="material-symbols-outlined text-lg">
        {{ theme === 'dark' ? 'light_mode' : 'dark_mode' }}
      </span>
    </button>

    <div class="absolute top-1/4 left-1/4 w-96 h-96 rounded-full bg-primary/5 blur-3xl pointer-events-none" />
    <div class="absolute bottom-1/4 right-1/4 w-96 h-96 rounded-full bg-secondary-container/10 blur-3xl pointer-events-none" />

    <div class="relative z-10 w-full max-w-sm px-4">
      <div class="flex flex-col items-center mb-10">
        <div class="w-16 h-16 rounded-2xl bg-primary flex items-center justify-center shadow-soft mb-4">
          <span class="material-symbols-outlined text-on-primary text-4xl icon-filled">neurology</span>
        </div>
        <h1 class="font-sans text-3xl font-bold tracking-tight" :class="theme === 'dark' ? 'text-white' : 'text-[#1a1d27]'">AgentIQ</h1>
        <p class="font-mono text-[11px] uppercase tracking-[0.25em] mt-1" :class="theme === 'dark' ? 'text-white' : 'text-[#1a1d27]'">Neural OS v4.2</p>
      </div>

      <div class="glass-panel rounded-3xl p-8">
        <h2 class="text-xl font-semibold mb-1 text-[var(--color-success)]">Welcome back</h2>
        <p class="text-sm text-on-surface-variant mb-8">Sign in to your command center</p>

        <form @submit.prevent="handleLogin" class="space-y-6">
          <div>
            <label class="block font-mono text-[11px] uppercase tracking-widest text-on-surface-variant mb-2">Email</label>
            <input v-model="form.email" type="email" required placeholder="your@gmail.com"
              class="w-full tactical-input rounded-lg px-4 py-3 text-sm" />
          </div>
          <div>
            <label class="block font-mono text-[11px] uppercase tracking-widest text-on-surface-variant mb-2">Password</label>
            <div class="relative">
              <input v-model="form.password" :type="showPassword ? 'text' : 'password'" required
                placeholder="••••••••" class="w-full tactical-input rounded-lg px-4 py-3 text-sm pr-12" />
              <button type="button" @click="showPassword = !showPassword"
                class="absolute right-2 top-1/2 -translate-y-1/2 text-on-surface-variant hover:text-on-surface p-2.5 -m-1 rounded-full flex items-center justify-center"
                style="min-width: 44px; min-height: 44px;"
                aria-label="Toggle password visibility">
                <span class="material-symbols-outlined text-lg">
                  {{ showPassword ? 'visibility_off' : 'visibility' }}
                </span>
              </button>
            </div>
          </div>

          <p v-if="error" class="text-error text-sm">{{ error }}</p>

          <button type="submit" :disabled="loading"
            class="w-full btn-primary py-3 rounded-xl font-semibold text-sm flex items-center justify-center gap-2 disabled:opacity-50">
            <span v-if="loading" class="material-symbols-outlined text-sm animate-spin">refresh</span>
            <span v-else class="material-symbols-outlined text-sm icon-filled">login</span>
            {{ loading ? 'Authenticating...' : 'Authenticate' }}
          </button>
        </form>

        <p class="text-center text-sm text-on-surface-variant mt-6">
          No account?
          <RouterLink to="/register" class="text-primary hover:text-primary/80 font-medium ml-1">Register operator</RouterLink>
        </p>
      </div>

      <p class="text-center font-mono text-[10px] text-on-surface-variant/40 mt-6 uppercase tracking-widest">
        Secure Neural Link · End-to-End Encrypted
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { apiFetch } from '@/composables/useApi'
import { useAuthTheme } from '@/composables/useTheme'
import { useSessionTimer } from '@/composables/useSessionTimer'

const router = useRouter()
const auth = useAuthStore()
const form = ref({ email: '', password: '' })
const loading = ref(false)
const error = ref('')
const showPassword = ref(false)
const { theme, toggle } = useAuthTheme()
const { startSessionTracking } = useSessionTimer()

async function handleLogin() {
  loading.value = true; error.value = ''
  try {
    const data = await apiFetch('/api/v1/auth/login', { method: 'POST', body: JSON.stringify(form.value) })
    auth.setAuth(data.access_token, data.user, data.refresh_token)
    startSessionTracking()
    router.push(auth.isSuperadmin ? '/admin' : '/')
  } catch (e) { error.value = e.message } finally { loading.value = false }
}
</script>

<style scoped>
.auth-theme-light {
  background: #f8f9fc;
  color: #1a1d27;
}
.auth-theme-dark {
  background: #0a0c14;
  color: #e8eaf0;
}
</style>
