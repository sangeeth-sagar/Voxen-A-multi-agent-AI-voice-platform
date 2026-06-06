<template>
  <AppLayout :focus-mode="true">
    <div class="h-full relative flex flex-col bg-neural-gradient overflow-hidden">
      <!-- Particle field -->
      <div class="absolute inset-0 overflow-hidden pointer-events-none" id="particle-field">
        <div
          v-for="p in particles"
          :key="p.id"
          class="particle"
          :style="{
            left: p.x + '%',
            top: p.y + '%',
            width: p.size + 'px',
            height: p.size + 'px',
            animationDuration: p.dur + 's',
            animationDelay: p.delay + 's',
          }"
        />
      </div>

      <!-- Status bar -->
      <header class="flex justify-between items-center px-10 h-20 relative z-30">
        <div class="flex items-center gap-3 px-3 py-1.5 rounded-full bg-primary/10 border border-primary/20 backdrop-blur-md">
          <span class="w-2 h-2 rounded-full bg-primary animate-pulse shadow-[0_0_8px_#c0c1ff]" />
          <span class="font-mono text-[11px] text-primary font-bold uppercase tracking-widest">Neural Link: Stable</span>
        </div>
        <div class="flex items-center gap-6">
          <LanguageSelector @change="onLanguageChange" />
          <div class="flex items-center gap-3 text-on-surface-variant/60">
            <span class="material-symbols-outlined hover:text-primary transition-colors cursor-pointer">settings_input_antenna</span>
            <span class="material-symbols-outlined hover:text-primary transition-colors cursor-pointer">equalizer</span>
          </div>
        </div>
      </header>

      <!-- Agent Selector -->
      <div class="mt-4 px-10 space-x-2 overflow-x-auto">
        <div v-for="agent in activeAgents" :key="agent.uuid" class="shrink-0">
          <button
            :class="[
              'flex items-center gap-2 px-3 py-2 rounded-full',
              agent.uuid === selectedAgent?.uuid ? 'bg-primary/20 text-primary' : 'bg-white/5 text-on-surface-variant hover:bg-white/10 hover:text-white transition-colors'
            ]"
            @click="selectedAgent = agent"
          >
            <span class="w-2 h-2" :class="[
              agent.uuid === selectedAgent?.uuid ? 'bg-primary' : 'bg-gray-400'
            ]" />
            <span class="text-xs font-mono">{{ agent.name }}</span>
            <span class="text-xs text-on-surface-variant/50 ml-1">{{ agent.wake_word }}</span>
          </button>
        </div>
      </div>

      <!-- Current Session Info Bar -->
      <div class="mt-4 px-10 flex items-center justify-between">
        <div class="flex items-center gap-3 text-xs font-mono">
          <span class="text-on-surface-variant">Session:</span>
          <span class="text-primary">{{ currentSessionId }}</span>
        </div>
        <div class="flex items-center gap-3 text-xs font-mono">
          <span class="text-on-surface-variant">Messages:</span>
          <span class="text-primary">{{ messageCount }}</span>
        </div>
        <button
          @click="newSession"
          class="px-3 py-1 bg-white/5 hover:bg-white/10 rounded text-xs font-medium transition-colors"
        >
          New Session
        </button>
      </div>

      <!-- Center orb canvas -->
      <main class="flex-1 flex flex-col items-center justify-center relative z-10">
        <!-- Outer rings -->
        <div class="absolute w-[600px] h-[600px] rounded-full border border-primary/5 animate-[pulse_8s_ease-in-out_infinite]" />
        <div class="absolute w-[500px] h-[500px] rounded-full border border-white/[0.03] animate-[pulse_10s_ease-in-out_infinite]" />

        <!-- Pulse rings when listening -->
        <template v-if="isListening">
          <div class="absolute w-72 h-72 rounded-full border border-primary/30 pulse-ring" />
          <div class="absolute w-72 h-72 rounded-full border border-primary/20 pulse-ring" style="animation-delay:0.75s" />
        </template>

        <!-- Glow blob -->
        <div class="absolute w-64 h-64 rounded-full bg-secondary-container/20 animate-orb-breathe blur-3xl" />

        <!-- Main orb -->
        <div
          @click="toggleListening"
          :class="[
            'relative neural-orb-large w-52 h-52 rounded-full flex flex-col items-center justify-center cursor-pointer z-10 transition-transform duration-500',
            isListening ? 'scale-110' : 'hover:scale-105'
          ]"
        >
          <span class="material-symbols-outlined text-on-primary text-7xl icon-filled">
            {{ isListening ? 'mic' : isSpeaking ? 'volume_up' : 'waves' }}
          </span>
          <span class="font-mono text-[10px] text-on-primary/60 uppercase tracking-widest mt-2">
            {{ isListening ? 'Listening…' : isSpeaking ? 'Speaking…' : 'Tap to speak' }}
          </span>
        </div>

        <!-- Waveform below orb -->
        <div class="mt-12 flex items-end gap-1.5 h-14">
          <div
            v-for="(h, i) in waveHeights"
            :key="i"
            class="w-1.5 rounded-full bg-primary transition-all duration-150"
            :style="{ height: h + 'px', opacity: isListening || isSpeaking ? '0.8' : '0.2' }"
          />
        </div>

        <!-- Status chip -->
        <div class="mt-6 flex items-center gap-2 px-4 py-2 rounded-full bg-white/5 border border-white/10 backdrop-blur-md">
          <span class="w-2 h-2 rounded-full"
            :class="isListening ? 'bg-error animate-pulse' : isSpeaking ? 'bg-secondary animate-pulse' : 'bg-primary/50'" />
          <span class="font-mono text-xs text-on-surface-variant">
            {{ isListening ? 'Recording voice input' : isSpeaking ? 'Agent is responding' : 'Click orb to begin' }}
          </span>
        </div>
      </main>

      <!-- Session History Panel -->
      <SessionHistoryPanel
        :sessions="sessions"
        :loading="loadingSessions"
        @load-session="loadSessionFromHistory"
      />

      <!-- Transcript drawer -->
      <div class="relative z-20 px-10 pb-8">
        <div class="max-w-2xl mx-auto glass-panel rounded-2xl p-5 max-h-40 overflow-y-auto font-mono text-xs leading-relaxed">
          <div v-if="transcript.length === 0" class="text-on-surface-variant/40 italic text-center py-4">
            Awaiting neural input…
          </div>
          <div v-else class="space-y-2">
            <p v-for="(msg, i) in transcript" :key="i">
              <span :class="['font-bold mr-2', msg.role === 'user' ? 'text-primary' : 'text-secondary']">
                {{ msg.role === 'user' ? 'YOU:' : (selectedAgent?.name || 'LUMINA') + ':' }}
              </span>
              <span :class="msg.role === 'user' ? 'text-on-surface-variant' : 'text-white'">{{ msg.text }}</span>
            </p>
            <p v-if="interimText" class="text-on-surface-variant/50 italic">{{ interimText }}</p>
          </div>
        </div>

        <!-- Voice install tip (dismissible banner about installing Marathi/Malayalam voice packs) -->
        <div v-if="showVoiceInstallTip" class="voice-install-tip max-w-2xl mx-auto mt-3">
          <span class="material-symbols-outlined">info</span>
          <span class="tip-text">
            For native Marathi &amp; Malayalam voice:
            <strong>Windows Settings → Time &amp; Language → Language &amp; Region → Add Malayalam/Marathi → Install Speech pack</strong>
          </span>
          <button @click="showVoiceInstallTip = false" aria-label="Dismiss">✕</button>
        </div>

        <!-- TTS warning (shown when no Indic voices are installed) -->
        <div v-if="ttsWarning" class="tts-warning max-w-2xl mx-auto mt-3">
          ⚠️ {{ ttsWarning }}
        </div>

        <!-- Clear button -->
        <div class="flex items-center justify-center gap-4 mt-4">
          <button @click="clearTranscript" class="px-4 py-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-full font-mono text-[11px] text-on-surface-variant transition-colors">
            Clear
          </button>
        </div>
      </div>
    </div>
  </AppLayout>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import AppLayout from '@/components/layout/AppLayout.vue'
