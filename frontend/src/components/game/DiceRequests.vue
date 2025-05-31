<template>
  <div class="fantasy-panel">
    <h3 class="text-lg font-cinzel font-semibold text-text-primary mb-4">Dice Requests</h3>
    
    <div class="space-y-4">
      <div
        v-for="group in groupedRequests"
        :key="group.request_id"
        class="border border-crimson/30 rounded-lg bg-crimson/10 p-4"
      >
        <!-- Request Header -->
        <div class="mb-3">
          <h4 class="font-semibold text-text-primary">{{ getRequestLabel(group) }}</h4>
          <p class="text-sm text-text-secondary">{{ group.reason }}</p>
          <p v-if="group.dc" class="text-sm text-crimson">DC: {{ group.dc }}</p>
        </div>

        <!-- Character Rolls -->
        <div class="space-y-2">
          <div
            v-for="character in group.characters"
            :key="character.character_id"
            class="flex items-center justify-between p-2 bg-parchment/50 rounded"
          >
            <div class="flex-1">
              <span class="font-medium">{{ character.character_name }}</span>
              <span class="text-sm text-text-secondary ml-2">{{ group.dice_formula }}</span>
            </div>
            
            <!-- Roll Button or Result -->
            <div class="flex items-center space-x-2">
              <button
                v-if="!getRollResult(group.request_id, character.character_id)"
                @click="performRoll(group, character)"
                :disabled="isRolling"
                class="fantasy-button-secondary px-3 py-1 text-sm"
              >
                <span v-if="isRolling">🎲 Rolling...</span>
                <span v-else>🎲 Roll</span>
              </button>
              
              <div
                v-else
                class="text-sm px-3 py-1 rounded"
                :class="getRollResultClass(group.request_id, character.character_id)"
              >
                {{ getRollResultText(group.request_id, character.character_id) }}
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
import { useDiceStore } from '../../stores/diceStore'
import { usePartyStore } from '../../stores/partyStore'

const emit = defineEmits(['roll-dice', 'submit-rolls'])
const gameStore = useGameStore()
const diceStore = useDiceStore()
const partyStore = usePartyStore()

// Use dice store for requests and party store for party data
const requests = computed(() => diceStore.pendingRequests)
const party = computed(() => partyStore.members)

// Group requests by request_id for better UI
const groupedRequests = computed(() => {
  const groups = new Map()
  
  requests.value.forEach(request => {
    if (!groups.has(request.request_id)) {
      groups.set(request.request_id, {
        request_id: request.request_id,
        roll_type: request.roll_type,
        type: request.type,
        reason: request.reason || request.purpose,
        dice_formula: request.dice_formula,
        dc: request.dc,
        characters: []
      })
    }
    
    groups.get(request.request_id).characters.push({
      character_id: request.character_id,
      character_name: request.character_name,
      skill: request.skill,
      ability: request.ability
    })
  })
  
  return Array.from(groups.values())
})

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
  const rollType = request.type || request.roll_type
  
  if (rollType === 'skill_check' && request.skill) {
    return request.skill.charAt(0).toUpperCase() + request.skill.slice(1) + " Check"
  } else if (rollType === 'saving_throw' && request.ability) {
    return request.ability.toUpperCase() + " Save"
  } else if (rollType === 'initiative') {
    return "Initiative"
  } else if (rollType) {
    return rollType.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())
  }
  return request.reason || request.purpose || 'Dice Roll'
}

function getCharacterName(characterId) {
  const character = party.value.find(c => c.id === characterId)
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

async function performRoll(group, character) {
  try {
    isRolling.value = true
    console.log('Performing roll for:', { group, character })
    
    const rollParams = {
      request_id: group.request_id,
      character_id: character.character_id,
      roll_type: group.type || group.roll_type,
      dice_formula: group.dice_formula,
      skill: character.skill || undefined,
      ability: character.ability || undefined,
      dc: group.dc ? parseInt(group.dc, 10) : undefined,
      reason: group.reason
    }
    
    const rollResult = await gameStore.performRoll(rollParams)
    
    if (rollResult && !rollResult.error) {
      // Store the roll result
      rollResults.value.set(`${group.request_id}-${character.character_id}`, rollResult)
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
