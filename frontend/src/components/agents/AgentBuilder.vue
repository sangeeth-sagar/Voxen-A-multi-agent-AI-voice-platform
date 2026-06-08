<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="open" class="fixed inset-0 z-[100] flex justify-end">
        <div @click="$emit('close')" class="absolute inset-0 bg-black/60 backdrop-blur-sm" />

        <Transition name="drawer">
          <div v-if="open" class="relative z-10 w-[460px] h-full glass-panel flex flex-col overflow-hidden">
            <!-- Header -->
            <div class="px-7 py-6 border-b border-white/5 flex items-center justify-between shrink-0">
              <div>
                <h2 class="font-sans font-bold text-lg text-white">{{ isEdit ? 'Edit Agent' : 'New Agent' }}</h2>
                <p class="font-mono text-[10px] text-on-surface-variant/60 uppercase tracking-widest mt-0.5">
                  {{ form.is_voice_agent ? 'Voice Agent' : 'BI Agent' }} Configuration
                </p>
              </div>
              <button @click="$emit('close')" class="p-2 hover:bg-white/5 rounded-xl transition-colors text-on-surface-variant hover:text-white">
                <span class="material-symbols-outlined">close</span>
              </button>
            </div>

            <!-- Form -->
            <div class="flex-1 overflow-y-auto p-7 space-y-5">
              <div class="flex rounded-xl overflow-hidden border border-white/10">
                <button
                  v-for="t in agentTypes"
                  :key="t.value"
                  @click="form.is_voice_agent = t.value"
                  :class="[
                    'flex-1 py-2.5 text-sm font-medium transition-colors flex items-center justify-center gap-2',
                    form.is_voice_agent === t.value
                      ? 'bg-primary/15 text-primary'
                      : 'text-on-surface-variant hover:text-white hover:bg-white/5'
                  ]"
                >
                  <span class="material-symbols-outlined text-[16px]">{{ t.icon }}</span> {{ t.label }}
                </button>
              </div>

              <div>
                <label class="field-label">Agent Name</label>
                <input v-model="form.name" type="text" placeholder="e.g. Market Analyst v2" class="field-input" />
              </div>

              <div v-if="form.is_voice_agent">
                <label class="field-label">Wake Word (activation name)</label>
                <input v-model="form.wake_word" type="text" placeholder="e.g. Nova, Aria, Max" class="field-input" />
                <p class="field-label text-on-surface-variant/60 text-[10px] mt-1 normal-case">
                  Say this name to activate the agent.
                </p>
              </div>

              <div>
                <label class="field-label">Description</label>
                <textarea v-model="form.description" rows="2" placeholder="What does this agent do?" class="field-input resize-none" />
              </div>

              <div>
                <label class="field-label">System Prompt</label>
                <textarea v-model="form.system_prompt" rows="4" placeholder="Core instructions for this agent…" class="field-input resize-none font-mono text-xs" />
              </div>

              <!-- ===== LLM Provider & Key ===== -->
              <div class="form-group">
                <label class="field-label">LLM Provider</label>
                <select v-model="form.llm_provider" class="field-input">
                  <option value="gemini">Google Gemini</option>
                  <option value="openai">OpenAI</option>
                  <option value="claude">Anthropic Claude</option>
                  <option value="groq">Groq (LLaMA)</option>
                </select>
              </div>

              <div class="form-group">
                <label class="field-label">LLM API Key</label>
                <select v-model="form.llm_key_id" class="field-input">
                  <option :value="null">— Select a saved key —</option>
                  <option
                    v-for="key in llmKeys"
                    :key="key.id"
                    :value="key.id"
                  >
                    {{ key.label }} ({{ key.key_preview || '••••' }})
                  </option>
                </select>
                <RouterLink to="/profile" class="add-key-link">+ Add a new key in Profile</RouterLink>
              </div>

              <!-- ===== TTS Provider & Key (voice only) ===== -->
              <template v-if="form.is_voice_agent">
                <div class="form-group">
                  <label class="field-label">Voice / TTS Provider</label>
                  <select v-model="form.tts_provider" class="field-input">
                    <option value="elevenlabs">ElevenLabs</option>
                    <option value="groq">Groq</option>
                    <option value="deepgram">Deepgram</option>
                    <option value="browser">Browser (Free, no key needed)</option>
                  </select>
                </div>

                <div class="form-group" v-if="form.tts_provider !== 'browser'">
                  <label class="field-label">TTS API Key</label>
                  <select v-model="form.tts_key_id" class="field-input">
                    <option :value="null">— Select a saved key —</option>
                    <option
                      v-for="key in ttsKeys"
                      :key="key.id"
                      :value="key.id"
                    >
                      {{ key.label }} ({{ key.key_preview || '••••' }})
                    </option>
                  </select>
                  <RouterLink to="/profile" class="add-key-link">+ Add a new key in Profile</RouterLink>
                </div>
              </template>

              <!-- Voice-specific fields -->
              <template v-if="form.is_voice_agent">
                <div>
                  <label class="field-label">Voice Language</label>
                  <select v-model="form.voice_language" class="field-input">
                    <option value="en">GB English</option>
                    <option value="hi">IN Hindi</option>
                    <option value="mr">IN Marathi</option>
                    <option value="ml">IN Malayalam</option>
                  </select>
                </div>
                <div>
                  <label class="field-label">Voice System Prompt</label>
                  <textarea v-model="form.voice_system_prompt" rows="3" placeholder="How should the agent speak?" class="field-input resize-none font-mono text-xs" />
                </div>
                <div>
                  <label class="field-label">Knowledge Base (plain text)</label>
                  <textarea v-model="form.knowledge_base_text" rows="4" placeholder="Paste reference content here…" class="field-input resize-none font-mono text-xs" />
                </div>
              </template>

              <!-- BI-specific fields -->
              <template v-else>
                <div>
                  <label class="field-label mb-3">Enabled Tools</label>
                  <div class="space-y-2">
                    <label v-for="tool in availableTools" :key="tool" class="flex items-center gap-3 cursor-pointer">
                      <input type="checkbox" :value="tool" v-model="form.tools_enabled"
                        class="w-4 h-4 accent-primary rounded bg-white/5 border-white/20" />
                      <span class="text-sm font-mono text-on-surface-variant">{{ tool }}</span>
                    </label>
                  </div>
                </div>
              </template>

              <div class="flex items-center gap-3">
                <input type="checkbox" v-model="form.is_public" id="pub" class="w-4 h-4 accent-primary" />
                <label for="pub" class="text-sm text-on-surface-variant cursor-pointer">Make agent public</label>
              </div>

              <p v-if="error" class="text-error text-sm">{{ error }}</p>

              <!-- Test panel (edit mode only) -->
              <div v-if="isEdit" class="test-panel">
                <h3 class="test-title">
                  <span class="material-symbols-outlined">science</span>
                  Test Agent
                </h3>
                <p class="test-desc">Send a prompt directly to the agent and see its response.</p>

                <div class="test-input-row">
                  <input
                    v-model="testInput"
                    type="text"
                    placeholder="Type a message for this agent…"
                    class="field-input"
                    @keydown.enter="testAgent"
                  />
                  <button @click="testAgent" :disabled="testLoading || !testInput.trim()" class="btn-primary test-btn">
                    <span v-if="testLoading" class="material-symbols-outlined text-sm animate-spin">refresh</span>
                    <span v-else class="material-symbols-outlined text-sm">send</span>
                    {{ testLoading ? 'Sending…' : 'Test' }}
                  </button>
                </div>

                <div v-if="testError" class="test-error">⚠️ {{ testError }}</div>
                <div v-if="testResponse" class="test-response">
                  <span class="material-symbols-outlined">smart_toy</span>
                  <span class="test-response-text">{{ testResponse }}</span>
                </div>
              </div>
            </div>

            <!-- Footer -->
            <div class="px-7 py-5 border-t border-white/5 flex gap-3 shrink-0">
              <button @click="$emit('close')" class="flex-1 py-2.5 bg-white/5 hover:bg-white/10 rounded-xl text-sm font-medium transition-colors">
                Cancel
              </button>
              <button @click="save" :disabled="loading"
                class="flex-1 py-2.5 btn-primary rounded-xl text-sm font-semibold flex items-center justify-center gap-2 disabled:opacity-50">
                <span v-if="loading" class="material-symbols-outlined text-sm animate-spin">refresh</span>
                {{ loading ? 'Saving…' : (isEdit ? 'Save Changes' : 'Deploy Agent') }}
              </button>
            </div>
          </div>
        </Transition>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, watch, onMounted, computed } from 'vue'
