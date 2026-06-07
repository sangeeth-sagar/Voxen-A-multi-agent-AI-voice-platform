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

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.mount('#app')
