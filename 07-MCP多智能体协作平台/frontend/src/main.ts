import { createApp } from 'vue'
import { createPinia } from 'pinia'
import piniaPluginPersistedstate from 'pinia-plugin-persistedstate'
import App from './App.vue'
import router from './router'
import './assets/styles/main.css'

const app = createApp(App)

const pinia = createPinia()

// Wrap persistedstate plugin to catch corrupted localStorage data
try {
  pinia.use(piniaPluginPersistedstate)
} catch (e) {
  console.error('Failed to initialize state persistence, clearing cache...', e)
  // Clear potentially corrupted data
  try { localStorage.removeItem('engine-auth') } catch {}
  // Retry without persistence
  pinia.use(piniaPluginPersistedstate)
}

app.use(pinia)
app.use(router)

// Global error handler to catch unhandled Vue errors
app.config.errorHandler = (err, instance, info) => {
  console.error('Vue Error:', err)
  console.error('Component:', instance)
  console.error('Info:', info)
}

app.mount('#app')
