import { ref, watch } from 'vue'

// MODULE-LEVEL refs — created once when first imported, shared by reference
// across every component that imports these composables. This is critical:
// if these were inside the function body, every caller would get its own copy.
const _authTheme = ref(localStorage.getItem('auth_theme') || 'light')
const _appTheme = ref(localStorage.getItem('app_theme') || 'light')

// Persist to localStorage on change
watch(_authTheme, (val) => {
  localStorage.setItem('auth_theme', val)
})
watch(_appTheme, (val) => {
  localStorage.setItem('app_theme', val)
})

// Auto-apply to DOM: auth theme watcher
watch(_authTheme, (val) => {
  const isAuthRoute = ['/login', '/register'].includes(window.location.pathname)
  if (isAuthRoute) {
    document.documentElement.classList.toggle('dark', val === 'dark')
  }
})

// Auto-apply to DOM: app theme watcher
watch(_appTheme, (val) => {
  const isAuthRoute = ['/login', '/register'].includes(window.location.pathname)
  if (!isAuthRoute) {
    document.documentElement.classList.toggle('dark', val === 'dark')
  }
})

// Call on initial app load or route change to apply the correct theme.
export function initThemeOnLoad(currentPath) {
  const path = currentPath || window.location.pathname
  const isAuthRoute = ['/login', '/register'].includes(path)
  if (isAuthRoute) {
    document.documentElement.classList.toggle('dark', _authTheme.value === 'dark')
  } else {
    document.documentElement.classList.toggle('dark', _appTheme.value === 'dark')
  }
}

export function useAuthTheme() {
  function toggle() {
    _authTheme.value = _authTheme.value === 'light' ? 'dark' : 'light'
  }
  function set(value) {
    _authTheme.value = value
  }
  return { theme: _authTheme, toggle, set }
}

export function useAppTheme() {
  function toggle() {
    _appTheme.value = _appTheme.value === 'light' ? 'dark' : 'light'
  }
  function set(value) {
    _appTheme.value = value
  }
  return { theme: _appTheme, toggle, set }
}

export function isDarkMode() {
  const isAuthRoute = ['/login', '/register'].includes(window.location.pathname)
  return isAuthRoute ? _authTheme.value === 'dark' : _appTheme.value === 'dark'
}
