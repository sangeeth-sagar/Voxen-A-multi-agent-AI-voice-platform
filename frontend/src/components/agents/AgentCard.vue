<template>
  <div 
    :class="[
      'glass-card rounded-2xl p-5 border relative overflow-hidden flex flex-col justify-between transition-all duration-300 group',
      agent.is_active ? 'border-primary/20' : 'border-outline-variant/50'
    ]"
    @click="$emit('detail', agent)"
  >
    <!-- Card Header -->
    <div class="flex items-start justify-between mb-3">
      <div :class="[
        'w-10 h-10 rounded-xl flex items-center justify-center',
        agent.is_active ? 'bg-primary/10 text-primary' : 'bg-surface-container-high text-on-surface-variant'
      ]">
        <!-- Dynamic Node Icon matching fleet theme -->
        <span class="material-symbols-outlined icon-filled text-lg">
          {{ nodeIcon }}
        </span>
      </div>

      <div class="flex items-center gap-1.5">
        <span v-if="agent.is_template" class="badge-tag">Template</span>
        <span :class="['status-indicator-badge', statusText]">
          <span class="pulse-dot" v-if="agent.is_active"></span>
          {{ statusText }}
        </span>
      </div>
    </div>

    <!-- Node Body -->
    <div class="space-y-1 flex-1">
      <h3 class="font-sans font-bold text-sm text-on-surface line-clamp-1">
        {{ agent.name }}
      </h3>
      <p class="text-[11px] text-on-surface-variant line-clamp-2 leading-relaxed">
        {{ agent.description || 'Monitoring network logs and processing voice system flows.' }}
      </p>
    </div>

    <!-- Node Metrics / Status Footer (Backend-backed) -->
    <div class="pt-4 mt-3 border-t border-outline-variant/30 flex items-center justify-between text-[10px] font-mono text-on-surface-variant">
      <div class="min-w-0 flex-1">
        <span class="text-[9px] text-on-surface-variant/50 uppercase font-mono block">INTEGRATION</span>
        <span class="font-bold text-on-surface truncate block pr-2">
          {{ agent.is_voice_agent ? agent.voice_language : (agent.tools_enabled || []).slice(0, 2).join(', ') || 'No tools' }}
        </span>
      </div>
      <div class="text-right shrink-0">
        <span class="text-[9px] text-on-surface-variant/50 uppercase font-mono block">USAGE</span>
        <span class="font-bold text-on-surface">{{ agent.use_count }} sessions</span>
      </div>
    </div>

    <!-- Hover Actions Cover Panel -->
    <div class="absolute inset-0 bg-surface/90 html-dark:bg-[#001710]/95 backdrop-blur-sm flex flex-col justify-center p-4 gap-2 translate-y-full group-hover:translate-y-0 transition-transform duration-300 ease-out z-20" @click.stop>
      <div class="text-center mb-1">
        <span class="text-xs font-bold text-on-surface block">{{ agent.name }}</span>
        <span class="text-[9px] font-mono text-on-surface-variant">{{ agent.is_voice_agent ? 'Voice Agent' : 'BI Agent' }}</span>
      </div>

      <div class="grid grid-cols-2 gap-2">
        <button @click="$emit('edit', agent)" class="btn-action">
          <span class="material-symbols-outlined text-xs">edit</span>
          Edit Node
        </button>
        <button @click="$emit('detail', agent)" class="btn-action">
          <span class="material-symbols-outlined text-xs">webhook</span>
          Webhook
        </button>
      </div>

      <div class="grid grid-cols-2 gap-2">
        <button v-if="agent.is_active" @click="$emit('deactivate', agent)" class="btn-action-danger">
          <span class="material-symbols-outlined text-xs">power_settings_new</span>
          Deactivate
        </button>
        <button v-else @click="$emit('activate', agent)" class="btn-action-success">
          <span class="material-symbols-outlined text-xs">play_circle</span>
          Activate
        </button>

        <button @click="testAgent" class="btn-action-primary">
          <span class="material-symbols-outlined text-xs">mic</span>
          Launch Lab
        </button>
      </div>

      <button @click="$emit('delete', agent)" class="text-[10px] text-error hover:underline flex items-center justify-center gap-1 mt-1">
        <span class="material-symbols-outlined text-xs">delete</span>
        Delete
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useToastStore } from '@/stores/toast'

const props = defineProps({ agent: { type: Object, required: true } })
const emit = defineEmits(['edit', 'clone', 'delete', 'activate', 'deactivate', 'test', 'detail'])
const router = useRouter()
const toast = useToastStore()

const statusText = computed(() => {
  if (props.agent.is_template) return 'SYNCING'
  return props.agent.is_active ? 'ACTIVE' : 'STANDBY'
})

const nodeIcon = computed(() => {
  if (props.agent.is_template) return 'sync'
  if (!props.agent.is_active) return 'nightlight'
  
  // Dynamic active icons
  const charSum = props.agent.name.charCodeAt(0) || 0
  if (charSum % 3 === 0) return 'bolt' // lightning
  if (charSum % 3 === 1) return 'shield' // shield/security
  return 'public' // globe/geo
})



function testAgent() {
  localStorage.setItem('active_agent', props.agent.uuid)
  toast.show(`Setting active agent: ${props.agent.name}`, 'info')
  router.push('/')
}
</script>

<style scoped>
.badge-tag {
  background: var(--color-primary-container);
  color: var(--color-primary);
  font-family: 'JetBrains Mono', monospace;
  font-size: 8px;
  font-weight: 700;
  text-transform: uppercase;
  padding: 2px 6px;
  border-radius: 4px;
}

