<template>
  <div class="admin-shell">
    <nav class="admin-sidebar">
      <div class="admin-logo">
        <span class="material-symbols-outlined">shield</span>
        <div>
          <div class="admin-logo-text">AgentIQ</div>
          <div class="admin-logo-sub">Admin Console</div>
        </div>
      </div>

      <RouterLink to="/admin" class="nav-item" :class="{ active: $route.path === '/admin' }">
        <span class="material-symbols-outlined">dashboard</span>
        <span class="nav-label">Dashboard</span>
      </RouterLink>

      <RouterLink to="/admin/users" class="nav-item" :class="{ active: $route.path === '/admin/users' }">
        <span class="material-symbols-outlined">group</span>
        <span class="nav-label">Users</span>
      </RouterLink>

      <RouterLink to="/admin/agents" class="nav-item" :class="{ active: $route.path === '/admin/agents' }">
        <span class="material-symbols-outlined">smart_toy</span>
        <span class="nav-label">All Agents</span>
      </RouterLink>

      <div class="spacer" />

      <ThemeToggle />

      <RouterLink to="/" class="nav-item">
        <span class="material-symbols-outlined">arrow_back</span>
        <span class="nav-label">User App</span>
      </RouterLink>

      <button class="nav-item logout" @click="logout">
        <span class="material-symbols-outlined">logout</span>
        <span class="nav-label">Logout</span>
      </button>
    </nav>

    <main class="admin-content">
      <RouterView />
    </main>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import ThemeToggle from '@/components/ui/ThemeToggle.vue'

const router = useRouter()
const auth = useAuthStore()

function logout() {
  auth.logout()
  router.push('/login')
}
</script>

<style scoped>
.admin-shell {
  display: flex;
  height: 100vh;
  width: 100vw;
  background: var(--color-background);
  color: var(--color-on-background);
  font-family: 'Inter', sans-serif;
  overflow: hidden;
}

.admin-sidebar {
  width: 240px;
  flex-shrink: 0;
  background: var(--color-surface);
  border-right: 1px solid var(--color-outline-variant);
  padding: 24px 16px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

html.dark .admin-sidebar {
  background: linear-gradient(180deg, rgba(40, 20, 12, 0.7) 0%, rgba(0, 23, 16, 0.7) 100%);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border-right: 1px solid rgba(255, 180, 171, 0.12);
}

.admin-logo {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 4px 12px 24px;
  color: var(--color-error);
}

.admin-logo .material-symbols-outlined {
  font-size: 28px;
  color: var(--color-error);
}

.admin-logo-text {
  font-size: 20px;
  font-weight: 700;
  color: var(--color-on-surface);
  letter-spacing: -0.01em;
}

.admin-logo-sub {
  font-family: 'JetBrains Mono', monospace;
  font-size: 9px;
  color: var(--color-error);
  text-transform: uppercase;
  letter-spacing: 0.2em;
  margin-top: 2px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  border-radius: 12px;
  color: var(--color-on-surface-variant);
  text-decoration: none;
  font-size: 14px;
  font-weight: 500;
  background: transparent;
  border: none;
  cursor: pointer;
  font-family: inherit;
  transition: background 0.15s ease, color 0.15s ease;
  text-align: left;
  width: 100%;
}

.nav-item:hover {
  background: var(--color-surface-container-high);
  color: var(--color-on-surface);
}

html.dark .nav-item:hover {
  background: rgba(255, 255, 255, 0.05);
  color: var(--color-on-surface);
}

.nav-item.active {
  background: var(--color-error-container);
  color: var(--color-error);
}

html.dark .nav-item.active {
  background: rgba(255, 77, 77, 0.12);
  color: #ffb4ab;
}

.nav-item.active .material-symbols-outlined {
  font-variation-settings: 'FILL' 1, 'wght' 400, 'GRAD' 0, 'opsz' 24;
}

.nav-item .material-symbols-outlined {
  font-size: 20px;
  flex-shrink: 0;
}

.nav-item.logout {
  color: var(--color-error);
  opacity: 0.7;
}

.nav-item.logout:hover {
  background: var(--color-error-container);
  color: var(--color-error);
  opacity: 1;
}

html.dark .nav-item.logout {
  color: rgba(255, 180, 171, 0.7);
}

html.dark .nav-item.logout:hover {
  background: rgba(255, 180, 171, 0.08);
  color: #ffb4ab;
}

.spacer {
  flex: 1;
}

.admin-content {
  flex: 1;
  min-width: 0;
  height: 100vh;
  overflow: auto;
}
</style>
