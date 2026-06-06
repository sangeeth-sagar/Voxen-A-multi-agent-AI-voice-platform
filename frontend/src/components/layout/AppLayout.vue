<template>
  <div class="flex h-screen overflow-hidden bg-background tactical-grid text-on-surface">
    <!-- Neural sphere background -->
    <div class="neural-sphere-bg" />

    <!-- SIDEBAR -->
    <aside
      :class="[
        'fixed left-0 top-0 h-full z-50 flex flex-col glass-panel border-r-0 transition-all duration-300',
        focusMode ? 'sidebar-focus' : 'w-64'
      ]"
    >
      <!-- Logo -->
      <div class="p-6 flex items-center gap-3 overflow-hidden">
        <div class="w-10 h-10 shrink-0 rounded-xl bg-primary flex items-center justify-center shadow-[0_0_20px_rgba(192,193,255,0.3)]">
          <span class="material-symbols-outlined text-on-primary text-2xl icon-filled">neurology</span>
        </div>
        <div :class="['nav-text', focusMode ? '' : 'opacity-100']">
          <h1 class="font-sans text-xl font-bold tracking-tight text-white">AgentIQ</h1>
          <p class="font-mono text-[10px] text-primary/60 uppercase tracking-[0.2em]">Neural OS v2.4</p>
        </div>
      </div>

      <!-- Nav items -->
      <nav class="flex-1 px-3 space-y-1 mt-2">
        <RouterLink
          v-for="item in navItems"
          :key="item.to"
          :to="item.to"
          v-slot="{ isActive }"
          custom
        >
          <a
            @click="$router.push(item.to)"
            :class="[
              'flex items-center gap-3 px-4 py-3 rounded-xl cursor-pointer transition-all duration-200',
              isActive
                ? 'text-primary bg-primary/10'
                : 'text-on-surface-variant hover:text-white hover:bg-white/5'
            ]"
          >
            <span class="material-symbols-outlined shrink-0" :class="isActive ? 'icon-filled' : ''">
              {{ item.icon }}
            </span>
            <span :class="['font-medium nav-text', focusMode ? '' : 'opacity-100']">{{ item.label }}</span>
          </a>
        </RouterLink>
      </nav>

      <!-- Bottom links -->
      <div class="p-4 border-t border-white/5 space-y-1">
        <a class="flex items-center gap-3 px-4 py-2 text-on-surface-variant hover:text-white transition-all rounded-xl cursor-pointer">
          <span class="material-symbols-outlined text-[20px] shrink-0">settings</span>
          <span :class="['text-sm nav-text', focusMode ? '' : 'opacity-100']">Settings</span>
        </a>
        <a class="flex items-center gap-3 px-4 py-2 text-on-surface-variant hover:text-white transition-all rounded-xl cursor-pointer">
          <span class="material-symbols-outlined text-[20px] shrink-0">help</span>
          <span :class="['text-sm nav-text', focusMode ? '' : 'opacity-100']">Support</span>
        </a>
        <a @click="logout" class="flex items-center gap-3 px-4 py-2 text-error/70 hover:text-error transition-all rounded-xl cursor-pointer">
          <span class="material-symbols-outlined text-[20px] shrink-0">logout</span>
          <span :class="['text-sm nav-text', focusMode ? '' : 'opacity-100']">Logout</span>
        </a>
      </div>
    </aside>

    <!-- MAIN CONTENT -->
    <div :class="['flex flex-col flex-1 min-w-0', focusMode ? 'ml-20' : 'ml-64']">
      <!-- Top header -->
      <header class="flex justify-between items-center px-8 h-20 border-b border-white/5 bg-background/20 backdrop-blur-sm shrink-0">
        <div class="flex items-center gap-6">
          <div class="flex items-center gap-2 px-3 py-1.5 bg-primary/5 rounded-full border border-primary/20">
            <span class="w-2 h-2 rounded-full bg-primary shadow-[0_0_8px_#c0c1ff] animate-pulse" />
            <span class="font-mono text-[11px] text-primary uppercase tracking-wider">Mission Control Active</span>
          </div>
          <!-- Wake Word Status -->
          <div class="flex items-center gap-2 px-3 py-1.5" :class="[
            voiceAgentStore.wakeWordEnabled && voiceAgentStore.activeAgent ? 'bg-primary/5 border border-primary/20' : 
            voiceAgentStore.wakeWordEnabled && !voiceAgentStore.activeAgent ? 'bg-yellow-500/5 border border-yellow-500/20' : 
            'bg-gray-800/50 border border-gray-700/20'
          ]" :title="voiceAgentStore.wakeWordEnabled ? (voiceAgentStore.activeAgent ? 'Wake Word Active' : 'No Active Agents') : 'Wake Word Disabled'">
            <span class="w-2 h-2 rounded-full" :class="[
              voiceAgentStore.wakeWordEnabled && voiceAgentStore.activeAgent ? 'bg-green-400 animate-pulse' : 
              voiceAgentStore.wakeWordEnabled && !voiceAgentStore.activeAgent ? 'bg-yellow-400 animate-pulse' : 
              'bg-gray-400'
            ]" />
            <span class="font-mono text-[11px] text-white uppercase tracking-wider">
              {{ voiceAgentStore.wakeWordEnabled ? (voiceAgentStore.activeAgent ? 'Wake Word Active' : 'No Active Agents') : 'Wake Word Disabled' }}
            </span>
          </div>
          <div class="hidden md:flex gap-6 text-on-surface-variant font-mono text-[11px]">
            <span class="flex items-center gap-2">
              <span class="material-symbols-outlined text-sm text-primary/60">memory</span> CPU: 12%
            </span>
            <span class="flex items-center gap-2">
              <span class="material-symbols-outlined text-sm text-primary/60">sensors</span> Latency: 4ms
            </span>
          </div>
        </div>

        <div class="flex items-center gap-4">
          <button class="p-2 text-on-surface-variant hover:text-white transition-colors">
            <span class="material-symbols-outlined">search</span>
          </button>
          <button class="p-2 text-on-surface-variant hover:text-white transition-colors">
            <span class="material-symbols-outlined">notifications</span>
          </button>
          <div class="h-8 w-px bg-white/10" />
          <div class="flex items-center gap-3">
            <div class="text-right hidden sm:block">
              <p class="text-sm font-semibold">{{ user?.username || 'User' }}</p>
              <p class="text-[10px] text-primary/60 font-mono uppercase">{{ user?.role || 'operator' }}</p>
            </div>
            <div class="w-10 h-10 rounded-full border-2 border-primary/20 bg-secondary-container/30 flex items-center justify-center">
              <span class="material-symbols-outlined text-primary icon-filled">person</span>
            </div>
          </div>
        </div>
      </header>

      <!-- Page slot -->
<main class="flex-1 overflow-hidden">
         <slot />
       </main>
       
       <!-- Wake Word Manager (background service) -->
       <WakeWordManager />
    </div>

    <!-- Toast container -->
    <ToastContainer />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useVoiceAgentStore } from '@/stores/voiceAgent'
import ToastContainer from '@/components/ui/ToastContainer.vue'
import WakeWordManager from '@/components/voice/WakeWordManager.vue'

const props = defineProps({
  focusMode: { type: Boolean, default: false }
})

const auth = useAuthStore()
const voiceAgentStore = useVoiceAgentStore()
const router = useRouter()
const user = computed(() => auth.user)

const navItems = [
  { to: '/workspace', icon: 'grid_view', label: 'Workspace' },
  { to: '/agents', icon: 'smart_toy', label: 'Agents' },
  { to: '/voice', icon: 'mic', label: 'Voice Mode' },
  { to: '/profile', icon: 'person', label: 'Profile' },
  { to: '/admin', icon: 'admin_panel_settings', label: 'Admin' },
]

function logout() {
  auth.logout()
  router.push('/login')
}
</script>
