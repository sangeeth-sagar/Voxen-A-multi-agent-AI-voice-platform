<template>
  <div
    v-if="isTestOpen"
    class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50"
  >
    <div
      class="w-96 bg-gray-800/80 backdrop-blur-lg rounded-2xl border border-gray-700/50 shadow-2xl"
    >
      <!-- Header -->
      <div class="flex items-center p-4 border-b border-gray-700/50">
        <!-- Neural Orb -->
        <div class="w-12 h-12 flex-shrink-0">
          <div
            class="neural-orb w-full h-full animate-pulse"
          ></div>
        </div>
        <div class="ml-3 flex-1">
          <h3 class="text-white font-semibold">{{ testAgent?.name }}</h3>
          <p class="text-sm text-gray-400">
            Wake word: <span class="text-white">{{ testAgent?.wake_word }}</span>
          </p>
        </div>
        <div class="flex items-center">
          <!-- Status Chip -->
          <span
            :class="[
              'px-2 py-1 text-xs rounded',
              testStatus === 'idle' && 'bg-gray-600',
              testStatus === 'listening_wake' && 'bg-blue-500',
              testStatus === 'listening' && 'bg-green-500',
              testStatus === 'processing' && 'bg-yellow-500',
              testStatus === 'speaking' && 'bg-purple-500'
            ]"
          >
            {{ testStatus }}
          </span>
          <!-- Close Button -->
          <button
            @click="closeTest"
            class="ml-4 text-gray-400 hover:text-white transition-colors"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              class="h-5 w-5"
              viewBox="0 0 20 20"
              fill="currentColor"
            >
              <path
                fill-rule="evenodd"
                d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                clip-rule="evenodd"
              />
            </svg>
          </button>
        </div>
      </div>

      <!-- Center Orb Area -->
      <div class="relative h-64 flex flex-col items-center justify-center p-6">
        <!-- Large Neural Orb -->
        <div class="w-36 h-36 flex-shrink-0">
          <div
            class="neural-orb-large w-full h-full"
            :class="{
              'animate-pulse': testStatus === 'listening' || testStatus === 'speaking'
            }"
          ></div>
        </div>

        <!-- Status Text -->
        <p class="mt-4 text-center text-gray-300">
          <template v-if="testStatus === 'idle'">
            Say "<strong>{{ testAgent?.wake_word }}</strong>" to activate
          </template>
          <template v-else-if="testStatus === 'listening_wake'">
            Listening for wake word...
          </template>
          <template v-else-if="testStatus === 'listening'">
            Listening...
          </template>
          <template v-else-if="testStatus === 'processing'">
            Processing...
          </template>
          <template v-else-if="testStatus === 'speaking'">
            Speaking...
          </template>
        </p>

        <!-- Waveform Bars -->
        <div class="mt-6 flex w-full justify-center space-x-1">
          <template v-for="i in 12" :key="i">
            <div
              class="w-1 bg-gray-600"
              :class="{
                'bg-primary': isWaveformActive,
                'transition-all duration-100': true
              }"
              :style="{ height: waveformBars[i] + 'px' }"
            ></div>
          </template>
        </div>
      </div>

      <!-- Transcript Panel -->
      <div class="flex-1 overflow-y-auto p-4">
        <div
          v-for="message in testTranscript"
          :key="message.timestamp"
          class="mb-3"
        >
          <div
            :class="[
              'max-w-xs px-3 py-2 rounded',
              message.role === 'user' && 'ml-auto bg-primary/20 text-primary',
              message.role === 'assistant' && 'mr-auto bg-secondary/20 text-secondary',
              message.role === 'system' && 'text-center text-xs text-gray-500 italic'
            ]"
          >
            <p class="whitespace-pre-wrap break-words">
              <template v-if="message.role === 'user'">
                <strong>YOU:</strong> {{ message.content }}
              </template>
              <template v-else-if="message.role === 'assistant'">
                <strong>{{ testAgent?.name }}:</strong> {{ message.content }}
              </template>
              <template v-else>
                {{ message.content }}
              </template>
            </p>
            <span class="block text-xs text-gray-600 mt-1">
              {{ new Date(message.timestamp).toLocaleTimeString() }}
            </span>
          </div>
        </div>
      </div>

      <!-- Footer -->
      <div class="px-4 pb-4 pt-2 border-t border-gray-700/50">
        <div class="flex justify-between">
          <button
            @click="resetSession"
            class="flex items-center px-3 py-2 text-sm font-medium text-gray-300 border border-gray-600 rounded hover:bg-gray-700 transition-colors"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              class="h-4 w-4 mr-2"
              viewBox="0 0 20 20"
              fill="currentColor"
            >
              <path
                fill-rule="evenodd"
                d="M4 4a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2v-2a2 2 0 00-2-2H4zm5 6a2 2 0 01-2 2H7a2 2 0 01-2-2v-2a2 2 0 012-2h2a2 2 0 012 2v2zm5-4a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2v-2a2 2 0 00-2-2h-2zm-3 10a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2a2 2 0 012-2h2a2 2 0 012 2v2z"
                clip-rule="evenodd"
              />
            </svg>
            Reset Session
          </button>
          <button
            @click="closeTest"
            class="flex items-center px-3 py-2 text-sm font-medium text-gray-300 border border-gray-600 rounded hover:bg-gray-700 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onBeforeUnmount } from 'vue'
