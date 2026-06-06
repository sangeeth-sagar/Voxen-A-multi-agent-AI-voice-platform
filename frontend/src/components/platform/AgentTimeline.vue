<template>
  <div class="glass-panel rounded-2xl flex flex-col overflow-hidden h-full">
    <div class="p-5 border-b border-white/5 flex items-center justify-between shrink-0">
      <h3 class="font-sans font-semibold text-sm">Active Pipeline</h3>
      <span class="material-symbols-outlined text-primary/40 text-lg">timeline</span>
    </div>
    <div class="p-5 space-y-5 flex-1 overflow-y-auto">
      <div
        v-for="(step, i) in steps"
        :key="i"
        class="flex gap-4 relative"
      >
        <!-- connector line -->
        <div v-if="i < steps.length - 1" class="absolute left-3.5 top-8 bottom-[-20px] w-px bg-white/5" />

        <!-- status icon -->
        <div :class="[
          'w-7 h-7 rounded-full flex items-center justify-center shrink-0 mt-0.5',
          step.status === 'done'
            ? 'bg-primary/20 border border-primary/40'
            : step.status === 'active'
            ? 'bg-secondary/20 border border-secondary shadow-[0_0_10px_rgba(208,188,255,0.2)]'
            : 'bg-white/5 border border-white/10 opacity-40'
        ]">
          <span :class="[
            'material-symbols-outlined text-[14px]',
            step.status === 'done' ? 'text-primary' :
            step.status === 'active' ? 'text-secondary animate-spin' : 'text-on-surface-variant'
          ]">
            {{ step.status === 'done' ? 'check' : step.status === 'active' ? 'refresh' : 'radio_button_unchecked' }}
          </span>
        </div>

        <!-- info -->
        <div :class="step.status === 'pending' ? 'opacity-40' : ''">
          <p class="text-xs font-bold text-white">{{ step.label }}</p>
          <p class="text-[10px] text-on-surface-variant mt-0.5">{{ step.meta }}</p>
          <div v-if="step.progress !== undefined && step.status === 'active'" class="mt-2 w-32 bg-white/5 h-1 rounded-full overflow-hidden">
            <div class="bg-secondary h-full transition-all duration-500" :style="{ width: step.progress + '%' }" />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const steps = ref([
  { label: 'Ingestion Complete', meta: '1.2GB processed (0.4s)', status: 'done' },
  { label: 'Neural Processing', meta: '98% Confidence threshold', status: 'active', progress: 85 },
  { label: 'Strategy Formation', meta: 'GTM + pricing analysis', status: 'pending' },
  { label: 'Critic Review', meta: 'Quality assurance pass', status: 'pending' },
  { label: 'Formatter Output', meta: 'JSON + Markdown render', status: 'pending' },
])

function setStepStatus(index, status, progress) {
  if (steps.value[index]) {
    steps.value[index].status = status
    if (progress !== undefined) steps.value[index].progress = progress
  }
}

defineExpose({ setStepStatus, steps })
</script>
