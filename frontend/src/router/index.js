import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  // Public
  { path: '/login',    name: 'Login',    component: () => import('@/views/LoginView.vue'),    meta: { guest: true } },
  { path: '/register', name: 'Register', component: () => import('@/views/RegisterView.vue'), meta: { guest: true } },

  // User app — requires auth
  {
    path: '/',
    component: () => import('@/layouts/UserLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      { path: '',        name: 'Voice',    component: () => import('@/views/VoiceView.vue') },
      { path: 'agents',  name: 'Agents',   component: () => import('@/views/AgentsView.vue') },
      { path: 'analytics', name: 'Analytics', component: () => import('@/views/MetricsDashboardView.vue') },
      { path: 'agents/:uuid/analytics', name: 'AgentAnalytics', component: () => import('@/views/MetricsDashboardView.vue') },
      { path: 'profile', name: 'Profile',  component: () => import('@/views/ProfileView.vue') },
    ]
  },

  // Admin app — requires superadmin
  {
    path: '/admin',
    component: () => import('@/layouts/AdminLayout.vue'),
    meta: { requiresAuth: true, requiresSuperadmin: true },
    children: [
      { path: '',        name: 'AdminDashboard', component: () => import('@/views/admin/DashboardView.vue') },
      { path: 'users',   name: 'AdminUsers',     component: () => import('@/views/admin/UsersView.vue') },
      { path: 'agents',  name: 'AdminAgents',    component: () => import('@/views/admin/AgentsView.vue') },
    ]
  },

  // Fallback
  { path: '/:pathMatch(.*)*', redirect: '/' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  try {
    const auth = useAuthStore()
    if (to.meta.requiresAuth && !auth.isLoggedIn) return next('/login')
    if (to.meta.guest && auth.isLoggedIn) {
      return next(auth.isSuperadmin ? '/admin' : '/')
    }
    if (to.meta.requiresSuperadmin && !auth.isSuperadmin) return next('/')
    next()
  } catch (e) {
    console.error('Router guard error:', e)
    try { localStorage.removeItem('user') } catch (_) {}
    next('/login')
  }
})

// Refresh user data after each navigation
router.afterEach(async () => {
  const auth = useAuthStore()
  if (auth.isLoggedIn) {
    try { await auth.fetchFreshUser() } catch (_) {}
  }
})

export default router
