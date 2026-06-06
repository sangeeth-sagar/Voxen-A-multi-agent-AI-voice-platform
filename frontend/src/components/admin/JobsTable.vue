<template>
  <div class="space-y-4">
    <!-- Filters row -->
    <div class="flex items-center gap-3 flex-wrap">
      <div class="flex-1 min-w-[200px] relative">
        <span class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant/40 text-[18px]">search</span>
        <input
          v-model="search"
          type="text"
          placeholder="Search by job ID or prompt…"
          class="w-full bg-white/5 border border-white/10 rounded-xl pl-10 pr-4 py-2.5 text-sm text-on-surface placeholder:text-on-surface-variant/40 outline-none focus:border-primary/30 transition-colors"
        />
      </div>
      <select v-model="statusFilter"
        class="bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 font-mono text-[11px] text-on-surface-variant outline-none cursor-pointer">
        <option value="">All Statuses</option>
        <option value="pending">Pending</option>
        <option value="processing">Processing</option>
        <option value="completed">Completed</option>
        <option value="failed">Failed</option>
      </select>
      <button @click="$emit('refresh')"
        class="p-2.5 bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl transition-colors text-on-surface-variant hover:text-white">
        <span class="material-symbols-outlined text-[18px]">refresh</span>
      </button>
    </div>

    <!-- Table -->
    <div class="glass-panel rounded-2xl overflow-hidden">
      <table class="w-full">
        <thead>
          <tr class="border-b border-white/5 bg-white/[0.02]">
            <th v-for="col in cols" :key="col"
              class="px-5 py-3.5 text-left font-mono text-[10px] uppercase tracking-widest text-on-surface-variant/50">
              {{ col }}
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="filtered.length === 0">
            <td :colspan="cols.length" class="px-5 py-10 text-center font-mono text-sm text-on-surface-variant/30">
              No jobs found
            </td>
          </tr>
          <tr
            v-for="job in filtered"
            :key="job.job_id"
            class="border-b border-white/5 hover:bg-white/[0.02] transition-colors"
          >
            <!-- Job ID -->
            <td class="px-5 py-4">
              <span class="font-mono text-[11px] text-primary/70 bg-primary/5 px-2 py-1 rounded-lg">
                {{ job.job_id.slice(0, 8) }}…
              </span>
            </td>

            <!-- Prompt -->
            <td class="px-5 py-4 max-w-[240px]">
              <p class="text-sm text-on-surface truncate" :title="job.user_prompt">
                {{ job.user_prompt || '—' }}
              </p>
            </td>

            <!-- Status badge -->
            <td class="px-5 py-4">
              <span :class="['px-2.5 py-1 rounded-full font-mono text-[10px] uppercase font-bold border', statusStyle(job.status)]">
                <span class="inline-block w-1.5 h-1.5 rounded-full mr-1.5 align-middle"
                  :class="statusDot(job.status)" />
                {{ job.status }}
              </span>
            </td>

            <!-- User -->
            <td class="px-5 py-4">
              <span class="font-mono text-[11px] text-on-surface-variant">
                {{ job.username || job.user_id?.slice(0, 8) || '—' }}
              </span>
            </td>

            <!-- Created at -->
            <td class="px-5 py-4 font-mono text-[11px] text-on-surface-variant/50">
              {{ formatDate(job.created_at) }}
            </td>

            <!-- Actions -->
            <td class="px-5 py-4">
              <button
                @click="viewJob(job)"
                class="p-1.5 hover:bg-white/5 rounded-lg transition-colors text-on-surface-variant hover:text-primary"
                title="View details"
              >
                <span class="material-symbols-outlined text-[16px]">open_in_new</span>
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Job Detail Modal -->
    <Transition name="modal">
      <div v-if="detailModal.open" class="fixed inset-0 z-[100] flex items-center justify-center">
        <div @click="detailModal.open = false" class="absolute inset-0 bg-black/70 backdrop-blur-sm" />
        <div class="modal-content relative z-10 glass-panel rounded-2xl p-7 w-full max-w-lg mx-4 max-h-[80vh] overflow-y-auto">
          <!-- Header -->
          <div class="flex items-start justify-between mb-5">
            <div>
              <h3 class="font-sans font-bold text-lg text-white">Job Details</h3>
              <p class="font-mono text-[10px] text-primary/60 mt-0.5">{{ detailModal.job?.job_id }}</p>
            </div>
            <button @click="detailModal.open = false"
              class="p-1.5 hover:bg-white/5 rounded-xl transition-colors text-on-surface-variant hover:text-white">
              <span class="material-symbols-outlined text-[18px]">close</span>
            </button>
          </div>

          <!-- Meta grid -->
          <div class="grid grid-cols-2 gap-3 mb-5">
            <div class="bg-white/3 rounded-xl p-4 border border-white/5">
              <p class="font-mono text-[9px] uppercase tracking-widest text-on-surface-variant/50 mb-1">Status</p>
              <span :class="['font-mono text-xs font-bold uppercase', statusTextColor(detailModal.job?.status)]">
                {{ detailModal.job?.status }}
              </span>
            </div>
            <div class="bg-white/3 rounded-xl p-4 border border-white/5">
              <p class="font-mono text-[9px] uppercase tracking-widest text-on-surface-variant/50 mb-1">Operator</p>
              <span class="font-mono text-xs text-on-surface">{{ detailModal.job?.username || '—' }}</span>
            </div>
            <div class="bg-white/3 rounded-xl p-4 border border-white/5">
              <p class="font-mono text-[9px] uppercase tracking-widest text-on-surface-variant/50 mb-1">Created</p>
              <span class="font-mono text-xs text-on-surface">{{ formatDate(detailModal.job?.created_at) }}</span>
            </div>
            <div class="bg-white/3 rounded-xl p-4 border border-white/5">
              <p class="font-mono text-[9px] uppercase tracking-widest text-on-surface-variant/50 mb-1">Job ID</p>
              <span class="font-mono text-[10px] text-primary/70">{{ detailModal.job?.job_id?.slice(0, 16) }}…</span>
            </div>
          </div>

          <!-- Prompt -->
          <div class="bg-white/3 rounded-xl p-4 border border-white/5 mb-4">
            <p class="font-mono text-[9px] uppercase tracking-widest text-on-surface-variant/50 mb-2">User Prompt</p>
            <p class="text-sm text-on-surface leading-relaxed">{{ detailModal.job?.user_prompt || '—' }}</p>
          </div>

          <!-- Error message if failed -->
          <div v-if="detailModal.job?.error_message"
            class="bg-error/5 rounded-xl p-4 border border-error/20">
            <p class="font-mono text-[9px] uppercase tracking-widest text-error/60 mb-2">Error</p>
            <p class="font-mono text-xs text-error/80 leading-relaxed">{{ detailModal.job.error_message }}</p>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, computed, reactive } from 'vue'

