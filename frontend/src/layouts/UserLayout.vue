<template>
  <div class="app-shell">
    <!-- Sidebar -->
    <nav class="sidebar">
      <!-- Logo Container -->
      <div class="logo-container">
        <div class="logo-icon">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect x="2" y="2" width="20" height="20" rx="6" fill="currentColor" fill-opacity="0.12"/>
            <rect x="2" y="2" width="20" height="20" rx="6" stroke="currentColor" stroke-width="1.5"/>
            <circle cx="8" cy="8" r="1.5" fill="currentColor"/>
            <circle cx="16" cy="8" r="1.5" fill="currentColor"/>
            <circle cx="8" cy="16" r="1.5" fill="currentColor"/>
            <circle cx="16" cy="16" r="1.5" fill="currentColor"/>
            <circle cx="12" cy="12" r="2" fill="currentColor"/>
            <line x1="8" y1="8" x2="12" y2="12" stroke="currentColor" stroke-width="1" opacity="0.6"/>
            <line x1="16" y1="8" x2="12" y2="12" stroke="currentColor" stroke-width="1" opacity="0.6"/>
            <line x1="8" y1="16" x2="12" y2="12" stroke="currentColor" stroke-width="1" opacity="0.6"/>
            <line x1="16" y1="16" x2="12" y2="12" stroke="currentColor" stroke-width="1" opacity="0.6"/>
          </svg>
        </div>
        <div class="logo-text">
          <span class="logo-title">AgentIQ</span>
          <span class="logo-subtitle">Neural OS v4.2</span>
        </div>
      </div>

      <!-- Main Section -->
      <div class="menu-section">
        <div class="menu-section-label">Main</div>
        
        <RouterLink to="/analytics" class="nav-item" :class="{ active: $route.path.startsWith('/analytics') }">
          <span class="material-symbols-outlined">dashboard</span>
          <span class="nav-label">Dashboard</span>
        </RouterLink>

        <RouterLink to="/" class="nav-item" :class="{ active: $route.path === '/' }">
          <span class="material-symbols-outlined">psychology</span>
          <span class="nav-label">Neural Engine</span>
        </RouterLink>

        <RouterLink to="/agents" class="nav-item" :class="{ active: $route.path.startsWith('/agents') && !$route.path.endsWith('/analytics') }">
          <span class="material-symbols-outlined">mic</span>
          <span class="nav-label">Voice Lab</span>
        </RouterLink>
      </div>

      <!-- System Section -->
      <div class="menu-section">
        <div class="menu-section-label">System</div>

        <RouterLink to="/profile" class="nav-item" :class="{ active: $route.path === '/profile' }">
          <span class="material-symbols-outlined">settings</span>
          <span class="nav-label">Settings</span>
        </RouterLink>
      </div>

      <div class="spacer" />

      <!-- Add New Agent Action Button -->
      <button class="btn-new-agent" @click="handleNewAgent">
        <span class="material-symbols-outlined">add</span>
        <span>New Agent</span>
      </button>

      <!-- Logout Action -->
      <button class="nav-item logout" @click="logout">
        <span class="material-symbols-outlined">logout</span>
        <span class="nav-label">Logout</span>
      </button>
    </nav>

    <!-- Main Content Area -->
    <div class="content-container">
      <header class="topbar justify-end">
        <div class="topbar-actions">
          <ThemeToggle />
          <div class="notification-bell" @click="showPlaceholderInfo('Notifications')">
            <span class="material-symbols-outlined">notifications</span>
            <span class="notification-dot" />
          </div>
          <div class="user-profile" @click="goToProfile">
            <div class="avatar-container">
              <span class="material-symbols-outlined avatar-icon">face</span>
            </div>
            <span class="profile-username">{{ user?.username || 'OP_ALPHA' }}</span>
          </div>
        </div>
      </header>
      <main class="content">
        <RouterView />
      </main>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'
import ThemeToggle from '@/components/ui/ThemeToggle.vue'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const toast = useToastStore()

