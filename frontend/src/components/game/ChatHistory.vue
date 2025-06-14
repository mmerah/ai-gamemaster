<template>
  <div class="fantasy-panel flex flex-col h-full overflow-hidden">
    <div class="flex items-center justify-between mb-4">
      <h3 class="text-lg font-cinzel font-semibold text-text-primary">Chat History</h3>
      <div class="flex items-center space-x-2">
        <!-- TTS Toggle -->
        <button
          v-if="ttsEnabled"
          @click="toggleAutoPlay"
          class="text-sm text-gold hover:text-gold-light transition-colors flex items-center space-x-1"
          :title="autoPlay ? 'Disable Auto-play' : 'Enable Auto-play'"
        >
          <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
            <path v-if="autoPlay" fill-rule="evenodd" d="M9.383 3.076A1 1 0 0110 4v12a1 1 0 01-1.617.816L4.17 13.31a1 1 0 01-.293-.71V7.39a1 1 0 01.293-.71l4.213-3.506z" clip-rule="evenodd"/>
            <path v-else fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clip-rule="evenodd"/>
          </svg>
          <span class="text-xs">{{ autoPlay ? 'Auto' : 'Manual' }}</span>
        </button>

        <button
          @click="scrollToBottom"
          class="text-sm text-gold hover:text-gold-light transition-colors"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 14l-7 7m0 0l-7-7m7 7V3" />
          </svg>
        </button>
      </div>
    </div>

    <div
      ref="chatContainer"
      class="flex-1 overflow-y-auto fantasy-scrollbar space-y-3"
    >
      <div v-if="!messages.length && !isLoading" class="text-center text-text-secondary py-8">
        <p>No messages yet. Start your adventure!</p>
      </div>

      <div
        v-for="message in messages"
        :key="message.id"
        :class="[
          'chat-message p-3 rounded-lg transition-all duration-300',
          message.type === 'user'
            ? 'bg-royal-blue/20 ml-8'
            : message.type === 'gm'
            ? 'bg-gold/20 mr-8'
            : 'bg-secondary/20 mx-4',
          message.animated ? 'animated-message' : '',
          message.superseded ? 'superseded-message' : ''
        ]"
      >
        <div class="flex items-start space-x-2">
          <div class="flex-shrink-0">
            <div :class="[
              'w-8 h-8 rounded-full flex items-center justify-center text-xs font-semibold',
              message.type === 'user'
                ? 'bg-royal-blue text-white'
                : message.type === 'gm'
                ? 'bg-gold text-primary-dark'
                : 'bg-secondary text-white'
            ]">
              {{ message.type === 'user' ? 'U' : message.type === 'gm' ? 'GM' : 'S' }}
            </div>
          </div>

          <div class="flex-1 min-w-0">
            <div class="flex items-center space-x-2 mb-1">
              <span class="text-sm font-medium text-text-primary">
                {{ message.type === 'user' ? 'You' : message.type === 'gm' ? 'Game Master' : 'System' }}
              </span>
              <span class="text-xs text-text-secondary">
                {{ formatTime(message.timestamp) }}
              </span>

              <!-- TTS Play button for GM messages -->
              <button
                v-if="message.type === 'gm' && ttsEnabled && (message.audio_path || voiceId) && (message.detailed_content || message.content)"
                @click="handlePlayStopClick(message)"
                :disabled="audioLoading[message.id]"
                class="text-xs text-gold hover:text-gold-light transition-colors flex items-center space-x-1"
                :title="audioLoading[message.id] ? 'Generating audio...' : currentlyPlaying === message.id ? 'Stop' : 'Play'"
              >
                <div v-if="audioLoading[message.id]" class="w-3 h-3 animate-spin rounded-full border border-gold border-t-transparent"></div>
                <svg v-else-if="currentlyPlaying === message.id" class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zM7 8a1 1 0 012 0v4a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v4a1 1 0 102 0V8a1 1 0 00-1-1z" clip-rule="evenodd"/>
                </svg>
                <svg v-else class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clip-rule="evenodd"/>
                </svg>
              </button>

              <!-- Queue indicator for auto-play -->
              <span v-if="ttsQueue.length > 0 && message.type === 'gm'" class="text-xs text-gold/70">
                {{ ttsQueue.includes(message.id) ? 'Queued' : '' }}
              </span>

              <!-- Reasoning toggle button for GM messages -->
              <button
                v-if="message.type === 'gm' && message.gm_thought"
                @click="toggleReasoning(message.id)"
                class="text-xs text-gold hover:text-gold-light transition-colors flex items-center space-x-1"
                :title="expandedReasoning[message.id] ? 'Hide Reasoning' : 'Show Reasoning'"
              >
                <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
                <span>{{ expandedReasoning[message.id] ? 'Hide' : 'Show' }} Reasoning</span>
                <svg
                  :class="['w-3 h-3 transition-transform', expandedReasoning[message.id] ? 'rotate-180' : '']"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                </svg>
              </button>
            </div>

            <div class="text-sm text-text-primary whitespace-pre-wrap">
              {{ message.content }}
            </div>

            <!-- Audio element for TTS playback -->
            <audio
              v-if="message.type === 'gm' && audioElements[message.id]"
              :ref="el => setAudioRef(message.id, el)"
              :src="audioElements[message.id]"
              @ended="onAudioEnded(message.id)"
              @error="onAudioError(message.id)"
              class="hidden"
              preload="none"
            ></audio>

            <!-- Expandable reasoning section for GM messages -->
            <div
              v-if="message.type === 'gm' && message.gm_thought && expandedReasoning[message.id]"
              class="mt-3 p-3 bg-primary-dark/30 border border-gold/30 rounded-md"
            >
              <div class="flex items-center space-x-2 mb-2">
                <svg class="w-4 h-4 text-gold" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
                <span class="text-xs font-medium text-gold">AI Reasoning</span>
              </div>
              <div class="text-xs text-text-secondary whitespace-pre-wrap leading-relaxed">
                {{ message.gm_thought }}
              </div>
            </div>

            <!-- Dice roll details -->
            <div v-if="message.type === 'dice' && message.details" class="mt-2 text-xs text-text-secondary">
              <div class="flex items-center space-x-2">
                <span>🎲 {{ message.details.expression }}</span>
                <span class="font-mono">{{ message.details.breakdown }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-if="isLoading" class="flex justify-center py-4">
        <div class="spinner"></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUpdated, nextTick, watch } from 'vue'
