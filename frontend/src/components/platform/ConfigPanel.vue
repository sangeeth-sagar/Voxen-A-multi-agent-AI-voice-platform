<template>
  <div class="glass-panel rounded-2xl p-6">
    <div class="flex items-center justify-between mb-5">
      <h3 class="font-sans font-semibold text-sm">Mission Parameters</h3>
      <span class="font-mono text-[10px] text-primary/60 uppercase">BI Agent</span>
    </div>

    <form @submit.prevent="generate" class="space-y-4">
      <div>
        <label class="block font-mono text-[10px] uppercase tracking-widest text-on-surface-variant mb-2">Target Objective</label>
        <textarea
          v-model="prompt"
          rows="3"
          placeholder="e.g. Generate a GTM strategy for a B2B SaaS targeting SMEs in Southeast Asia…"
          class="w-full bg-white/3 border border-white/10 rounded-xl px-4 py-3 font-sans text-sm text-on-surface placeholder:text-on-surface-variant/40 outline-none focus:border-primary/30 transition-colors resize-none"
        />
      </div>

      <button
        type="submit"
        :disabled="loading || !prompt.trim()"
        class="w-full btn-primary py-3 rounded-xl font-semibold text-sm flex items-center justify-center gap-2 disabled:opacity-40"
      >
        <span v-if="loading" class="material-symbols-outlined text-sm animate-spin">refresh</span>
        <span v-else class="material-symbols-outlined text-sm icon-filled">rocket_launch</span>
        {{ loading ? 'Deploying Agents...' : 'Deploy Intelligence' }}
      </button>
    </form>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { apiFetch } from '@/composables/useApi'
import { useToastStore } from '@/stores/toast'

const emit = defineEmits(['job-started'])
const toast = useToastStore()
const prompt = ref('')
const loading = ref(false)

async function generate() {
  if (!prompt.value.trim()) return
  loading.value = true
  try {
    const data = await apiFetch('/api/v1/plan', {
      method: 'POST',
      body: JSON.stringify({ user_prompt: prompt.value }),
    })
    emit('job-started', data.job_id)
    toast.show('Intelligence deployment initiated', 'success')
  } catch (e) {
    toast.show(e.message, 'error')
  } finally {
    loading.value = false
  }
}
</script>
