<template>
  <div class="app-shell">
    <nav class="sidebar">
      <div class="logo">AgentIQ</div>

      <RouterLink to="/" class="nav-item" :class="{ active: $route.path === '/' }">
        <span class="material-symbols-outlined">mic</span>
        <span class="nav-label">Voice</span>
      </RouterLink>

      <RouterLink to="/agents" class="nav-item" :class="{ active: $route.name === 'Agents' }">
        <span class="material-symbols-outlined">smart_toy</span>
        <span class="nav-label">Agents</span>
      </RouterLink>

      <RouterLink to="/analytics" class="nav-item" :class="{ active: $route.name === 'Analytics' || $route.name === 'AgentAnalytics' }">
        <span class="material-symbols-outlined">bar_chart</span>
        <span class="nav-label">Analytics</span>
      </RouterLink>

      <RouterLink to="/profile" class="nav-item" :class="{ active: $route.path === '/profile' }">
        <span class="material-symbols-outlined">person</span>
        <span class="nav-label">Profile</span>
      </RouterLink>

      <div class="spacer" />

      <button class="nav-item logout" @click="logout">
        <span class="material-symbols-outlined">logout</span>
        <span class="nav-label">Logout</span>
      </button>
    </nav>

    <main class="content">
      <RouterView />
    </main>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()

function logout() {
  auth.logout()
  router.push('/login')
}
</script>

<style scoped>
.app-shell {
  display: flex;
  height: 100vh;
  width: 100vw;
  background: #0c0e14;
  color: #e2e2eb;
  font-family: 'Inter', sans-serif;
  overflow: hidden;
}

.sidebar {
  width: 220px;
  flex-shrink: 0;
  background: rgba(17, 19, 25, 0.7);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border-right: 1px solid rgba(255, 255, 255, 0.08);
  padding: 24px 16px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.logo {
  font-size: 22px;
  font-weight: 700;
  letter-spacing: -0.01em;
  color: #fff;
  padding: 4px 12px 24px;
  background: linear-gradient(135deg, #c0c1ff, #d0bcff);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  border-radius: 12px;
  color: #c7c4d7;
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
  background: rgba(255, 255, 255, 0.05);
  color: #fff;
}

.nav-item.active {
  background: rgba(192, 193, 255, 0.1);
  color: #c0c1ff;
}

.nav-item.active .material-symbols-outlined {
  font-variation-settings: 'FILL' 1, 'wght' 400, 'GRAD' 0, 'opsz' 24;
}

.nav-item .material-symbols-outlined {
  font-size: 20px;
  flex-shrink: 0;
}

.nav-item.logout {
  color: rgba(255, 180, 171, 0.7);
}

.nav-item.logout:hover {
  background: rgba(255, 180, 171, 0.08);
  color: #ffb4ab;
}

.spacer {
  flex: 1;
}

.content {
  flex: 1;
  min-width: 0;
  height: 100vh;
  overflow: auto;
}
</style>
