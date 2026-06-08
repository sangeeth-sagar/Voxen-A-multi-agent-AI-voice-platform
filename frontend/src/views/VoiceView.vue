<template>
  <div class="voice-view h-full flex flex-col bg-neural-gradient overflow-hidden">
    <!-- Particle field -->
    <div class="absolute inset-0 overflow-hidden pointer-events-none" id="particle-field">
      <div
        v-for="p in particles" :key="p.id"
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

    <!-- Header bar: agent switcher + ws status + language -->
    <header class="flex justify-between items-center px-8 h-20 relative z-30 gap-4 flex-wrap">
      <div class="agent-switcher">
        <label class="switcher-label">Active Agent</label>
        <select v-model="activeAgentUuid" @change="reconnectWebSocket" class="agent-select">
          <option :value="null" disabled>— Select an agent —</option>
          <option v-for="agent in userAgents" :key="agent.uuid" :value="agent.uuid">
            {{ agent.name }}
          </option>
        </select>
        <span class="ws-status" :class="wsStatus">
          <span class="ws-dot" />
          {{ wsStatus === 'connected' ? 'Live' : wsStatus === 'connecting' ? 'Connecting…' : 'Offline' }}
        </span>
      </div>

      <div class="flex items-center gap-3">
        <LanguageSelector @change="onLanguageChange" />
        <button @click="newSession" class="px-3 py-1.5 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg font-mono text-[11px] text-on-surface-variant transition-colors">
          New Session
        </button>
      </div>
    </header>

    <!-- Agent error banner -->
    <transition name="fade">
      <div v-if="agentError" class="error-banner relative z-30 mx-8 mb-3">
        <span class="material-symbols-outlined">warning</span>
        <span class="error-text">{{ agentError }}</span>
        <button class="error-dismiss" @click="agentError = ''" title="Dismiss">✕</button>
      </div>
    </transition>

    <!-- Setup banner for missing API key (code 4005) -->
    <transition name="fade">
      <div v-if="showKeySetupBanner" class="setup-banner relative z-30 mx-8 mb-3">
        <span class="material-symbols-outlined">key_off</span>
        <div class="setup-banner-text">
          <strong>No API key attached to this agent.</strong>
          <span> Go to Agents → Edit Agent → select your Gemini key, then save.</span>
        </div>
        <div class="setup-banner-actions">
          <RouterLink to="/agents" class="setup-btn">Fix in Agents →</RouterLink>
          <RouterLink to="/profile" class="setup-btn-secondary">Add Key in Profile</RouterLink>
        </div>
        <button @click="showKeySetupBanner = false" class="error-dismiss" title="Dismiss">✕</button>
      </div>
    </transition>

    <!-- Center orb -->
    <main class="flex-1 flex flex-col items-center justify-center relative z-10">
      <div class="absolute w-[600px] h-[600px] rounded-full border border-primary/5 animate-[pulse_8s_ease-in-out_infinite]" />
      <div class="absolute w-[500px] h-[500px] rounded-full border border-white/[0.03] animate-[pulse_10s_ease-in-out_infinite]" />

      <template v-if="isListening">
        <div class="absolute w-72 h-72 rounded-full border border-primary/30 pulse-ring" />
        <div class="absolute w-72 h-72 rounded-full border border-primary/20 pulse-ring" style="animation-delay:0.75s" />
      </template>

      <div class="absolute w-64 h-64 rounded-full bg-secondary-container/20 animate-orb-breathe blur-3xl" />

      <div
        @click="toggleOrb"
        :class="[
          'relative neural-orb-large w-52 h-52 rounded-full flex flex-col items-center justify-center cursor-pointer z-10 transition-transform duration-500',
          isListening ? 'scale-110' : 'hover:scale-105'
        ]"
      >
        <span class="material-symbols-outlined text-on-primary text-7xl icon-filled">
          {{ isListening ? 'mic' : isSpeaking ? 'volume_up' : 'waves' }}
        </span>
        <span class="font-mono text-[10px] text-on-primary/60 uppercase tracking-widest mt-2">
          {{ isListening ? 'Listening…' : isSpeaking ? 'Speaking…' : wsStatus === 'connected' ? 'Tap to speak' : 'Connecting…' }}
        </span>
      </div>

      <!-- Waveform -->
      <div class="mt-12 flex items-end gap-1.5 h-14">
        <div
          v-for="(h, i) in waveHeights" :key="i"
          class="w-1.5 rounded-full bg-primary transition-all duration-150"
          :style="{ height: h + 'px', opacity: isListening || isSpeaking ? '0.8' : '0.2' }"
        />
      </div>

      <!-- Status chip -->
      <div class="mt-6 flex items-center gap-2 px-4 py-2 rounded-full bg-white/5 border border-white/10 backdrop-blur-md">
        <span class="w-2 h-2 rounded-full"
          :class="isListening ? 'bg-error animate-pulse' : isSpeaking ? 'bg-secondary animate-pulse' : 'bg-primary/50'" />
        <span class="font-mono text-xs text-on-surface-variant">
          {{ isListening ? 'Recording voice input' : isSpeaking ? 'Agent is responding' : wsStatus === 'connected' ? 'Click orb to begin' : 'Reconnecting…' }}
        </span>
      </div>
    </main>

    <!-- Streaming response / thinking -->
    <div class="agent-response relative z-20 px-8 pb-2" v-if="isStreaming || isThinking">
      <div class="max-w-2xl mx-auto glass-panel rounded-2xl px-5 py-3">
        <div class="flex items-start gap-2">
          <span class="material-symbols-outlined text-primary text-[18px] icon-filled mt-0.5">auto_awesome</span>
          <div class="flex-1 font-mono text-sm leading-relaxed text-white whitespace-pre-wrap break-words">
            <span v-if="isThinking" class="thinking-indicator">
              <span class="thinking-dot"></span>
              <span class="thinking-dot"></span>
              <span class="thinking-dot"></span>
            </span>
            <span v-show="!isThinking" ref="streamingEl"></span>
            <span v-show="!isThinking && isStreaming" class="cursor-blink">|</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Transcript drawer -->
    <div class="relative z-20 px-8 pb-8">
      <div class="max-w-2xl mx-auto glass-panel rounded-2xl p-5 max-h-40 overflow-y-auto font-mono text-xs leading-relaxed">
        <div v-if="transcript.length === 0 && !isStreaming && !isThinking" class="text-on-surface-variant/40 italic text-center py-4">
          Awaiting neural input…
        </div>
        <div v-else class="space-y-2">
          <p v-for="(msg, i) in transcript" :key="i">
            <span :class="['font-bold mr-2', msg.role === 'user' ? 'text-primary' : 'text-secondary']">
              {{ msg.role === 'user' ? 'YOU:' : 'AGENT:' }}
            </span>
            <span :class="msg.role === 'user' ? 'text-on-surface-variant' : 'text-white'">{{ msg.text }}</span>
          </p>
          <p v-if="interimText" class="text-on-surface-variant/50 italic">{{ interimText }}</p>
        </div>
      </div>

      <div class="flex items-center justify-center gap-4 mt-4">
        <button @click="clearTranscript" class="px-4 py-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-full font-mono text-[11px] text-on-surface-variant transition-colors">
          Clear
        </button>
        <button v-if="isSpeaking || isStreaming" @click="interruptAgent"
          class="px-4 py-2 bg-error/15 hover:bg-error/25 border border-error/30 rounded-full font-mono text-[11px] text-error transition-colors flex items-center gap-1">
          <span class="material-symbols-outlined text-[14px]">stop_circle</span>
          Interrupt
        </button>
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

