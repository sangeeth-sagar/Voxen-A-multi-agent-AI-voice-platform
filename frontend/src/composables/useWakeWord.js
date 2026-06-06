import { ref, watch, onUnmounted } from 'vue'
import { useVoiceAgentStore } from '@/stores/voiceAgent'
import { useAuthStore } from '@/stores/auth'
import { useLanguage } from './useLanguage'
import { useTTS } from './useTTS'
import { apiFetch, apiFetchBlob } from '@/composables/useApi'

export function useWakeWord() {
  const { getSttLocale, selectedLanguage } = useLanguage()
  const { speak } = useTTS()

  let recognition = null
  let conversationRecognition = null
  const isDetecting = ref(false)
  const isListening = ref(false)
  const detectedWakeWord = ref('')
  let activeConversationAgent = null

  function startDetection(agents) {
    // Check browser support for SpeechRecognition
    if (!('SpeechRecognition' in window || 'webkitSpeechRecognition' in window)) {
      console.warn('SpeechRecognition not supported in this browser')
      return
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    recognition = new SpeechRecognition()
    recognition.continuous = true
    recognition.interimResults = false
    recognition.lang = getSttLocale()
    recognition.maxAlternatives = 3

    recognition.onresult = (event) => {
      const transcript = Array.from(event.results)
        .map(result => result[0])
        .map(result => result.transcript)
        .join('')
        .toLowerCase()

      for (const agent of agents) {
        if (transcript.includes(agent.wake_word.toLowerCase())) {
          detectedWakeWord.value = agent.wake_word
          onWakeWordDetected(agent)
          break
        }
      }
    }

    recognition.onerror = (event) => {
      if (event.error !== 'no-speech') {
        console.error('SpeechRecognition error:', event.error)
      }
    }

    recognition.onend = () => {
      if (isDetecting.value) {
        // Auto-restart to keep listening
        recognition.start()
      }
    }

    recognition.start()
    isDetecting.value = true
  }

  function stopDetection() {
    if (recognition) {
      recognition.stop()
    }
    isDetecting.value = false
  }

  function stopListening() {
    if (conversationRecognition) {
      try { conversationRecognition.stop() } catch (_) {}
      conversationRecognition = null
    }
    isListening.value = false
  }

  function startListening() {
    if (conversationRecognition) {
      try { conversationRecognition.start() } catch (_) {}
    }
  }

  async function onWakeWordDetected(agent) {
    const voiceAgentStore = useVoiceAgentStore()
    if (voiceAgentStore.isProcessing || voiceAgentStore.isSpeaking) {
      return
    }

    // Temporarily stop detection to avoid echo
    stopDetection()

    // Set active agent
    voiceAgentStore.setActiveAgent(agent)

    // Play wake confirm audio
    try {
      const wakeConfirmBlob = await apiFetchBlob(`/api/v1/voice-agent/wake-confirm/${agent.uuid}`)
      const wakeConfirmUrl = URL.createObjectURL(wakeConfirmBlob)
      const wakeConfirmAudio = new Audio(wakeConfirmUrl)
      wakeConfirmAudio.play()
      wakeConfirmAudio.onended = () => {
        URL.revokeObjectURL(wakeConfirmUrl)
        // Play welcome audio
        playWelcomeAudio(agent)
      }
    } catch (error) {
      console.error('Failed to play wake confirm audio:', error)
      // If wake confirm fails, still try to play welcome
      playWelcomeAudio(agent)
    }
  }

  async function playWelcomeAudio(agent) {
    try {
      const welcomeBlob = await apiFetchBlob(`/api/v1/voice-agent/welcome/${agent.uuid}`)
      const welcomeUrl = URL.createObjectURL(welcomeBlob)
      const welcomeAudio = new Audio(welcomeUrl)
      welcomeAudio.play()
      welcomeAudio.onended = () => {
        URL.revokeObjectURL(welcomeUrl)
        // Start conversation listening
        startConversationLoop(agent)
      }
    } catch (error) {
      console.error('Failed to play welcome audio:', error)
      // If welcome fails, still start conversation
      startConversationLoop(agent)
    }
  }

  function startConversationLoop(agent) {
    const voiceAgentStore = useVoiceAgentStore()
    activeConversationAgent = agent

    // Create a new SpeechRecognition instance for conversation
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    conversationRecognition = new SpeechRecognition()
    conversationRecognition.continuous = false
    conversationRecognition.interimResults = true
    conversationRecognition.lang = getSttLocale()

    conversationRecognition.onresult = (event) => {
      const transcript = Array.from(event.results)
        .map(result => result[0])
        .map(result => result.transcript)
        .join('')
        .trim()

      if (!transcript) {
        // Empty transcript, restart listening
        conversationRecognition.start()
        return
      }

      const stopWords = ["goodbye", "bye", "stop", "exit", "quit", "that's all"]
      const lowerTranscript = transcript.toLowerCase()
      if (stopWords.some(word => lowerTranscript.includes(word))) {
        // End conversation
        endConversation()
        return
      }

      voiceAgentStore.setStatus(false, true, false) // listening=false, processing=true, speaking=false
      sendToAgent(transcript, agent)
    }

    conversationRecognition.onend = () => {
      isListening.value = false
      if (!voiceAgentStore.isProcessing && !voiceAgentStore.isSpeaking) {
        // Restart if not busy
        if (activeConversationAgent) {
          try { conversationRecognition.start() } catch (_) {}
        }
      }
    }

    try { conversationRecognition.start() } catch (_) {}
    isListening.value = true
  }

  async function sendToAgent(text, agent) {
    const voiceAgentStore = useVoiceAgentStore()
     try {
       // Parameters must be sent as JSON body — backend expects a Pydantic model, NOT query params
       const response = await apiFetch('/api/v1/voice-agent/chat', {
         method: 'POST',
         body: JSON.stringify({
           text,
           agent_uuid: agent.uuid,
           session_id: voiceAgentStore.sessionId,
           language: selectedLanguage.value
         })
       })

      voiceAgentStore.setSessionId(response.session_id)
      voiceAgentStore.addMessage('assistant', response.response_text)

      // Set status to speaking
      voiceAgentStore.setStatus(false, false, true)

      // Play response via TTS in selected language
      try {
        await speak(response.response_text, selectedLanguage.value)
      } finally {
        // After speaking, go back to listening
        voiceAgentStore.setStatus(true, false, false)
        if (activeConversationAgent) {
          try { conversationRecognition?.start() } catch (_) {}
          isListening.value = true
        }
      }
     } catch (error) {
       console.error('Failed to send to agent:', error)
       let errorMessage = 'Sorry, I couldn\'t process that. Please try again.'
       if (error.message.includes('422')) {
         errorMessage = 'Request format error: check that all required fields (text, agent_uuid, language) are present in the request body.'
       }
       // Play error message in selected language
       try {
         await speak(errorMessage, selectedLanguage.value)
       } finally {
         // After error, go back to listening
         voiceAgentStore.setStatus(true, false, false)
         if (activeConversationAgent) {
           try { conversationRecognition?.start() } catch (_) {}
           isListening.value = true
         }
       }
     }
  }

  function endConversation() {
    const voiceAgentStore = useVoiceAgentStore()
    voiceAgentStore.setStatus(false, false, false)
    stopListening()
    activeConversationAgent = null
    // Restart wake word detection
    const authStore = useAuthStore()
    if (authStore.isLoggedIn) {
      // We would need to refetch agents here, but for simplicity, we'll rely on the WakeWordManager
      // In a real implementation, we might pass the agents or have a way to get them
      // For now, we just restart detection and let WakeWordManager handle it
      startDetection([]) // This is a placeholder, actual agents should be passed
    }
  }

  // Restart recognition with new locale when language changes mid-session
  watch(selectedLanguage, (newLang) => {
    const wakeWasRunning = isDetecting.value
    const convoWasRunning = isListening.value
    if (wakeWasRunning) stopDetection()
    if (convoWasRunning) stopListening()
    if (recognition) {
      recognition.lang = getSttLocale()
    }
    if (conversationRecognition) {
      conversationRecognition.lang = getSttLocale()
    }
    if (wakeWasRunning) startDetection([])
    if (convoWasRunning && activeConversationAgent) {
      startConversationLoop(activeConversationAgent)
    }
  })

  // Cleanup on unmount
  onUnmounted(() => {
    stopDetection()
    stopListening()
    if (recognition) {
      recognition.stop()
    }
    // Cancel any ongoing speech
    speechSynthesis.cancel()
  })

  return { isDetecting, isListening, detectedWakeWord, startDetection, stopDetection, startListening, stopListening }
}
