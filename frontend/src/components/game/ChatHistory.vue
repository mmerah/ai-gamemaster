<template>
  <BasePanel class="flex flex-col h-full overflow-hidden">
    <div class="flex items-center justify-between mb-4">
      <h3 class="text-lg font-cinzel font-semibold text-foreground">
        Chat History
      </h3>
      <div class="flex items-center space-x-2">
        <!-- TTS Toggle -->
        <AppButton
          v-if="ttsEnabled"
          variant="secondary"
          size="sm"
          class="flex items-center space-x-1"
          :title="autoPlay ? 'Disable Auto-play' : 'Enable Auto-play'"
          @click="toggleAutoPlay"
        >
          <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
            <path
              v-if="autoPlay"
              fill-rule="evenodd"
              d="M9.383 3.076A1 1 0 0110 4v12a1 1 0 01-1.617.816L4.17 13.31a1 1 0 01-.293-.71V7.39a1 1 0 01.293-.71l4.213-3.506z"
              clip-rule="evenodd"
            />
            <path
              v-else
              fill-rule="evenodd"
              d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z"
              clip-rule="evenodd"
            />
          </svg>
          <span class="text-xs">{{ autoPlay ? 'Auto' : 'Manual' }}</span>
        </AppButton>

        <AppButton variant="secondary" size="sm" @click="scrollToBottom">
          <svg
            class="w-4 h-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M19 14l-7 7m0 0l-7-7m7 7V3"
            />
          </svg>
        </AppButton>
      </div>
    </div>

    <div
      ref="chatContainer"
      class="flex-1 overflow-y-auto fantasy-scrollbar space-y-3"
    >
      <div
        v-if="!messages.length && !isLoading"
        class="text-center text-foreground/60 py-8"
      >
        <p>No messages yet. Start your adventure!</p>
      </div>

      <ChatMessage
        v-for="message in messages"
        :key="message.id"
        :message="message"
        :expanded-reasoning="expandedReasoning[message.id] || false"
        :audio-loading="audioLoading[message.id] || false"
        :is-playing="currentlyPlaying === message.id"
        :is-queued="ttsQueue.includes(message.id)"
        :audio-element="audioElements[message.id]"
        :tts-enabled="ttsEnabled"
        :voice-id="voiceId"
        @toggle-reasoning="toggleReasoning(message.id)"
        @toggle-play="handlePlayStopClick(message)"
        @audio-ended="onAudioEnded(message.id)"
        @audio-error="onAudioError(message.id)"
      />

      <div v-if="isLoading" class="flex justify-center py-4">
        <BaseLoader size="md" />
      </div>
    </div>
  </BasePanel>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUpdated, nextTick, watch, Ref } from 'vue'
import { ttsApi } from '../../services/ttsApi'
import type { UIChatMessage } from '@/types/ui'
import BasePanel from '../base/BasePanel.vue'
import AppButton from '../base/AppButton.vue'
import BaseLoader from '../base/BaseLoader.vue'
import ChatMessage from './ChatMessage.vue'

interface Props {
  messages: UIChatMessage[]
  isLoading?: boolean
  ttsEnabled?: boolean
  autoPlay?: boolean
  voiceId?: string | null
}

const props = withDefaults(defineProps<Props>(), {
  isLoading: false,
  ttsEnabled: false,
  autoPlay: false,
  voiceId: null,
})

interface Emits {
  (e: 'update:autoPlay', value: boolean): void
}

const emit = defineEmits<Emits>()

const chatContainer = ref<HTMLElement | null>(null)
const expandedReasoning = reactive<Record<string, boolean>>({})
const audioElements = reactive<Record<string, string>>({})
const audioRefs = reactive<Record<string, HTMLAudioElement>>({})
const audioLoading = reactive<Record<string, boolean>>({})
const currentlyPlaying = ref<string | null>(null)

// TTS Queue System - Enhanced state tracking
const playedMessageIds = ref(new Set<string>())
const ttsQueue = ref<string[]>([])
const isProcessingQueue = ref(false)
const audioCompletionResolvers = reactive<Record<string, () => void>>({}) // To track Promise resolvers for audio completion

onMounted(() => {
  scrollToBottom()

  // If auto-play is enabled on mount, mark all existing messages as already seen
  // This prevents auto-playing old messages when loading a game with auto-play enabled
  if (props.autoPlay && props.ttsEnabled) {
    const existingGmMessages = props.messages.filter(
      msg => msg.type === 'assistant'
    )
    for (const message of existingGmMessages) {
      playedMessageIds.value.add(message.id)
    }
    console.log(
      `Component mounted with auto-play enabled. Marked ${existingGmMessages.length} existing messages as already seen`
    )
  }
})

onUpdated(() => {
  nextTick(() => {
    scrollToBottom()
  })
})