const props = defineProps({ jobs: { type: Array, default: () => [] } })
defineEmits(['refresh'])

const search = ref('')
const statusFilter = ref('')
const cols = ['Job ID', 'Prompt', 'Status', 'Operator', 'Created', 'Actions']

const filtered = computed(() =>
  props.jobs.filter(j => {
    const q = search.value.toLowerCase()
    const matchSearch = !q
      || j.job_id?.toLowerCase().includes(q)
      || j.user_prompt?.toLowerCase().includes(q)
      || j.username?.toLowerCase().includes(q)
    const matchStatus = !statusFilter.value || j.status === statusFilter.value
    return matchSearch && matchStatus
  })
)

const detailModal = reactive({ open: false, job: null })

function viewJob(job) {
  detailModal.job = job
  detailModal.open = true
}

function formatDate(dt) {
  if (!dt) return '—'
  return new Date(dt).toLocaleString('en-US', {
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
  })
}

function statusStyle(status) {
  return {
    pending:    'bg-tactical-amber/10 text-tactical-amber border-tactical-amber/30',
    processing: 'bg-secondary/10 text-secondary border-secondary/30',
    completed:  'bg-green-900/30 text-green-400 border-green-500/20',
    failed:     'bg-error/10 text-error border-error/30',
  }[status] ?? 'bg-white/5 text-on-surface-variant border-white/10'
}

function statusDot(status) {
  return {
    pending:    'bg-tactical-amber',
    processing: 'bg-secondary animate-pulse',
    completed:  'bg-green-400',
    failed:     'bg-error',
  }[status] ?? 'bg-on-surface-variant'
}

function statusTextColor(status) {
  return {
    pending:    'text-tactical-amber',
    processing: 'text-secondary',
    completed:  'text-green-400',
    failed:     'text-error',
  }[status] ?? 'text-on-surface-variant'
}
</script>
