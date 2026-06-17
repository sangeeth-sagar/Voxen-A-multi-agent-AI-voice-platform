<template>
  <div class="voice-view-container h-full flex flex-col bg-neural-gradient overflow-hidden">
    <!-- Top Action Bar -->
    <header class="flex justify-between items-center px-6 h-16 shrink-0 border-b border-outline-variant/30 bg-surface/40 relative z-30">
      <div class="agent-switcher">
        <label class="switcher-label">Active Agent</label>
        <select v-model="activeAgentUuid" @change="reconnectWebSocket" class="agent-select">
          <option :value="null" disabled>— Select an agent —</option>
          <option v-for="agent in userAgents" :key="agent.uuid" :value="agent.uuid">{{ agent.name }}</option>
        </select>
        <span class="ws-status" :class="wsStatus">
          <span class="ws-dot" />
          {{ wsStatus === 'connected' ? 'Live' : wsStatus === 'connecting' ? 'Connecting…' : 'Offline' }}
        </span>
      </div>

      <div class="flex items-center gap-3">
        <LanguageSelector @change="onLanguageChange" />
        <button @click="newSession" class="btn-micro">
          New Session
        </button>
      </div>
    </header>

    <!-- Error/Setup banners -->
    <div class="banner-area relative z-30 px-6 pt-3 shrink-0">
      <transition name="fade">
        <div v-if="agentError" class="error-banner mb-2">
          <span class="material-symbols-outlined">warning</span>
          <span class="error-text">{{ agentError }}</span>
          <button class="error-dismiss" @click="agentError = ''" title="Dismiss">✕</button>
        </div>
      </transition>
      <transition name="fade">
        <div v-if="showKeySetupBanner" class="setup-banner mb-2">
          <span class="material-symbols-outlined">key_off</span>
          <div class="setup-banner-text">
            <strong>No API key attached to this agent.</strong>
            <span> Go to Voice Lab (Agents) → Edit Agent → select key, then save.</span>
          </div>
          <div class="setup-banner-actions">
            <RouterLink to="/agents" class="setup-btn">Fix in Voice Lab →</RouterLink>
            <RouterLink to="/profile" class="setup-btn-secondary">Add Key in Settings</RouterLink>
          </div>
          <button @click="showKeySetupBanner = false" class="error-dismiss" title="Dismiss">✕</button>
        </div>
      </transition>
    </div>

    <!-- Main Centered Content -->
    <div class="flex-1 flex flex-col items-center justify-center p-6 overflow-y-auto min-h-0 relative z-10">
      <!-- Background floating particle field inside lab -->
      <div class="absolute inset-0 overflow-hidden pointer-events-none z-0">
        <div v-for="p in particles" :key="p.id" class="particle"
          :style="{ left: p.x + '%', top: p.y + '%', width: p.size + 'px', height: p.size + 'px', animationDuration: p.dur + 's', animationDelay: p.delay + 's' }" />
      </div>

      <!-- Center Column: Neural Core Orb & Visualizer -->
      <div class="w-full max-w-2xl flex flex-col items-center justify-center z-10 relative space-y-8">
        <div class="text-center pt-2">
          <h2 class="font-sans text-lg font-extrabold text-on-surface uppercase tracking-widest">NEURAL CORE ACTIVE</h2>
          <p class="text-[11px] text-on-surface-variant max-w-sm mx-auto leading-relaxed mt-1">
            Synthesizing complex data streams into coherent actionable intelligence across all distributed nodes.
          </p>
        </div>

        <!-- 3D Glowing Green Neural Core Orb -->
        <div class="orb-container relative my-2 flex items-center justify-center h-48 w-48 shrink-0">
          <!-- Outer Pulsing Energy Rings -->
          <div class="absolute w-72 h-72 rounded-full border border-primary/10 animate-[pulse_8s_ease-in-out_infinite]" />
          <div class="absolute w-60 h-60 rounded-full border border-primary/20 animate-[pulse_5s_ease-in-out_infinite]" />
          <div class="absolute w-52 h-52 rounded-full bg-primary/10 blur-3xl animate-pulse" />

          <template v-if="isListening">
            <div class="absolute w-52 h-52 rounded-full border border-primary/40 pulse-ring" />
            <div class="absolute w-52 h-52 rounded-full border border-primary/25 pulse-ring" style="animation-delay:0.75s" />
          </template>

          <!-- The Core Sphere Sphere -->
          <div 
            @click="toggleOrb"
            :class="[
              'relative neural-core-orb w-44 h-44 rounded-full flex flex-col items-center justify-center cursor-pointer z-10 transition-all duration-500',
              isListening ? 'scale-105 shadow-[0_0_50px_rgba(165,209,170,0.6)]' : 'hover:scale-103'
            ]"
          >
            <!-- Core Sphere Inner Gradient Light Overlay -->
            <div class="absolute inset-0 rounded-full bg-radial-sphere-gradient opacity-90"></div>
            <div class="absolute inset-2 rounded-full bg-radial-sphere-light opacity-50 blur-[2px]"></div>

            <span class="material-symbols-outlined text-white text-5xl icon-filled relative z-20">
              {{ isListening ? 'mic' : isSpeaking ? 'volume_up' : 'waves' }}
            </span>
            <span class="font-mono text-[9px] text-white/70 uppercase tracking-widest mt-2 relative z-20">
              {{ isListening ? 'Listening…' : isSpeaking ? 'Speaking…' : wsStatus === 'connected' ? 'TAP TO SPEAK' : 'CONNECTING…' }}
            </span>
          </div>
        </div>

        <!-- Dynamic Visualizer Audio Wave & Info -->
        <div class="w-full space-y-4 flex flex-col items-center">
          <div class="flex items-end gap-1 h-10">
            <div v-for="(h, i) in waveHeights" :key="i"
              class="w-1 rounded-full bg-primary transition-all duration-150"
              :style="{ height: h + 'px', opacity: isListening || isSpeaking ? '0.8' : '0.2' }" />
          </div>

          <div class="flex items-center gap-2 px-4 py-1.5 rounded-full bg-surface-container-high/80 border border-outline-variant/60 backdrop-blur-md">
            <span class="w-2 h-2 rounded-full"
              :class="isListening ? 'bg-error animate-pulse' : isSpeaking ? 'bg-secondary animate-pulse' : 'bg-primary/50'" />
            <span class="font-mono text-[11px] text-on-surface-variant">
              {{ isListening ? 'Recording voice input' : isSpeaking ? 'Agent is responding' : wsStatus === 'connected' ? 'Click core to begin session' : 'Reconnecting…' }}
            </span>
          </div>

          <!-- Conversation Transcript Block -->
          <div class="w-full max-w-md bg-surface-container/60 border border-outline-variant/40 rounded-2xl p-4 max-h-36 overflow-y-auto font-mono text-[11px] leading-relaxed">
            <div v-if="transcript.length === 0 && !isStreaming && !isThinking" class="text-on-surface-variant/40 italic text-center py-4">
              Awaiting neural input…
            </div>
            <div v-else class="space-y-2">
              <p v-for="(msg, i) in transcript" :key="i">
                <span :class="['font-bold mr-2', msg.role === 'user' ? 'text-primary' : 'text-secondary']">
                  {{ msg.role === 'user' ? 'YOU:' : 'AGENT:' }}
                </span>
                <span :class="msg.role === 'user' ? 'text-on-surface-variant' : 'text-on-surface'">{{ msg.text }}</span>
              </p>
              <p v-if="interimText" class="text-on-surface-variant/50 italic">{{ interimText }}</p>
            </div>
          </div>

          <!-- Streaming Live Typing Response Drawer -->
          <div class="w-full max-w-md" v-if="isStreaming || isThinking">
            <div class="bg-primary/10 border border-primary/20 rounded-xl p-3 flex items-start gap-2">
              <span class="material-symbols-outlined text-primary text-base icon-filled mt-0.5 animate-pulse">auto_awesome</span>
              <div class="flex-1 font-mono text-[11px] leading-relaxed text-on-surface whitespace-pre-wrap break-words">
                <span v-if="isThinking" class="thinking-indicator">
                  <span class="thinking-dot"></span><span class="thinking-dot"></span><span class="thinking-dot"></span>
                </span>
                <span v-show="!isThinking" ref="streamingEl"></span>
                <span v-show="!isThinking && isStreaming" class="cursor-blink">|</span>
              </div>
            </div>
          </div>

          <!-- Session Controls -->
          <div class="flex items-center justify-center gap-3 mt-1 pb-2">
            <button @click="clearTranscript" class="btn-micro">
              Clear History
            </button>
            <button v-if="isSpeaking || isStreaming" @click="interruptAgent"
              class="px-3 py-1 bg-error/15 hover:bg-error/25 border border-error/30 rounded-lg font-mono text-[10px] text-error transition-colors flex items-center gap-1">
              <span class="material-symbols-outlined text-sm">stop_circle</span>
              Interrupt
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { apiFetch } from '@/composables/useApi'
import { useLanguage } from '@/composables/useLanguage'
import { useToastStore } from '@/stores/toast'
import LanguageSelector from '@/components/LanguageSelector.vue'

