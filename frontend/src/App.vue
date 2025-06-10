<script setup lang="ts">
import { onMounted, inject, ref, computed, onUnmounted, Ref } from 'vue'
import eventService from './services/eventService'

// Types
type ConnectionState = 'connected' | 'connecting' | 'disconnected' | 'reconnecting' | 'failed'
type InitializeApp = () => Promise<void>

// Get the initialization function from main.ts
const initializeApp = inject<InitializeApp>('initializeApp')

// Connection status
const connectionState: Ref<ConnectionState> = ref('disconnected')
let unsubscribeConnection: (() => void) | null = null

onMounted(async () => {
  if (initializeApp) {
    await initializeApp()
  }

  // Subscribe to connection state changes
  unsubscribeConnection = eventService.onConnectionStateChange((state) => {
    connectionState.value = state
  })
})

onUnmounted(() => {
  if (unsubscribeConnection) {
    unsubscribeConnection()
  }
})

// Computed properties for connection status display
const connectionStatusClass = computed(() => {
  switch (connectionState.value) {
    case 'connected':
      return 'bg-green-500 shadow-green-500/50 shadow-sm'
    case 'connecting':
    case 'reconnecting':
      return 'bg-yellow-500 animate-pulse'
    case 'failed':
      return 'bg-red-500'
    default:
      return 'bg-gray-500'
  }
})

const connectionTextClass = computed(() => {
  switch (connectionState.value) {
    case 'connected':
      return 'text-green-400'
    case 'connecting':
    case 'reconnecting':
      return 'text-yellow-400'
    case 'failed':
      return 'text-red-400'
    default:
      return 'text-gray-400'
  }
})

const connectionStatusText = computed(() => {
  switch (connectionState.value) {
    case 'connected':
      return 'Connected'
    case 'connecting':
      return 'Connecting...'
    case 'reconnecting':
      return 'Reconnecting...'
    case 'failed':
      return 'Connection Failed'
    default:
      return 'Disconnected'
  }
})
</script>

<template>
  <div id="app" class="min-h-screen bg-parchment">
    <!-- Navigation -->
    <nav class="bg-secondary-dark shadow-lg border-b-2 border-gold/20">
      <div class="max-w-7xl mx-auto px-4">
        <div class="flex justify-between h-14">
          <div class="flex items-center">
            <router-link
              to="/"
              class="text-gold font-cinzel text-xl font-bold hover:text-gold-light transition-colors"
            >
              AI Game Master
            </router-link>
          </div>
          <div class="flex items-center">
            <!-- Connection Status Indicator -->
            <div class="flex items-center mr-6">
              <div
                class="w-2 h-2 rounded-full mr-2 transition-all duration-300"
                :class="connectionStatusClass"
              ></div>
              <span class="text-sm font-medium transition-colors duration-300" :class="connectionTextClass">
                {{ connectionStatusText }}
              </span>
            </div>
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