// ── Refs ──────────────────────────────────────────────
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

// Plain JavaScript state (bypasses Vue reactivity to prevent Chrome crashes)
const ws = ref(null)
const streamingEl = ref(null)        // DOM ref — not reactive string
let streamingBuffer = ''             // plain string — not ref
const audioQueue = []                // plain array — NOT ref
let isPlayingAudio = false           // plain bool — NOT ref
const audioChunkBuffer = {}          // indexed chunk buffer

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

const waveHeights = ref(Array(18).fill(8))
let waveInterval = null

function animateWave() {
  waveInterval = setInterval(() => {
    if (!isListening.value && !isSpeaking.value) {
      waveHeights.value = waveHeights.value.map((_, i) => 4 + Math.sin(Date.now() / 500 + i) * 4)
    } else {
      waveHeights.value = waveHeights.value.map(() => Math.random() * 48 + 4)
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
  wsStatus.value = 'connecting'
  agentError.value = ''

  const socket = new WebSocket(
    `${wsBase}/ws/voice/${activeAgentUuid.value}?token=${token}`
  )
  ws.value = socket

  let tokenCount = 0

  socket.onopen = () => {
    wsStatus.value = 'connected'
    reconnectAttempts.value = 0
    agentError.value = ''
    clearInterval(pingInterval.value)
    pingInterval.value = setInterval(() => {
      if (socket.readyState === WebSocket.OPEN) {
        try { socket.send(JSON.stringify({ type: 'ping' })) } catch (_) {}
      }
    }, 30000)
  }

  socket.onclose = (event) => {
    wsStatus.value = 'disconnected'
    clearInterval(pingInterval.value)
    pingInterval.value = null

    if (event.code === 4005) {
      agentError.value = 'No API key attached to this agent.'
      wsStatus.value = 'failed'
      showKeySetupBanner.value = true
      return
    }

    if (event.code === 4004) {
      agentError.value = 'Agent not found.'
      wsStatus.value = 'failed'
      return
    }

    if (!intentionalClose.value && reconnectAttempts.value < MAX_RECONNECT) {
      reconnectAttempts.value++
      reconnectTimer = setTimeout(connectWebSocket, 3000)
    } else if (reconnectAttempts.value >= MAX_RECONNECT) {
      wsStatus.value = 'failed'
      agentError.value = 'Cannot connect. Check that API keys are attached in Agents → Edit Agent.'
    }
  }

  socket.onerror = () => {
    wsStatus.value = 'error'
  }

  socket.onmessage = (event) => {
    let msg
    try { msg = JSON.parse(event.data) } catch { return }

    switch (msg.type) {
      case 'ready':
        wsStatus.value = 'connected'
        agentError.value = ''
        break

      case 'agent_thinking':
        isThinking.value = true
        isStreaming.value = false
        streamingBuffer = ''
        if (streamingEl.value) streamingEl.value.textContent = ''
        agentError.value = ''
        break

      case 'agent_token':
        tokenCount++
        if (tokenCount > 2000) {
          console.error('[FLOOD] Over 2000 tokens received — possible infinite stream loop')
          if (socket.readyState === WebSocket.OPEN) {
            socket.send(JSON.stringify({ type: 'interrupt' }))
          }
          break
        }
        isThinking.value = false
        isStreaming.value = true
        streamingBuffer += msg.token || ''
        if (streamingEl.value) {
          streamingEl.value.textContent = streamingBuffer
        }
        break

      case 'agent_response_complete':
      case 'agent_done':
        console.log('[STREAM] Total tokens received:', tokenCount)
        tokenCount = 0
        isStreaming.value = false
        isThinking.value = false
        if (streamingBuffer) {
          transcript.value.push({ role: 'agent', text: streamingBuffer })
          streamingBuffer = ''
          if (streamingEl.value) streamingEl.value.textContent = ''
        }
        break

      case 'tts_start':
        Object.keys(audioChunkBuffer).forEach(k => delete audioChunkBuffer[k])
        break

      case 'tts_chunk':
        audioChunkBuffer[msg.index] = msg.audio
        if (msg.is_last) {
          const keys = Object.keys(audioChunkBuffer).sort((a, b) => a - b)
          const fullB64 = keys.map(k => audioChunkBuffer[k]).join('')
          Object.keys(audioChunkBuffer).forEach(k => delete audioChunkBuffer[k])
          if (fullB64.length < 3 * 1024 * 1024) {
            audioQueue.push(fullB64)
            if (!isPlayingAudio) playNextAudio()
          } else {
            console.warn('Assembled TTS audio too large:', fullB64.length)
            fallbackBrowserTTS(streamingBuffer)
          }
        }
        break

      case 'tts_audio':
        if (!msg.audio || msg.audio.length > 3 * 1024 * 1024) {
          console.warn('TTS single audio chunk too large or missing')
          fallbackBrowserTTS(streamingBuffer)
          break
        }
        audioQueue.push(msg.audio)
        if (!isPlayingAudio) playNextAudio()
        break

      case 'tts_browser':
        fallbackBrowserTTS(msg.text)
        break

      case 'tts_end':
        break

      case 'interrupted':
        audioQueue.length = 0
        Object.keys(audioChunkBuffer).forEach(k => delete audioChunkBuffer[k])
        isPlayingAudio = false
        window.speechSynthesis?.cancel()
        if (currentAudio) {
          try { currentAudio.pause() } catch (_) {}
          currentAudio = null
        }
        if (currentAudioUrl) {
          try { URL.revokeObjectURL(currentAudioUrl) } catch (_) {}
          currentAudioUrl = null
        }
        if (resolveCurrentAudio) {
          resolveCurrentAudio()
          resolveCurrentAudio = null
        }
        isSpeaking.value = false
        break

      case 'llm_error':
      case 'error':
        agentError.value = msg.message || 'Voice error'
        isThinking.value = false
        isStreaming.value = false
        break

      case 'pong':
        break

      default:
        break
    }
  }
}

function reconnectWebSocket() {
  intentionalClose.value = true
  reconnectAttempts.value = 0
  showKeySetupBanner.value = false
  clearInterval(pingInterval.value)
  pingInterval.value = null
  if (reconnectTimer) { clearTimeout(reconnectTimer); reconnectTimer = null }
  if (ws.value) { try { ws.value.close() } catch (_) {} ws.value = null }
  wsStatus.value = 'disconnected'
  streamingBuffer = ''
  if (streamingEl.value) streamingEl.value.textContent = ''
  isStreaming.value = false
  isThinking.value = false
  audioQueue.length = 0
  Object.keys(audioChunkBuffer).forEach(k => delete audioChunkBuffer[k])
  isPlayingAudio = false
  isSpeaking.value = false
  if (currentAudio) {
    try { currentAudio.pause() } catch (_) {}
    currentAudio = null
  }
  if (currentAudioUrl) {
    try { URL.revokeObjectURL(currentAudioUrl) } catch (_) {}
    currentAudioUrl = null
  }
  if (resolveCurrentAudio) {
    resolveCurrentAudio()
    resolveCurrentAudio = null
  }
  if (activeAgentUuid.value && activeAgentUuid.value !== 'default') {
    localStorage.setItem('active_agent', activeAgentUuid.value)
  }
  setTimeout(() => {
    intentionalClose.value = false
    connectWebSocket()
  }, 500)
}

async function fallbackBrowserTTS(text) {
  if (!text || !window.speechSynthesis) return

  const MAX_CHARS = 200
  const chunks = splitIntoChunks(text, MAX_CHARS)

  window.speechSynthesis.cancel()

  const LOCALE_MAP = { en: 'en-GB', hi: 'hi-IN', mr: 'mr-IN', ml: 'ml-IN' }
  const locale = LOCALE_MAP[selectedLanguage.value] || 'en-GB'

  const FALLBACK_CHAIN = {
    'en-GB': ['en-GB', 'en-US', 'en-IN', 'en'],
    'hi-IN': ['hi-IN', 'en-IN', 'en-US'],
    'mr-IN': ['mr-IN', 'hi-IN', 'en-IN', 'en-US'],
    'ml-IN': ['ml-IN', 'hi-IN', 'en-IN', 'en-US'],
  }

  let voices = window.speechSynthesis.getVoices()
  if (!voices.length) {
    await new Promise(resolve => {
      window.speechSynthesis.onvoiceschanged = () => {
        voices = window.speechSynthesis.getVoices()
        resolve()
      }
      setTimeout(resolve, 1000)
    })
  }

  const chain = FALLBACK_CHAIN[locale] || [locale, 'en-US']
  let selectedVoice = null
  for (const fallbackLocale of chain) {
    selectedVoice =
      voices.find(v => v.lang === fallbackLocale) ||
      voices.find(v => v.lang.startsWith(fallbackLocale.split('-')[0]))
    if (selectedVoice) break
  }

  isSpeaking.value = true

  for (let i = 0; i < chunks.length; i++) {
    await new Promise((resolve) => {
      const u = new SpeechSynthesisUtterance(chunks[i])
      u.lang = selectedVoice ? selectedVoice.lang : locale
      if (selectedVoice) u.voice = selectedVoice
      u.rate = 0.92
      u.pitch = 1.0
      u.volume = 1.0

      const resumeTimer = setInterval(() => {
        if (window.speechSynthesis.paused) {
          window.speechSynthesis.resume()
        }
      }, 500)

      u.onend = () => { clearInterval(resumeTimer); resolve() }
      u.onerror = (e) => { clearInterval(resumeTimer); console.warn('[TTS] error:', e.error); resolve() }

      window.speechSynthesis.speak(u)
    })
  }

  isSpeaking.value = false
}

function splitIntoChunks(text, maxChars) {
  if (text.length <= maxChars) return [text]
  const chunks = []
  let remaining = text
  while (remaining.length > 0) {
    if (remaining.length <= maxChars) {
      chunks.push(remaining)
      break
    }
    const slice = remaining.slice(0, maxChars)
    const lastBreak = Math.max(
      slice.lastIndexOf('. '),
      slice.lastIndexOf('? '),
      slice.lastIndexOf('! '),
      slice.lastIndexOf('। '),
      slice.lastIndexOf('\n')
    )
    const cutAt = lastBreak > 50 ? lastBreak + 1 : maxChars
    chunks.push(remaining.slice(0, cutAt).trim())
    remaining = remaining.slice(cutAt).trim()
  }
  return chunks.filter(c => c.length > 0)
}

async function playNextAudio() {
  if (isPlayingAudio) return
  isPlayingAudio = true
  isSpeaking.value = true

  while (audioQueue.length > 0) {
    const b64 = audioQueue.shift()
    if (!b64) continue

    let url = null
    try {
      const binary = atob(b64)
      const bytes = new Uint8Array(binary.length)
      for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i)
      const blob = new Blob([bytes], { type: 'audio/mpeg' })
      url = URL.createObjectURL(blob)
      currentAudioUrl = url

      await new Promise((resolve) => {
        resolveCurrentAudio = resolve
        const audio = new Audio(url)
        currentAudio = audio

        audio.onended = () => {
          if (url) {
            try { URL.revokeObjectURL(url) } catch (_) {}
          }
          if (currentAudioUrl === url) currentAudioUrl = null
          currentAudio = null
          resolveCurrentAudio = null
          resolve()
        }
        audio.onerror = () => {
          if (url) {
            try { URL.revokeObjectURL(url) } catch (_) {}
          }
          if (currentAudioUrl === url) currentAudioUrl = null
          currentAudio = null
          resolveCurrentAudio = null
          resolve()
        }
        audio.play().catch(() => {
          if (url) {
            try { URL.revokeObjectURL(url) } catch (_) {}
          }
          if (currentAudioUrl === url) currentAudioUrl = null
          currentAudio = null
          resolveCurrentAudio = null
          resolve()
        })
      })
    } catch (err) {
      console.error('playNextAudio error:', err)
      if (url) {
        try { URL.revokeObjectURL(url) } catch (_) {}
      }
      if (currentAudioUrl === url) currentAudioUrl = null
      currentAudio = null
      resolveCurrentAudio = null
      // Yield to the event loop before continuing the loop to prevent freezing the UI thread if many errors happen
      await new Promise(r => setTimeout(r, 0))
    }
  }

  isPlayingAudio = false
  isSpeaking.value = false
}

function sendToAgent(transcript_text) {
  if (ws.value && ws.value.readyState === WebSocket.OPEN) {
    streamingBuffer = ''
    if (streamingEl.value) streamingEl.value.textContent = ''
    isThinking.value = true
    ws.value.send(JSON.stringify({
      type: 'user_text',
      text: transcript_text,
      language: selectedLanguage.value
    }))
  } else {
    toast.show('Not connected. Reconnecting…', 'error')
    connectWebSocket()
  }
}

function interruptAgent() {
  audioQueue.length = 0
  Object.keys(audioChunkBuffer).forEach(k => delete audioChunkBuffer[k])
  isPlayingAudio = false
  isSpeaking.value = false
  isStreaming.value = false
  isThinking.value = false
  streamingBuffer = ''
  if (streamingEl.value) streamingEl.value.textContent = ''
  if (currentAudio) {
    try { currentAudio.pause() } catch (_) {}
    currentAudio = null
  }
  if (currentAudioUrl) {
    try { URL.revokeObjectURL(currentAudioUrl) } catch (_) {}
    currentAudioUrl = null
  }
  if (resolveCurrentAudio) {
    resolveCurrentAudio()
    resolveCurrentAudio = null
  }
  if (ws.value && ws.value.readyState === WebSocket.OPEN) {
    ws.value.send(JSON.stringify({ type: 'interrupt' }))
  }
}

function startListening() {
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition
  if (!SR) { toast.show('Speech recognition not supported in this browser.', 'error'); return }
  recognition = new SR()
  recognition.lang = getSttLocale()
  recognition.interimResults = true
  recognition.continuous = false
  recognition.onresult = (e) => {
    let interim = '', final = ''
    for (const r of e.results) {
      if (r.isFinal) final += r[0].transcript
      else interim += r[0].transcript
    }
    interimText.value = interim
    if (final) {
      interimText.value = ''
      transcript.value.push({ role: 'user', text: final })
      sendToAgent(final)
    }
  }
  recognition.onend = () => { isListening.value = false }
  recognition.onerror = (e) => {
    isListening.value = false
    console.warn('[STT] Recognition error:', e.error, 'lang:', recognition.lang)

    if (e.error === 'language-not-supported') {
      agentError.value = `Speech recognition for ${getCurrentLanguage().label} is not supported in this browser. Try speaking in English or Hindi, or install the language pack from Windows Settings → Time & Language → Language.`
      toast.show(`STT not supported for ${getCurrentLanguage().label} on this device`, 'error', 6000)
    } else if (e.error === 'not-allowed') {
      agentError.value = 'Microphone access denied. Please allow microphone access and try again.'
    } else if (e.error === 'network') {
      agentError.value = 'Network error during speech recognition. Check your connection.'
    } else if (e.error !== 'no-speech' && e.error !== 'aborted') {
      console.warn('[STT] Unhandled error:', e.error)
    }
  }
  try { recognition.start(); isListening.value = true } catch (e) { isListening.value = false }
}

function stopListening() {
  try { recognition?.stop() } catch (_) {}
  isListening.value = false
}

function toggleOrb() {
  if (isListening.value) {
    stopListening()
  } else {
    if (isSpeaking.value || isStreaming.value) { interruptAgent() }
    startListening()
  }
}

function onLanguageChange() {
  if (isListening.value) { stopListening(); setTimeout(startListening, 50) }
}

function clearTranscript() {
  transcript.value = []
  interimText.value = ''
  streamingBuffer = ''
  if (streamingEl.value) streamingEl.value.textContent = ''
  isThinking.value = false
  isStreaming.value = false
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
  test.lang = locale
  test.continuous = false
  test.interimResults = false

  await new Promise((resolve) => {
    test.onerror = (e) => {
      if (e.error === 'language-not-supported') {
        agentError.value = `⚠️ Speech recognition for ${getCurrentLanguage().label} may not be available on this device. Voice input may not work. Try switching to English or Hindi.`
      }
      resolve()
    }
    test.onstart = () => { test.abort(); resolve() }
    test.onend = resolve
    try { test.start() } catch { resolve() }
    setTimeout(resolve, 2000)
  })
}

onMounted(async () => {
  animateWave()

  try {
    const data = await apiFetch('/api/v1/agents')
    userAgents.value = Array.isArray(data) ? data : (data?.agents || data?.items || [])

    const saved = localStorage.getItem('active_agent')
    const savedExists = userAgents.value.find(a => a.uuid === saved)

    if (savedExists) {
      activeAgentUuid.value = saved
    } else if (userAgents.value.length > 0) {
      const firstVoice =
        userAgents.value.find(a => a.is_voice_agent) || userAgents.value[0]
      activeAgentUuid.value = firstVoice.uuid
      localStorage.setItem('active_agent', firstVoice.uuid)
    } else {
      activeAgentUuid.value = null
      agentError.value = 'No agents found. Create one in Agents first.'
      return
    }

    connectWebSocket()
    await checkSTTSupport()
  } catch (err) {
    agentError.value = 'Failed to load agents: ' + (err.message || err)
  }

  // Detect voice availability
  detectVoiceStatus()
  if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
    window.speechSynthesis.onvoiceschanged = detectVoiceStatus
  }

  window.addEventListener('storage', handleStorageEvent)
})

function handleStorageEvent(e) {
  if (e.key === 'agent_updated') {
    console.log('[VOXEN] Agent config updated — reconnecting WebSocket')
    showKeySetupBanner.value = false
    reconnectWebSocket()
  }
}

onUnmounted(() => {
  intentionalClose.value = true
  clearInterval(pingInterval.value)
  pingInterval.value = null
  if (reconnectTimer) { clearTimeout(reconnectTimer); reconnectTimer = null }
  if (ws.value) try { ws.value.close() } catch (_) {}
  if (recognition) try { recognition.stop() } catch (_) {}
  if (currentAudio) {
    try { currentAudio.pause() } catch (_) {}
    currentAudio = null
  }
  if (currentAudioUrl) {
    try { URL.revokeObjectURL(currentAudioUrl) } catch (_) {}
    currentAudioUrl = null
  }
  if (resolveCurrentAudio) {
    resolveCurrentAudio()
    resolveCurrentAudio = null
  }
  if (waveInterval) clearInterval(waveInterval)
  window.speechSynthesis?.cancel()
  audioQueue.length = 0
  Object.keys(audioChunkBuffer).forEach(k => delete audioChunkBuffer[k])
  window.removeEventListener('storage', handleStorageEvent)
})

watch(activeAgentUuid, (v) => {
  if (v && v !== 'default' && v !== 'null' && v !== 'undefined') {
    localStorage.setItem('active_agent', v)
  }
})
</script>

<style scoped>
.voice-view { position: relative; height: 100%; }

.agent-switcher {
  display: flex;
  align-items: center;
  gap: 12px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 999px;
  padding: 6px 6px 6px 16px;
  backdrop-filter: blur(8px);
}

.switcher-label {
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: #c7c4d7;
}

.agent-select {
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 999px;
  padding: 6px 14px;
  font-size: 13px;
  color: #fff;
  font-family: inherit;
  outline: none;
  cursor: pointer;
  min-width: 200px;
}

.ws-status {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  padding: 4px 10px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.06);
}

