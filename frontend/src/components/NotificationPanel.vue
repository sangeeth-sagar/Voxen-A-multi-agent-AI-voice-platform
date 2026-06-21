<template>
  <Teleport to="body">
    <Transition name="notif-fade">
      <div
        v-if="isOpen"
        class="fixed inset-0 bg-black/40 z-40"
        @click="$emit('close')"
      />
    </Transition>

    <Transition name="notif-slide">
      <div
        v-if="isOpen"
        class="fixed top-0 right-0 h-full z-50 bg-surface-container
               shadow-2xl flex flex-col"
        style="width: 320px;"
      >
        <!-- Header -->
        <div class="flex items-center justify-between px-5 py-4 border-b border-outline-variant">
          <h2 class="text-sm font-mono uppercase tracking-widest text-on-surface">
            Notifications
          </h2>
          <button @click="$emit('close')"
            class="w-8 h-8 rounded-full flex items-center justify-center
                   hover:bg-surface-container-high transition-colors">
            <span class="material-symbols-outlined text-lg">close</span>
          </button>
        </div>

        <!-- List -->
        <div class="flex-1 overflow-y-auto px-3 py-3">
          <div v-if="notifications.length === 0"
               class="flex flex-col items-center justify-center h-full text-center px-6">
            <span class="material-symbols-outlined text-4xl text-on-surface-variant opacity-30 mb-2">
              notifications_off
            </span>
            <p class="text-xs text-on-surface-variant">No notifications yet this session</p>
          </div>

          <TransitionGroup name="notif-item" tag="div" class="flex flex-col gap-2">
            <div
              v-for="n in notifications"
              :key="n.id"
              class="rounded-lg p-3 border-l-2 bg-surface-container-low"
              :class="severityBorderClass(n.severity)"
            >
              <div class="flex items-start gap-2">
                <span class="material-symbols-outlined text-base mt-0.5"
                      :class="severityIconClass(n.severity)">
                  {{ severityIcon(n.severity) }}
                </span>
                <div class="flex-1 min-w-0">
                  <p class="text-xs font-medium text-on-surface">{{ n.title }}</p>
                  <p class="text-[11px] text-on-surface-variant mt-0.5 leading-relaxed">
                    {{ n.message }}
                  </p>
                  <p class="text-[10px] text-on-surface-variant opacity-60 mt-1">
                    {{ formatTime(n.created_at) }}
                  </p>
                </div>
              </div>
            </div>
          </TransitionGroup>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
defineProps({
  isOpen: { type: Boolean, default: false },
  notifications: { type: Array, default: () => [] },
})
defineEmits(['close'])

function severityIcon(severity) {
  return {
    success: 'check_circle',
    error: 'error',
    warning: 'warning',
    info: 'info',
  }[severity] || 'info'
}

function severityIconClass(severity) {
  return {
    success: 'text-green-500',
    error: 'text-red-500',
    warning: 'text-amber-500',
    info: 'text-blue-400',
  }[severity] || 'text-blue-400'
}

function severityBorderClass(severity) {
  return {
    success: 'border-green-500',
    error: 'border-red-500',
    warning: 'border-amber-500',
    info: 'border-blue-400',
  }[severity] || 'border-blue-400'
}

function formatTime(isoString) {
  const date = new Date(isoString)
  const now = new Date()
  const diffMs = now - date
  const diffMin = Math.floor(diffMs / 60000)
  if (diffMin < 1) return 'Just now'
  if (diffMin < 60) return `${diffMin}m ago`
  const diffHr = Math.floor(diffMin / 60)
  return `${diffHr}h ago`
}
</script>

<style scoped>
.notif-slide-enter-active,
.notif-slide-leave-active {
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
.notif-slide-enter-from,
.notif-slide-leave-to {
  transform: translateX(100%);
}

.notif-fade-enter-active,
.notif-fade-leave-active {
  transition: opacity 0.25s ease;
}
.notif-fade-enter-from,
.notif-fade-leave-to {
  opacity: 0;
}

.notif-item-enter-active {
  transition: all 0.3s ease;
}
.notif-item-enter-from {
  opacity: 0;
  transform: translateX(20px);
}
.notif-item-move {
  transition: transform 0.3s ease;
}
</style>
