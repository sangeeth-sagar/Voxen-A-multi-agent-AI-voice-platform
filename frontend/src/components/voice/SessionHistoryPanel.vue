<template>
  <div class="glass-panel">
    <div class="flex items-center justify-between px-4 py-3 border-b border-gray-700/50">
      <h3 class="text-lg font-semibold text-white">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-2" viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10l-3.293-3.293a1 1 0 111.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clip-rule="evenodd"/>
          <path fill-rule="evenodd" d="M12.293 14.707a1 1 0 00-1.414 0L9 11.293l-3.293 3.293a1 1 0 101.414 1.414l4-4a1 1 0 000-1.414l-3.293 3.293z" clip-rule="evenodd"/>
        </svg>
        Conversation History
      </h3>
      <button
        @click="clearHistory"
        class="text-sm text-gray-400 hover:text-white transition-colors"
        :disabled="loading || sessions.length === 0"
      >
        Clear
      </button>
    </div>

    <div class="px-4 py-3">
      <div v-if="loading" class="flex items-center justify-center py-8">
        <div class="animate-spin rounded-full border-4 border-primary/50 border-t-primary w-8 h-8"></div>
      </div>
      
      <div v-else-if="sessions.length === 0" class="text-center py-8">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 mx-auto mb-4 text-gray-500" viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l2-2z" clip-rule="evenodd"/>
          <path fill-rule="evenodd" d="M9 6a1 1 0 000 2h2a1 1 0 100-2H9z" clip-rule="evenodd"/>
        </svg>
        <p class="text-gray-400">No conversations yet</p>
      </div>
      
      <div v-else class="space-y-3">
        <div
          v-for="session in sessions"
          :key="session.id"
          class="bg-gray-800/50 rounded-xl border border-gray-700/50 overflow-hidden transition-all duration-200"
          :class="{ 'border-primary/50': session.expanded }"
        >
          <!-- Session Header -->
          <div
            @click="toggleExpand(session)"
            class="flex items-center justify-between px-4 py-3 cursor-pointer"
          >
            <div class="flex items-center">
              <div class="flex-shrink-0 w-8 h-8 bg-primary/20 rounded flex items-center justify-center">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-primary" viewBox="0 0 20 20" fill="currentColor">
                  <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 100 2h3a1 1 0 100-2h-3zm-1 4a1 1 0 100 2h1a1 1 0 100-2h-1zm4-6a1 1 0 100 2h3a1 1 0 100-2h-3z" clip-rule="evenodd"/>
                </svg>
              </div>
              <div class="ml-3">
                <p class="text-white font-medium">{{ session.agent_name || 'Unknown agent' }}</p>
                <p class="text-sm text-gray-400">
                  {{ formatDate(session.created_at) }} · {{ session.message_count }} messages
                </p>
              </div>
            </div>
            
            <!-- Chevron -->
            <svg
              xmlns="http://www.w3.org/2000/svg"
              class="h-4 w-4 text-gray-400 transition-transform duration-200"
              :class="{ 'rotate-180': session.expanded }"
              viewBox="0 0 20 20"
              fill="currentColor"
            >
              <path fill-rule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 011.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clip-rule="evenodd"/>
            </svg>
          </div>

          <!-- Expanded Messages -->
          <div v-if="session.expanded" class="px-4 py-3 border-t border-gray-700/50 max-h-[300px] overflow-y-auto">
            <div
              v-for="message in session.messages"
              :key="message.id"
              class="mb-3"
            >
              <div
                :class="[
                  'max-w-xs px-3 py-2 rounded',
                  message.role === 'user' && 'ml-auto bg-primary/20 text-primary',
                  message.role === 'assistant' && 'mr-auto bg-secondary/20 text-secondary'
                ]"
              >
                <p class="whitespace-pre-wrap break-words text-sm">
                  <template v-if="message.role === 'user'">
                    <strong>YOU:</strong> {{ message.content }}
                  </template>
                  <template v-else>
                    <strong>Assistant:</strong> {{ message.content }}
                  </template>
                </p>
                <span class="block text-xs text-gray-600 mt-1">
                  {{ formatTime(message.timestamp) }}
                </span>
              </div>
            </div>
            
            <div class="mt-3 flex justify-end">
              <button
                @click="loadSession(session)"
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
                Load in current session
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useVoiceAgentStore } from '@/stores/voiceAgent'
import { apiFetch } from '@/composables/useApi'

const props = defineProps({
  sessions: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['load-session'])

const voiceAgentStore = useVoiceAgentStore()

// Add expanded property to each session for UI state
const sessionsWithState = ref(
  props.sessions.map(session => ({
    ...session,
    expanded: false
  }))
)

// Watch for prop changes
watch(
  () => props.sessions,
  (newSessions) => {
    sessionsWithState.value = newSessions.map(session => ({
      ...session,
      expanded: false
    }))
  }
)

function toggleExpand(session) {
  const index = sessionsWithState.value.findIndex(s => s.id === session.id)
  if (index !== -1) {
    sessionsWithState.value[index].expanded = !sessionsWithState.value[index].expanded
  }
}

function loadSession(session) {
  emit('load-session', session)
}

function clearHistory() {
  if (window.confirm('Are you sure you want to clear all conversation history?')) {
    // This would typically call an API endpoint
    // For now, we'll just emit an event that the parent can handle
    emit('load-session', { clear: true })
  }
}

function formatDate(dateString) {
  const options = { year: 'numeric', month: 'long', day: 'numeric' }
  return new Date(dateString).toLocaleDateString(undefined, options)
}

function formatTime(dateString) {
  return new Date(dateString).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}
</script>

<style scoped>
.glass-panel {
  background: rgba(30, 30, 30, 0.7);
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
}

.glass-panel:hover {
  border-color: rgba(255, 255, 255, 0.2);
  box-shadow: 0 12px 48px rgba(0, 0, 0, 0.3);
}
</style>