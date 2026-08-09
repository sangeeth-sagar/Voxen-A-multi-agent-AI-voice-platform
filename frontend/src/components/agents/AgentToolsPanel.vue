<template>
  <div class="space-y-3">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <label class="field-label !mb-0 font-bold text-sm tracking-wide">Tools</label>
      <button v-if="agentUuid" @click="openFormModal(null)" type="button" class="flex items-center gap-1 text-xs font-semibold text-primary hover:opacity-80 transition-opacity">
        <span class="material-symbols-outlined text-[16px]">add</span> Add Tool
      </button>
    </div>

    <!-- Disabled State for New Agents -->
    <div v-if="!agentUuid" class="bg-surface-container/20 border border-dashed border-outline-variant/60 rounded-xl px-4 py-6 text-center text-xs text-on-surface-variant/60">
      <span class="material-symbols-outlined text-[20px] text-on-surface-variant/40 mb-1">build_circle</span>
      <p>Custom tools can be configured after deploying the agent node.</p>
    </div>

    <div v-else>
      <!-- Loading state -->
      <div v-if="loading" class="flex items-center justify-center py-6">
        <span class="material-symbols-outlined text-xl text-primary animate-spin">refresh</span>
      </div>

      <!-- Empty State -->
      <div v-else-if="tools.length === 0" class="border border-dashed border-outline-variant rounded-xl py-6 flex flex-col items-center justify-center space-y-2 bg-surface-container/20">
        <span class="material-symbols-outlined text-2xl text-on-surface-variant/40">build</span>
        <span class="text-xs text-on-surface-variant/70">No tools configured yet.</span>
        <button @click="openFormModal(null)" type="button" class="text-primary text-xs font-semibold hover:underline">
          + Add your first tool
        </button>
      </div>

      <!-- Tools List -->
      <div v-else class="space-y-2">
        <div v-for="tool in tools" :key="tool.uuid"
          :class="[
            'bg-surface-container rounded-xl border border-outline-variant px-3.5 py-3 flex items-center justify-between gap-3 transition-opacity duration-200',
            tool.is_active ? '' : 'opacity-60'
          ]"
        >
          <!-- Left side icon + details -->
          <div class="flex items-center gap-3 min-w-0">
            <span class="material-symbols-outlined text-[16px] text-on-surface-variant shrink-0">build</span>
            <div class="min-w-0">
              <h4 class="text-sm font-semibold text-on-surface truncate">{{ tool.name }}</h4>
              <p class="text-xs text-on-surface-variant/70 truncate font-mono text-[10px]" :title="tool.description">
                {{ tool.description || 'No description provided' }}
              </p>
            </div>
          </div>

          <!-- Right side actions -->
          <div class="flex items-center gap-3 shrink-0">
            <!-- Active Toggle -->
            <ToggleSwitch :model-value="tool.is_active" @update:model-value="toggleTool(tool)" />

            <!-- Edit Button -->
            <button @click="openFormModal(tool)" type="button" class="p-1 hover:bg-surface-container-high rounded-lg text-on-surface-variant hover:text-on-surface transition-colors" title="Edit tool">
              <span class="material-symbols-outlined text-[16px]">edit</span>
            </button>

            <!-- Delete Button -->
            <button @click="deleteTool(tool)" type="button" class="p-1 hover:bg-surface-container-high rounded-lg text-on-surface-variant hover:text-error transition-colors" title="Delete tool">
              <span class="material-symbols-outlined text-[16px]">delete</span>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Add/Edit Modal -->
    <ToolFormModal
      v-if="formModalOpen"
      :open="formModalOpen"
      :agent-uuid="agentUuid"
      :tool="editingTool"
      @close="closeFormModal"
      @saved="onToolSaved"
    />
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { apiFetch } from '@/composables/useApi'
import ToggleSwitch from '@/components/ui/ToggleSwitch.vue'
import ToolFormModal from '@/components/agents/ToolFormModal.vue'
import { useToastStore } from '@/stores/toast'

const props = defineProps({
  agentUuid: {
    type: String,
    default: null
  }
})

const toast = useToastStore()
const tools = ref([])
const loading = ref(false)
const formModalOpen = ref(false)
const editingTool = ref(null)

async function fetchTools() {
  if (!props.agentUuid) {
    tools.value = []
    return
  }
  loading.value = true
  try {
    tools.value = await apiFetch(`/api/v1/agents/${props.agentUuid}/tools`)
  } catch (err) {
    toast.show(err.message || 'Failed to load tools', 'error')
  } finally {
    loading.value = false
  }
}

watch(() => props.agentUuid, (newVal) => {
  if (newVal) fetchTools()
  else tools.value = []
}, { immediate: true })

function openFormModal(tool = null) {
  editingTool.value = tool
  formModalOpen.value = true
}

function closeFormModal() {
  editingTool.value = null
  formModalOpen.value = false
}

function onToolSaved() {
  closeFormModal()
  fetchTools()
  toast.show('Tool configuration saved', 'success')
}

async function toggleTool(tool) {
  try {
    const updated = await apiFetch(`/api/v1/agents/${props.agentUuid}/tools/${tool.uuid}`, {
      method: 'PUT',
      body: JSON.stringify({ is_active: !tool.is_active })
    })
    const idx = tools.value.findIndex(t => t.uuid === tool.uuid)
    if (idx !== -1) {
      tools.value[idx] = updated
    }
  } catch (err) {
    toast.show(err.message || 'Failed to update tool state', 'error')
  }
}

async function deleteTool(tool) {
  if (!confirm(`Are you sure you want to delete tool "${tool.name}"?`)) return
  try {
    await apiFetch(`/api/v1/agents/${props.agentUuid}/tools/${tool.uuid}`, {
      method: 'DELETE'
    })
    tools.value = tools.value.filter(t => t.uuid !== tool.uuid)
    toast.show('Tool deleted successfully', 'success')
  } catch (err) {
    toast.show(err.message || 'Failed to delete tool', 'error')
  }
}
</script>
