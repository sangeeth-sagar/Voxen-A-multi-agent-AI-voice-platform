<template>
  <Teleport to="body">
    <div class="fixed bottom-6 right-6 z-[200] flex flex-col gap-3 pointer-events-none">
      <TransitionGroup name="toast">
        <div
          v-for="toast in toasts"
          :key="toast.id"
          :class="[
            'pointer-events-auto flex items-center gap-3 px-5 py-3.5 rounded-xl border font-sans text-sm font-medium shadow-xl backdrop-blur-md',
            toast.type === 'success' ? 'bg-success/15 border-success/30 text-success' :
            toast.type === 'error' ? 'bg-error-container border-error/30 text-error' :
            'bg-surface-container border-outline-variant text-on-surface'
          ]"
        >
          <span class="material-symbols-outlined text-base icon-filled">
            {{ toast.type === 'success' ? 'check_circle' : toast.type === 'error' ? 'error' : 'info' }}
          </span>
          {{ toast.message }}
          <button @click="remove(toast.id)" class="ml-2 opacity-60 hover:opacity-100 transition-opacity">
            <span class="material-symbols-outlined text-sm">close</span>
          </button>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<script setup>
import { storeToRefs } from 'pinia'
import { useToastStore } from '@/stores/toast'
const { toasts } = storeToRefs(useToastStore())
const { remove } = useToastStore()
</script>

<style scoped>
.toast-enter-active { transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); }
.toast-leave-active { transition: all 0.2s ease; }
.toast-enter-from { transform: translateX(100%); opacity: 0; }
.toast-leave-to { transform: translateX(100%); opacity: 0; }
</style>