// Watch for new GM messages to queue for auto-play if enabled
watch(
  () => props.messages,
  newMessages => {
    if (!props.autoPlay || !props.ttsEnabled) return

    // Find new GM messages that haven't been played yet
    const newGmMessages = newMessages.filter(
      msg =>
        msg.type === 'assistant' &&
        !playedMessageIds.value.has(msg.id) &&
        (msg.audio_path || props.voiceId)
    )

    // Add new messages to queue (avoid duplicates)
    for (const message of newGmMessages) {
      if (!ttsQueue.value.includes(message.id)) {
        ttsQueue.value.push(message.id)
        console.log(`Added message ${message.id} to TTS queue`)
      }
    }

    // Start processing queue if not already processing
    if (!isProcessingQueue.value && ttsQueue.value.length > 0) {
      nextTick(() => {
        processQueue()
      })
    }
  },
  { deep: true }
)

// Watch for auto-play toggle changes
watch(
  () => props.autoPlay,
  (isEnabled, wasEnabled) => {
    if (!isEnabled) {
      // Clear queue and stop current playback when auto-play is disabled
      console.log('Auto-play disabled, clearing TTS queue')
      ttsQueue.value = []
      isProcessingQueue.value = false
      stopCurrentAudio()
    } else if (isEnabled && !wasEnabled) {
      // When auto-play is enabled, mark all existing GM messages as "already seen"
      // This prevents past messages from being queued for auto-play
      console.log(
        'Auto-play enabled, marking existing messages as already seen'
      )

      const existingGmMessages = props.messages.filter(
        msg => msg.type === 'assistant'
      )
      for (const message of existingGmMessages) {
        playedMessageIds.value.add(message.id)
      }

      console.log(
        `Marked ${existingGmMessages.length} existing GM messages as already seen`
      )
    }
  }
)

// Watch for TTS enabled/disabled
watch(
  () => props.ttsEnabled,
  isEnabled => {
    if (!isEnabled) {
      // Clear queue and stop current playback when TTS is disabled
      console.log('TTS disabled, clearing TTS queue')
      ttsQueue.value = []
      isProcessingQueue.value = false
      stopCurrentAudio()
    }
  }
)

// Process TTS queue sequentially - ENHANCED VERSION
async function processQueue(): Promise<void> {
  if (isProcessingQueue.value || ttsQueue.value.length === 0) {
    return
  }

  isProcessingQueue.value = true
  console.log(`Processing TTS queue: ${ttsQueue.value.length} items`)

  while (ttsQueue.value.length > 0) {
    // Stop processing if auto-play is disabled or TTS is disabled
    if (!props.autoPlay || !props.ttsEnabled) {
      console.log('Auto-play or TTS disabled during queue processing, stopping')
      break
    }

    const messageId = ttsQueue.value.shift()
    const message = props.messages.find(
      (msg: UIChatMessage) => msg.id === messageId
    )

    if (!message) {
      console.warn(`Message ${messageId} not found, skipping`)
      continue
    }

    // Skip if already played
    if (playedMessageIds.value.has(messageId)) {
      console.log(`Message ${messageId} already played, skipping`)
      continue
    }

    console.log(`Auto-playing message ${messageId}`)

    try {
      // ENHANCED: Wait for the audio to actually complete before continuing
      await playMessageAudioInternal(message, true)
      playedMessageIds.value.add(messageId)

      // Brief pause between messages for better UX
      await new Promise(resolve => setTimeout(resolve, 300))
    } catch (error) {
      console.error(`Error auto-playing message ${messageId}:`, error)
      // Mark as played even if it failed to avoid infinite retries
      playedMessageIds.value.add(messageId)
    }
  }

  isProcessingQueue.value = false
  console.log('TTS queue processing complete')
}

function scrollToBottom(): void {
  if (chatContainer.value) {
    chatContainer.value.scrollTop = chatContainer.value.scrollHeight
  }
}

function toggleReasoning(messageId: string): void {
  expandedReasoning[messageId] = !expandedReasoning[messageId]
}

function toggleAutoPlay(): void {
  emit('update:autoPlay', !props.autoPlay)
}

// Audio refs now managed per message in ChatMessage component

// Public function for manual play (from button clicks)
async function playMessageAudio(message: UIChatMessage): Promise<void> {
  return playMessageAudioInternal(message, false)
}

function handlePlayStopClick(message: UIChatMessage): void {
  if (currentlyPlaying.value === message.id) {
    stopCurrentAudio()
  } else {
    playMessageAudio(message)
  }
}

