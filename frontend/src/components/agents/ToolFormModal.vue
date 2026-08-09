<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="open" class="fixed inset-0 z-[110] flex items-center justify-center p-4">
        <!-- Backdrop -->
        <div @click="$emit('close')" class="absolute inset-0 bg-black/40 dark:bg-black/60 backdrop-blur-sm" />

        <!-- Modal Card -->
        <Transition name="scale">
          <div v-if="open" class="relative z-10 w-[560px] max-h-[85vh] glass-panel rounded-2xl flex flex-col overflow-hidden shadow-heavy animate-fade-in">
            <!-- Header -->
            <div class="px-6 py-5 border-b border-outline-variant flex items-center justify-between shrink-0">
              <div>
                <h3 class="font-sans font-bold text-lg text-on-surface">{{ isEdit ? 'Edit Tool' : 'Add Tool' }}</h3>
                <p class="text-xs text-on-surface-variant/70 mt-0.5">
                  Let this agent take real actions via a webhook.
                </p>
              </div>
              <button @click="$emit('close')" class="p-2 hover:bg-surface-container-high rounded-xl transition-colors text-on-surface-variant hover:text-on-surface">
                <span class="material-symbols-outlined text-lg">close</span>
              </button>
            </div>

            <!-- Content -->
            <div class="flex-1 overflow-y-auto p-6 space-y-5">
              <div>
                <label class="field-label">Name</label>
                <input v-model="form.name" @blur="touched.name = true" type="text" placeholder="e.g. book_meeting" class="field-input font-mono text-sm" />
                <p class="text-[10px] text-on-surface-variant/60 mt-1">Letters, numbers, underscore only.</p>
                <p v-if="nameError" class="text-[11px] text-error mt-1">{{ nameError }}</p>
              </div>

              <div>
                <label class="field-label">Description (tells the AI when to use this)</label>
                <textarea v-model="form.description" rows="2" placeholder="e.g. Books a meeting slot when the caller asks to schedule a call..." class="field-input resize-none text-sm" />
              </div>

              <div>
                <label class="field-label">Webhook URL</label>
                <input v-model="form.webhook_url" @blur="touched.webhook_url = true" type="text" placeholder="https://hooks.example.com/book" class="field-input text-sm" />
                <p :class="['text-[10px] mt-1', isLocalhostUrl ? 'text-error font-medium' : 'text-on-surface-variant/60']">
                  {{ isLocalhostUrl ? '⚠ Must be a public URL — localhost and private IPs are blocked.' : 'Must be a public URL — localhost/private IPs are blocked' }}
                </p>
              </div>

              <!-- Parameters -->
              <div class="space-y-3">
                <div class="flex items-center justify-between">
                  <label class="field-label !mb-0">Parameters</label>
                  <button @click="addParameter" type="button" class="text-xs font-semibold text-primary hover:opacity-85 flex items-center gap-1">
                    <span class="material-symbols-outlined text-sm">add</span> Add Parameter
                  </button>
                </div>

                <div v-if="form.parameters.length === 0" class="text-xs text-on-surface-variant/60 bg-surface-container/30 border border-dashed border-outline-variant/60 rounded-xl p-4 text-center">
                  No parameters — this tool takes no input.
                </div>

                <div v-else class="space-y-3">
                  <div v-for="(param, idx) in form.parameters" :key="idx" class="bg-surface-container-low rounded-lg p-3 border border-outline-variant/40 space-y-2 relative">
                    <!-- Delete button in top-right -->
                    <button @click="removeParameter(idx)" type="button" class="absolute top-2.5 right-2.5 p-1 text-on-surface-variant hover:text-error transition-colors rounded-lg hover:bg-surface-container">
                      <span class="material-symbols-outlined text-[16px]">delete</span>
                    </button>

                    <!-- Parameter Fields Grid -->
                    <div class="grid grid-cols-[1fr,110px,100px] gap-2 pr-7">
                      <div>
                        <input v-model="param.name" type="text" placeholder="name" class="field-input font-mono !text-xs !py-1.5 !px-2.5" />
                      </div>
                      <div>
                        <select v-model="param.type" class="field-input !text-xs !py-1.5 !px-2">
                          <option value="string">string</option>
                          <option value="number">number</option>
                          <option value="boolean">boolean</option>
                        </select>
                      </div>
                      <label class="flex items-center gap-1.5 cursor-pointer select-none">
                        <input v-model="param.required" type="checkbox" class="w-3.5 h-3.5 accent-primary bg-surface-container border-outline-variant" />
                        <span class="text-[11px] font-medium text-on-surface-variant">Required</span>
                      </label>
                    </div>

                    <!-- Parameter Description Row -->
                    <div>
                      <input v-model="param.description" type="text" placeholder="Parameter description..." class="field-input !text-xs !py-1.5 !px-2.5" />
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Footer -->
            <div class="px-6 py-4 border-t border-outline-variant flex items-center justify-between shrink-0 bg-surface-container-low/40">
              <!-- Left aligned test runner -->
              <div class="flex items-center gap-3">
                <button @click="testTool" :disabled="testing || !canTest" type="button"
                  class="py-1.5 px-3.5 bg-surface-container-high border border-outline-variant hover:bg-surface-container-highest rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-colors disabled:opacity-50 text-on-surface">
                  <span v-if="testing" class="material-symbols-outlined text-sm animate-spin">refresh</span>
                  <span v-else class="material-symbols-outlined text-sm">science</span>
                  {{ testing ? 'Testing…' : 'Test this tool' }}
                </button>

                <!-- Test results pill -->
                <Transition name="fade">
                  <div v-if="testResult" :class="[
                    'flex items-center gap-1 px-2.5 py-1 rounded-full text-[10px] font-medium font-mono border',
                    testResult.success
                      ? 'bg-primary/10 text-primary border-primary/20'
                      : 'bg-error/10 text-error border-error/20'
                  ]">
                    <span class="material-symbols-outlined text-[12px]">
                      {{ testResult.success ? 'check' : 'close' }}
                    </span>
                    <span>{{ testResult.text }}</span>
                  </div>
                </Transition>
              </div>

              <!-- Right aligned submit buttons -->
              <div class="flex gap-2">
                <button @click="$emit('close')" type="button" class="py-2 px-4 hover:bg-surface-container rounded-xl text-xs font-semibold transition-colors text-on-surface-variant">
                  Cancel
                </button>
                <button @click="save" :disabled="!isValid" type="button"
                  class="py-2 px-4 bg-primary text-on-primary hover:opacity-90 rounded-xl text-xs font-semibold transition-opacity disabled:opacity-40">
                  Save Tool
                </button>
              </div>
            </div>
          </div>
        </Transition>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { apiFetch } from '@/composables/useApi'