import { apiFetch } from '@/composables/useApi'
import { useApiKeys } from '@/composables/useApiKeys'
import { useToastStore } from '@/stores/toast'

const props = defineProps({
  open: Boolean,
  agent: { type: Object, default: null },
})
const emit = defineEmits(['close', 'saved'])
const toast = useToastStore()
const loading = ref(false)
const error = ref('')
const isEdit = ref(false)

const { apiKeys, fetchKeys } = useApiKeys()

const LLM_PROVIDERS = ['gemini', 'openai', 'claude', 'groq']
const TTS_PROVIDERS = ['elevenlabs', 'groq', 'azure_tts', 'deepgram']

const llmKeys = computed(() =>
  apiKeys.value.filter(k => LLM_PROVIDERS.includes(k.provider))
)
const ttsKeys = computed(() =>
  apiKeys.value.filter(k => TTS_PROVIDERS.includes(k.provider))
)

const testInput = ref('')
const testResponse = ref('')
const testError = ref('')
const testLoading = ref(false)

function resetTest() {
  testInput.value = ''
  testResponse.value = ''
  testError.value = ''
}

async function testAgent() {
  if (!testInput.value.trim() || !props.agent?.uuid) return
  testLoading.value = true
  testError.value = ''
  testResponse.value = ''
  try {
    const res = await apiFetch(`/api/v1/agents/${props.agent.uuid}/test`, {
      method: 'POST',
      body: JSON.stringify({
        text: testInput.value,
        language: form.value.voice_language || 'en'
      })
    })
    testResponse.value = typeof res === 'string'
      ? res
      : (res?.response || res?.message || res?.text || JSON.stringify(res))
  } catch (err) {
    testError.value = err.message || 'Test failed. Check that API keys are attached to this agent.'
  } finally {
    testLoading.value = false
  }
}