const { selectedLanguage, getSttLocale, getCurrentLanguage, detectVoiceStatus } = useLanguage()
const toast = useToastStore()

// State
const activeAgentUuid = ref(localStorage.getItem('active_agent') || null)
const userAgents = ref([])
const wsStatus = ref('disconnected')
const isStreaming = ref(false)
const agentError = ref('')
const showKeySetupBanner = ref(false)
const isThinking = ref(false)
const intentionalClose = ref(false)

const isListening = ref(false)
const isSpeaking = ref(false)
const transcript = ref([])
const interimText = ref('')

const reconnectAttempts = ref(0)
const MAX_RECONNECT = 5

const ws = ref(null)
const streamingEl = ref(null)
let streamingBuffer = ''
const audioQueue = []
let isPlayingAudio = false
const audioChunkBuffer = {}

let currentAudio = null
let currentAudioUrl = null
let resolveCurrentAudio = null
let recognition = null
let reconnectTimer = null
const pingInterval = ref(null)

const particles = Array.from({ length: 24 }, (_, i) => ({
  id: i, x: Math.random() * 100, y: Math.random() * 100,
  size: Math.random() * 2 + 1, dur: Math.random() * 6 + 4, delay: Math.random() * 4,
}))

const waveHeights = ref(Array(24).fill(8))
let waveInterval = null