import { apiFetch } from '@/composables/useApi'
import { useAuthStore } from '@/stores/auth'
import { useLanguage } from '@/composables/useLanguage'
import { useTTS } from '@/composables/useTTS'
import LanguageSelector from '@/components/LanguageSelector.vue'
import SessionHistoryPanel from '@/components/voice/SessionHistoryPanel.vue'

const { selectedLanguage, getSttLocale, voiceStatus } = useLanguage()
const { speak, stop: stopTTS } = useTTS()

const isListening = ref(false)
const isSpeaking = ref(false)
const transcript = ref([])
const interimText = ref('')
let recognition = null
const synth = window.speechSynthesis

// TTS fallback warning (shown when browser has no Indic voices installed)
const ttsWarning = ref('')

// Dismissible banner: tip for installing Marathi/Malayalam native voice packs.
// Hidden once user closes it; can be re-shown by reloading the page.
const showVoiceInstallTip = ref(true)

// New state for agent selector and session info
const selectedAgent = ref(null)
const currentSessionId = ref('')
const messageCount = ref(0)
const sessions = ref([])
const loadingSessions = ref(false)
const activeAgents = ref([])

// Particle field
const particles = Array.from({ length: 30 }, (_, i) => ({
  id: i, x: Math.random() * 100, y: Math.random() * 100,
  size: Math.random() * 2 + 1, dur: Math.random() * 6 + 4, delay: Math.random() * 4,
}))

