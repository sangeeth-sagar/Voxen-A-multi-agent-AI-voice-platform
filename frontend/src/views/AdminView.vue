<template>
  <AppLayout>
    <div class="h-full flex flex-col p-6 overflow-hidden">

      <!-- Page header -->
      <div class="flex items-center justify-between mb-6 shrink-0">
        <div>
          <div class="flex items-center gap-3">
            <div class="w-9 h-9 rounded-xl bg-error/15 border border-error/30 flex items-center justify-center">
              <span class="material-symbols-outlined text-error text-[18px] icon-filled">admin_panel_settings</span>
            </div>
            <div>
              <h1 class="font-sans text-2xl font-bold text-white tracking-tight">Command Center</h1>
              <p class="font-mono text-[10px] text-on-surface-variant/50 uppercase tracking-widest mt-0.5">
                Admin access · {{ currentTime }}
              </p>
            </div>
          </div>
        </div>
        <!-- System status strip -->
        <div class="hidden md:flex items-center gap-4">
          <div class="flex items-center gap-2 px-3 py-1.5 bg-green-900/20 border border-green-500/20 rounded-full">
            <span class="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
            <span class="font-mono text-[10px] text-green-400 uppercase tracking-wider">All Systems Nominal</span>
          </div>
        </div>
      </div>

      <!-- Tab navigation -->
      <div class="flex gap-1 mb-6 shrink-0 border-b border-white/5 pb-1">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          @click="activeTab = tab.key"
          :class="[
            'flex items-center gap-2 px-5 py-2.5 rounded-t-xl font-mono text-[11px] uppercase tracking-wider transition-all',
            activeTab === tab.key
              ? 'bg-primary/15 text-primary border border-primary/20 border-b-transparent -mb-px'
              : 'text-on-surface-variant hover:text-white hover:bg-white/5'
          ]"
        >
          <span class="material-symbols-outlined text-[15px]">{{ tab.icon }}</span>
          {{ tab.label }}
          <span v-if="tab.count !== undefined"
            class="px-1.5 py-0.5 rounded-full text-[9px] font-bold"
            :class="activeTab === tab.key ? 'bg-primary/20 text-primary' : 'bg-white/5 text-on-surface-variant'">
            {{ tab.count }}
          </span>
        </button>
      </div>

      <!-- Tab content -->
      <div class="flex-1 overflow-y-auto">

        <!-- TAB 1: Overview -->
        <div v-if="activeTab === 'overview'">
          <AdminStats :stats="stats" />
        </div>

        <!-- TAB 2: Users -->
        <div v-if="activeTab === 'users'">
          <UsersTable :users="users" @refresh="fetchAll" />
        </div>

        <!-- TAB 3: Jobs -->
        <div v-if="activeTab === 'jobs'">
          <JobsTable :jobs="jobs" @refresh="fetchJobs" />
        </div>

      </div>
    </div>
  </AppLayout>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import AppLayout from '@/components/layout/AppLayout.vue'
import AdminStats from '@/components/admin/AdminStats.vue'
import UsersTable from '@/components/admin/UsersTable.vue'
import JobsTable from '@/components/admin/JobsTable.vue'
import { apiFetch } from '@/composables/useApi'
import { useToastStore } from '@/stores/toast'

const toast = useToastStore()
const activeTab = ref('overview')

const stats = ref({})
const users = ref([])
const jobs = ref([])
const loading = ref(false)

// Live clock
const currentTime = ref('')
let clockInterval = null
function updateClock() {
  currentTime.value = new Date().toLocaleTimeString('en-US', {
    hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false
  })
}

const tabs = computed(() => [
  { key: 'overview', icon: 'bar_chart', label: 'Overview' },
  { key: 'users',    icon: 'group',     label: 'Users',  count: users.value.length },
  { key: 'jobs',     icon: 'work',      label: 'Jobs',   count: jobs.value.length },
])

async function fetchStats() {
  try { stats.value = await apiFetch('/api/v1/admin/stats') }
  catch (e) { toast.show('Failed to load stats', 'error') }
}

async function fetchUsers() {
  try { users.value = await apiFetch('/api/v1/admin/users') }
  catch (e) { toast.show('Failed to load users', 'error') }
}

async function fetchJobs() {
  try { jobs.value = await apiFetch('/api/v1/admin/jobs') }
  catch (e) { toast.show('Failed to load jobs', 'error') }
}

async function fetchAll() {
  loading.value = true
  await Promise.all([fetchStats(), fetchUsers(), fetchJobs()])
  loading.value = false
}

onMounted(() => {
  fetchAll()
  updateClock()
  clockInterval = setInterval(updateClock, 1000)
})

onUnmounted(() => clearInterval(clockInterval))
</script>
