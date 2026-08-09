<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="open" class="fixed inset-0 z-[100] flex justify-end">
        <div @click="$emit('close')" class="absolute inset-0 bg-black/40 dark:bg-black/60 backdrop-blur-sm" />

        <Transition name="drawer">
          <div v-if="open" class="relative z-10 w-[460px] h-full glass-panel flex flex-col overflow-hidden">
            <!-- Header -->
            <div class="px-7 py-6 border-b border-outline-variant flex items-center justify-between shrink-0">
              <div>
                <h2 class="font-sans font-bold text-lg text-on-surface">{{ isEdit ? 'Edit Agent' : 'New Agent' }}</h2>
                <p class="font-mono text-[10px] text-on-surface-variant/60 uppercase tracking-widest mt-0.5">
                  {{ form.is_voice_agent ? 'Voice Agent' : 'Chat Agent' }} Configuration
                </p>
              </div>
              <button @click="$emit('close')" class="p-2 hover:bg-surface-container-high rounded-xl transition-colors text-on-surface-variant hover:text-on-surface">
                <span class="material-symbols-outlined">close</span>
              </button>
            </div>

            <!-- Tabs Navigation -->
            <div class="flex border-b border-outline-variant bg-surface/30 shrink-0">
              <button 
                @click="activeTab = 'config'" 
                :class="['flex-1 py-3 text-xs font-semibold uppercase tracking-wider transition-colors border-b-2', activeTab === 'config' ? 'border-primary text-primary bg-primary/5' : 'border-transparent text-on-surface-variant hover:text-on-surface hover:bg-surface-container-high']"
              >
                Configuration
              </button>
              <button 
                @click="activeTab = 'kb'" 
                :class="['flex-1 py-3 text-xs font-semibold uppercase tracking-wider transition-colors border-b-2', activeTab === 'kb' ? 'border-primary text-primary bg-primary/5' : 'border-transparent text-on-surface-variant hover:text-on-surface hover:bg-surface-container-high']"
              >
                Knowledge Base
              </button>
            </div>

            <!-- Scrollable Content -->
            <div class="flex-1 overflow-y-auto p-7 space-y-5">
              <!-- CONFIGURATION TAB -->
              <div v-show="activeTab === 'config'" class="space-y-5">
                <div class="flex rounded-xl overflow-hidden border border-outline-variant">
                  <button
                    v-for="t in agentTypes" :key="t.value"
                    @click="form.is_voice_agent = t.value"
                    :class="[
                      'flex-1 py-2.5 text-sm font-medium transition-colors flex items-center justify-center gap-2',
                      form.is_voice_agent === t.value
                        ? 'bg-primary/15 text-primary'
                        : 'text-on-surface-variant hover:text-on-surface hover:bg-surface-container-high'
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

                <!-- Remembers past conversations toggle -->
                <div class="flex items-start justify-between bg-surface-container/30 border border-outline-variant/40 rounded-xl p-3">
                  <div class="space-y-0.5">
                    <label class="field-label !mb-0 font-medium text-xs normal-case tracking-normal">Remembers past conversations</label>
                    <p class="text-[10px] text-on-surface-variant/60 leading-normal">
                      Summarizes each session so the agent recalls context next time.
                    </p>
                  </div>
                  <ToggleSwitch v-model="remembersConversations" />
                </div>

                <!-- Tools List Block (Only when editing) -->
                <AgentToolsPanel v-if="isEdit" :agent-uuid="agent?.uuid" />

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
                    <option v-for="key in llmKeys" :key="key.id" :value="key.id">
                      {{ key.label }} ({{ key.key_preview || '••••' }})
                    </option>
                  </select>
                  <RouterLink to="/profile" class="add-key-link">+ Add a new key in Profile</RouterLink>
                </div>

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
                      <option v-for="key in ttsKeys" :key="key.id" :value="key.id">
                        {{ key.label }} ({{ key.key_preview || '••••' }})
                      </option>
                    </select>
                    <RouterLink to="/profile" class="add-key-link">+ Add a new key in Profile</RouterLink>
                  </div>
                </template>

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

                <template v-else>
                  <div>
                    <label class="field-label mb-3">Enabled Tools</label>
                    <div class="space-y-2">
                      <label v-for="tool in availableTools" :key="tool" class="flex items-center gap-3 cursor-pointer">
                        <input type="checkbox" :value="tool" v-model="form.tools_enabled"
                          class="w-4 h-4 accent-primary rounded bg-surface-container border-outline-variant" />
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

                <!-- Sandbox Testing Section (Only when editing) -->
                <div v-if="isEdit" class="test-panel">
                  <h3 class="test-title">
                    <span class="material-symbols-outlined">science</span>
                    Test Agent
                  </h3>
                  <p class="test-desc">Send a prompt directly to the agent and see its response.</p>

                  <div class="test-input-row">
                    <input v-model="testInput" type="text" placeholder="Type a message for this agent…" class="field-input" @keydown.enter="testAgent" />
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

              <!-- KNOWLEDGE BASE TAB -->
              <div v-show="activeTab === 'kb'" class="space-y-5">
                <div class="p-5 border border-outline-variant/60 rounded-xl bg-surface-container/20 space-y-4">
                  <label class="field-label !mb-0.5 font-bold text-xs uppercase tracking-wider flex items-center gap-1.5 text-on-surface">
                    <span class="material-symbols-outlined text-sm">database</span>
                    Knowledge Base (pgvector)
                  </label>
                  <p class="text-[10px] text-on-surface-variant/60 leading-normal">
                    Upload PDF/Text reference files or scrape website links to index into the agent's vector database.
                  </p>

                  <!-- Toggle RAG KB activation state -->
                  <div class="flex items-center justify-between border-b border-outline-variant/30 pb-3 mb-2 bg-surface-container/10 p-2.5 rounded-xl">
                    <span class="text-xs font-medium text-on-surface">Enable Knowledge Base Retrieval</span>
                    <ToggleSwitch v-model="form.kb_enabled" />
                  </div>

                  <!-- URL Scraping Input -->
                  <div class="flex items-center gap-2">
                    <input v-model="kbUrl" type="url" placeholder="https://example.com/docs" class="field-input text-xs py-2 input-glow-focus" />
                    <button @click="scrapeUrl" :disabled="kbLoading || !kbUrl.trim()" class="px-3 py-2 btn-ghost-glow text-xs font-mono transition-colors flex items-center gap-1 shrink-0 disabled:opacity-50">
                      <span v-if="kbLoading && kbLoadType === 'url'" class="material-symbols-outlined text-[14px] animate-spin">refresh</span>
                      Scrape
                    </button>
                  </div>

                  <!-- File Upload Input -->
                  <div class="flex items-center gap-2">
                    <input type="file" ref="kbFileInput" class="hidden" accept=".pdf,.txt" @change="onKbFileSelected" />
                    <button @click="$refs.kbFileInput.click()" :disabled="kbLoading" class="w-full py-2.5 bg-surface-container-high hover:bg-surface-container-highest border border-outline-variant rounded-xl text-xs font-semibold text-on-surface-variant transition-colors flex items-center justify-center gap-2">
                      <span v-if="kbLoading && kbLoadType === 'file'" class="material-symbols-outlined text-[14px] animate-spin">refresh</span>
                      <span v-else class="material-symbols-outlined text-[16px]">upload_file</span>
                      {{ kbLoading && kbLoadType === 'file' ? 'Uploading…' : 'Upload PDF / Text Document' }}
                    </button>
                  </div>

                  <!-- Ingested Source List -->
                  <div v-if="allDocs.length > 0" class="space-y-2 mt-2">
                    <label class="field-label text-[10px] uppercase tracking-wider text-on-surface-variant/70 mb-1">Indexed Sources</label>
                    <div v-for="doc in allDocs" :key="doc.id || doc.tempId" class="flex items-center justify-between p-2.5 rounded-lg bg-surface-container-low border border-outline-variant/40 text-xs">
                      <div class="flex items-center gap-2 min-w-0 pr-2">
                        <span class="material-symbols-outlined text-sm text-on-surface-variant/70">
                          {{ doc.source_type === 'file' ? 'description' : 'language' }}
                        </span>
                        <span class="font-mono text-[11px] truncate text-on-surface" :title="doc.source_name">
                          {{ doc.source_name }}
                          <span v-if="doc.isTemp" class="text-[9px] bg-primary/10 text-primary px-1.5 py-0.5 rounded font-sans uppercase font-bold shrink-0 ml-1">Pending</span>
                        </span>
                      </div>
                      <div class="flex items-center gap-2.5 shrink-0">
                        <span class="font-mono text-[10px] text-on-surface-variant/70">{{ doc.total_chunks }}</span>
                        <button @click="removeDoc(doc)" class="text-error/70 hover:text-error transition-colors p-1 rounded hover:bg-error/5 flex items-center">
                          <span class="material-symbols-outlined text-sm">delete</span>
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Footer Buttons -->
            <div class="px-7 py-5 border-t border-outline-variant flex gap-3 shrink-0">
              <button @click="$emit('close')" class="flex-1 py-2.5 bg-surface-container-high hover:bg-surface-container-highest rounded-xl text-sm font-medium transition-colors text-on-surface-variant">
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
import ToggleSwitch from '@/components/ui/ToggleSwitch.vue'
import AgentToolsPanel from '@/components/agents/AgentToolsPanel.vue'