.ws-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #908fa0;
}

.ws-status.connected {
  color: #4ade80;
  border-color: rgba(74, 222, 128, 0.3);
  background: rgba(74, 222, 128, 0.08);
}

.ws-status.connected .ws-dot { background: #4ade80; animation: pulse 2s infinite; }

.ws-status.connecting {
  color: #fbbf24;
  border-color: rgba(251, 191, 36, 0.3);
  background: rgba(251, 191, 36, 0.08);
}

.ws-status.connecting .ws-dot { background: #fbbf24; animation: pulse 1s infinite; }

.ws-status.disconnected {
  color: #ffb4ab;
  border-color: rgba(255, 180, 171, 0.3);
  background: rgba(255, 180, 171, 0.08);
}

.ws-status.disconnected .ws-dot { background: #ffb4ab; }

.ws-status.error {
  color: #ffb4ab;
  border-color: rgba(255, 180, 171, 0.3);
  background: rgba(255, 180, 171, 0.08);
}

.ws-status.error .ws-dot { background: #ffb4ab; }

.error-banner {
  display: flex;
  align-items: center;
  gap: 10px;
  max-width: 42rem;
  margin-left: auto;
  margin-right: auto;
  background: rgba(239, 68, 68, 0.15);
  border: 1px solid rgba(239, 68, 68, 0.3);
  color: #fca5a5;
  padding: 10px 14px;
  border-radius: 10px;
  font-size: 13px;
  font-family: 'JetBrains Mono', monospace;
}

.error-banner .material-symbols-outlined {
  font-size: 20px;
  color: #ef4444;
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
  background: rgba(251, 191, 36, 0.12);
  border: 1px solid rgba(251, 191, 36, 0.3);
  color: #fbbf24;
  padding: 12px 14px;
  border-radius: 10px;
  font-size: 13px;
  font-family: 'JetBrains Mono', monospace;
}

.setup-banner > .material-symbols-outlined {
  font-size: 20px;
  color: #fbbf24;
  flex-shrink: 0;
}

.setup-banner-text {
  flex: 1;
  line-height: 1.5;
  min-width: 200px;
}

.setup-banner-text strong {
  color: #fcd34d;
  font-weight: 600;
}

.setup-banner-text span {
  color: rgba(251, 191, 36, 0.85);
}

.setup-banner-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

.setup-btn {
  padding: 5px 12px;
  background: rgba(251, 191, 36, 0.2);
  border: 1px solid rgba(251, 191, 36, 0.4);
  border-radius: 6px;
  color: #fbbf24;
  font-size: 11px;
  text-decoration: none;
  font-weight: 600;
  transition: background 0.15s ease;
}

.setup-btn:hover {
  background: rgba(251, 191, 36, 0.3);
  color: #fcd34d;
}

.setup-btn-secondary {
  padding: 5px 12px;
  background: transparent;
  border: 1px solid rgba(251, 191, 36, 0.2);
  border-radius: 6px;
  color: rgba(251, 191, 36, 0.7);
  font-size: 11px;
  text-decoration: none;
  transition: background 0.15s ease;
}

.setup-btn-secondary:hover {
  background: rgba(251, 191, 36, 0.08);
  color: #fbbf24;
}

.error-text {
  flex: 1;
}

.error-dismiss {
  margin-left: auto;
  background: none;
  border: none;
  color: #ef4444;
  cursor: pointer;
  font-size: 14px;
  padding: 0 4px;
  opacity: 0.7;
  transition: opacity 0.15s ease;
  font-family: inherit;
}

.error-dismiss:hover { opacity: 1; }

.fade-enter-active, .fade-leave-active { transition: opacity 0.2s ease, transform 0.2s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; transform: translateY(-4px); }

.thinking-indicator {
  display: inline-flex;
  gap: 4px;
  align-items: center;
  padding: 4px 0;
}

.thinking-dot {
  width: 6px;
  height: 6px;
  background: #C4A671;
  border-radius: 50%;
  animation: thinking-bounce 1.2s infinite;
}

.thinking-dot:nth-child(2) { animation-delay: 0.2s; }
.thinking-dot:nth-child(3) { animation-delay: 0.4s; }

@keyframes thinking-bounce {
  0%, 80%, 100% { transform: scale(0.8); opacity: 0.5; }
  40% { transform: scale(1.2); opacity: 1; }
}

.cursor-blink {
  display: inline-block;
  width: 8px;
  height: 14px;
  background: #c0c1ff;
  margin-left: 2px;
  vertical-align: middle;
  animation: blink 0.9s steps(2, end) infinite;
}

@keyframes blink { 50% { opacity: 0; } }
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }
</style>
