<template>
  <div class="fantasy-panel">
    <h3 class="text-lg font-cinzel font-semibold text-text-primary mb-4">Dice Requests</h3>
    
    <div class="space-y-4">
      <div
        v-for="request in requests"
        :key="request.request_id"
        class="border border-crimson/30 rounded-lg bg-crimson/10 p-4"
      >
        <!-- Request Header -->
        <div class="mb-3">
          <h4 class="font-semibold text-text-primary">{{ getRequestLabel(request) }}</h4>
          <p class="text-sm text-text-secondary">{{ request.reason }}</p>
          <p v-if="request.dc" class="text-sm text-crimson">DC: {{ request.dc }}</p>
        </div>

        <!-- Character Rolls -->
        <div class="space-y-2">
          <div
            v-for="characterId in request.character_ids"
            :key="`${request.request_id}-${characterId}`"
            class="flex items-center justify-between p-2 bg-parchment/50 rounded"
          >
            <div class="flex-1">
              <span class="font-medium">{{ getCharacterName(characterId) }}</span>
              <span class="text-sm text-text-secondary ml-2">{{ request.dice_formula }}</span>
            </div>
            
            <!-- Roll Button or Result -->
            <div class="flex items-center space-x-2">
              <button
                v-if="!getRollResult(request.request_id, characterId)"
                @click="performRoll(request, characterId)"
                :disabled="isRolling"
                class="fantasy-button-secondary px-3 py-1 text-sm"
              >
                <span v-if="isRolling">🎲 Rolling...</span>
                <span v-else>🎲 Roll</span>
              </button>
              
              <div
                v-else
                class="text-sm px-3 py-1 rounded"
                :class="getRollResultClass(request.request_id, characterId)"
              >
                {{ getRollResultText(request.request_id, characterId) }}
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Submit Rolls Button -->
      <div v-if="hasCompletedRolls" class="text-center mt-4">
        <button
          @click="submitAllRolls"
          :disabled="isSubmitting"
          class="fantasy-button-primary px-6 py-2"
        >
          <span v-if="isSubmitting">Submitting...</span>
          <span v-else>Submit Completed Rolls ({{ completedRolls.length }})</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useGameStore } from '../../stores/gameStore'

const props = defineProps({
  requests: {
    type: Array,
    required: true
  },
  party: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['roll-dice', 'submit-rolls'])
const gameStore = useGameStore()

const isRolling = ref(false)
const isSubmitting = ref(false)
const rollResults = ref(new Map()) // Map of `${requestId}-${characterId}` -> rollResult

const completedRolls = computed(() => {
  return Array.from(rollResults.value.values())
})

const hasCompletedRolls = computed(() => {
  return completedRolls.value.length > 0
})

function getRequestLabel(request) {
  if (request.type === 'skill_check' && request.skill) {
    return request.skill.charAt(0).toUpperCase() + request.skill.slice(1) + " Check"
  } else if (request.type === 'saving_throw' && request.ability) {
    return request.ability.toUpperCase() + " Save"
  } else if (request.type === 'initiative') {
    return "Initiative"
  } else if (request.type) {
    return request.type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())
  }
  return request.reason || 'Dice Roll'
}

function getCharacterName(characterId) {
  const character = props.party.find(c => c.id === characterId)
  return character ? character.name : `Character ${characterId}`
}

function getRollResult(requestId, characterId) {
  return rollResults.value.get(`${requestId}-${characterId}`)
}

function getRollResultClass(requestId, characterId) {
  const result = getRollResult(requestId, characterId)
  if (!result) return ''
  
  if (result.success === true) return 'bg-forest-light text-parchment'
  if (result.success === false) return 'bg-crimson text-parchment'
  return 'bg-gold text-primary-dark'
}

function getRollResultText(requestId, characterId) {
  const result = getRollResult(requestId, characterId)
  if (!result) return ''
  
  return result.result_message || `Rolled ${result.total_result}`
}

async function performRoll(request, characterId) {
  try {
    isRolling.value = true
    console.log('Performing roll for:', { request, characterId })
    
    const rollParams = {
      request_id: request.request_id,
      character_id: characterId,
      roll_type: request.type,
      dice_formula: request.dice_formula,
      skill: request.skill || undefined,
      ability: request.ability || undefined,
      dc: request.dc ? parseInt(request.dc, 10) : undefined,
      reason: request.reason
    }
    
    const rollResult = await gameStore.performRoll(rollParams)
    
    if (rollResult && !rollResult.error) {
      // Store the roll result
      rollResults.value.set(`${request.request_id}-${characterId}`, rollResult)
      console.log('Roll completed:', rollResult)
    } else {
      console.error('Roll failed:', rollResult?.error || 'Unknown error')
    }
  } catch (error) {
    console.error('Error performing roll:', error)
  } finally {
    isRolling.value = false
  }
}

async function submitAllRolls() {
  try {
    isSubmitting.value = true
    const rollsToSubmit = Array.from(rollResults.value.values())
    console.log('Submitting all completed rolls:', rollsToSubmit)
    
    if (rollsToSubmit.length > 0) {
      // Call the correct store action with the collected rolls
      await gameStore.submitMultipleCompletedRolls(rollsToSubmit)
    } else {
      console.warn("No rolls to submit.")
    }
    
    rollResults.value.clear() // Clear local results after successful submission
    
    emit('submit-rolls', rollsToSubmit)
  } catch (error) {
    console.error('Error submitting rolls:', error)
    // Optionally, add a local error message for the user in this component
  } finally {
    isSubmitting.value = false
  }
}
</script>