const props = defineProps({ open: Boolean, agent: { type: Object, default: null } })
const emit = defineEmits(['close', 'saved'])
const toast = useToastStore()
const loading = ref(false)
const error = ref('')
const isEdit = ref(false)

const { apiKeys, fetchKeys } = useApiKeys()

const LLM_PROVIDERS = ['gemini', 'openai', 'claude', 'groq']
const TTS_PROVIDERS = ['elevenlabs', 'groq', 'azure_tts', 'deepgram']

const llmKeys = computed(() => apiKeys.value.filter(k => LLM_PROVIDERS.includes(k.provider)))
const ttsKeys = computed(() => apiKeys.value.filter(k => TTS_PROVIDERS.includes(k.provider)))

const testInput = ref('')
const testResponse = ref('')
const testError = ref('')
const testLoading = ref(false)

function resetTest() { testInput.value = ''; testResponse.value = ''; testError.value = '' }

async function testAgent() {
  if (!testInput.value.trim() || !props.agent?.uuid) return
  testLoading.value = true; testError.value = ''; testResponse.value = ''
  try {
    const res = await apiFetch(`/api/v1/agents/${props.agent.uuid}/test`, {
      method: 'POST',
      body: JSON.stringify({ text: testInput.value, language: form.value.voice_language || 'en' })
    })
    testResponse.value = typeof res === 'string' ? res : (res?.response || res?.message || res?.text || JSON.stringify(res))
  } catch (err) {
    testError.value = err.message || 'Test failed. Check that API keys are attached to this agent.'
  } finally { testLoading.value = false }
}

