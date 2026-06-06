import { ref, computed } from 'vue'
import { useWakeWord } from './useWakeWord'

export function useAgentTest() {
  const isTestOpen = ref(false)
  const testAgent = ref(null)
  const testTranscript = ref([])
  const testSessionId = ref(null)
  const testStatus = ref('idle')
  // 'idle' | 'listening_wake' | 'listening' | 'processing' | 'speaking'

  const { startDetection, stopDetection } = useWakeWord()

  function openTest(agent) {
    testAgent.value = agent
    testTranscript.value = []
    testSessionId.value = null
    isTestOpen.value = true
    testStatus.value = 'listening_wake'
    
    // Start wake word detection with [agent] array only
    startDetection([agent])
    
    // Add system message to transcript
    addTestMessage('system', `Say "${agent.wake_word}" to activate`)
  }

  function closeTest() {
    stopDetection()
    // Stop all speechSynthesis
    speechSynthesis.cancel()
    isTestOpen.value = false
    testStatus.value = 'idle'
    testAgent.value = null
    testTranscript.value = []
    testSessionId.value = null
  }

  function addTestMessage(role, content) {
    testTranscript.value.push({
      role,
      content,
      timestamp: Date.now()
    })
  }

  const isActive = computed(() => testStatus.value !== 'idle')

  return { 
    isTestOpen, 
    testAgent, 
    testTranscript, 
    testSessionId, 
    testStatus, 
    isActive,
    openTest, 
    closeTest, 
    addTestMessage 
  }
}