import { ttsApi } from '../../services/ttsApi'

const props = defineProps({
  messages: {
    type: Array,
    required: true
  },
  isLoading: {
    type: Boolean,
    default: false
  },
  ttsEnabled: {
    type: Boolean,
    default: false
  },
  autoPlay: {
    type: Boolean,
    default: false
  },
  voiceId: {
    type: String,
    default: null
  }
})

const emit = defineEmits(['update:autoPlay'])

const chatContainer = ref(null)
const expandedReasoning = reactive({})
const audioElements = reactive({})
const audioRefs = reactive({})
const audioLoading = reactive({})
const currentlyPlaying = ref(null)

// TTS Queue System - Enhanced state tracking
const playedMessageIds = ref(new Set())
const ttsQueue = ref([])
const isProcessingQueue = ref(false)
const audioCompletionResolvers = reactive({}) // To track Promise resolvers for audio completion

onMounted(() => {
  scrollToBottom()

  // If auto-play is enabled on mount, mark all existing messages as already seen
  // This prevents auto-playing old messages when loading a game with auto-play enabled
  if (props.autoPlay && props.ttsEnabled) {
    const existingGmMessages = props.messages.filter(msg => msg.type === 'gm')
    for (const message of existingGmMessages) {
      playedMessageIds.value.add(message.id)
    }
    console.log(`Component mounted with auto-play enabled. Marked ${existingGmMessages.length} existing messages as already seen`)
  }
})

onUpdated(() => {
  nextTick(() => {
    scrollToBottom()
  })
})

