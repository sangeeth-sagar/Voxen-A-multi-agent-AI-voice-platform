<template>
  <AppLayout>
    <div class="h-full p-6 grid grid-cols-12 gap-6 overflow-hidden">

      <!-- LEFT: Voice Agent -->
      <VoiceAgent class="col-span-12 lg:col-span-5" />

      <!-- RIGHT: BI Tools -->
      <section class="col-span-12 lg:col-span-7 flex flex-col gap-5 overflow-hidden">

        <!-- Config -->
        <ConfigPanel @job-started="onJobStarted" />

        <!-- Terminal + Timeline row -->
        <div class="flex-1 grid grid-cols-1 md:grid-cols-2 gap-5 min-h-0">
          <ExecutionTerminal ref="terminalRef" :active="jobActive" class="h-full" />
          <AgentTimeline ref="timelineRef" class="h-full" />
        </div>

        <!-- Stats -->
        <StatsBar />
      </section>
    </div>
  </AppLayout>
</template>

<script setup>
import { ref } from 'vue'
import AppLayout from '@/components/layout/AppLayout.vue'
import VoiceAgent from '@/components/voice/VoiceAgent.vue'
import ConfigPanel from '@/components/platform/ConfigPanel.vue'
import ExecutionTerminal from '@/components/platform/ExecutionTerminal.vue'
import AgentTimeline from '@/components/platform/AgentTimeline.vue'
import StatsBar from '@/components/platform/StatsBar.vue'
import { apiFetch } from '@/composables/useApi'

const terminalRef = ref(null)
const timelineRef = ref(null)
const jobActive = ref(false)
let pollInterval = null

function onJobStarted(jobId) {
  jobActive.value = true
  terminalRef.value?.addLog(`Job ${jobId.slice(0, 8)}… queued`, 'agent', 'SYSTEM:')
  pollJob(jobId)
}

async function pollJob(jobId) {
  if (pollInterval) clearInterval(pollInterval)
  pollInterval = setInterval(async () => {
    try {
      const data = await apiFetch(`/api/v1/plan/${jobId}`)
      terminalRef.value?.addLog(`Status: ${data.status}`, 'default')
      if (data.status === 'completed') {
        terminalRef.value?.addLog('Intelligence compiled successfully.', 'success', 'DONE:')
        jobActive.value = false
        clearInterval(pollInterval)
      } else if (data.status === 'failed') {
        terminalRef.value?.addLog('Mission failed. Check logs.', 'error', 'ERR:')
        jobActive.value = false
        clearInterval(pollInterval)
      }
    } catch (e) {
      clearInterval(pollInterval)
    }
  }, 2000)
}
</script>