const defaultForm = () => ({
  name: '', description: '', agent_type: 'business_intel', system_prompt: '',
  tools_enabled: ['web_search', 'memory'], output_format: 'markdown',
  is_public: false, is_voice_agent: false, voice_language: 'en',
  voice_system_prompt: '', knowledge_base_text: '',
  wake_word: 'Nova',
  llm_provider: 'gemini',
  llm_key_id: null,
  tts_provider: 'browser',
  tts_key_id: null,
  stt_provider: 'groq',
  stt_key_id: null,
})

const form = ref(defaultForm())

function _coerceKeyId(v) {
  if (v === null || v === undefined || v === '') return null
  const n = Number(v)
  return Number.isFinite(n) ? n : null
}

watch(() => props.agent, (a) => {
  if (a) {
    isEdit.value = true
    form.value = {
      ...defaultForm(),
      ...a,
      llm_key_id: a.llm_key_id ?? null,
      tts_key_id: a.tts_key_id ?? null,
    }
  } else {
    isEdit.value = false
    form.value = defaultForm()
  }
  resetTest()
}, { immediate: true })

const agentTypes = [
  { value: false, icon: 'smart_toy', label: 'BI Agent' },
  { value: true, icon: 'mic', label: 'Voice Agent' },
]
const availableTools = ['web_search', 'memory', 'critic', 'formatter', 'planner']

onMounted(() => { fetchKeys() })

async function save() {
  if (!form.value.name.trim()) { error.value = 'Name is required'; return }
  loading.value = true; error.value = ''
  try {
    const payload = {
      ...form.value,
      // Always include key assignment fields with coerced numeric IDs
      llm_provider: form.value.llm_provider || 'gemini',
      llm_key_id:   _coerceKeyId(form.value.llm_key_id),
      tts_provider: form.value.tts_provider || 'browser',
      tts_key_id:   _coerceKeyId(form.value.tts_key_id),
      stt_provider: form.value.stt_provider || 'groq',
      stt_key_id:   _coerceKeyId(form.value.stt_key_id),
    }
    const data = isEdit.value
      ? await apiFetch(`/api/v1/agents/${props.agent.uuid}`, { method: 'PUT', body: JSON.stringify(payload) })
      : await apiFetch('/api/v1/agents', { method: 'POST', body: JSON.stringify(payload) })
    toast.show(isEdit.value ? 'Agent updated' : 'Agent deployed', 'success')
    emit('saved', data)
    emit('close')
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.field-label {
  display: block;
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: #c7c4d7;
  margin-bottom: 6px;
}

.field-label.normal-case {
  text-transform: none;
  letter-spacing: 0;
  font-family: 'Inter', sans-serif;
  font-size: 11px;
}

.field-input {
  width: 100%;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 10px 14px;
  font-size: 14px;
  color: #e2e2eb;
  outline: none;
  transition: border-color 0.15s ease;
  font-family: inherit;
}

.field-input:focus {
  border-color: rgba(192, 193, 255, 0.4);
}

.form-group {
  display: block;
}

.add-key-link {
  display: inline-block;
  margin-top: 6px;
  font-size: 11px;
  color: #c0c1ff;
  text-decoration: none;
  opacity: 0.8;
}

.add-key-link:hover {
  opacity: 1;
  text-decoration: underline;
}

.test-panel {
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  padding-top: 18px;
  margin-top: 6px;
}

.test-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 600;
  color: #fff;
  margin-bottom: 4px;
}

.test-title .material-symbols-outlined {
  font-size: 18px;
  color: #c0c1ff;
}

.test-desc {
  font-size: 12px;
  color: #908fa0;
  margin-bottom: 12px;
  line-height: 1.4;
}

.test-input-row {
  display: flex;
  gap: 8px;
}

.test-input-row .field-input {
  flex: 1;
}

.test-btn {
  white-space: nowrap;
  padding: 0 14px;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.test-error {
  margin-top: 10px;
  padding: 10px 12px;
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 8px;
  color: #fca5a5;
  font-size: 12px;
  font-family: 'JetBrains Mono', monospace;
}

.test-response {
  margin-top: 10px;
  padding: 12px;
  background: rgba(192, 193, 255, 0.06);
  border: 1px solid rgba(192, 193, 255, 0.15);
  border-radius: 10px;
  display: flex;
  align-items: flex-start;
  gap: 10px;
  font-size: 13px;
  color: #fff;
  line-height: 1.5;
}

.test-response .material-symbols-outlined {
  font-size: 18px;
  color: #c0c1ff;
  margin-top: 2px;
  flex-shrink: 0;
}

.test-response-text {
  flex: 1;
  word-break: break-word;
  white-space: pre-wrap;
}
</style>