// Watch for new GM messages to queue for auto-play if enabled
watch(() => props.messages, (newMessages) => {
  if (!props.autoPlay || !props.ttsEnabled) return

  // Find new GM messages that haven't been played yet
  const newGmMessages = newMessages
    .filter(msg =>
      msg.type === 'gm' &&
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
}, { deep: true })

// Watch for auto-play toggle changes
watch(() => props.autoPlay, (isEnabled, wasEnabled) => {
  if (!isEnabled) {
    // Clear queue and stop current playback when auto-play is disabled
    console.log('Auto-play disabled, clearing TTS queue')
    ttsQueue.value = []
    isProcessingQueue.value = false
    stopCurrentAudio()
  } else if (isEnabled && !wasEnabled) {
    // When auto-play is enabled, mark all existing GM messages as "already seen"
    // This prevents past messages from being queued for auto-play
    console.log('Auto-play enabled, marking existing messages as already seen')

    const existingGmMessages = props.messages.filter(msg => msg.type === 'gm')
    for (const message of existingGmMessages) {
      playedMessageIds.value.add(message.id)
    }

    console.log(`Marked ${existingGmMessages.length} existing GM messages as already seen`)
  }
})

// Watch for TTS enabled/disabled
watch(() => props.ttsEnabled, (isEnabled) => {
  if (!isEnabled) {
    // Clear queue and stop current playback when TTS is disabled
    console.log('TTS disabled, clearing TTS queue')
    ttsQueue.value = []
    isProcessingQueue.value = false
    stopCurrentAudio()
  }
})

// Process TTS queue sequentially - ENHANCED VERSION
async function processQueue() {
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
    const message = props.messages.find(msg => msg.id === messageId)

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

function scrollToBottom() {
  if (chatContainer.value) {
    chatContainer.value.scrollTop = chatContainer.value.scrollHeight
  }
}

function toggleReasoning(messageId) {
  expandedReasoning[messageId] = !expandedReasoning[messageId]
}

function toggleAutoPlay() {
  emit('update:autoPlay', !props.autoPlay)
}

function setAudioRef(messageId, el) {
  if (el) {
    audioRefs[messageId] = el
  }
}

// Public function for manual play (from button clicks)
async function playMessageAudio(message) {
  return playMessageAudioInternal(message, false)
}

function handlePlayStopClick(message) {
  if (currentlyPlaying.value === message.id) {
    stopCurrentAudio()
  } else {
    playMessageAudio(message)
  }
}

// ENHANCED: Internal function that handles both manual and auto-play with proper completion waiting
async function playMessageAudioInternal(message, isAutoPlay = false) {
  // Check if message has any content (prefer detailed_content over content)
  const messageText = message.detailed_content || message.content
  if (!messageText) return


  // For manual play, stop any currently playing audio
  if (!isAutoPlay) {
    stopCurrentAudio()
  } else {
    // For auto-play, ensure no other audio is playing before starting
    if (currentlyPlaying.value && currentlyPlaying.value !== message.id) {
      console.log(`Auto-play waiting: Another message (${currentlyPlaying.value}) is still playing`)
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
  if (message.type !== 'gm') {
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

    if (response.audio_url) {
      audioElements[message.id] = response.audio_url
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
async function playAudioElement(messageId) {
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

    const onError = (error) => {
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

function stopCurrentAudio() {
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
      console.log(`Removed manually stopped message ${stoppedMessageId} from TTS queue`)
    }

    // Resolve any pending completion promises
    if (audioCompletionResolvers[stoppedMessageId]) {
      audioCompletionResolvers[stoppedMessageId]()
      delete audioCompletionResolvers[stoppedMessageId]
    }
  }
  currentlyPlaying.value = null
}

function onAudioEnded(messageId) {
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

function onAudioError(messageId) {
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

function formatTime(timestamp) {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  return date.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit'
  })
}
</script>

<style scoped>
/* Animation styles for messages appearing during NPC turn animations */
.animated-message {
  animation: messageSlideIn 0.5s ease-out;
}

@keyframes messageSlideIn {
  0% {
    opacity: 0;
    transform: translateY(10px);
  }
  100% {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Pulse effect for newly animated messages */
.chat-message.animated-message:not(:last-child) {
  animation: messagePulse 0.6s ease-in-out;
}

@keyframes messagePulse {
  0% {
    opacity: 0;
    transform: translateY(10px) scale(0.98);
  }
  50% {
    opacity: 0.8;
    transform: translateY(5px) scale(0.99);
  }
  100% {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

/* Enhanced glow effect for animated GM messages */
.chat-message.animated-message.bg-gold\/20 {
  box-shadow: 0 0 0 1px rgba(251, 191, 36, 0.2);
  animation: messageGlow 0.6s ease-in-out;
}

@keyframes messageGlow {
  0% {
    box-shadow: 0 0 0 1px rgba(251, 191, 36, 0);
  }
  50% {
    box-shadow: 0 0 10px 2px rgba(251, 191, 36, 0.3);
  }
  100% {
    box-shadow: 0 0 0 1px rgba(251, 191, 36, 0.2);
  }
}

/* Smooth transitions for message updates */
.chat-message {
  transition: all 0.3s ease-out;
}

/* Loading spinner styles */
.spinner {
  border: 2px solid rgba(251, 191, 36, 0.2);
  border-top-color: #fbbf24;
  border-radius: 50%;
  width: 24px;
  height: 24px;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* Superseded message styles */
.superseded-message {
  opacity: 0.5;
  position: relative;
}

.superseded-message::after {
  content: '';
  position: absolute;
  top: 50%;
  left: 0;
  right: 0;
  height: 1px;
  background-color: rgba(255, 255, 255, 0.3);
  transform: translateY(-50%);
}
</style>
