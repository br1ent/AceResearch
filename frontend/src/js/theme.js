import { ref } from 'vue'
import { defineStore } from 'pinia'

const STORAGE_KEY = 'ace-theme'

export const useThemeStore = defineStore('theme', () => {
  const isDark = ref(false)

  function applyTheme(dark) {
    isDark.value = dark
    const theme = dark ? 'dark' : 'light'
    document.documentElement.setAttribute('data-theme', theme)
    document.documentElement.classList.toggle('dark', dark)
    localStorage.setItem(STORAGE_KEY, theme)
  }

  function toggleTheme() {
    applyTheme(!isDark.value)
  }

  function initTheme() {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved) {
      applyTheme(saved === 'dark')
    } else {
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
      applyTheme(prefersDark)
    }
  }

  return { isDark, toggleTheme, initTheme }
})
