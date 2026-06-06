import { defineStore } from 'pinia'

export const useVoiceAgentStore = defineStore('voiceAgent', {
  state: () => ({
    activeAgent: null,
    isListening: false,
    isProcessing: false,
    isSpeaking: false,
    sessionId: null,
    conversationHistory: [],
    wakeWordEnabled: false,
    detectionMode: 'browser'
  }),
  actions: {
    setActiveAgent(agent) {
      this.activeAgent = agent
      this.conversationHistory = []
      this.sessionId = null
    },
    clearSession() {
      this.sessionId = null
      this.conversationHistory = []
    },
    addMessage(role, content) {
      this.conversationHistory.push({
        role,
        content,
        timestamp: Date.now()
      })
    },
    setSessionId(id) {
      this.sessionId = id
    },
    toggleWakeWord(bool) {
      this.wakeWordEnabled = bool
    },
    setStatus(listening, processing, speaking) {
      this.isListening = listening
      this.isProcessing = processing
      this.isSpeaking = speaking
    }
  }
})