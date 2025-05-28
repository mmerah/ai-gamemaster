<template>
  <div class="game-view h-screen bg-parchment overflow-hidden">
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
          <h3 class="text-lg font-cinzel font-semibold text-text-primary mb-4">Voice Settings</h3>
          
          <!-- TTS Enable Toggle -->
          <div class="mb-4">
            <label class="flex items-center space-x-2">
              <input
                type="checkbox"
                v-model="gameStore.ttsState.enabled"
                @change="handleTTSToggle"
                class="rounded border-brown-400 text-gold focus:ring-gold"
              />
              <span class="text-sm text-text-primary">Enable Narration</span>
            </label>
          </div>
          
          <!-- Voice Selection -->
          <div v-if="gameStore.ttsState.enabled" class="space-y-3">
            <div>
              <label class="block text-sm font-medium text-text-primary mb-1">Voice</label>
              <select
                v-model="gameStore.ttsState.voiceId"
                @change="handleVoiceChange"
                class="w-full rounded border-brown-400 bg-parchment-light text-text-primary focus:ring-gold"
                :disabled="gameStore.ttsState.isLoading"
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
                  type="checkbox"
                  v-model="gameStore.ttsState.autoPlay"
                  @change="handleAutoPlayToggle"
                  :disabled="!gameStore.ttsState.voiceId"
                  class="rounded border-brown-400 text-gold focus:ring-gold"
                />
                <span class="text-sm text-text-primary">Auto-play new messages</span>
              </label>
            </div>
            
            <!-- Voice Preview Button -->
            <button
              v-if="gameStore.ttsState.voiceId"
              @click="handleVoicePreview"
              :disabled="previewLoading"
              class="w-full fantasy-button-secondary text-sm"
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
            :messages="gameState.chatHistory" 
            :is-loading="isGameLoading"
            :tts-enabled="gameStore.ttsState.enabled"
            :auto-play="gameStore.ttsState.autoPlay"
            :voice-id="gameStore.ttsState.voiceId"
            @update:auto-play="handleAutoPlayUpdate"
            class="h-full"
          />
        </div>

        <!-- Bottom Section: Dice Requests and Input Controls -->
        <div class="flex-shrink-0 space-y-4 bg-parchment z-10">
          <!-- Dice Requests (if any) -->
          <DiceRequests 
            v-if="gameState.diceRequests?.length"
            :requests="gameState.diceRequests"
            :party="gameState.party"
            @submit-rolls="handleSubmitRolls"
          />

          <!-- Input Controls -->
          <InputControls 
            @send-message="handleSendMessage"
            :disabled="isGameLoading || gameState.diceRequests?.length > 0"
          />
        </div>
      </div>

      <!-- Right Column: Game Panels -->
      <div class="lg:col-span-1 space-y-6">
        <!-- Retry Button -->
        <button 
          v-if="gameState.canRetryLastRequest" 
          @click="handleRetryLastRequest" 
          class="fantasy-button-secondary w-full"
          :disabled="isGameLoading"
        >
          🔁 Retry Last AI Request
        </button>
        
        <!-- Party Panel -->
        <PartyPanel :party="gameState.party" />

        <!-- Combat Status (if in combat) -->
        <CombatStatus 
          v-if="gameState.combatState?.is_active"
          :combatState="gameState.combatState"
          :party="gameState.party"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, computed, nextTick } from 'vue'
import { useGameStore } from '../stores/gameStore'
import { useCampaignStore } from '../stores/campaignStore'
import ChatHistory from '../components/game/ChatHistory.vue'
import InputControls from '../components/game/InputControls.vue'
import DiceRequests from '../components/game/DiceRequests.vue'
import PartyPanel from '../components/game/PartyPanel.vue'
import CombatStatus from '../components/game/CombatStatus.vue'
import MapPanel from '../components/game/MapPanel.vue'

const gameStore = useGameStore()
const campaignStore = useCampaignStore()

const isGameLoading = ref(false)
const connectionStatus = ref('connecting')
const previewLoading = ref(false)
const isTriggering = ref(false)

// Computed properties
const gameState = computed(() => gameStore.gameState)

onMounted(async () => {
  // Initialize game connection
  await initializeGame()
  
  // Load TTS voices
  await loadTTSVoices()
  
  // Set up polling for game state updates - increased interval to reduce server load
  const pollInterval = setInterval(pollGameState, 10000)
  
  onUnmounted(() => {
    clearInterval(pollInterval)
  })
})

async function initializeGame() {
  isGameLoading.value = true
  connectionStatus.value = 'connecting'
  
  try {
    await gameStore.initializeGame()
    connectionStatus.value = 'connected'
    
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
    connectionStatus.value = 'error'
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

async function pollGameState() {
  // Skip polling if the game is currently processing a request
  if (gameStore.isLoading) {
    console.log("Polling skipped: game is busy.")
    return;
  }

  try {
    await gameStore.pollGameState()
    if (connectionStatus.value !== 'connected') {
      connectionStatus.value = 'connected'
    }
  } catch (error) {
    console.error('Failed to poll game state:', error)
    connectionStatus.value = 'error'
  }
}

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

// TTS Event Handlers
async function handleTTSToggle() {
  if (gameStore.ttsState.enabled) {
    gameStore.enableTTS()
  } else {
    gameStore.disableTTS()
  }
  
  // Save preference to campaign
  const campaignId = gameState.value?.campaignId
  if (campaignId) {
    try {
      await campaignStore.updateCampaign(campaignId, {
        narration_enabled: gameStore.ttsState.enabled
      })
    } catch (error) {
      console.error('Failed to save narration preference:', error)
    }
  }
}

async function handleVoiceChange() {
  if (gameStore.ttsState.voiceId) {
    gameStore.setTTSVoice(gameStore.ttsState.voiceId)
    
    // Save voice preference to campaign
    const campaignId = gameState.value?.campaignId
    if (campaignId) {
      try {
        await campaignStore.updateCampaign(campaignId, {
          tts_voice: gameStore.ttsState.voiceId
        })
      } catch (error) {
        console.error('Failed to save voice preference:', error)
      }
    }
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
