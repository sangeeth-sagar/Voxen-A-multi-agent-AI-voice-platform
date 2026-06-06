<template>
  <div
    :class="[
      'glass-card rounded-2xl p-6 cursor-pointer',
      agent.is_voice_agent ? 'card-voice' : 'card-bi'
    ]"
  >
    <!-- Header -->
    <div class="flex items-start justify-between mb-4">
      <div :class="[
        'w-11 h-11 rounded-xl flex items-center justify-center',
        agent.is_voice_agent ? 'bg-secondary/10' : 'bg-primary/10'
      ]">
        <span :class="['material-symbols-outlined icon-filled', agent.is_voice_agent ? 'text-secondary' : 'text-primary']">
          {{ agent.is_voice_agent ? 'mic' : 'smart_toy' }}
        </span>
      </div>
      <div class="flex items-center gap-1.5">
        <span v-if="agent.is_template" class="px-2 py-0.5 rounded-full bg-primary/10 text-primary font-mono text-[10px] uppercase">Template</span>
        <span v-if="agent.is_public" class="px-2 py-0.5 rounded-full bg-white/5 text-on-surface-variant font-mono text-[10px] uppercase">Public</span>
        <!-- Activation Status Indicator -->
        <span
          :class="[
            'w-2 h-2 rounded-full',
            agent.is_active ? 'bg-green-400 animate-pulse' : 'bg-gray-400'
          ]"
        ></span>
      </div>
    </div>

    <h3 class="font-sans font-semibold text-sm text-white mb-1 line-clamp-1">{{ agent.name }}</h3>
    <!-- Webhook Badge -->
    <div v-if="agent.is_active" class="flex items-center gap-1 mb-2">
      <span
        class="px-2 py-0.5 rounded-full bg-green-500/20 text-green-400 text-[10px] font-mono"
      >
        WEBHOOK ACTIVE
      </span>
      <button
        @click.stop="copyWebhook"
        class="text-green-400 hover:text-green-300 transition-colors text-[10px]"
        title="Copy webhook URL"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          class="h-3 w-3"
          viewBox="0 0 20 20"
          fill="currentColor"
        >
          <path
            fill-rule="evenodd"
            d="M4 4a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2v-2a2 2 0 00-2-2H4zm5 6a2 2 0 01-2 2H7a2 2 0 01-2-2v-2a2 2 0 012-2h2a2 2 0 012 2v2zm5-4a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2v-2a2 2 0 00-2-2h-2zm-3 10a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2a2 2 0 012-2h2a2 2 0 012 2v2z"
            clip-rule="evenodd"
          />
        </svg>
      </button>
    </div>
    <p class="text-[12px] text-on-surface-variant line-clamp-2 mb-4">{{ agent.description || 'No description' }}</p>

    <!-- Meta -->
    <div class="flex items-center justify-between text-[11px] font-mono">
      <span class="text-on-surface-variant/50">
        <span v-if="agent.is_voice_agent">{{ agent.voice_language }}</span>
        <span v-else>{{ (agent.tools_enabled || []).slice(0, 2).join(', ') }}</span>
      </span>
      <span class="text-on-surface-variant/40">{{ agent.use_count }} uses</span>
    </div>

    <!-- Actions -->
    <div class="flex flex-col gap-2 mt-4 pt-4 border-t border-white/5">
      <!-- Row 1 (always visible) -->
      <div class="flex items-center gap-2">
        <button @click.stop="$emit('edit', agent)"
          class="flex-1 py-1.5 bg-white/5 hover:bg-white/10 rounded-lg text-xs font-medium transition-colors flex items-center justify-center gap-1">
          <span class="material-symbols-outlined text-[14px]">edit</span> Edit
        </button>
        <button @click.stop="$emit('delete', agent)"
          class="flex-1 py-1.5 bg-white/5 hover:bg-error/20 hover:text-error rounded-lg transition-colors">
          <span class="material-symbols-outlined text-[14px]">delete</span>
        </button>
      </div>
      
      <!-- Row 2 (conditional) -->
      <div v-if="agent.is_active" class="flex items-center gap-2">
        <button @click.stop="$emit('deactivate', agent)"
          class="flex-1 py-1.5 bg-error/10 hover:bg-error/20 hover:text-error rounded-lg text-xs font-medium transition-colors flex items-center justify-center gap-1">
          <span class="material-symbols-outlined text-[14px]">radio_button_unchecked</span> Deactivate
        </button>
        <button @click.stop="$emit('test', agent)"
          class="flex-1 py-1.5 bg-secondary/10 hover:bg-secondary/20 hover:text-secondary rounded-lg text-xs font-medium transition-colors flex items-center justify-center gap-1">
          <span class="material-symbols-outlined text-[14px]">mic</span> Test
        </button>
      </div>
      <div v-else class="flex items-center gap-2">
        <button @click.stop="$emit('activate', agent)"
          class="flex-1 py-1.5 bg-success/10 hover:bg-success/20 hover:text-success rounded-lg text-xs font-medium transition-colors flex items-center justify-center gap-1">
          <span class="material-symbols-outlined text-[14px]">check_circle</span> Activate
        </button>
      </div>
      
      <!-- Clone button (only if is_public or is_template) -->
      <div class="flex justify-center">
        <button v-if="agent.is_public || agent.is_template" @click.stop="$emit('clone', agent)"
          class="px-3 py-1.5 bg-primary/10 hover:bg-primary/20 rounded-lg text-xs font-medium text-primary transition-colors flex items-center justify-center gap-1">
          <span class="material-symbols-outlined text-[14px]">content_copy</span> Clone
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useToastStore } from '@/stores/toast'

defineProps({ agent: { type: Object, required: true } })
defineEmits(['edit', 'clone', 'delete', 'activate', 'deactivate', 'test'])

function copyWebhook() {
  navigator.clipboard.writeText(agent.webhook_url || '').then(() => {
    // Use toast store to show success message
    const toastStore = useToastStore()
    toastStore.show('Webhook URL copied!', 'success')
  }).catch(err => {
    console.error('Failed to copy webhook URL:', err)
    const toastStore = useToastStore()
    toastStore.show('Failed to copy webhook URL', 'error')
  })
}
</script>
