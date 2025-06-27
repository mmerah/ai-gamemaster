<template>
  <div class="game-view h-screen bg-background overflow-hidden">
    <!-- Connection Status Banner -->
    <div
      v-if="uiStore.connectionStatus !== 'connected'"
      class="bg-accent/20 border-b border-accent/40 px-4 py-2"
    >
      <div class="max-w-7xl mx-auto flex items-center justify-center space-x-2">
        <svg
          v-if="uiStore.connectionStatus === 'connecting'"
          class="animate-spin h-4 w-4 text-accent"
          fill="none"
          viewBox="0 0 24 24"
        >
          <circle
            class="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            stroke-width="4"
          />
          <path
            class="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
          />
        </svg>
        <span class="text-sm text-accent-foreground">
          {{
            uiStore.connectionStatus === 'connecting'
              ? 'Connecting to server...'
              : 'Connection lost - attempting to reconnect...'
          }}
        </span>
      </div>
    </div>

    <!-- Notification Toast -->
    <NotificationToast
      v-model:show="notification.show"
      :message="notification.message"
      :type="notification.type"
    />

    <!-- Main Game Area -->
    <div
      class="h-full max-w-7xl mx-auto p-6 pb-8 grid grid-cols-1 lg:grid-cols-4 gap-6"
    >
      <!-- Left Column: Map Panel -->
      <div class="lg:col-span-1 space-y-6">
        <!-- Map Panel (if available) -->
        <MapPanel
          v-if="gameState.location"
          :location="gameState.location"
          :description="gameState.locationDescription"
        />

        <!-- TTS Settings Panel -->
        <BasePanel>
          <h3 class="text-lg font-cinzel font-semibold text-foreground mb-4">
            Voice Settings
          </h3>

          <!-- TTS Enable Toggle -->
          <div class="mb-4">
            <label class="flex items-center space-x-2">
              <input
                v-model="gameStore.ttsState.enabled"
                type="checkbox"
                class="rounded border-border text-accent focus:ring-accent"
                @change="handleTTSToggle"
              />
              <span class="text-sm text-foreground">Enable Narration</span>
            </label>
          </div>

          <!-- Voice Selection -->
          <div v-if="gameStore.ttsState.enabled" class="space-y-3">
            <div>
              <label class="block text-sm font-medium text-foreground mb-1"
                >Voice</label
              >
              <select
                v-model="gameStore.ttsState.voiceId"
                class="w-full rounded border-border bg-card text-foreground focus:ring-accent"
                :disabled="gameStore.ttsState.isLoading"
                @change="handleVoiceChange"
              >
                <option value="">Select a voice...</option>
                <option
                  v-for="voice in gameStore.ttsState.availableVoices"
                  :key="voice.id"
                  :value="voice.id"
                >
                  {{ voice.name }}
                </option>
              </select>
            </div>

            <!-- Auto-play Toggle -->
            <div>
              <label class="flex items-center space-x-2">
                <input
                  v-model="gameStore.ttsState.autoPlay"
                  type="checkbox"
                  :disabled="!gameStore.ttsState.voiceId"
                  class="rounded border-border text-accent focus:ring-accent"
                  @change="handleAutoPlayToggle"
                />
                <span class="text-sm text-foreground"
                  >Auto-play new messages</span
                >
              </label>
            </div>

            <!-- Voice Preview Button -->
            <AppButton
              v-if="gameStore.ttsState.voiceId"
              :disabled="previewLoading"
              variant="secondary"
              size="sm"
              class="w-full"
              @click="handleVoicePreview"
            >
              {{ previewLoading ? 'Generating...' : '🔊 Preview Voice' }}
            </AppButton>
          </div>
        </BasePanel>
      </div>

      <!-- Middle Column: Chat and Controls -->
      <div class="lg:col-span-2 h-full flex flex-col gap-4">
        <!-- Chat History with controlled height -->
        <div class="flex-1 min-h-0 max-h-[60vh] lg:max-h-[65vh]">
          <ChatHistory
            :messages="chatStore.sortedMessages"
            :is-loading="isGameLoading"
            :tts-enabled="gameStore.ttsState.enabled"
            :auto-play="gameStore.ttsState.autoPlay"
            :voice-id="gameStore.ttsState.voiceId"
            class="h-full"
            @update:auto-play="handleAutoPlayUpdate"
          />
        </div>

        <!-- Bottom Section: Dice Requests and Input Controls -->
        <div class="flex-shrink-0 space-y-4 bg-background z-10">
          <!-- Dice Requests (if any) -->
          <DiceRequests
            v-if="diceStore.hasPendingRequests"
            @submit-rolls="handleSubmitRolls"
          />

          <!-- Input Controls -->
          <InputControls
            :disabled="isGameLoading || diceStore.hasPendingRequests"
            @send-message="handleSendMessage"
          />
        </div>
      </div>

      <!-- Right Column: Game Panels -->
      <div class="lg:col-span-1 space-y-6">
        <!-- Game Action Buttons -->
        <div class="space-y-2">
          <!-- Save Game Button -->
          <AppButton
            variant="primary"
            class="w-full"
            :disabled="isGameLoading || isSaving"
            @click="handleSaveGame"
          >
            <span v-if="isSaving">💾 Saving...</span>
            <span v-else>💾 Save Game</span>
          </AppButton>

          <!-- Retry Button -->
          <AppButton
            v-if="uiStore.canRetryLastRequest"
            variant="secondary"
            class="w-full"
            :disabled="isGameLoading"
            @click="handleRetryLastRequest"
          >
            🔁 Retry Last AI Request
          </AppButton>
        </div>

        <!-- Party Panel -->
        <PartyPanel :party="partyStore.members" />

        <!-- Combat Status (if in combat) -->
        <CombatStatus
          v-if="combatStore.isActive"
          :combat-state="combatStore"
          :party="partyStore.members"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { logger } from '@/utils/logger'