html.dark .badge-tag {
  background: rgba(165, 209, 170, 0.15);
  color: #a5d1aa;
}

/* Status Indicator Badges */
.status-indicator-badge {
  font-family: 'JetBrains Mono', monospace;
  font-size: 9px;
  font-weight: 700;
  text-transform: uppercase;
  padding: 2px 8px;
  border-radius: 4px;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.status-indicator-badge.ACTIVE {
  background: rgba(14, 108, 74, 0.12);
  color: var(--color-success);
  border: 1px solid rgba(14, 108, 74, 0.25);
}

html.dark .status-indicator-badge.ACTIVE {
  background: rgba(165, 209, 170, 0.15);
  color: #a5d1aa;
  border-color: rgba(165, 209, 170, 0.3);
}

.status-indicator-badge.STANDBY {
  background: var(--color-surface-container-high);
  color: var(--color-on-surface-variant);
  border: 1px solid var(--color-outline-variant);
}

html.dark .status-indicator-badge.STANDBY {
  background: rgba(255, 255, 255, 0.05);
  color: var(--color-outline);
  border-color: rgba(255, 255, 255, 0.08);
}

.status-indicator-badge.SYNCING {
  background: rgba(196, 138, 0, 0.12);
  color: var(--color-tactical-amber);
  border: 1px solid rgba(196, 138, 0, 0.25);
}

html.dark .status-indicator-badge.SYNCING {
  background: rgba(255, 187, 12, 0.12);
  color: #ffbb0c;
  border-color: rgba(255, 187, 12, 0.25);
}

.pulse-dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: currentColor;
  animation: pulse-animation 1.5s infinite;
}

@keyframes pulse-animation {
  0% { transform: scale(0.9); opacity: 1; }
  50% { transform: scale(1.4); opacity: 0.5; }
  100% { transform: scale(0.9); opacity: 1; }
}

/* Action covers */
.btn-action {
  background: var(--color-surface-container-high);
  border: 1px solid var(--color-outline-variant);
  color: var(--color-on-surface);
  border-radius: 8px;
  padding: 6px;
  font-size: 10px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  cursor: pointer;
}

.btn-action:hover {
  background: var(--color-surface-container-highest);
}

html.dark .btn-action {
  background: rgba(255, 255, 255, 0.04);
  border-color: rgba(255, 255, 255, 0.08);
}

html.dark .btn-action:hover {
  background: rgba(255, 255, 255, 0.08);
}

.btn-action-primary {
  background: var(--color-primary);
  color: var(--color-on-primary);
  border: none;
  border-radius: 8px;
  padding: 6px;
  font-size: 10px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  cursor: pointer;
}

html.dark .btn-action-primary {
  background: #0d3c2f;
  color: #a5d1aa;
  border: 1px solid rgba(165, 209, 170, 0.2);
}

.btn-action-primary:hover {
  filter: brightness(1.15);
}

.btn-action-danger {
  background: rgba(186, 26, 26, 0.1);
  color: var(--color-error);
  border: 1px solid rgba(186, 26, 26, 0.2);
  border-radius: 8px;
  padding: 6px;
  font-size: 10px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  cursor: pointer;
}

.btn-action-danger:hover {
  background: rgba(186, 26, 26, 0.15);
}

.btn-action-success {
  background: rgba(14, 108, 74, 0.1);
  color: var(--color-success);
  border: 1px solid rgba(14, 108, 74, 0.2);
  border-radius: 8px;
  padding: 6px;
  font-size: 10px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  cursor: pointer;
}

.btn-action-success:hover {
  background: rgba(14, 108, 74, 0.15);
}

/* Dark mode light card override */
html.dark .glass-card {
  background: #f3f4f5 !important;
  color: #191c1d !important;
  border-color: #d9dadb !important;
}

html.dark .glass-card h3 {
  color: #191c1d !important;
}

html.dark .glass-card p {
  color: #414844 !important;
}

html.dark .glass-card .font-bold.text-on-surface {
  color: #191c1d !important;
}

html.dark .glass-card .text-on-surface-variant {
  color: #414844 !important;
}

html.dark .glass-card .status-indicator-badge.STANDBY {
  background: #d9dadb !important;
  color: #414844 !important;
  border-color: #c1c8c2 !important;
}

/* Hover cover panel on dark mode cards */
html.dark .translate-y-full {
  background: rgba(243, 244, 245, 0.98) !important;
  color: #191c1d !important;
}

html.dark .group-hover\:translate-y-0 {
  background: rgba(243, 244, 245, 0.98) !important;
  color: #191c1d !important;
}

html.dark .btn-action {
  background: #edeeef !important;
  border-color: #c1c8c2 !important;
  color: #012d1d !important;
}

html.dark .btn-action:hover {
  background: #d9dadb !important;
}

html.dark .btn-action-primary {
  background: #0e6c4a !important;
  color: #ffffff !important;
  border: none !important;
}

html.dark .btn-action-primary:hover {
  background: #012d1d !important;
}

html.dark .btn-action-danger {
  background: rgba(186, 26, 26, 0.1) !important;
  color: #ba1a1a !important;
  border: 1px solid rgba(186, 26, 26, 0.3) !important;
}

html.dark .btn-action-danger:hover {
  background: rgba(186, 26, 26, 0.2) !important;
}

html.dark .btn-action-success {
  background: rgba(14, 108, 74, 0.1) !important;
  color: #0e6c4a !important;
  border: 1px solid rgba(14, 108, 74, 0.3) !important;
}

html.dark .btn-action-success:hover {
  background: rgba(14, 108, 74, 0.2) !important;
}
</style>