function appendTerminalLog(log) {
  const timestamp = new Date().toLocaleTimeString('en-US', { hour12: false })
  console.log(`[${timestamp}] ${log}`)
}

function animateWave() {
  waveInterval = setInterval(() => {
    if (!isListening.value && !isSpeaking.value) {
      waveHeights.value = waveHeights.value.map((_, i) => 4 + Math.sin(Date.now() / 400 + i) * 3)
    } else {
      waveHeights.value = waveHeights.value.map(() => Math.random() * 30 + 4)
    }
  }, 100)
}

function connectWebSocket() {
  if (!activeAgentUuid.value || activeAgentUuid.value === 'default' || activeAgentUuid.value === 'null' || activeAgentUuid.value === 'undefined') {
    agentError.value = 'No agent selected. Please create an agent first.'
    return
  }
  const token = localStorage.getItem('token')
  if (!token) return

  const wsBase = import.meta.env.VITE_WS_URL || 'ws://localhost:8000'
  wsStatus.value = 'connecting'; agentError.value = ''
  appendTerminalLog(`>> WS_GATEWAY: Connecting to neural endpoint...`)

  const socket = new WebSocket(`${wsBase}/ws/voice/${activeAgentUuid.value}?token=${token}`)
  ws.value = socket

  let tokenCount = 0

  socket.onopen = () => {
    wsStatus.value = 'connected'; reconnectAttempts.value = 0; agentError.value = ''
    appendTerminalLog(`>> WS_GATEWAY: Handshake completed. Connection live.`)
    clearInterval(pingInterval.value)
    pingInterval.value = setInterval(() => {
      if (socket.readyState === WebSocket.OPEN) {
        try { socket.send(JSON.stringify({ type: 'ping' })) } catch (_) {}
      }
    }, 30000)
  }

  socket.onclose = (event) => {
    wsStatus.value = 'disconnected'; clearInterval(pingInterval.value); pingInterval.value = null
    appendTerminalLog(`>> WS_GATEWAY: Connection closed. Code: ${event.code}`)
    if (event.code === 4005) { agentError.value = 'No API key attached to this agent.'; wsStatus.value = 'failed'; showKeySetupBanner.value = true; return }
    if (event.code === 4004) { agentError.value = 'Agent not found.'; wsStatus.value = 'failed'; return }
    if (!intentionalClose.value && reconnectAttempts.value < MAX_RECONNECT) {
      reconnectAttempts.value++
      reconnectTimer = setTimeout(connectWebSocket, 3000)
    } else if (reconnectAttempts.value >= MAX_RECONNECT) {
      wsStatus.value = 'failed'
      agentError.value = 'Cannot connect. Check that API keys are attached in Settings → API Keys.'
    }
  }

  socket.onerror = () => { 
    wsStatus.value = 'error'
    appendTerminalLog(`>> WS_GATEWAY: Connection encountered a network socket error.`)
  }

  socket.onmessage = (event) => {
    let msg
    try { msg = JSON.parse(event.data) } catch { return }

    switch (msg.type) {
      case 'ready': 
        wsStatus.value = 'connected'; agentError.value = ''; 
        appendTerminalLog(`>> WS_GATEWAY: Core operational state reported ready.`); 
        break
      case 'agent_thinking':
        isThinking.value = true; isStreaming.value = false; streamingBuffer = ''
        appendTerminalLog(`>> NEURAL_CORE: Synthesizing response context...`)
        if (streamingEl.value) streamingEl.value.textContent = ''
        agentError.value = ''; break
      case 'agent_token':
        tokenCount++
        isThinking.value = false; isStreaming.value = true; streamingBuffer += msg.token || ''
        if (streamingEl.value) streamingEl.value.textContent = streamingBuffer
        break
      case 'agent_response_complete': case 'agent_done':
        appendTerminalLog(`>> NEURAL_CORE: Output stream synthesis complete. [Tokens: ${tokenCount}]`)
        tokenCount = 0
        isStreaming.value = false; isThinking.value = false
        if (streamingBuffer) { transcript.value.push({ role: 'agent', text: streamingBuffer }); streamingBuffer = ''; if (streamingEl.value) streamingEl.value.textContent = '' }
        break
      case 'tts_start': 
        Object.keys(audioChunkBuffer).forEach(k => delete audioChunkBuffer[k]); 
        appendTerminalLog(`>> TTS_ENGINE: Audio streaming started...`)
        break
      case 'tts_chunk':
        audioChunkBuffer[msg.index] = msg.audio
        if (msg.is_last) {
          const keys = Object.keys(audioChunkBuffer).sort((a, b) => a - b)
          const fullB64 = keys.map(k => audioChunkBuffer[k]).join('')
          Object.keys(audioChunkBuffer).forEach(k => delete audioChunkBuffer[k])
          if (fullB64.length < 3 * 1024 * 1024) { audioQueue.push(fullB64); if (!isPlayingAudio) playNextAudio() }
          else { console.warn('Assembled TTS audio too large:', fullB64.length); fallbackBrowserTTS(streamingBuffer) }
        }
        break
      case 'tts_audio':
        if (!msg.audio || msg.audio.length > 3 * 1024 * 1024) { fallbackBrowserTTS(streamingBuffer); break }
        audioQueue.push(msg.audio); if (!isPlayingAudio) playNextAudio()
        break
      case 'tts_browser': fallbackBrowserTTS(msg.text?.length > 500 ? msg.text.slice(0, 500) + '…' : msg.text); break
      case 'interrupted':
        audioQueue.length = 0; Object.keys(audioChunkBuffer).forEach(k => delete audioChunkBuffer[k])
        isPlayingAudio = false; window.speechSynthesis?.cancel()
        if (currentAudio) { try { currentAudio.pause() } catch (_) {} currentAudio = null }
        if (currentAudioUrl) { try { URL.revokeObjectURL(currentAudioUrl) } catch (_) {} currentAudioUrl = null }
        if (resolveCurrentAudio) { resolveCurrentAudio(); resolveCurrentAudio = null }
        isSpeaking.value = false;
        appendTerminalLog(`>> DECODER: Speech interrupted by user input.`)
        break
      case 'llm_error': case 'error':
        agentError.value = msg.message || 'Voice error'; isThinking.value = false; isStreaming.value = false; 
        appendTerminalLog(`>> ERROR: Core engine reported error: ${msg.message}`); 
        break
    }
  }
}