const user = computed(() => auth.user)

const searchPlaceholder = computed(() => {
  if (route.path.startsWith('/profile')) return 'Search system commands...'
  if (route.path.startsWith('/analytics')) return 'Search architecture...'
  if (route.path.startsWith('/agents')) return 'Search Fleet...'
  return 'Search parameters...'
})

function logout() {
  auth.logout()
  router.push('/login')
}

function goToProfile() {
  router.push('/profile')
}

function handleNewAgent() {
  if (route.path.startsWith('/agents')) {
    // If already on agents page, trigger query param or custom event
    router.replace({ path: '/agents', query: { new: 'true', t: Date.now() } })
  } else {
    router.push({ path: '/agents', query: { new: 'true' } })
  }
}

function showPlaceholderInfo(feature) {
  toast.show(`${feature} module is loaded in simulation mode.`, 'info')
}
</script>

<style scoped>
.app-shell {
  display: flex;
  height: 100vh;
  width: 100vw;
  background: var(--color-background);
  color: var(--color-on-background);
  font-family: 'Inter', sans-serif;
  overflow: hidden;
}

/* Sidebar styling */
.sidebar {
  width: 250px;
  flex-shrink: 0;
  background: var(--color-surface);
  border-right: 1px solid var(--color-outline-variant);
  padding: 24px 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  z-index: 40;
}

html.dark .sidebar {
  background: rgba(0, 18, 12, 0.95);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border-right: 1px solid rgba(255, 255, 255, 0.05);
}

.logo-container {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 4px 8px 12px;
}

.logo-icon {
  width: 32px;
  height: 32px;
  color: var(--color-primary);
  flex-shrink: 0;
}

html.dark .logo-icon {
  color: #a5d1aa;
  filter: drop-shadow(0 0 6px rgba(165, 209, 170, 0.4));
}

.logo-text {
  display: flex;
  flex-direction: column;
}

.logo-title {
  font-size: 18px;
  font-weight: 700;
  letter-spacing: -0.01em;
  color: var(--color-on-background);
  line-height: 1.1;
}

.logo-subtitle {
  font-size: 11px;
  font-weight: 500;
  color: var(--color-outline);
  font-family: 'JetBrains Mono', monospace;
  letter-spacing: 0.05em;
  margin-top: 1px;
}

.menu-section {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.menu-section-label {
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--color-outline);
  padding: 8px 12px 4px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  border-radius: 12px;
  color: #012d1d; /* Dark green/black text when unselected in light mode */
  text-decoration: none;
  font-size: 14px;
  font-weight: 500;
  background: transparent;
  border: none;
  cursor: pointer;
  font-family: inherit;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  text-align: left;
  width: 100%;
}

html.dark .nav-item {
  color: #beedd9; /* Light green text when unselected in dark mode */
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
  background: #0e6c4a !important; /* Emerald green highlight in light mode */
  font-weight: 600;
}

.nav-item.active,
.nav-item.active .nav-label,
.nav-item.active .material-symbols-outlined {
  color: #ffffff !important; /* White text when selected */
}

html.dark .nav-item.active {
  background: rgba(165, 209, 170, 0.15) !important; /* Soft highlighted green back */
  border-left: 3px solid #a5d1aa;
  border-radius: 4px 12px 12px 4px;
  padding-left: 9px;
}

html.dark .nav-item.active,
html.dark .nav-item.active .nav-label,
html.dark .nav-item.active .material-symbols-outlined {
  color: #ffffff !important; /* White text when active in dark mode too */
}

.nav-item.active .material-symbols-outlined {
  font-variation-settings: 'FILL' 1, 'wght' 500, 'GRAD' 0, 'opsz' 24;
}

.nav-item .material-symbols-outlined {
  font-size: 20px;
  flex-shrink: 0;
}

.disabled-link {
  opacity: 0.6;
  cursor: not-allowed;
}

.disabled-link:hover {
  background: transparent;
  color: var(--color-on-surface-variant);
}

