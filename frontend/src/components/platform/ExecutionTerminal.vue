<template>
  <div class="glass-panel rounded-2xl flex flex-col h-full overflow-hidden">
    <!-- Terminal chrome -->
    <div class="px-6 py-3 border-b border-white/5 flex items-center justify-between bg-white/[0.02] shrink-0">
      <div class="flex items-center gap-4">
        <div class="flex gap-1.5">
          <div class="w-2.5 h-2.5 rounded-full bg-error/40 hover:bg-error/70 transition-colors cursor-pointer" />
          <div class="w-2.5 h-2.5 rounded-full bg-tactical-amber/40 hover:bg-tactical-amber/70 transition-colors cursor-pointer" />
          <div class="w-2.5 h-2.5 rounded-full bg-primary/40 hover:bg-primary/70 transition-colors cursor-pointer" />
        </div>
        <span class="font-mono text-[10px] text-white/40 uppercase tracking-[0.2em]">Execution Core</span>
      </div>
      <div class="flex items-center gap-3">
        <span class="font-mono text-[10px] text-primary/60">TTY: CORE-01</span>
        <button @click="clearLogs" class="text-on-surface-variant/40 hover:text-on-surface-variant transition-colors">
          <span class="material-symbols-outlined text-sm">delete_sweep</span>
        </button>
      </div>
    </div>

    <!-- Log output -->
    <div ref="logEl" class="p-5 font-mono text-xs overflow-y-auto flex-1 bg-black/30 text-primary/80 space-y-1">
      <p v-for="(line, i) in logs" :key="i" :class="line.type === 'success' ? 'text-green-400' : line.type === 'error' ? 'text-error' : line.type === 'agent' ? 'text-secondary' : 'text-primary/80'">
        <span class="text-white/20 mr-2 select-none">[{{ line.ts }}]</span>
        <span v-if="line.label" :class="['font-bold mr-1', line.type === 'success' ? 'text-green-400' : line.type === 'error' ? 'text-error' : 'text-white']">
          {{ line.label }}
        </span>
        {{ line.text }}
      </p>
      <span v-if="active" class="inline-block w-2 h-3 bg-primary animate-pulse" />
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue'

const props = defineProps({
  active: { type: Boolean, default: false }
})

const logEl = ref(null)
const logs = ref([
  { ts: '09:42:12', text: 'Kernel initialized...', type: 'dim' },
  { ts: '09:42:13', text: 'Loading high-fidelity workspace...', type: 'agent' },
  { ts: '09:42:15', label: 'root@agent-iq:~$', text: 'launch --mission-control', type: 'default' },
  { ts: '09:42:16', text: 'System operational. 128 nodes online.', type: 'success' },
])

function addLog(text, type = 'default', label = '') {
  const now = new Date()
  const ts = now.toTimeString().slice(0, 8)
  logs.value.push({ ts, text, type, label })
  nextTick(() => {
    if (logEl.value) logEl.value.scrollTop = logEl.value.scrollHeight
  })
}

function clearLogs() { logs.value = [] }

defineExpose({ addLog })
</script>