// Dynamic waveform
const waveHeights = ref(Array(18).fill(8))
let waveInterval = null

// Fetch active agents for selector
async function fetchActiveAgents() {
  try {
    const data = await apiFetch('/api/v1/agents')
    activeAgents.value = data.filter(agent => agent.is_active === true)
    // Select first agent by default if none selected
    if (!selectedAgent.value && activeAgents.value.length > 0) {
      selectedAgent.value = activeAgents.value[0]
    }
  } catch (error) {
    console.error('Failed to fetch active agents:', error)
  }
}

// Fetch session history
async function fetchSessionHistory() {
  loadingSessions.value = true
  try {
    const data = await apiFetch('/api/v1/voice-agent/sessions')
    sessions.value = data
  } catch (error) {
    console.error('Failed to fetch session history:', error)
  } finally {
    loadingSessions.value = false
  }
}

// Load session from history
function loadSessionFromHistory(session) {
  // Set selected agent if available
  if (session.agent_name) {
    const agent = activeAgents.value.find(a => a.name === session.agent_name)
    if (agent) {
      selectedAgent.value = agent
    }
  }
  
  // Set transcript
  transcript.value = session.messages.map(msg => ({
    role: msg.role,
    text: msg.content
  }))
  
  // Update session info
  currentSessionId.value = session.id || ''
  messageCount.value = session.message_count || 0
}

// Start listening
function startListening() {
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition
  if (!SR) {
    transcript.value.push({ role: 'agent', text: 'Speech recognition not supported.' });
    return
  }
  recognition = new SR()
  recognition.lang = getSttLocale()
  recognition.interimResults = true
  recognition.onresult = (e) => {
    let interim = '', final = ''
    for (const r of e.results) { 
      if (r.isFinal) final += r[0].transcript; 
      else interim += r[0].transcript 
    }
    interimText.value = interim
    if (final) { 
      interimText.value = ''; 
      sendToAgent(final) 
    }
  }
  recognition.onend = () => { 
    isListening.value = false 
    // Auto-restart if still supposed to be listening
    if (isListening.value) {
      startListening()
    }
  }
  recognition.start()
  isListening.value = true
}

// Stop listening
function stopListening() { 
  recognition?.stop(); 
  isListening.value = false 
}

// Send message to agent
async function sendToAgent(text) {
  if (!selectedAgent.value) {
    transcript.value.push({ role: 'agent', text: 'Please select an agent first.' })
    return
  }

   transcript.value.push({ role: 'user', text })
  try {
    // Parameters must be sent as JSON body — backend expects a Pydantic model, NOT query params
    const res = await apiFetch('/api/v1/voice-agent/chat', {
      method: 'POST',
      body: JSON.stringify({
        text,
        agent_uuid: selectedAgent.value.uuid,
        session_id: currentSessionId.value || undefined,
        language: selectedLanguage.value
      }),
    })

    // Update session ID if provided
    if (res.session_id) {
      currentSessionId.value = res.session_id
    }

    transcript.value.push({ role: 'agent', text: res.response_text })
    isSpeaking.value = true
    try {
      await speak(res.response_text, selectedLanguage.value)
    } finally {
      isSpeaking.value = false
      // Auto-restart listening after speaking
      if (isListening.value) {
        startListening()
      }
    }

    // Update message count
    messageCount.value = transcript.value.length
   } catch (error) {
     console.error('Error sending to agent:', error)
     if (error.message.includes('422')) {
       transcript.value.push({ role: 'agent', text: 'Request format error: check that all required fields (text, agent_uuid, language) are present in the request body.' })
     } else {
       transcript.value.push({ role: 'agent', text: 'Connection error.' })
     }
   }
}

