<template>
  <div class="game-view h-screen bg-parchment overflow-hidden">
    <!-- Connection Status Banner -->
    <div v-if="uiStore.connectionStatus !== 'connected'" class="bg-amber-100 border-b border-amber-300 px-4 py-2">
      <div class="max-w-7xl mx-auto flex items-center justify-center space-x-2">
        <svg
          v-if="uiStore.connectionStatus === 'connecting'"
          class="animate-spin h-4 w-4 text-amber-600"
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
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
        </svg>
        <span class="text-sm text-amber-800">
          {{ uiStore.connectionStatus === 'connecting' ? 'Connecting to server...' : 'Connection lost - attempting to reconnect...' }}
        </span>
      </div>
    </div>

    <!-- Main Game Area -->
    <div class="h-full max-w-7xl mx-auto p-6 pb-8 grid grid-cols-1 lg:grid-cols-4 gap-6">
      <!-- Left Column: Map Panel -->
      <div class="lg:col-span-1 space-y-6">
        <!-- Map Panel (if available) -->
        <MapPanel
          v-if="gameState.location"
          :location="gameState.location"
          :description="gameState.locationDescription"
        />

        <!-- TTS Settings Panel -->
        <div class="fantasy-panel">
          <h3 class="text-lg font-cinzel font-semibold text-text-primary mb-4">
            Voice Settings
          </h3>

          <!-- TTS Enable Toggle -->
          <div class="mb-4">
            <label class="flex items-center space-x-2">
              <input
                v-model="gameStore.ttsState.enabled"
                type="checkbox"
                class="rounded border-brown-400 text-gold focus:ring-gold"
                @change="handleTTSToggle"
              >
              <span class="text-sm text-text-primary">Enable Narration</span>
            </label>
          </div>

          <!-- Voice Selection -->
          <div v-if="gameStore.ttsState.enabled" class="space-y-3">
            <div>
              <label class="block text-sm font-medium text-text-primary mb-1">Voice</label>
              <select
                v-model="gameStore.ttsState.voiceId"
                class="w-full rounded border-brown-400 bg-parchment-light text-text-primary focus:ring-gold"
                :disabled="gameStore.ttsState.isLoading"
                @change="handleVoiceChange"
              >
                <option value="">
                  Select a voice...
                </option>
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
                  class="rounded border-brown-400 text-gold focus:ring-gold"
                  @change="handleAutoPlayToggle"
                >
                <span class="text-sm text-text-primary">Auto-play new messages</span>
              </label>
            </div>

            <!-- Voice Preview Button -->
            <button
              v-if="gameStore.ttsState.voiceId"
              :disabled="previewLoading"
              class="w-full fantasy-button-secondary text-sm"
              @click="handleVoicePreview"
            >
              {{ previewLoading ? 'Generating...' : '🔊 Preview Voice' }}
            </button>
          </div>
        </div>
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
        <div class="flex-shrink-0 space-y-4 bg-parchment z-10">
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
          <button
            class="fantasy-button-primary w-full"
            :disabled="isGameLoading || isSaving"
            @click="handleSaveGame"
          >
            <span v-if="isSaving">💾 Saving...</span>
            <span v-else>💾 Save Game</span>
          </button>

          <!-- Retry Button -->
          <button
            v-if="uiStore.canRetryLastRequest"
            class="fantasy-button-secondary w-full"
            :disabled="isGameLoading"
            @click="handleRetryLastRequest"
          >
            🔁 Retry Last AI Request
          </button>
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

<script setup>
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
import ChatHistory from '../components/game/ChatHistory.vue'
import InputControls from '../components/game/InputControls.vue'
import DiceRequests from '../components/game/DiceRequests.vue'
import PartyPanel from '../components/game/PartyPanel.vue'
import CombatStatus from '../components/game/CombatStatus.vue'
import MapPanel from '../components/game/MapPanel.vue'

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

async function initializeGame() {
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
    console.error('Failed to initialize game:', error)
    uiStore.connectionStatus = 'error'
  } finally {
    isGameLoading.value = false
  }
}

async function loadTTSVoices() {
  try {
    await gameStore.loadTTSVoices()
  } catch (error) {
    console.error('Failed to load TTS voices:', error)
  }
}

// Monitor SSE connection status
watch(() => gameStore.isConnected, (connected) => {
  uiStore.connectionStatus = connected ? 'connected' : 'disconnected'
})