function reconnectWebSocket() {
  intentionalClose.value = true; reconnectAttempts.value = 0; showKeySetupBanner.value = false
  clearInterval(pingInterval.value); pingInterval.value = null
  if (reconnectTimer) { clearTimeout(reconnectTimer); reconnectTimer = null }
  if (ws.value) { try { ws.value.close() } catch (_) {} ws.value = null }
  wsStatus.value = 'disconnected'; streamingBuffer = ''
  if (streamingEl.value) streamingEl.value.textContent = ''
  isStreaming.value = false; isThinking.value = false
  audioQueue.length = 0; Object.keys(audioChunkBuffer).forEach(k => delete audioChunkBuffer[k])
  isPlayingAudio = false; isSpeaking.value = false
  if (currentAudio) { try { currentAudio.pause() } catch (_) {} currentAudio = null }
  if (currentAudioUrl) { try { URL.revokeObjectURL(currentAudioUrl) } catch (_) {} currentAudioUrl = null }
  if (resolveCurrentAudio) { resolveCurrentAudio(); resolveCurrentAudio = null }
  if (activeAgentUuid.value && activeAgentUuid.value !== 'default') localStorage.setItem('active_agent', activeAgentUuid.value)
  setTimeout(() => { intentionalClose.value = false; connectWebSocket() }, 500)
}

