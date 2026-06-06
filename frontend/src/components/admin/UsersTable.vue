<template>
  <div class="space-y-4">
    <!-- Search + filter -->
    <div class="flex items-center gap-3">
      <div class="flex-1 relative">
        <span class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant/40 text-[18px]">search</span>
        <input
          v-model="search"
          type="text"
          placeholder="Search users…"
          class="w-full bg-white/5 border border-white/10 rounded-xl pl-10 pr-4 py-2.5 text-sm text-on-surface placeholder:text-on-surface-variant/40 outline-none focus:border-primary/30 transition-colors"
        />
      </div>
      <select v-model="roleFilter"
        class="bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 font-mono text-[11px] text-on-surface-variant outline-none cursor-pointer">
        <option value="">All Roles</option>
        <option value="admin">Admin</option>
        <option value="user">User</option>
      </select>
    </div>

    <!-- Table -->
    <div class="glass-panel rounded-2xl overflow-hidden">
      <table class="w-full">
        <thead>
          <tr class="border-b border-white/5 bg-white/[0.02]">
            <th v-for="col in cols" :key="col" class="px-5 py-3.5 text-left font-mono text-[10px] uppercase tracking-widest text-on-surface-variant/50">{{ col }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="filtered.length === 0">
            <td :colspan="cols.length" class="px-5 py-10 text-center font-mono text-sm text-on-surface-variant/30">No users found</td>
          </tr>
          <tr v-for="user in filtered" :key="user.uuid"
            class="border-b border-white/5 hover:bg-white/[0.02] transition-colors">
            <td class="px-5 py-4">
              <div class="flex items-center gap-3">
                <div class="w-8 h-8 rounded-full bg-primary/10 border border-primary/20 flex items-center justify-center">
                  <span class="material-symbols-outlined text-primary text-[14px] icon-filled">person</span>
                </div>
                <div>
                  <p class="text-sm font-medium text-white">{{ user.username }}</p>
                  <p class="font-mono text-[10px] text-on-surface-variant/50">{{ user.email }}</p>
                </div>
              </div>
            </td>
            <td class="px-5 py-4">
              <span :class="[
                'px-2.5 py-1 rounded-full font-mono text-[10px] uppercase font-bold',
                user.role === 'admin'
                  ? 'bg-error/15 text-error border border-error/30'
                  : 'bg-primary/10 text-primary border border-primary/20'
              ]">{{ user.role }}</span>
            </td>
            <td class="px-5 py-4">
              <span :class="[
                'px-2.5 py-1 rounded-full font-mono text-[10px] uppercase',
                user.is_active
                  ? 'bg-green-900/30 text-green-400 border border-green-500/20'
                  : 'bg-error/10 text-error border border-error/20'
              ]">{{ user.is_active ? 'Active' : 'Suspended' }}</span>
            </td>
            <td class="px-5 py-4 font-mono text-sm text-on-surface-variant">{{ user.total_jobs }}</td>
            <td class="px-5 py-4 font-mono text-[11px] text-on-surface-variant/50">
              {{ user.last_login ? new Date(user.last_login).toLocaleDateString() : 'Never' }}
            </td>
            <td class="px-5 py-4">
              <div class="flex items-center gap-2">
                <!-- Role toggle -->
                <button @click="toggleRole(user)"
                  class="p-1.5 hover:bg-white/5 rounded-lg transition-colors text-on-surface-variant hover:text-primary"
                  :title="user.role === 'admin' ? 'Demote to user' : 'Promote to admin'">
                  <span class="material-symbols-outlined text-[16px]">
                    {{ user.role === 'admin' ? 'person_remove' : 'admin_panel_settings' }}
                  </span>
                </button>
                <!-- Suspend/activate -->
                <button @click="toggleActive(user)"
                  class="p-1.5 hover:bg-white/5 rounded-lg transition-colors text-on-surface-variant"
                  :class="user.is_active ? 'hover:text-tactical-amber' : 'hover:text-green-400'">
                  <span class="material-symbols-outlined text-[16px]">{{ user.is_active ? 'person_off' : 'person_check' }}</span>
                </button>
                <!-- Password reset -->
                <button @click="openReset(user)"
                  class="p-1.5 hover:bg-white/5 rounded-lg transition-colors text-on-surface-variant hover:text-secondary"
                  title="Reset password">
                  <span class="material-symbols-outlined text-[16px]">key</span>
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Password Reset Modal -->
    <Transition name="modal">
      <div v-if="resetModal.open" class="fixed inset-0 z-[100] flex items-center justify-center">
        <div @click="resetModal.open = false" class="absolute inset-0 bg-black/70 backdrop-blur-sm" />
        <div class="modal-content relative z-10 glass-panel rounded-2xl p-7 w-full max-w-sm mx-4">
          <h3 class="font-sans font-bold text-lg text-white mb-1">Reset Password</h3>
          <p class="font-mono text-[11px] text-on-surface-variant/60 mb-5 uppercase">
            For: <span class="text-primary">{{ resetModal.user?.username }}</span>
          </p>
          <div class="space-y-4">
            <div>
              <label class="block font-mono text-[10px] uppercase tracking-widest text-on-surface-variant mb-1.5">New Password</label>
              <input v-model="resetModal.password" type="password" placeholder="min. 8 characters"
                class="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-on-surface outline-none focus:border-primary/30 transition-colors" />
            </div>
            <div>
              <label class="block font-mono text-[10px] uppercase tracking-widest text-on-surface-variant mb-1.5">Confirm Password</label>
              <input v-model="resetModal.confirm" type="password" placeholder="repeat new password"
                class="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-on-surface outline-none focus:border-primary/30 transition-colors" />
            </div>
            <p v-if="resetModal.error" class="text-error text-sm">{{ resetModal.error }}</p>
          </div>
          <div class="flex gap-3 mt-6">
            <button @click="resetModal.open = false"
              class="flex-1 py-2.5 bg-white/5 hover:bg-white/10 rounded-xl text-sm font-medium transition-colors">
              Cancel
            </button>
            <button @click="submitReset" :disabled="resetModal.loading"
              class="flex-1 py-2.5 btn-primary rounded-xl text-sm font-semibold flex items-center justify-center gap-2 disabled:opacity-50">
              <span v-if="resetModal.loading" class="material-symbols-outlined text-sm animate-spin">refresh</span>
              Reset Password
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, computed, reactive } from 'vue'
import { apiFetch } from '@/composables/useApi'
import { useToastStore } from '@/stores/toast'

