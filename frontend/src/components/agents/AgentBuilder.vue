<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="open" class="fixed inset-0 z-[100] flex justify-end">
        <!-- Backdrop -->
        <div @click="$emit('close')" class="absolute inset-0 bg-black/60 backdrop-blur-sm" />

        <!-- Drawer -->
        <Transition name="drawer">
          <div v-if="open" class="relative z-10 w-[420px] h-full glass-panel flex flex-col overflow-hidden">
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
              <!-- Agent type toggle -->
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
            
            <!-- Wake Word field -->
            <div>
              <label class="field-label">Wake Word (activation name)</label>
              <input v-model="form.wake_word" type="text" placeholder="e.g. Nova, Aria, Max" class="field-input" />
              <p class="field-label text-on-surface-variant/60 text-[10px] mt-1">
                Say this name to activate the agent. Default agent uses 'Nova'
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
               
               <!-- Knowledge Base section -->
               <div>
                 <label class="field-label">Knowledge Base</label>
                 <div class="flex items-center gap-3">
                   <input type="checkbox" v-model="form.kb_enabled" id="kb" class="w-4 h-4 accent-primary" />
                   <label for="kb" class="text-sm text-on-surface-variant cursor-pointer">Enable Knowledge Base</label>
                 </div>
                 <div v-if="form.kb_enabled" class="mt-4">
                   <div class="mb-3">
                     <label class="field-label">Upload Knowledge File</label>
                     <div class="flex flex-col gap-2">
                       <div class="flex-1 border border-dashed border-gray-600/50 rounded-xl p-4 text-center cursor-pointer" @click="fileInput.click()">
                         <p class="text-on-surface-variant/60">Drag and drop PDF or TXT files here, or click to browse</p>
                         <p class="text-xs text-on-surface-variant/40 mt-1">Accepted: .pdf, .txt</p>
                         <input
                           ref="fileInput"
                           type="file"
                           accept=".pdf,.txt"
                           class="hidden"
                           @change="onFileChange"
                         />
                       </div>
                       <button @click="uploadKBFile" class="px-4 py-2 bg-primary/10 hover:bg-primary/20 rounded text-sm font-medium text-primary transition-colors">
                         Upload File
                       </button>
                     </div>
                   </div>
                   <div v-if="form.kb_progress" class="mb-3">
                     <div class="flex items-center justify-between mb-1">
                       <span class="text-sm text-on-surface-variant">Uploading...</span>
                       <span class="text-sm text-primary">{{ Math.round(form.kb_progress * 100) }}%</span>
                     </div>
                     <div class="w-full bg-gray-800/50 rounded h-2">
                       <div
                         :style="{ width: form.kb_progress * 100 + '%' }"
                         class="bg-primary rounded h-2"
                       ></div>
                     </div>
                   </div>
                   <div v-if="form.has_knowledge_base" class="flex items-center justify-between mb-3">
                     <span class="flex items-center gap-2">
                       <span class="w-2 h-2 bg-green-400 rounded"></span>
                       <span class="text-sm text-green-400">Knowledge base active</span>
                     </span>
                     <button @click="deleteKB" class="text-sm text-error hover:text-error/80 transition-colors">
                       Delete Knowledge Base
                     </button>
                   </div>
                 </div>
               </div>

              <!-- Voice-specific fields -->
              <template v-if="form.is_voice_agent">
                <div>
                  <label class="field-label">Voice Language</label>
                  <select v-model="form.voice_language" class="field-input lang-dropdown">
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
import { ref, watch } from 'vue'
import { apiFetch } from '@/composables/useApi'
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

const defaultForm = () => ({
  name: '', description: '', agent_type: 'business_intel', system_prompt: '',
  tools_enabled: ['web_search', 'memory'], output_format: 'markdown',
  is_public: false, is_voice_agent: false, voice_language: 'en',
  voice_system_prompt: '', knowledge_base_text: '',
  wake_word: 'Nova', // Default wake word
  kb_enabled: false,
  kb_progress: 0,
  has_knowledge_base: false
})

const form = ref(defaultForm())

watch(() => props.agent, (a) => {
  if (a) { isEdit.value = true; form.value = { ...defaultForm(), ...a } }
  else { isEdit.value = false; form.value = defaultForm() }
}, { immediate: true })

const agentTypes = [
  { value: false, icon: 'smart_toy', label: 'BI Agent' },
  { value: true, icon: 'mic', label: 'Voice Agent' },
]
const availableTools = ['web_search', 'memory', 'critic', 'formatter', 'planner']

async function uploadKBFile() {
  const fileInput = document.getElementById('kb-file-input')
  if (!fileInput || !fileInput.files || fileInput.files.length === 0) {
    toast.show('Please select a file to upload', 'error')
    return
  }
  
  const file = fileInput.files[0]
  const formData = new FormData()
  formData.append('file', file)
  
  try {
    loading.value = true
    error.value = ''
    
    // Reset progress
    form.kb_progress = 0
    
    // Simulate upload progress (in a real app, you'd use xhr.upload.onprogress)
    const progressInterval = setInterval(() => {
      if (form.kb_progress < 0.9) {
        form.kb_progress += 0.05
      }
    }, 100)
    
    const res = await fetch(
      `/api/v1/agents/${props.agent.uuid}/kb/upload`,
      {
        method: 'POST',
        headers: {
          // Don't set Content-Type - let browser set it with boundary
          Authorization: `Bearer ${localStorage.getItem('token')}`
        },
        body: formData
      }
    )
    
    clearInterval(progressInterval)
    form.kb_progress = 1
    
    if (!res.ok) {
      throw new Error(`Upload failed: ${res.status}`)
    }
    
    const data = await res.json()
    form.has_knowledge_base = true
    toast.show('Knowledge base updated', 'success')
  } catch (err) {
    console.error('KB upload error:', err)
    toast.show(err.message || 'Failed to upload knowledge base', 'error')
  } finally {
    loading.value = false
    // Reset progress after a delay
    setTimeout(() => {
      form.kb_progress = 0
    }, 1000)
  }
}

async function deleteKB() {
  if (!window.confirm('Are you sure you want to delete the knowledge base? This action cannot be undone.')) {
    return
  }
  
  try {
    loading.value = true
    error.value = ''
    
    await apiFetch(
      `/api/v1/agents/${props.agent.uuid}/kb`,
      { method: 'DELETE' }
    )
    
    form.has_knowledge_base = false
    toast.show('Knowledge base deleted', 'success')
  } catch (err) {
    console.error('KB delete error:', err)
    toast.show(err.message || 'Failed to delete knowledge base', 'error')
  } finally {
    loading.value = false
  }
}

async function save() {
  if (!form.value.name.trim()) { error.value = 'Name is required'; return }
  loading.value = true; error.value = ''
  try {
    const payload = { ...form.value }
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
.field-label { @apply block font-mono text-[10px] uppercase tracking-widest text-on-surface-variant mb-1.5; }
.field-input { @apply w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-on-surface placeholder:text-on-surface-variant/40 outline-none focus:border-primary/30 transition-colors; }
</style>