import { useAgentTest } from '@/composables/useAgentTest'

const props = defineProps({
  agent: {
    type: Object,
    required: true
  },
  open: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['close'])

const {
  isTestOpen,
  testAgent,
  testTranscript,
  testSessionId,
  testStatus,
  isActive,
  openTest,
  closeTest,
  addTestMessage
} = useAgentTest()

// Sync with parent's open prop
watch(
  () => props.open,
  (newVal) => {
    if (newVal) {
      openTest(props.agent)
    } else {
      closeTest()
    }
  }
)

// Update testAgent when prop changes
watch(
  () => props.agent,
  (newAgent) => {
    if (props.open && newAgent) {
      // Re-open test with new agent
      closeTest()
      openTest(newAgent)
    }
  }
)

// Handle close from internal close button
function handleClose() {
  closeTest()
  emit('close')
}

// Reset session function
function resetSession() {
  // Clear transcript and reset session
  testTranscript.value = []
  testSessionId.value = null
  addTestMessage('system', 'Session reset. Say the wake word to activate.')
}

// Waveform animation
const waveformBars = ref(Array(12).fill(8)) // Start with flat bars
let waveformInterval = null

watch(
  () => testStatus.value,
  (newStatus) => {
    const isActive = newStatus === 'listening' || newStatus === 'speaking'
    if (isActive && !waveformInterval) {
      waveformInterval = setInterval(() => {
        waveformBars.value = waveformBars.value.map(() =>
          Math.floor(Math.random() * 41) + 8 // Random between 8px and 48px
        )
      }, 100)
    } else if (!isActive && waveformInterval) {
      clearInterval(waveformInterval)
      waveformInterval = null
      waveformBars.value = waveformBars.value.map(() => 8) // Flat when inactive
    }
  }
)

// Cleanup interval on unmount
onBeforeUnmount(() => {
  if (waveformInterval) {
    clearInterval(waveformInterval)
  }
})
</script>

<style scoped>
.neural-orb {
  position: relative;
  width: 100%;
  height: 100%;
  border-radius: 50%;
  background: radial-gradient(
    circle at center,
    rgba(59, 130, 246, 0.2) 0%,
    transparent 70%
  );
  box-shadow: 0 0 15px rgba(59, 130, 246, 0.3);
  overflow: hidden;
}

.neural-orb::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  width: 60%;
  height: 60%;
  background: radial-gradient(
    circle at center,
    rgba(59, 130, 246, 0.4) 0%,
    transparent 70%
  );
  transform: translate(-50%, -50%);
  animation: pulse 2s ease-in-out infinite;
}

.neural-orb-large {
  position: relative;
  width: 100%;
  height: 100%;
  border-radius: 50%;
  background: radial-gradient(
    circle at center,
    rgba(59, 130, 246, 0.2) 0%,
    transparent 70%
  );
  box-shadow: 0 0 25px rgba(59, 130, 246, 0.4);
  overflow: hidden;
}

.neural-orb-large::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  width: 70%;
  height: 70%;
  background: radial-gradient(
    circle at center,
    rgba(59, 130, 246, 0.4) 0%,
    transparent 70%
  );
  transform: translate(-50%, -50%);
  animation: pulse 3s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% {
    transform: translate(-50%, -50%) scale(1);
  }
  50% {
    transform: translate(-50%, -50%) scale(1.05);
  }
}
</style>