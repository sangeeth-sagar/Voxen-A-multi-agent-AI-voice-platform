import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  { path: '/', redirect: '/workspace' },
  { path: '/login', component: () => import('@/views/LoginView.vue'), meta: { guest: true } },
  { path: '/register', component: () => import('@/views/RegisterView.vue'), meta: { guest: true } },
  { path: '/workspace', component: () => import('@/views/WorkspaceView.vue'), meta: { auth: true } },
  { path: '/voice', component: () => import('@/views/VoiceView.vue'), meta: { auth: true } },
  { path: '/agents', component: () => import('@/views/AgentsView.vue'), meta: { auth: true } },
  { path: '/profile', component: () => import('@/views/ProfileView.vue'), meta: { auth: true } },
  { path: '/admin', component: () => import('@/views/AdminView.vue'), meta: { auth: true, admin: true } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
  const auth = useAuthStore()
  if (to.meta.auth && !auth.isLoggedIn) return '/login'
  if (to.meta.guest && auth.isLoggedIn) return '/workspace'
  if (to.meta.admin && !auth.isAdmin) return '/workspace'
})

// Navigation guard to fetch fresh user data on each navigation
router.afterEach(async () => {
  const auth = useAuthStore()
  if (auth.isLoggedIn) {
    await auth.fetchFreshUser()
  }
})

export default router
