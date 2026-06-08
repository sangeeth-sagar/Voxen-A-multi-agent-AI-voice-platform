import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import './assets/main.css'

// Clears any corrupted localStorage values that would crash JSON.parse
;['user', 'token'].forEach(key => {
  try {
    const val = localStorage.getItem(key)
    if (val === 'undefined' || val === 'null') {
      localStorage.removeItem(key)
    }
  } catch {
    // localStorage unavailable — ignore
  }
})

// Global error boundary — prevents Chrome from killing the page
window.addEventListener('unhandledrejection', (event) => {
  console.error('[VOXEN] Unhandled promise rejection:', event.reason)
  event.preventDefault()
})

window.addEventListener('error', (event) => {
  console.error('[VOXEN] Global error:', event.message, 'at', event.filename, event.lineno)
})

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.mount('#app')