function fallbackBrowserTTS(text) {
  if (!text?.trim()) return
  try { window.speechSynthesis.cancel() } catch (_) {}
  const LOCALE_MAP = { en: 'en-US', hi: 'hi-IN', mr: 'hi-IN', ml: 'hi-IN' }
  const lang = LOCALE_MAP[selectedLanguage.value] || 'en-US'
  const chunks = chunkText(text, 180)
  isSpeaking.value = true
  let index = 0

  function speakNext() {
    if (index >= chunks.length) { isSpeaking.value = false; return }
    const chunk = chunks[index++]
    const utter = new SpeechSynthesisUtterance(chunk)
    utter.lang = lang; utter.rate = 0.9; utter.pitch = 1; utter.volume = 1
    const voices = window.speechSynthesis.getVoices()
    const voice = voices.find(v => v.lang === lang) || voices.find(v => v.lang.startsWith(lang.split('-')[0])) || voices.find(v => v.lang.startsWith('en'))
    if (voice) utter.voice = voice
    utter.onend = () => speakNext()
    utter.onerror = (e) => { speakNext() }
    const timer = setInterval(() => { if (window.speechSynthesis.paused) window.speechSynthesis.resume() }, 250)
    utter.onend = () => { clearInterval(timer); speakNext() }
    utter.onerror = (e) => { clearInterval(timer); speakNext() }
    try { window.speechSynthesis.speak(utter) } catch (e) { clearInterval(timer); speakNext() }
  }

  setTimeout(speakNext, 50)
}

function chunkText(text, maxLen) {
  if (text.length <= maxLen) return [text]
  const chunks = []
  const sentences = text.match(/[^.!?।\n]+[.!?।\n]*/g) || [text]
  let current = ''
  for (const s of sentences) {
    if ((current + s).length > maxLen && current.length > 0) { chunks.push(current.trim()); current = s }
    else { current += s }
  }
  if (current.trim()) chunks.push(current.trim())
  return chunks.filter(c => c.length > 0)
}

async function playNextAudio() {
  if (isPlayingAudio) return
  isPlayingAudio = true; isSpeaking.value = true
  while (audioQueue.length > 0) {
    const b64 = audioQueue.shift()
    if (!b64) continue
    let url = null
    try {
      const binary = atob(b64); const bytes = new Uint8Array(binary.length)
      for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i)
      const blob = new Blob([bytes], { type: 'audio/mpeg' })
      url = URL.createObjectURL(blob); currentAudioUrl = url
      await new Promise((resolve) => {
        resolveCurrentAudio = resolve
        const audio = new Audio(url); currentAudio = audio
        audio.onended = () => { if (url) try { URL.revokeObjectURL(url) } catch (_) {} if (currentAudioUrl === url) currentAudioUrl = null; currentAudio = null; resolveCurrentAudio = null; resolve() }
        audio.onerror = () => { if (url) try { URL.revokeObjectURL(url) } catch (_) {} if (currentAudioUrl === url) currentAudioUrl = null; currentAudio = null; resolveCurrentAudio = null; resolve() }
        audio.play().catch(() => { if (url) try { URL.revokeObjectURL(url) } catch (_) {} if (currentAudioUrl === url) currentAudioUrl = null; currentAudio = null; resolveCurrentAudio = null; resolve() })
      })
    } catch (err) {
      if (url) try { URL.revokeObjectURL(url) } catch (_) {}
      if (currentAudioUrl === url) currentAudioUrl = null; currentAudio = null; resolveCurrentAudio = null
      await new Promise(r => setTimeout(r, 0))
    }
  }
  isPlayingAudio = false; isSpeaking.value = false
}

function sendToAgent(transcript_text) {
  if (ws.value && ws.value.readyState === WebSocket.OPEN) {
    streamingBuffer = ''; if (streamingEl.value) streamingEl.value.textContent = ''
    isThinking.value = true
    ws.value.send(JSON.stringify({ type: 'user_text', text: transcript_text, language: selectedLanguage.value }))
    appendTerminalLog(`>> TRANSLATOR: Request routed to agent core. Payload size: ${transcript_text.length} chars.`)
  } else { toast.show('Not connected. Reconnecting…', 'error'); connectWebSocket() }
}