async function handleSendMessage(message) {
  isGameLoading.value = true
  try {
    await gameStore.sendMessage(message)
  } catch (error) {
    console.error('Failed to send message:', error)
  } finally {
    isGameLoading.value = false
  }
}

async function handleSubmitRolls(rollResultsFromEmit) {
  // This function is called when DiceRequests emits 'submit-rolls'
  try {
    console.log('GameView: Handling submitted rolls signal from DiceRequests.vue')
    isGameLoading.value = true
    // The actual submission is handled within DiceRequests.vue via gameStore.submitMultipleCompletedRolls
    // This function now mostly acts as a response to the emit and manages local loading state
  } catch (error) {
    console.error('Failed to handle submitted rolls:', error)
  } finally {
    isGameLoading.value = false
  }
}

async function handleRetryLastRequest() {
  console.log('Retry Last Request button clicked.')
  isGameLoading.value = true
  try {
    await gameStore.retryLastAIRequest()
  } catch (error) {
    console.error('Failed to retry last request:', error)
  } finally {
    isGameLoading.value = false
  }
}

async function handleSaveGame() {
  console.log('Save Game button clicked.')
  isSaving.value = true
  try {
    await gameStore.saveGame()
    // Show success message
    console.log('Game saved successfully!')
    // TODO: Add visual feedback for successful save
  } catch (error) {
    console.error('Failed to save game:', error)
    // TODO: Add visual feedback for save error
  } finally {
    isSaving.value = false
  }
}

// TTS Event Handlers
async function handleTTSToggle() {
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
    console.error('Failed to toggle narration:', error)
    // Revert the toggle on error
    gameStore.ttsState.enabled = !gameStore.ttsState.enabled
  }
}

async function handleVoiceChange() {
  if (gameStore.ttsState.voiceId) {
    gameStore.setTTSVoice(gameStore.ttsState.voiceId)

    // Save voice preference to game state (not campaign)
    // The backend will handle this when we call the TTS API
    // No need to update campaign directly
  }
}

function handleAutoPlayToggle() {
  gameStore.setAutoPlay(gameStore.ttsState.autoPlay)
}

function handleAutoPlayUpdate(enabled) {
  gameStore.setAutoPlay(enabled)
}

async function handleVoicePreview() {
  if (!gameStore.ttsState.voiceId) return

  previewLoading.value = true
  try {
    await gameStore.previewVoice(gameStore.ttsState.voiceId)
  } catch (error) {
    console.error('Failed to preview voice:', error)
  } finally {
    previewLoading.value = false
  }
}

// Watch for changes in store's isLoading state to handle post-API call logic
watch(() => gameStore.isLoading, (newIsLoading, oldIsLoading) => {
  console.log(`isLoading changed: ${oldIsLoading} -> ${newIsLoading}, needsBackendTrigger: ${gameState.value.needsBackendTrigger}, isTriggering: ${isTriggering.value}`);
  if (oldIsLoading === true && newIsLoading === false) {
    // An API call just finished
    if (gameState.value.needsBackendTrigger) {
      if (!gameState.value.diceRequests || gameState.value.diceRequests.length === 0) {
        console.log("isLoading watcher: Need to trigger next step...");

        // Use nextTick to ensure state is fully updated before checking
        nextTick(() => {
          if (!isTriggering.value && gameState.value.needsBackendTrigger) {
            console.log("Confirmed: Auto-triggering next step...");
            isTriggering.value = true;

            setTimeout(async () => {
              console.log("Timeout fired, calling triggerNextStep...");
              try {
                await gameStore.triggerNextStep();
                console.log("triggerNextStep completed successfully");
              } catch (error) {
                console.error("Failed to trigger next step:", error);
              } finally {
                // Reset after a short delay to allow state updates
                setTimeout(() => {
                  isTriggering.value = false;
                  console.log("Reset isTriggering to false");
                }, 100);
              }
            }, 3000); // Increased to 3 seconds to help avoid rate limits
          } else {
            console.log(`Skipping trigger - isTriggering: ${isTriggering.value}, needsBackendTrigger: ${gameState.value.needsBackendTrigger}`);
          }
        });
      } else {
        console.log("isLoading watcher: Needs backend trigger, but waiting for player dice rolls.");
      }
    } else {
      console.log(`isLoading watcher: No backend trigger needed`);
    }
  }
});

// Watch for changes in game loading state to sync with local loading state
watch(() => gameStore.isLoading, (newValue) => {
  isGameLoading.value = newValue;
});
</script>

<style scoped>
/* Component-specific styles if needed */
</style>