.btn-new-agent {
  background: #0d3c2f;
  color: #a5d1aa;
  border: 1px solid rgba(165, 209, 170, 0.2);
  border-radius: 12px;
  padding: 12px;
  font-size: 14px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  margin-bottom: 8px;
}

.btn-new-agent:hover {
  background: #134e3e;
  box-shadow: 0 0 12px rgba(165, 209, 170, 0.25);
  transform: translateY(-1px);
}

.nav-item.logout {
  color: var(--color-error);
  margin-top: 4px;
}

.nav-item.logout:hover {
  background: var(--color-error-container);
  color: var(--color-error);
}

html.dark .nav-item.logout {
  color: #ffb4ab;
}

html.dark .nav-item.logout:hover {
  background: rgba(255, 180, 171, 0.08);
}

.spacer {
  flex: 1;
}

/* Content Container & Topbar */
.content-container {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-width: 0;
  height: 100vh;
  overflow: hidden;
}

.topbar {
  height: 64px;
  border-bottom: 1px solid var(--color-outline-variant);
  background: var(--color-surface);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  z-index: 30;
  flex-shrink: 0;
}

html.dark .topbar {
  background: rgba(0, 18, 12, 0.7);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.search-box {
  display: flex;
  align-items: center;
  gap: 8px;
  background: var(--color-surface-container-low);
  border: 1px solid var(--color-outline-variant);
  border-radius: 999px;
  padding: 6px 14px;
  width: 280px;
  transition: all 0.2s ease;
}

html.dark .search-box {
  background: rgba(0, 0, 0, 0.15);
  border-color: rgba(255, 255, 255, 0.08);
}

.search-box:focus-within {
  border-color: var(--color-primary);
  width: 320px;
}

html.dark .search-box:focus-within {
  border-color: #a5d1aa;
  box-shadow: 0 0 10px rgba(165, 209, 170, 0.15);
}

.search-icon {
  font-size: 18px;
  color: var(--color-outline);
}

.search-input {
  background: transparent;
  border: none;
  outline: none;
  font-size: 13px;
  color: var(--color-on-background);
  width: 100%;
}

.search-input::placeholder {
  color: var(--color-outline);
  opacity: 0.8;
}

.topbar-nav {
  display: flex;
  align-items: center;
  gap: 20px;
}

.topbar-link {
  font-size: 13px;
  font-weight: 500;
  color: var(--color-on-surface-variant);
  text-decoration: none;
  transition: color 0.2s ease;
}

.topbar-link:hover {
  color: var(--color-on-surface);
}

.topbar-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}

.notification-bell {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  color: var(--color-on-surface-variant);
  cursor: pointer;
  transition: background 0.2s ease;
}

.notification-bell:hover {
  background: var(--color-surface-container-high);
  color: var(--color-on-surface);
}

html.dark .notification-bell:hover {
  background: rgba(255, 255, 255, 0.05);
}

.notification-dot {
  position: absolute;
  top: 8px;
  right: 8px;
  width: 7px;
  height: 7px;
  background: var(--color-error);
  border-radius: 50%;
  border: 1.5px solid var(--color-surface);
}

html.dark .notification-dot {
  background: #ff4d4d;
  border-color: #00120b;
}

.user-profile {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 4px 8px;
  border-radius: 999px;
  cursor: pointer;
  transition: background 0.2s ease;
}

.user-profile:hover {
  background: var(--color-surface-container-high);
}

html.dark .user-profile:hover {
  background: rgba(255, 255, 255, 0.05);
}

.avatar-container {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--color-primary-container);
  color: var(--color-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

html.dark .avatar-container {
  background: rgba(165, 209, 170, 0.15);
  color: #a5d1aa;
}

.avatar-icon {
  font-size: 20px;
}

.profile-username {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-on-surface);
  font-family: 'JetBrains Mono', monospace;
  letter-spacing: 0.02em;
}

.content {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  background: var(--color-background);
}
</style>