function interruptAgent() {
  audioQueue.length = 0; Object.keys(audioChunkBuffer).forEach(k => delete audioChunkBuffer[k])
  isPlayingAudio = false; isSpeaking.value = false; isStreaming.value = false; isThinking.value = false
  streamingBuffer = ''; if (streamingEl.value) streamingEl.value.textContent = ''
  if (currentAudio) { try { currentAudio.pause() } catch (_) {} currentAudio = null }
  if (currentAudioUrl) { try { URL.revokeObjectURL(currentAudioUrl) } catch (_) {} currentAudioUrl = null }
  if (resolveCurrentAudio) { resolveCurrentAudio(); resolveCurrentAudio = null }
  if (ws.value && ws.value.readyState === WebSocket.OPEN) ws.value.send(JSON.stringify({ type: 'interrupt' }))
}

function startListening() {
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition
  if (!SR) { toast.show('Speech recognition not supported in this browser.', 'error'); return }
  recognition = new SR()
  const sttLocale = getSttLocale()
  const CHROME_UNSUPPORTED = ['ml-IN', 'mr-IN']
  recognition.lang = CHROME_UNSUPPORTED.includes(sttLocale) ? 'en-IN' : sttLocale
  
  recognition.interimResults = true; recognition.continuous = false
  recognition.onresult = (e) => {
    let interim = '', final = ''
    for (const r of e.results) { if (r.isFinal) final += r[0].transcript; else interim += r[0].transcript }
    interimText.value = interim
    if (final) { 
      interimText.value = ''; 
      transcript.value.push({ role: 'user', text: final }); 
      sendToAgent(final) 
      appendTerminalLog(`>> DECODER: Decoding user vocal waves... Result: "${final}"`)
    }
  }
  recognition.onend = () => { isListening.value = false }
  recognition.onerror = (e) => {
    isListening.value = false
    if (e.error === 'language-not-supported') { recognition.lang = 'en-US'; try { recognition.start(); isListening.value = true } catch (_) {} }
    else if (e.error === 'not-allowed') { agentError.value = 'Microphone access denied. Please allow microphone.' }
  }
  try { 
    recognition.start(); 
    isListening.value = true 
    appendTerminalLog(`>> AUDIO_INPUT: Audio record channel initialized. Recording vocal waves...`)
  } catch (e) { 
    isListening.value = false; 
    console.error('[STT] start failed:', e) 
  }
}

function stopListening() { 
  try { recognition?.stop() } catch (_) {} 
  isListening.value = false 
  appendTerminalLog(`>> AUDIO_INPUT: Audio channel closed.`)
}

function toggleOrb() {
  if (isListening.value) { stopListening() }
  else { if (isSpeaking.value || isStreaming.value) { interruptAgent() }; startListening() }
}

function onLanguageChange() { if (isListening.value) { stopListening(); setTimeout(startListening, 50) } }

function clearTranscript() {
  transcript.value = []; interimText.value = ''; streamingBuffer = ''
  if (streamingEl.value) streamingEl.value.textContent = ''
  isThinking.value = false; isStreaming.value = false
}

function newSession() {
  if (transcript.value.length === 0 && !streamingBuffer) return
  if (confirm('Start a new session? Current transcript will be cleared.')) clearTranscript()
}

async function checkSTTSupport() {
  const locale = getSttLocale()
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition
  if (!SR) return
  const test = new SR()
  test.lang = locale; test.continuous = false; test.interimResults = false
  await new Promise((resolve) => {
    test.onerror = (e) => { if (e.error === 'language-not-supported') agentError.value = `⚠️ Speech recognition for ${getCurrentLanguage().label} may not be available on this device.`; resolve() }
    test.onstart = () => { test.abort(); resolve() }
    test.onend = resolve
    try { test.start() } catch { resolve() }
    setTimeout(resolve, 2000)
  })
}

let speakingCheckTimer = null

function startSpeakingWatchdog() {
  clearInterval(speakingCheckTimer)
  speakingCheckTimer = setInterval(() => {
    if (isSpeaking.value && !window.speechSynthesis.speaking && !window.speechSynthesis.pending) isSpeaking.value = false
  }, 1000)
}

function handleStorageEvent(e) { if (e.key === 'agent_updated') { showKeySetupBanner.value = false; reconnectWebSocket() } }