import { ref, onMounted, onUnmounted, watch, computed, nextTick } from 'vue'
import { useGameStore } from '../stores/gameStore'
import { useCampaignStore } from '../stores/campaignStore'
import { useDiceStore } from '../stores/diceStore'
import { usePartyStore } from '../stores/partyStore'
import { useCombatStore } from '../stores/combatStore'
import { useUiStore } from '../stores/uiStore'
import { useChatStore } from '../stores/chatStore'
import { initializeEventRouter } from '../stores/eventRouter'
import { ttsApi } from '../services/ttsApi'
import type { DiceRollResultResponseModel } from '@/types/unified'
import ChatHistory from '../components/game/ChatHistory.vue'
import InputControls from '../components/game/InputControls.vue'
import DiceRequests from '../components/game/DiceRequests.vue'
import PartyPanel from '../components/game/PartyPanel.vue'
import CombatStatus from '../components/game/CombatStatus.vue'
import MapPanel from '../components/game/MapPanel.vue'
import AppButton from '../components/base/AppButton.vue'
import BasePanel from '../components/base/BasePanel.vue'
import NotificationToast from '../components/base/NotificationToast.vue'

const gameStore = useGameStore()
const campaignStore = useCampaignStore()
const diceStore = useDiceStore()
const partyStore = usePartyStore()
const combatStore = useCombatStore()
const uiStore = useUiStore()
const chatStore = useChatStore()

const isGameLoading = ref(false)
const previewLoading = ref(false)
const isTriggering = ref(false)
const isSaving = ref(false)

// Notification state
const notification = ref<{
  show: boolean
  message: string
  type: 'success' | 'error' | 'info'
}>({
  show: false,
  message: '',
  type: 'success',
})

// Show notification helper
function showNotification(
  message: string,
  type: 'success' | 'error' | 'info' = 'success'
) {
  notification.value = { show: true, message, type }
}

// Computed properties
const gameState = computed(() => gameStore.gameState)

onMounted(async () => {
  // Initialize event router for all stores
  initializeEventRouter()

  // Initialize game connection
  await initializeGame()

  // Load TTS voices
  await loadTTSVoices()
})

onUnmounted(() => {
  // Cleanup event handlers when component is destroyed
  gameStore.cleanupEventHandlers()
})

async function initializeGame(): Promise<void> {
  isGameLoading.value = true
  uiStore.connectionStatus = 'connecting'

  try {
    await gameStore.initializeGame()
    uiStore.connectionStatus = 'connected'

    // Sync TTS state with campaign narration settings
    const campaignId = gameState.value?.campaignId
    if (campaignId) {
      const campaign = await campaignStore.getCampaignByIdAsync(campaignId)
      if (campaign) {
        // Set TTS enabled state from campaign
        if (campaign.narration_enabled) {
          gameStore.enableTTS()
          // Set voice if available
          if (campaign.tts_voice) {
            gameStore.setTTSVoice(campaign.tts_voice)
          }
        } else {
          gameStore.disableTTS()
        }
      }
    }
  } catch (error) {
    logger.error('Failed to initialize game:', error)
    uiStore.connectionStatus = 'error'
  } finally {
    isGameLoading.value = false
  }
}