const defaultForm = () => ({
  name: '', description: '', agent_type: 'business_intel', system_prompt: '',
  tools_enabled: ['web_search', 'memory'], output_format: 'markdown',
  is_public: false, is_voice_agent: false, voice_language: 'en',
  voice_system_prompt: '', knowledge_base_text: '', wake_word: 'Nova',
  llm_provider: 'gemini', llm_key_id: null,
  tts_provider: 'browser', tts_key_id: null,
  stt_provider: 'groq', stt_key_id: null,
  kb_enabled: false,
})

const form = ref(defaultForm())

const remembersConversations = computed({
  get() {
    return form.value.tools_enabled && form.value.tools_enabled.includes('memory')
  },
  set(val) {
    if (!form.value.tools_enabled) {
      form.value.tools_enabled = []
    }
    if (val) {
      if (!form.value.tools_enabled.includes('memory')) {
        form.value.tools_enabled.push('memory')
      }
    } else {
      form.value.tools_enabled = form.value.tools_enabled.filter(t => t !== 'memory')
    }
  }
})

function _coerceKeyId(v) {
  if (v === null || v === undefined || v === '') return null
  const n = Number(v); return Number.isFinite(n) ? n : null
}

// Knowledge Base variables
const activeTab = ref('config')
const kbUrl = ref('')
const kbLoading = ref(false)
const kbLoadType = ref('')
const kbDocs = ref([])
const tempDocs = ref([])
const kbFileInput = ref(null)

