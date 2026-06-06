<template>
  <section class="col-span-12 lg:col-span-5 flex flex-col glass-panel rounded-3xl overflow-hidden relative group">
    <!-- Header -->
    <div class="p-8 flex justify-between items-start z-10">
      <div>
        <h2 class="font-sans text-2xl font-bold text-white tracking-tight">Lumina-4</h2>
        <p class="font-mono text-xs text-primary/60 uppercase tracking-widest mt-1">Autonomous Intelligence</p>
      </div>
      <div :class="['flex items-center gap-2 px-3 py-1 rounded-lg border text-xs font-mono font-bold uppercase',
        isListening
          ? 'bg-error/10 border-error/30 text-error'
          : isSpeaking
          ? 'bg-secondary-container/20 border-secondary-container/30 text-secondary'
          : 'bg-primary/10 border-primary/20 text-primary'
      ]">
        <span class="w-1.5 h-1.5 rounded-full animate-pulse"
          :class="isListening ? 'bg-error' : isSpeaking ? 'bg-secondary' : 'bg-primary'" />
        {{ statusLabel }}
      </div>
    </div>

    <!-- Orb area -->
    <div class="flex-1 flex flex-col items-center justify-center relative -mt-12">
      <div class="absolute orb-glow w-[300px] h-[300px] rounded-full" />

      <!-- Main orb -->
      <div
        @click="toggleListening"
        :class="['relative z-10 neural-orb-large w-48 h-48 rounded-full flex items-center justify-center cursor-pointer transition-transform duration-700',
          isListening ? 'scale-110 group-hover:scale-105' : 'group-hover:scale-105'
        ]"
      >
        <span class="material-symbols-outlined text-on-primary text-6xl icon-filled">
          {{ isListening ? 'mic' : 'waves' }}
        </span>

        <!-- Waveform -->
        <div class="absolute -bottom-16 w-48 flex justify-center items-end gap-1.5 h-12">
          <div
            v-for="(h, i) in waveHeights"
            :key="i"
            class="w-1 rounded-full waveform-bar"
            :class="[`bg-primary/${isListening || isSpeaking ? '80' : '30'}`, `animate-[bounce_${waveTimes[i]}s_infinite]`]"
            :style="{ height: h + 'px' }"
          />
        </div>
      </div>

      <!-- Pulse rings when listening -->
      <template v-if="isListening">
        <div class="absolute w-60 h-60 border border-primary/20 rounded-full pulse-ring" />
        <div class="absolute w-72 h-72 border border-primary/10 rounded-full pulse-ring" style="animation-delay:0.5s" />
      </template>

      <!-- Ambient rings always -->
      <div class="absolute w-72 h-72 border border-white/5 rounded-full animate-pulse" />
      <div class="absolute w-96 h-96 border border-white/[0.03] rounded-full animate-[pulse_6s_ease-in-out_infinite]" />
    </div>

    <!-- Transcript + controls -->
    <div class="p-8 z-10">
      <!-- Language selector -->
      <div class="flex items-center justify-between mb-3">
        <span class="font-mono text-[10px] text-on-surface-variant/60 uppercase tracking-widest">Transcript</span>
        <LanguageSelector @change="onLanguageChange" />
      </div>

      <div class="bg-black/40 backdrop-blur-md rounded-2xl p-5 border border-white/5 h-36 overflow-y-auto font-mono text-xs leading-relaxed">
        <div v-if="transcript.length === 0" class="text-on-surface-variant/40 italic">
          Click the orb to start speaking…
        </div>
        <div v-else class="space-y-3">
          <p v-for="(msg, i) in transcript" :key="i" :class="msg.role === 'user' ? 'text-on-surface-variant' : 'text-white'">
            <span :class="['font-bold mr-2', msg.role === 'user' ? 'text-primary' : 'text-secondary']">
              {{ msg.role === 'user' ? 'YOU:' : 'AGENT:' }}
            </span>
            {{ msg.text }}
          </p>
          <p v-if="interimText" class="text-on-surface-variant/60 italic">{{ interimText }}</p>
        </div>
      </div>

      <div class="grid grid-cols-2 gap-4 mt-5">
        <button
          @click="toggleListening"
          class="py-3 px-5 bg-white/5 hover:bg-white/10 rounded-xl transition-all flex items-center justify-center gap-2 font-medium border border-white/5 text-sm"
        >
          <span class="material-symbols-outlined text-[18px]">{{ isListening ? 'mic_off' : 'mic' }}</span>
          {{ isListening ? 'Mute Agent' : 'Start Agent' }}
        </button>
        <button
          @click="clearTranscript"
          class="py-3 px-5 bg-secondary-container text-white rounded-xl transition-all hover:brightness-110 flex items-center justify-center gap-2 font-bold text-sm shadow-[0_4px_20px_rgba(87,27,193,0.3)]"
        >
          <span class="material-symbols-outlined text-[18px]">terminal</span>
          Clear Log
        </button>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref, computed, onUnmounted, watch } from 'vue'