async function loadTTSVoices(): Promise<void> {
  try {
    await gameStore.loadTTSVoices()
  } catch (error) {
    logger.error('Failed to load TTS voices:', error)
  }
}

// Monitor SSE connection status
watch(
  () => uiStore.isConnected,
  (connected: boolean) => {
    uiStore.connectionStatus = connected ? 'connected' : 'disconnected'
  }
)

async function handleSendMessage(message: string): Promise<void> {
  isGameLoading.value = true
  try {
    await gameStore.sendMessage(message)
  } catch (error) {
    logger.error('Failed to send message:', error)
  } finally {
    isGameLoading.value = false
  }
}

async function handleSubmitRolls(
  rollResultsFromEmit?: DiceRollResultResponseModel[]
): Promise<void> {
  // This function is called when DiceRequests emits 'submit-rolls'
  try {
    isGameLoading.value = true
    // The actual submission is handled within DiceRequests.vue via gameStore.submitMultipleCompletedRolls
    // This function now mostly acts as a response to the emit and manages local loading state
  } catch (error) {
    logger.error('Failed to handle submitted rolls:', error)
  } finally {
    isGameLoading.value = false
  }
}

async function handleRetryLastRequest(): Promise<void> {
  isGameLoading.value = true
  try {
    await gameStore.retryLastAIRequest()
  } catch (error) {
    logger.error('Failed to retry last request:', error)
  } finally {
    isGameLoading.value = false
  }
}

async function handleSaveGame(): Promise<void> {
  isSaving.value = true
  try {
    await gameStore.saveGame()
    showNotification('Game saved successfully!', 'success')
  } catch (error) {
    logger.error('Failed to save game:', error)
    showNotification('Failed to save game. Please try again.', 'error')
  } finally {
    isSaving.value = false
  }
}

// TTS Event Handlers
async function handleTTSToggle(): Promise<void> {
  try {
    // Call the backend API to toggle narration
    await ttsApi.toggleNarration(gameStore.ttsState.enabled)

    // Update local state
    if (gameStore.ttsState.enabled) {
      gameStore.enableTTS()
    } else {
      gameStore.disableTTS()
    }
  } catch (error) {
    logger.error('Failed to toggle narration:', error)
    // Revert the toggle on error
    gameStore.ttsState.enabled = !gameStore.ttsState.enabled
  }
}

async function handleVoiceChange(): Promise<void> {
  if (gameStore.ttsState.voiceId) {
    gameStore.setTTSVoice(gameStore.ttsState.voiceId)

    // Save voice preference to game state (not campaign)
    // The backend will handle this when we call the TTS API
    // No need to update campaign directly
  }
}

function handleAutoPlayToggle(): void {
  gameStore.setAutoPlay(gameStore.ttsState.autoPlay)
}

function handleAutoPlayUpdate(enabled: boolean): void {
  gameStore.setAutoPlay(enabled)
}

async function handleVoicePreview(): Promise<void> {
  if (!gameStore.ttsState.voiceId) return

  previewLoading.value = true
  try {
    await gameStore.previewVoice(gameStore.ttsState.voiceId)
  } catch (error) {
    logger.error('Failed to preview voice:', error)
  } finally {
    previewLoading.value = false
  }
}

// Watch for changes in store's isLoading state to handle post-API call logic
watch(
  () => gameStore.isLoading,
  (newIsLoading, oldIsLoading) => {
    if (oldIsLoading === true && newIsLoading === false) {
      // An API call just finished
      if (gameState.value.needsBackendTrigger) {
        if (!diceStore.hasPendingRequests) {
          // Use nextTick to ensure state is fully updated before checking
          nextTick(() => {
            if (!isTriggering.value && gameState.value.needsBackendTrigger) {
              isTriggering.value = true

              setTimeout(async () => {
                try {
                  await gameStore.triggerNextStep()
                } catch (error) {
                  logger.error('Failed to trigger next step:', error)
                } finally {
                  // Reset after a short delay to allow state updates
                  setTimeout(() => {
                    isTriggering.value = false
                  }, 100)
                }
              }, 3000) // Increased to 3 seconds to help avoid rate limits
            }
          })
        }
      }
    }
  }
)

// Watch for changes in game loading state to sync with local loading state
watch(
  () => gameStore.isLoading,
  newValue => {
    isGameLoading.value = newValue
  }
)
</script>

<style scoped>
/* Component-specific styles if needed */
</style>