onMounted(async () => {
  if (window.speechSynthesis) { window.speechSynthesis.getVoices(); window.speechSynthesis.onvoiceschanged = () => { window.speechSynthesis.getVoices() } }
  animateWave(); startSpeakingWatchdog()
  try {
    const data = await apiFetch('/api/v1/agents')
    userAgents.value = Array.isArray(data) ? data : (data?.agents || data?.items || [])
    const saved = localStorage.getItem('active_agent')
    const savedExists = userAgents.value.find(a => a.uuid === saved)
    if (savedExists) { activeAgentUuid.value = saved }
    else if (userAgents.value.length > 0) {
      const firstVoice = userAgents.value.find(a => a.is_voice_agent) || userAgents.value[0]
      activeAgentUuid.value = firstVoice.uuid; localStorage.setItem('active_agent', firstVoice.uuid)
    } else { activeAgentUuid.value = null; agentError.value = 'No agents found. Create one in Voice Lab first.'; return }
    connectWebSocket(); await checkSTTSupport()
  } catch (err) { agentError.value = 'Failed to load agents: ' + (err.message || err) }
  detectVoiceStatus()
  if (typeof window !== 'undefined' && 'speechSynthesis' in window) window.speechSynthesis.onvoiceschanged = detectVoiceStatus
  window.addEventListener('storage', handleStorageEvent)
})

onUnmounted(() => {
  intentionalClose.value = true; clearInterval(pingInterval.value); pingInterval.value = null; clearInterval(speakingCheckTimer)
  if (reconnectTimer) { clearTimeout(reconnectTimer); reconnectTimer = null }
  if (ws.value) try { ws.value.close() } catch (_) {}
  if (recognition) try { recognition.stop() } catch (_) {}
  if (currentAudio) { try { currentAudio.pause() } catch (_) {} currentAudio = null }
  if (currentAudioUrl) { try { URL.revokeObjectURL(currentAudioUrl) } catch (_) {} currentAudioUrl = null }
  if (resolveCurrentAudio) { resolveCurrentAudio(); resolveCurrentAudio = null }
  if (waveInterval) clearInterval(waveInterval)
  window.speechSynthesis?.cancel()
  audioQueue.length = 0; Object.keys(audioChunkBuffer).forEach(k => delete audioChunkBuffer[k])
  window.removeEventListener('storage', handleStorageEvent)
})

watch(activeAgentUuid, (v) => { if (v && v !== 'default' && v !== 'null' && v !== 'undefined') localStorage.setItem('active_agent', v) })
</script>

<script>
export default {
  name: 'VoiceView'
}
</script>

<style scoped>
.voice-view-container {
  position: relative;
  height: 100%;
}

.agent-switcher {
  display: flex;
  align-items: center;
  gap: 12px;
  background: var(--color-surface-container);
  border: 1px solid var(--color-outline-variant);
  border-radius: 999px;
  padding: 4px 4px 4px 12px;
}

html.dark .agent-switcher {
  background: rgba(255, 255, 255, 0.04);
  border-color: rgba(255, 255, 255, 0.08);
}

.switcher-label {
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--color-on-surface-variant);
}

.agent-select {
  background: var(--color-surface-container-high);
  border: 1px solid var(--color-outline-variant);
  border-radius: 999px;
  padding: 4px 12px;
  font-size: 12px;
  color: var(--color-on-surface);
  font-family: inherit;
  outline: none;
  cursor: pointer;
  min-width: 150px;
}

html.dark .agent-select {
  background: rgba(0, 0, 0, 0.3);
  border-color: rgba(255, 255, 255, 0.1);
  color: #fff;
}

.ws-status {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 9px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  padding: 4px 10px;
  border-radius: 999px;
  background: var(--color-surface-container-high);
  border: 1px solid var(--color-outline-variant);
}

html.dark .ws-status {
  background: rgba(255, 255, 255, 0.04);
  border-color: rgba(255, 255, 255, 0.06);
}

.ws-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--color-outline);
}

.ws-status.connected {
  color: var(--color-success);
  border-color: var(--color-success);
  background: rgba(14, 108, 74, 0.12);
}

.ws-status.connected .ws-dot {
  background: var(--color-success);
  animation: pulse 2s infinite;
}

.ws-status.connecting {
  color: var(--color-tactical-amber);
  border-color: var(--color-tactical-amber);
  background: rgba(196, 138, 0, 0.12);
}

.ws-status.connecting .ws-dot {
  background: var(--color-tactical-amber);
  animation: pulse 1s infinite;
}

.ws-status.disconnected, .ws-status.error {
  color: var(--color-error);
  border-color: var(--color-error);
  background: var(--color-error-container);
}

.ws-status.disconnected .ws-dot, .ws-status.error .ws-dot {
  background: var(--color-error);
}

