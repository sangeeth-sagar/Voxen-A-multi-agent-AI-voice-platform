<template>
  <div class="admin-users p-6">
    <header class="flex items-center justify-between mb-5">
      <div>
        <h1 class="font-sans text-2xl font-bold text-white tracking-tight">
          Users <span class="count text-on-surface-variant/40 font-mono text-base ml-2">{{ users.length }}</span>
        </h1>
        <p class="font-mono text-[11px] text-on-surface-variant/60 uppercase tracking-wider mt-1">
          Manage operators and permissions
        </p>
      </div>
      <button @click="fetchUsers" class="p-2.5 bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl transition-colors text-on-surface-variant hover:text-white">
        <span class="material-symbols-outlined text-[18px]">refresh</span>
      </button>
    </header>

    <div class="glass-panel rounded-2xl overflow-hidden">
      <table class="w-full">
        <thead>
          <tr class="border-b border-white/5 bg-white/[0.02]">
            <th class="th">ID</th>
            <th class="th">Email</th>
            <th class="th">Name</th>
            <th class="th">Agents</th>
            <th class="th">Status</th>
            <th class="th">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading">
            <td :colspan="6" class="td text-center text-on-surface-variant/40 py-10">
              <span class="material-symbols-outlined text-3xl animate-spin">refresh</span>
            </td>
          </tr>
          <tr v-else-if="users.length === 0">
            <td :colspan="6" class="td text-center text-on-surface-variant/30 py-10 font-mono text-sm">No users found</td>
          </tr>
          <tr v-for="user in users" :key="user.id" class="row border-b border-white/5">
            <td class="td font-mono text-xs text-on-surface-variant/70">{{ user.id }}</td>
            <td class="td text-white">{{ user.email }}</td>
            <td class="td text-on-surface-variant">{{ user.full_name || '—' }}</td>
            <td class="td font-mono text-primary">{{ user.agent_count || 0 }}</td>
            <td class="td">
              <span :class="['status-badge', user.is_active ? 'active' : 'inactive']">
                {{ user.is_active ? 'Active' : 'Suspended' }}
              </span>
            </td>
            <td class="td">
              <div class="flex items-center gap-2">
                <button @click="toggleUser(user.id)" class="btn-sm" :title="user.is_active ? 'Suspend' : 'Reactivate'">
                  {{ user.is_active ? 'Suspend' : 'Reactivate' }}
                </button>
                <button v-if="!user.is_superadmin" @click="promoteUser(user.id)" class="btn-sm" title="Make admin">
                  Make Admin
                </button>
                <span v-else class="font-mono text-[10px] text-error uppercase tracking-wider">Admin</span>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { apiFetch } from '@/composables/useApi'
import { useToastStore } from '@/stores/toast'

const toast = useToastStore()
const users = ref([])
const loading = ref(false)
const token = localStorage.getItem('token')
const headers = { Authorization: `Bearer ${token}` }

async function fetchUsers() {
  loading.value = true
  try {
    const res = await fetch(`${import.meta.env.VITE_API_URL}/api/v1/admin/users`, { headers })
    if (res.ok) users.value = await res.json()
    else toast.show('Failed to load users', 'error')
  } catch (e) {
    toast.show(e.message, 'error')
  } finally {
    loading.value = false
  }
}

async function toggleUser(id) {
  try {
    await fetch(`${import.meta.env.VITE_API_URL}/api/v1/admin/users/${id}/toggle`, {
      method: 'PATCH', headers
    })
    toast.show('User status updated', 'success')
    await fetchUsers()
  } catch (e) {
    toast.show(e.message, 'error')
  }
}

async function promoteUser(id) {
  if (!confirm('Promote this user to superadmin?')) return
  try {
    await fetch(`${import.meta.env.VITE_API_URL}/api/v1/admin/users/${id}/promote`, {
      method: 'PATCH', headers
    })
    toast.show('User promoted to superadmin', 'success')
    await fetchUsers()
  } catch (e) {
    toast.show(e.message, 'error')
  }
}

onMounted(fetchUsers)
</script>

<style scoped>
.glass-panel {
  background: rgba(17, 19, 25, 0.7);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.th {
  padding: 14px 16px;
  text-align: left;
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: rgba(199, 196, 215, 0.5);
  font-weight: 600;
}

.td {
  padding: 14px 16px;
  font-size: 13px;
}

.row {
  transition: background 0.15s ease;
}

.row:hover {
  background: rgba(255, 255, 255, 0.02);
}

.status-badge {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 999px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.status-badge.active {
  background: rgba(74, 222, 128, 0.12);
  color: #4ade80;
  border: 1px solid rgba(74, 222, 128, 0.3);
}

.status-badge.inactive {
  background: rgba(255, 180, 171, 0.12);
  color: #ffb4ab;
  border: 1px solid rgba(255, 180, 171, 0.3);
}

.btn-sm {
  padding: 6px 12px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.08);
  color: #c7c4d7;
  font-size: 11px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.15s ease;
  font-family: inherit;
}

.btn-sm:hover {
  background: rgba(192, 193, 255, 0.12);
  color: #c0c1ff;
}
</style>
