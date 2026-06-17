<template>
  <div class="admin-agents p-6">
    <header class="flex items-center justify-between mb-5">
      <div>
        <h1 class="font-sans text-2xl font-bold text-on-surface tracking-tight">
          All Agents <span class="text-on-surface-variant/40 font-mono text-base ml-2">{{ agents.length }}</span>
        </h1>
        <p class="font-mono text-[11px] text-on-surface-variant/60 uppercase tracking-wider mt-1">Every agent across every operator</p>
      </div>
      <button @click="fetchAgents" class="p-2.5 bg-surface-container-high hover:bg-surface-container-highest border border-outline-variant rounded-xl transition-colors text-on-surface-variant hover:text-on-surface">
        <span class="material-symbols-outlined text-[18px]">refresh</span>
      </button>
    </header>

    <div v-if="loading" class="flex items-center justify-center py-12">
      <span class="material-symbols-outlined text-4xl text-primary/30 animate-spin">refresh</span>
    </div>

    <div v-else-if="agents.length === 0" class="glass-panel rounded-2xl p-12 text-center text-on-surface-variant/40">
      <span class="material-symbols-outlined text-5xl mb-3 block">smart_toy</span>
      <p class="font-mono text-sm uppercase">No agents deployed yet</p>
    </div>

    <div v-else class="glass-panel rounded-2xl overflow-hidden">
      <table class="w-full">
        <thead>
          <tr class="border-b border-outline-variant bg-surface-container-low">
            <th class="th">Name</th>
            <th class="th">Owner</th>
            <th class="th">Type</th>
            <th class="th">Status</th>
            <th class="th">Uses</th>
            <th class="th">Created</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="a in agents" :key="a.uuid" class="row border-b border-outline-variant">
            <td class="td font-medium text-on-surface">{{ a.name }}</td>
            <td class="td text-on-surface-variant">{{ a.owner_email || a.user_email || '—' }}</td>
            <td class="td font-mono text-[11px] text-on-surface-variant">{{ a.is_voice_agent ? 'voice' : 'bi' }}</td>
            <td class="td">
              <span :class="['status-badge', a.is_active ? 'active' : 'inactive']">
                {{ a.is_active ? 'Active' : 'Inactive' }}
              </span>
            </td>
            <td class="td font-mono text-on-surface-variant">{{ a.use_count || 0 }}</td>
            <td class="td font-mono text-[11px] text-on-surface-variant/60">{{ formatDate(a.created_at) }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { apiFetch } from '@/composables/useApi'
import { useToastStore } from '@/stores/toast'

const toast = useToastStore()
const agents = ref([])
const loading = ref(false)

async function fetchAgents() {
  loading.value = true
  try { agents.value = await apiFetch('/api/v1/admin/agents') }
  catch (e) { toast.show('Failed to load agents', 'error') }
  finally { loading.value = false }
}

function formatDate(dt) {
  if (!dt) return '—'
  return new Date(dt).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

onMounted(fetchAgents)
</script>

<style scoped>
.th {
  padding: 14px 16px; text-align: left; font-family: 'JetBrains Mono', monospace;
  font-size: 10px; text-transform: uppercase; letter-spacing: 0.1em;
  color: var(--color-on-surface-variant); font-weight: 600;
}
.td { padding: 12px 16px; font-size: 13px; color: var(--color-on-surface); }
.row { transition: background 0.15s ease; }
.row:hover { background: var(--color-surface-container-high); }

html.dark .row:hover { background: rgba(255, 255, 255, 0.02); }

.status-badge {
  display: inline-block; padding: 4px 10px; border-radius: 999px;
  font-family: 'JetBrains Mono', monospace; font-size: 10px; font-weight: 600;
  text-transform: uppercase; letter-spacing: 0.05em;
}
.status-badge.active { background: var(--color-success-container, rgba(14, 108, 74, 0.12)); color: var(--color-success); border: 1px solid var(--color-success); }
.status-badge.inactive { background: var(--color-surface-container-high); color: var(--color-outline); border: 1px solid var(--color-outline-variant); }
</style>