// ENHANCED: Internal function that handles both manual and auto-play with proper completion waiting
async function playMessageAudioInternal(
  message: UIChatMessage,
  isAutoPlay = false
): Promise<void> {
  // Check if message has any content (prefer detailed_content over content)
  const messageText = message.detailed_content || message.content
  if (!messageText) return

  // For manual play, stop any currently playing audio
  if (!isAutoPlay) {
    stopCurrentAudio()
  } else {
    // For auto-play, ensure no other audio is playing before starting
    if (currentlyPlaying.value && currentlyPlaying.value !== message.id) {
      console.log(
        `Auto-play waiting: Another message (${currentlyPlaying.value}) is still playing`
      )
      // In auto-play mode, wait for current audio to finish
      if (audioCompletionResolvers[currentlyPlaying.value]) {
        await audioCompletionResolvers[currentlyPlaying.value]
      }
    }
  }

  // Check if message has pre-generated TTS audio
  if (message.audio_path && !audioElements[message.id]) {
    audioElements[message.id] = message.audio_path
  }

  // If audio already exists (either pre-generated or previously fetched), use it
  if (audioElements[message.id]) {
    // Wait for next tick to ensure audio element exists
    await nextTick()
    if (audioRefs[message.id]) {
      return playAudioElement(message.id)
    }
  }

  // Only generate new audio if:
  // 1. No pre-generated audio exists
  // 2. Message is from GM
  // 3. Voice is selected
  if (message.type !== 'assistant') {
    const errorMsg = `Cannot generate TTS for ${message.type} messages`
    console.error(errorMsg)
    if (!isAutoPlay) {
      throw new Error(errorMsg)
    }
    return
  }

  if (!props.voiceId) {
    const errorMsg = 'No voice selected for TTS generation'
    console.warn(errorMsg)
    if (!isAutoPlay) {
      throw new Error(errorMsg)
    }
    return
  }

  // Generate new audio only if needed
  audioLoading[message.id] = true

  try {
    const textToSynthesize = message.detailed_content || message.content
    const response = await ttsApi.synthesize(textToSynthesize, props.voiceId)

    if (response.data.audio_url) {
      audioElements[message.id] = response.data.audio_url
      await nextTick()

      if (audioRefs[message.id]) {
        return playAudioElement(message.id)
      }
    }

    throw new Error('Failed to create audio element or get audio URL')
  } catch (error) {
    console.error('Error generating TTS audio:', error)
    throw error
  } finally {
    audioLoading[message.id] = false
  }
}

// ENHANCED: Helper function to play audio element and return a Promise that resolves when it ends
async function playAudioElement(messageId: string): Promise<void> {
  return new Promise((resolve, reject) => {
    const audioElement = audioRefs[messageId]
    if (!audioElement) {
      reject(new Error('Audio element not found'))
      return
    }

    // Store resolver for potential interruption handling
    audioCompletionResolvers[messageId] = resolve

    currentlyPlaying.value = messageId

    // Set up one-time event listeners
    const onEnded = () => {
      cleanup()
      resolve()
    }

    const onError = (error: Event) => {
      cleanup()
      reject(error)
    }

    const cleanup = () => {
      audioElement.removeEventListener('ended', onEnded)
      audioElement.removeEventListener('error', onError)
      delete audioCompletionResolvers[messageId]
      if (currentlyPlaying.value === messageId) {
        currentlyPlaying.value = null
      }
    }

    audioElement.addEventListener('ended', onEnded, { once: true })
    audioElement.addEventListener('error', onError, { once: true })

    // Start playing
    audioElement.play().catch(error => {
      cleanup()
      reject(error)
    })
  })
}

function stopCurrentAudio(): void {
  if (currentlyPlaying.value && audioRefs[currentlyPlaying.value]) {
    const audioElement = audioRefs[currentlyPlaying.value]
    const stoppedMessageId = currentlyPlaying.value

    audioElement.pause()
    audioElement.currentTime = 0

    // Mark the manually stopped message as "played" to prevent it from replaying in auto-play
    playedMessageIds.value.add(stoppedMessageId)

    // Remove from TTS queue if it's still there
    const queueIndex = ttsQueue.value.indexOf(stoppedMessageId)
    if (queueIndex !== -1) {
      ttsQueue.value.splice(queueIndex, 1)
      console.log(
        `Removed manually stopped message ${stoppedMessageId} from TTS queue`
      )
    }

    // Resolve any pending completion promises
    if (audioCompletionResolvers[stoppedMessageId]) {
      audioCompletionResolvers[stoppedMessageId]()
      delete audioCompletionResolvers[stoppedMessageId]
    }
  }
  currentlyPlaying.value = null
}

function onAudioEnded(messageId: string): void {
  console.log(`Audio ended for message ${messageId}`)
  if (currentlyPlaying.value === messageId) {
    currentlyPlaying.value = null
  }

  // Mark as played for auto-play tracking
  playedMessageIds.value.add(messageId)

  // Clean up any completion resolver
  if (audioCompletionResolvers[messageId]) {
    audioCompletionResolvers[messageId]()
    delete audioCompletionResolvers[messageId]
  }
}

function onAudioError(messageId: string): void {
  console.error('Audio playback error for message:', messageId)
  if (currentlyPlaying.value === messageId) {
    currentlyPlaying.value = null
  }
  audioLoading[messageId] = false

  // Mark as "played" to avoid retrying in auto-play
  playedMessageIds.value.add(messageId)

  // Clean up any completion resolver
  if (audioCompletionResolvers[messageId]) {
    audioCompletionResolvers[messageId]()
    delete audioCompletionResolvers[messageId]
  }
}

// formatTime is now handled in ChatMessage component
</script>

<style scoped>
/* ChatHistory specific styles only */
/* All message-specific animations and styles have been moved to ChatMessage.vue */
</style>