const allDocs = computed(() => {
  return [
    ...kbDocs.value,
    ...tempDocs.value.map(d => ({
      ...d,
      id: null,
      tempId: d.tempId,
      source_type: d.type,
      source_name: d.name,
      total_chunks: 'Pending deploy',
      isTemp: true
    }))
  ]
})

async function fetchKbDocs() {
  if (!props.agent?.uuid) return
  try {
    kbDocs.value = await apiFetch(`/api/v1/agents/${props.agent.uuid}/kb`)
  } catch (err) {
    console.error('Failed to load KB docs:', err)
  }
}

async function scrapeUrl() {
  const url = kbUrl.value.trim()
  if (!url) return
  
  if (isEdit.value) {
    if (!props.agent?.uuid) return
    kbLoading.value = true
    kbLoadType.value = 'url'
    try {
      await apiFetch(`/api/v1/agents/${props.agent.uuid}/kb/url`, {
        method: 'POST',
        body: JSON.stringify({ url })
      })
      form.value.kb_enabled = true
      toast.show('Website content scraped and indexed!', 'success')
      kbUrl.value = ''
      await fetchKbDocs()
    } catch (err) {
      toast.show(err.message || 'Scraping failed', 'error')
    } finally {
      kbLoading.value = false
      kbLoadType.value = ''
    }
  } else {
    tempDocs.value.push({
      tempId: Math.random().toString(36).substring(7),
      type: 'url',
      url: url,
      name: url
    })
    form.value.kb_enabled = true
    kbUrl.value = ''
    toast.show('Website added to pending knowledge base sources', 'info')
  }
}

async function onKbFileSelected(event) {
  const file = event.target.files?.[0]
  if (!file) return
  
  if (isEdit.value) {
    if (!props.agent?.uuid) return
    kbLoading.value = true
    kbLoadType.value = 'file'
    try {
      const fd = new FormData()
      fd.append('file', file)
      await apiFetch(`/api/v1/agents/${props.agent.uuid}/kb/file`, {
        method: 'POST',
        body: fd
      })
      form.value.kb_enabled = true
      toast.show('Document indexed successfully!', 'success')
      await fetchKbDocs()
    } catch (err) {
      toast.show(err.message || 'Upload failed', 'error')
    } finally {
      kbLoading.value = false
      kbLoadType.value = ''
      if (kbFileInput.value) kbFileInput.value.value = ''
    }
  } else {
    tempDocs.value.push({
      tempId: Math.random().toString(36).substring(7),
      type: 'file',
      file: file,
      name: file.name
    })
    form.value.kb_enabled = true
    toast.show('Document added to pending knowledge base sources', 'info')
    if (kbFileInput.value) kbFileInput.value.value = ''
  }
}

async function deleteKbDoc(id) {
  if (!props.agent?.uuid) return
  try {
    await apiFetch(`/api/v1/agents/${props.agent.uuid}/kb/${id}`, {
      method: 'DELETE'
    })
    toast.show('Document removed from index', 'success')
    await fetchKbDocs()
  } catch (err) {
    toast.show(err.message || 'Failed to delete doc', 'error')
  }
}

function removeDoc(doc) {
  if (doc.isTemp) {
    tempDocs.value = tempDocs.value.filter(d => d.tempId !== doc.tempId)
  } else {
    deleteKbDoc(doc.id)
  }
}

watch(() => props.agent, (a) => {
  activeTab.value = 'config'
  tempDocs.value = []
  if (a) { 
    isEdit.value = true
    form.value = { ...defaultForm(), ...a, llm_key_id: a.llm_key_id ?? null, tts_key_id: a.tts_key_id ?? null }
    fetchKbDocs()
  }
  else { 
    isEdit.value = false
    form.value = defaultForm()
    kbDocs.value = []
  }
  resetTest()
}, { immediate: true })

