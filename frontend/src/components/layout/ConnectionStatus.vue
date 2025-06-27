<script setup lang="ts">
import { computed } from 'vue'

// Types
type ConnectionState =
  | 'connected'
  | 'connecting'
  | 'disconnected'
  | 'reconnecting'
  | 'failed'

// Props
const props = defineProps<{
  connectionState: ConnectionState
}>()

// Computed properties for connection status display
const connectionStatusClass = computed(() => {
  switch (props.connectionState) {
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
  switch (props.connectionState) {
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
  switch (props.connectionState) {
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
  <div class="flex items-center">
    <div
      class="w-2 h-2 rounded-full mr-2 transition-all duration-300"
      :class="connectionStatusClass"
    />
    <span
      class="text-sm font-medium transition-colors duration-300"
      :class="connectionTextClass"
    >
      {{ connectionStatusText }}
    </span>
  </div>
</template>
