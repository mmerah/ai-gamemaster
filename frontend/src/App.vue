<script setup lang="ts">
import { onMounted, inject, ref, onUnmounted, Ref } from 'vue'
import eventService from './services/eventService'
import ConnectionStatus from './components/layout/ConnectionStatus.vue'

// Types
type ConnectionState =
  | 'connected'
  | 'connecting'
  | 'disconnected'
  | 'reconnecting'
  | 'failed'
type InitializeApp = () => Promise<void>

// Get the initialization function from main.ts
const initializeApp = inject<InitializeApp>('initializeApp')

// Connection status
const connectionState: Ref<ConnectionState> = ref('disconnected')
let unsubscribeConnection: (() => void) | null = null

// Theme management
const isDarkMode = ref(false)

// Initialize theme from localStorage
const initializeTheme = () => {
  const savedTheme = localStorage.getItem('theme')
  if (savedTheme === 'dark') {
    isDarkMode.value = true
    document.documentElement.classList.add('dark')
  } else if (savedTheme === 'light') {
    isDarkMode.value = false
    document.documentElement.classList.remove('dark')
  } else {
    // Default to light theme
    isDarkMode.value = false
    document.documentElement.classList.remove('dark')
  }
}

// Toggle theme function
const toggleTheme = () => {
  isDarkMode.value = !isDarkMode.value
  if (isDarkMode.value) {
    document.documentElement.classList.add('dark')
    localStorage.setItem('theme', 'dark')
  } else {
    document.documentElement.classList.remove('dark')
    localStorage.setItem('theme', 'light')
  }
}

onMounted(async () => {
  initializeTheme()

  if (initializeApp) {
    await initializeApp()
  }

  // Subscribe to connection state changes
  unsubscribeConnection = eventService.onConnectionStateChange(state => {
    connectionState.value = state
  })
})

onUnmounted(() => {
  if (unsubscribeConnection) {
    unsubscribeConnection()
  }
})
</script>

<template>
  <div
    id="app"
    class="min-h-screen bg-background text-foreground transition-colors duration-300"
  >
    <!-- Navigation -->
    <nav class="bg-card shadow-lg border-b border-border/50">
      <div class="max-w-7xl mx-auto px-4">
        <div class="flex justify-between h-14">
          <div class="flex items-center">
            <router-link
              to="/"
              class="text-primary font-cinzel text-xl font-bold hover:text-primary/80 transition-colors duration-200"
            >
              AI Game Master
            </router-link>
          </div>
          <div class="flex items-center space-x-4">
            <!-- Theme Toggle -->
            <button
              class="p-2 rounded-md hover:bg-primary/10 transition-colors duration-200"
              :aria-label="
                isDarkMode ? 'Switch to light mode' : 'Switch to dark mode'
              "
              @click="toggleTheme"
            >
              <svg
                v-if="isDarkMode"
                xmlns="http://www.w3.org/2000/svg"
                class="h-5 w-5 text-accent"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"
                />
              </svg>
              <svg
                v-else
                xmlns="http://www.w3.org/2000/svg"
                class="h-5 w-5 text-primary"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"
                />
              </svg>
            </button>

            <!-- Connection Status Indicator -->
            <ConnectionStatus :connection-state="connectionState" />
          </div>
        </div>
      </div>
    </nav>

    <!-- Main content -->
    <main class="flex-1">
      <router-view />
    </main>
  </div>
</template>

<style scoped>
/* Component-specific styles can go here */
</style>