/* Micro controls */
.btn-micro {
  background: var(--color-surface-container-high);
  border: 1px solid var(--color-outline-variant);
  color: var(--color-on-surface-variant);
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 10px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-micro:hover {
  background: var(--color-surface-container-highest);
  color: var(--color-on-surface);
}

html.dark .btn-micro {
  background: rgba(255, 255, 255, 0.04);
  border-color: rgba(255, 255, 255, 0.08);
}

html.dark .btn-micro:hover {
  background: rgba(255, 255, 255, 0.08);
}

/* Telemetry tags */
.badge-status-optimal {
  background: rgba(14, 108, 74, 0.12);
  color: var(--color-success);
  font-family: 'JetBrains Mono', monospace;
  font-size: 9px;
  font-weight: 700;
  padding: 1px 6px;
  border-radius: 4px;
}

html.dark .badge-status-optimal {
  background: rgba(165, 209, 170, 0.15);
  color: #a5d1aa;
}

/* Orb elements styling */
.neural-core-orb {
  box-shadow: 0 0 40px rgba(165, 209, 170, 0.35), inset -6px -6px 20px rgba(0, 0, 0, 0.6);
  border: 1px solid rgba(165, 209, 170, 0.25);
  overflow: hidden;
  transition: all 0.4s ease;
}

.bg-radial-sphere-gradient {
  background: radial-gradient(circle at 35% 35%, #9ae2b3 0%, #156c49 55%, #00120b 100%);
}

.bg-radial-sphere-light {
  background: radial-gradient(circle at 20% 20%, rgba(255, 255, 255, 0.6) 0%, transparent 60%);
}

/* Error/Alert design */
.error-banner {
  display: flex;
  align-items: center;
  gap: 10px;
  max-width: 42rem;
  margin-left: auto;
  margin-right: auto;
  background: var(--color-error-container);
  border: 1px solid var(--color-error);
  color: var(--color-on-error-container);
  padding: 10px 14px;
  border-radius: 10px;
  font-size: 12px;
  font-family: 'JetBrains Mono', monospace;
}

.error-banner .material-symbols-outlined {
  font-size: 18px;
  color: var(--color-error);
  flex-shrink: 0;
}

.setup-banner {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
  max-width: 42rem;
  margin-left: auto;
  margin-right: auto;
  background: rgba(196, 138, 0, 0.12);
  border: 1px solid var(--color-tactical-amber);
  color: var(--color-tactical-amber);
  padding: 10px 14px;
  border-radius: 10px;
  font-size: 12px;
  font-family: 'JetBrains Mono', monospace;
}

.setup-banner > .material-symbols-outlined {
  font-size: 18px;
  color: var(--color-tactical-amber);
  flex-shrink: 0;
}

.setup-banner-text {
  flex: 1;
  line-height: 1.5;
  min-width: 200px;
}

.setup-banner-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

.setup-btn {
  padding: 4px 10px;
  background: rgba(196, 138, 0, 0.2);
  border: 1px solid var(--color-tactical-amber);
  border-radius: 6px;
  color: var(--color-tactical-amber);
  font-size: 10px;
  text-decoration: none;
  font-weight: 600;
}

.setup-btn-secondary {
  padding: 4px 10px;
  background: transparent;
  border: 1px solid rgba(196, 138, 0, 0.2);
  border-radius: 6px;
  color: var(--color-tactical-amber);
  opacity: 0.7;
  font-size: 10px;
  text-decoration: none;
}

.error-dismiss {
  margin-left: auto;
  background: none;
  border: none;
  color: var(--color-error);
  cursor: pointer;
  font-size: 12px;
  padding: 0 4px;
  opacity: 0.7;
  transition: opacity 0.15s ease;
}

.error-dismiss:hover {
  opacity: 1;
}

.fade-enter-active, .fade-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.fade-enter-from, .fade-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}

.thinking-indicator {
  display: inline-flex;
  gap: 4px;
  align-items: center;
  padding: 4px 0;
}

.thinking-dot {
  width: 5px;
  height: 5px;
  background: var(--color-tactical-amber);
  border-radius: 50%;
  animation: thinking-bounce 1.2s infinite;
}

.thinking-dot:nth-child(2) {
  animation-delay: 0.2s;
}

.thinking-dot:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes thinking-bounce {
  0%, 80%, 100% { transform: scale(0.8); opacity: 0.5; }
  40% { transform: scale(1.2); opacity: 1; }
}

.cursor-blink {
  display: inline-block;
  width: 6px;
  height: 12px;
  background: var(--color-primary);
  margin-left: 2px;
  vertical-align: middle;
  animation: blink 0.9s steps(2, end) infinite;
}

@keyframes blink {
  50% { opacity: 0; }
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}
</style>