const props = defineProps({
  open: Boolean,
  agentUuid: String,
  tool: {
    type: Object,
    default: null
  }
})
const emit = defineEmits(['close', 'saved'])

const isEdit = computed(() => !!props.tool)

const defaultForm = () => ({
  name: '',
  description: '',
  webhook_url: '',
  parameters: [],
  is_active: true
})

const form = ref(defaultForm())
const touched = reactive({
  name: false,
  webhook_url: false
})

const testing = ref(false)
const testResult = ref(null)

watch(() => props.tool, (newTool) => {
  if (newTool) {
    form.value = JSON.parse(JSON.stringify(newTool))
  } else {
    form.value = defaultForm()
  }
  touched.name = false
  touched.webhook_url = false
  testResult.value = null
}, { immediate: true })

// Validations
const nameRegex = /^[a-zA-Z0-9_-]+$/
const nameError = computed(() => {
  if (!touched.name) return ''
  if (!form.value.name.trim()) return 'Name is required'
  if (!nameRegex.test(form.value.name)) return 'Letters, numbers, underscores, and dashes only'
  return ''
})

const isLocalhostUrl = computed(() => {
  const url = form.value.webhook_url.trim().toLowerCase()
  if (!url) return false
  return url.includes('localhost') || url.includes('127.0.0.1') || url.includes('0.0.0.0') || url.includes('192.168.') || url.includes('10.') || url.includes('172.16.')
})

const isValid = computed(() => {
  return (
    form.value.name.trim() &&
    nameRegex.test(form.value.name) &&
    form.value.webhook_url.trim() &&
    !isLocalhostUrl.value
  )
})

const canTest = computed(() => {
  return form.value.webhook_url.trim() && !isLocalhostUrl.value
})

function addParameter() {
  form.value.parameters.push({
    name: '',
    type: 'string',
    description: '',
    required: false
  })
}

function removeParameter(idx) {
  form.value.parameters.splice(idx, 1)
}

async function testTool() {
  if (!canTest.value) return
  testing.value = true
  testResult.value = null
  
  // construct test params dummy structure
  const dummyParams = {}
  form.value.parameters.forEach(p => {
    if (p.name.trim()) {
      if (p.type === 'number') dummyParams[p.name] = 123
      else if (p.type === 'boolean') dummyParams[p.name] = true
      else dummyParams[p.name] = 'test_value'
    }
  })

  try {
    const data = await apiFetch(`/api/v1/agents/${props.agentUuid}/tools/test`, {
      method: 'POST',
      body: JSON.stringify({
        webhook_url: form.value.webhook_url.trim(),
        parameters: dummyParams
      })
    })

    if (data.status === 'success') {
      testResult.value = {
        success: data.success,
        text: data.success ? `✓ ${data.status_code} (${data.latency_ms}ms)` : `✗ Failed (${data.status_code})`
      }
    } else {
      testResult.value = {
        success: false,
        text: `✗ ${data.message || 'failed'}`
      }
    }
  } catch (err) {
    testResult.value = {
      success: false,
      text: `✗ ${err.message || 'error'}`
    }
  } finally {
    testing.value = false
  }
}

async function save() {
  if (!isValid.value) return
  
  try {
    let savedTool
    if (isEdit.value) {
      savedTool = await apiFetch(`/api/v1/agents/${props.agentUuid}/tools/${props.tool.uuid}`, {
        method: 'PUT',
        body: JSON.stringify(form.value)
      })
    } else {
      savedTool = await apiFetch(`/api/v1/agents/${props.agentUuid}/tools`, {
        method: 'POST',
        body: JSON.stringify(form.value)
      })
    }
    emit('saved', savedTool)
  } catch (err) {
    alert(err.message || 'Failed to save tool')
  }
}
</script>