const props = defineProps({ users: { type: Array, default: () => [] } })
const emit = defineEmits(['refresh'])
const toast = useToastStore()

const search = ref('')
const roleFilter = ref('')
const cols = ['Operator', 'Role', 'Status', 'Jobs', 'Last Login', 'Actions']

const filtered = computed(() =>
  props.users.filter(u => {
    const q = search.value.toLowerCase()
    const matchSearch = !q || u.username.toLowerCase().includes(q) || u.email.toLowerCase().includes(q)
    const matchRole = !roleFilter.value || u.role === roleFilter.value
    return matchSearch && matchRole
  })
)

const resetModal = reactive({ open: false, user: null, password: '', confirm: '', error: '', loading: false })

function openReset(user) {
  Object.assign(resetModal, { open: true, user, password: '', confirm: '', error: '', loading: false })
}

async function submitReset() {
  if (resetModal.password !== resetModal.confirm) { resetModal.error = 'Passwords do not match'; return }
  if (resetModal.password.length < 8) { resetModal.error = 'Minimum 8 characters'; return }
  resetModal.loading = true; resetModal.error = ''
  try {
    await apiFetch(`/api/v1/admin/users/${resetModal.user.uuid}/reset-password`, {
      method: 'POST',
      body: JSON.stringify({ new_password: resetModal.password }),
    })
    toast.show(`Password reset for ${resetModal.user.username}`, 'success')
    resetModal.open = false
  } catch (e) {
    resetModal.error = e.message
  } finally {
    resetModal.loading = false
  }
}

async function toggleRole(user) {
  const newRole = user.role === 'admin' ? 'user' : 'admin'
  try {
    await apiFetch(`/api/v1/admin/users/${user.uuid}`, {
      method: 'PATCH',
      body: JSON.stringify({ role: newRole }),
    })
    toast.show(`${user.username} → ${newRole}`, 'success')
    emit('refresh')
  } catch (e) { toast.show(e.message, 'error') }
}

async function toggleActive(user) {
  try {
    await apiFetch(`/api/v1/admin/users/${user.uuid}`, {
      method: 'PATCH',
      body: JSON.stringify({ is_active: !user.is_active }),
    })
    toast.show(`${user.username} ${user.is_active ? 'suspended' : 'activated'}`, 'success')
    emit('refresh')
  } catch (e) { toast.show(e.message, 'error') }
}
</script>