import { apiFetch } from '@/composables/useApi'
import { useLanguage } from '@/composables/useLanguage'
import { useTTS } from '@/composables/useTTS'
import LanguageSelector from '@/components/LanguageSelector.vue'

const props = defineProps({ agentUuid: { type: String, default: null } })

const { selectedLanguage, getSttLocale } = useLanguage()
const { speak, stop: stopTTS } = useTTS()

const isListening = ref(false)
const isSpeaking = ref(false)
const transcript = ref([])
const interimText = ref('')
let recognition = null
let synth = window.speechSynthesis

const statusLabel = computed(() =>
  isListening.value ? 'Listening' : isSpeaking.value ? 'Speaking' : 'Standby'
)

const waveHeights = ref([16, 32, 48, 40, 24])
const waveTimes = ['1.2', '0.8', '1.0', '0.7', '1.1']

function animateWave() {
  if (!isListening.value && !isSpeaking.value) {
    waveHeights.value = [16, 32, 48, 40, 24]
    return
  }
  waveHeights.value = waveHeights.value.map(() => Math.floor(Math.random() * 44) + 8)
  setTimeout(animateWave, 150)
}

function toggleListening() {
  if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
    transcript.value.push({ role: 'agent', text: 'Speech recognition is not supported in this browser.' })
    return
  }
  isListening.value ? stopListening() : startListening()
}

function startListening() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
  recognition = new SpeechRecognition()
  recognition.lang = getSttLocale()
  recognition.interimResults = true
  recognition.continuous = false

  recognition.onresult = (e) => {
    let interim = ''
    let final = ''
    for (const result of e.results) {
      if (result.isFinal) final += result[0].transcript
      else interim += result[0].transcript
    }
    interimText.value = interim
    if (final) {
      interimText.value = ''
      sendToAgent(final)
    }
  }
  recognition.onend = () => {
    isListening.value = false
  }
  recognition.start()
  isListening.value = true
  animateWave()
}

function stopListening() {
  recognition?.stop()
  isListening.value = false
}

async function sendToAgent(text) {
  transcript.value.push({ role: 'user', text })
  try {
    const res = await apiFetch('/api/v1/voice/chat', {
      method: 'POST',
      body: JSON.stringify({ text, agent_uuid: props.agentUuid, language: selectedLanguage.value }),
    })
    const reply = res.response_text
    transcript.value.push({ role: 'agent', text: reply })
    isSpeaking.value = true
    try {
      await speak(reply, selectedLanguage.value)
    } finally {
      isSpeaking.value = false
    }
  } catch (e) {
    transcript.value.push({ role: 'agent', text: 'Connection error. Please try again.' })
  }
}

function onLanguageChange() {
  stopTTS()
  if (isListening.value) {
    stopListening()
    startListening()
  }
}

// Restart recognition with new STT locale when language changes
watch(selectedLanguage, () => {
  if (isListening.value) {
    stopListening()
    startListening()
  }
})

function clearTranscript() {
  transcript.value = []
  interimText.value = ''
}

onUnmounted(() => {
  recognition?.stop()
  synth?.cancel()
})
</script>