// Stop speech when user switches language mid-session
function onLanguageChange() {
  stopTTS()
  // If currently listening, restart with the new STT locale
  if (isListening.value) {
    stopListening()
    startListening()
  }
}

// Toggle listening
function toggleListening() {
  isListening.value ? stopListening() : startListening()
}

// Clear transcript
function clearTranscript() {
  transcript.value = []
  interimText.value = ''
  messageCount.value = 0
}

// Start new session
function newSession() {
  if (transcript.value.length > 0 && !window.confirm('Clear current transcript and start a new session?')) {
    return
  }
  
  transcript.value = []
  interimText.value = ''
  currentSessionId.value = ''
  messageCount.value = 0
}

// Animate waveform
function animateWave() {
  waveInterval = setInterval(() => {
    if (!isListening.value && !isSpeaking.value) {
      waveHeights.value = waveHeights.value.map((_, i) => 4 + Math.sin(Date.now() / 500 + i) * 4)
    } else {
      waveHeights.value = waveHeights.value.map(() => Math.random() * 48 + 4)
    }
  }, 100)
}

// Initialize
onMounted(() => {
  fetchActiveAgents()
  fetchSessionHistory()
  animateWave()

  // Detect whether browser has any Indic TTS voices installed
  // and populate per-language voiceStatus so the LanguageSelector
  // can show the yellow "↩ fallback" badge for missing voices (e.g. mr-IN, ml-IN on Windows).
  const detectIndicVoices = () => {
    const voices = speechSynthesis.getVoices()
    if (!voices || voices.length === 0) return

    const locales = {
      en: 'en-GB',
      hi: 'hi-IN',
      mr: 'mr-IN',
      ml: 'ml-IN'
    }
    const next = { ...voiceStatus.value }
    Object.entries(locales).forEach(([code, locale]) => {
      const hasVoice = voices.some(v =>
        v.lang === locale ||
        v.lang.startsWith(locale.split('-')[0])
      )
      next[code] = hasVoice ? 'native' : 'fallback'
    })
    voiceStatus.value = next

    const hasIndic = voices.some(v =>
      v.lang.startsWith('hi') || v.lang.startsWith('mr') || v.lang.startsWith('ml')
    )
    if (!hasIndic) {
      ttsWarning.value = 'Hindi, Marathi & Malayalam voice playback may require installing language packs in your OS settings.'
    }
  }
  // voices may load asynchronously
  detectIndicVoices()
  if (typeof speechSynthesis !== 'undefined') {
    speechSynthesis.onvoiceschanged = detectIndicVoices
  }
  // Fallback: re-check after a short delay in case onvoiceschanged never fires
  setTimeout(detectIndicVoices, 600)

  // Refresh session history periodically
  setInterval(fetchSessionHistory, 30000) // Every 30 seconds
})

onUnmounted(() => { 
  recognition?.stop(); 
  synth?.cancel(); 
  clearInterval(waveInterval) 
})

// Watch for selected agent changes
watch(selectedAgent, (newAgent) => {
  if (newAgent) {
    // Reset session when agent changes
    currentSessionId.value = ''
    messageCount.value = 0
    // Clear transcript if desired
    // transcript.value = []
  }
})
</script>

<style scoped>
.tts-warning {
  padding: 10px 14px;
  border-radius: 12px;
  background: rgba(196, 166, 113, 0.08);
  border: 1px solid rgba(196, 166, 113, 0.25);
  color: #C4A671;
  font-family: monospace;
  font-size: 11px;
  line-height: 1.4;
  text-align: center;
}

.voice-install-tip {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 10px 14px;
  border-radius: 12px;
  background: rgba(59, 130, 246, 0.08);
  border: 1px solid rgba(59, 130, 246, 0.25);
  color: rgba(255, 255, 255, 0.85);
  font-family: monospace;
  font-size: 11px;
  line-height: 1.4;
}

.voice-install-tip .material-symbols-outlined {
  font-size: 18px;
  color: #60a5fa;
  flex-shrink: 0;
  margin-top: 1px;
}

.voice-install-tip .tip-text {
  flex: 1;
}

.voice-install-tip strong {
  color: #93c5fd;
  font-weight: 600;
}

.voice-install-tip button {
  background: transparent;
  border: none;
  color: rgba(255, 255, 255, 0.5);
  cursor: pointer;
  font-size: 14px;
  padding: 0 6px;
  flex-shrink: 0;
  transition: color 0.15s ease;
}

.voice-install-tip button:hover {
  color: white;
}
</style>