const agentTypes = [
  { value: false, icon: 'smart_toy', label: 'Chat Agent' },
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
      llm_provider: form.value.llm_provider || 'gemini',
      llm_key_id: _coerceKeyId(form.value.llm_key_id),
      tts_provider: form.value.tts_provider || 'browser',
      tts_key_id: _coerceKeyId(form.value.tts_key_id),
      stt_provider: form.value.stt_provider || 'groq',
      stt_key_id: _coerceKeyId(form.value.stt_key_id),
    }
    const data = isEdit.value
      ? await apiFetch(`/api/v1/agents/${props.agent.uuid}`, { method: 'PUT', body: JSON.stringify(payload) })
      : await apiFetch('/api/v1/agents', { method: 'POST', body: JSON.stringify(payload) })

    // If it was a new agent, deploy pending KB items
    if (!isEdit.value && tempDocs.value.length > 0) {
      toast.show('Ingesting pending knowledge base items...', 'info')
      for (const doc of tempDocs.value) {
        try {
          if (doc.type === 'file') {
            const fd = new FormData()
            fd.append('file', doc.file)
            await apiFetch(`/api/v1/agents/${data.uuid}/kb/file`, { method: 'POST', body: fd })
          } else {
            await apiFetch(`/api/v1/agents/${data.uuid}/kb/url`, { method: 'POST', body: JSON.stringify({ url: doc.url }) })
          }
        } catch (kbErr) {
          console.error(`Failed to ingest pending KB item ${doc.name}:`, kbErr)
          toast.show(`Failed to index ${doc.name}`, 'error')
        }
      }
    }

    toast.show(isEdit.value ? 'Agent updated' : 'Agent deployed', 'success')
    emit('saved', data); emit('close')
  } catch (e) { error.value = e.message } finally { loading.value = false }
}
</script>

<style scoped>
.field-label {
  display: block;
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--color-on-surface-variant);
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
  background: var(--color-surface-container);
  border: 1px solid var(--color-outline-variant);
  border-radius: 12px;
  padding: 10px 14px;
  font-size: 14px;
  color: var(--color-on-surface);
  outline: none;
  transition: border-color 0.15s ease;
  font-family: inherit;
}

html.dark .field-input {
  background: rgba(255, 255, 255, 0.05);
  border-color: rgba(255, 255, 255, 0.1);
  color: #E1EFE6;
}

.field-input:focus {
  border-color: var(--color-primary);
}

.form-group { display: block; }

.add-key-link {
  display: inline-block;
  margin-top: 6px;
  font-size: 11px;
  color: var(--color-primary);
  text-decoration: none;
  opacity: 0.8;
}
.add-key-link:hover { opacity: 1; text-decoration: underline; }

.test-panel {
  border-top: 1px solid var(--color-outline-variant);
  padding-top: 18px;
  margin-top: 6px;
}

.test-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 600;
  color: var(--color-on-surface);
  margin-bottom: 4px;
}
.test-title .material-symbols-outlined { font-size: 18px; color: var(--color-primary); }

.test-desc {
  font-size: 12px;
  color: var(--color-outline);
  margin-bottom: 12px;
  line-height: 1.4;
}

.test-input-row { display: flex; gap: 8px; }
.test-input-row .field-input { flex: 1; }

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
  background: var(--color-error-container);
  border: 1px solid var(--color-error);
  border-radius: 8px;
  color: var(--color-error);
  font-size: 12px;
  font-family: 'JetBrains Mono', monospace;
}

.test-response {
  margin-top: 10px;
  padding: 12px;
  background: var(--color-primary-container);
  border: 1px solid var(--color-primary);
  border-radius: 10px;
  display: flex;
  align-items: flex-start;
  gap: 10px;
  font-size: 13px;
  color: var(--color-on-surface);
  line-height: 1.5;
}
.test-response .material-symbols-outlined { font-size: 18px; color: var(--color-primary); margin-top: 2px; flex-shrink: 0; }
.test-response-text { flex: 1; word-break: break-word; white-space: pre-wrap; }
</style>
