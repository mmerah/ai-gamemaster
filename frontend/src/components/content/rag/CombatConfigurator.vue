<template>
  <div class="combat-configurator">
    <h5 class="combat-configurator__title">
      Combat State
    </h5>
    
    <div class="combat-configurator__settings">
      <label class="combat-configurator__toggle">
        <input
          v-model="localCombat.is_active"
          type="checkbox"
          @change="emitUpdate"
        >
        <span>Combat Active</span>
      </label>
      
      <div v-if="localCombat.is_active" class="combat-configurator__details">
        <div class="combat-configurator__field-group">
          <div class="combat-configurator__field combat-configurator__field--small">
            <label>Round:</label>
            <input
              v-model.number="localCombat.round_number"
              type="number"
              min="1"
              class="combat-configurator__input"
              @input="emitUpdate"
            >
          </div>
          <div class="combat-configurator__field combat-configurator__field--small">
            <label>Current Turn:</label>
            <select
              v-model.number="localCombat.current_turn_index"
              class="combat-configurator__select"
              @change="emitUpdate"
            >
              <option :value="-1">Not Started</option>
              <option
                v-for="(combatant, index) in localCombat.combatants"
                :key="index"
                :value="index"
              >
                {{ combatant.name }} ({{ combatant.initiative }})
              </option>
            </select>
          </div>
        </div>
        
        <div class="combat-configurator__combatants">
          <h6>Combatants</h6>
          <div
            v-for="(combatant, index) in localCombat.combatants"
            :key="combatant.id"
            class="combat-configurator__combatant"
          >
            <div class="combat-configurator__combatant-header">
              <input
                v-model="combatant.name"
                type="text"
                placeholder="Combatant name"
                class="combat-configurator__input combat-configurator__input--name"
                @input="emitUpdate"
              >
              <button
                @click="removeCombatant(index)"
                class="combat-configurator__button combat-configurator__button--remove"
                title="Remove combatant"
              >
                ✕
              </button>
            </div>
            
            <div class="combat-configurator__combatant-details">
              <div class="combat-configurator__field-group">
                <div class="combat-configurator__field">
                  <label>Type:</label>
                  <select
                    v-model="combatant.combatant_type"
                    class="combat-configurator__select"
                    @change="emitUpdate"
                  >
                    <option value="player">Player</option>
                    <option value="monster">Monster</option>
                    <option value="npc">NPC</option>
                  </select>
                </div>
                <div class="combat-configurator__field combat-configurator__field--small">
                  <label>Initiative:</label>
                  <input
                    v-model.number="combatant.initiative"
                    type="number"
                    class="combat-configurator__input"
                    @input="emitUpdate"
                  >
                </div>
                <div class="combat-configurator__field combat-configurator__field--small">
                  <label>Init Mod:</label>
                  <input
                    v-model.number="combatant.initiative_modifier"
                    type="number"
                    class="combat-configurator__input"
                    @input="emitUpdate"
                  >
                </div>
              </div>
              
              <div class="combat-configurator__field-group">
                <div class="combat-configurator__field combat-configurator__field--small">
                  <label>HP:</label>
                  <input
                    v-model.number="combatant.current_hp"
                    type="number"
                    min="0"
                    class="combat-configurator__input"
                    @input="emitUpdate"
                  >
                  <span class="combat-configurator__separator">/</span>
                  <input
                    v-model.number="combatant.max_hp"
                    type="number"
                    min="1"
                    class="combat-configurator__input"
                    @input="emitUpdate"
                  >
                </div>
                <div class="combat-configurator__field combat-configurator__field--small">
                  <label>AC:</label>
                  <input
                    v-model.number="combatant.armor_class"
                    type="number"
                    min="0"
                    class="combat-configurator__input"
                    @input="emitUpdate"
                  >
                </div>
              </div>
              
              <div class="combat-configurator__field">
                <label>Conditions:</label>
                <input
                  v-model="combatant.conditionsString"
                  type="text"
                  placeholder="e.g., stunned, prone"
                  class="combat-configurator__input"
                  @input="updateCombatantConditions(index, $event)"
                >
              </div>
              
              <details v-if="combatant.combatant_type === 'monster'" class="combat-configurator__monster-details">
                <summary>Monster Details</summary>
                <div class="combat-configurator__monster-content">
                  <div class="combat-configurator__field">
                    <label>Monster Type:</label>
                    <input
                      v-model="combatant.monster_type"
                      type="text"
                      placeholder="e.g., goblin, orc"
                      class="combat-configurator__input"
                      @input="emitUpdate"
                    >
                  </div>
                  <div class="combat-configurator__field-group">
                    <div class="combat-configurator__field combat-configurator__field--small">
                      <label>CR:</label>
                      <input
                        v-model.number="combatant.challenge_rating"
                        type="number"
                        min="0"
                        step="0.125"
                        class="combat-configurator__input"
                        @input="emitUpdate"
                      >
                    </div>
                    <div class="combat-configurator__field combat-configurator__field--small">
                      <label>Size:</label>
                      <select
                        v-model="combatant.size"
                        class="combat-configurator__select"
                        @change="emitUpdate"
                      >
                        <option value="Tiny">Tiny</option>
                        <option value="Small">Small</option>
                        <option value="Medium">Medium</option>
                        <option value="Large">Large</option>
                        <option value="Huge">Huge</option>
                        <option value="Gargantuan">Gargantuan</option>
                      </select>
                    </div>
                  </div>
                </div>
              </details>
            </div>
          </div>
          
          <button
            @click="addCombatant"
            class="combat-configurator__button combat-configurator__button--add"
          >
            + Add Combatant
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import type { CombatStateModel, CombatantModel } from '@/types/unified'

// Props
const props = defineProps<{
  modelValue: CombatStateModel
}>()

// Emits
const emit = defineEmits<{
  'update:modelValue': [value: CombatStateModel]
}>()

// Extended interface for UI convenience
interface UICombatant extends CombatantModel {
  conditionsString: string
}

interface UICombatState extends Omit<CombatStateModel, 'combatants'> {
  combatants: UICombatant[]
}

// Local state
const localCombat = ref<UICombatState>({
  is_active: false,
  combatants: [],
  current_turn_index: -1,
  round_number: 1,
  current_turn_instruction_given: false
})

// Initialize from props
watch(() => props.modelValue, (newValue) => {
  localCombat.value = {
    ...newValue,
    combatants: newValue.combatants.map(c => ({
      ...c,
      conditionsString: c.conditions?.join(', ') || ''
    }))
  }
}, { immediate: true })

// Methods
const emitUpdate = () => {
  const combatState: CombatStateModel = {
    ...localCombat.value,
    combatants: localCombat.value.combatants.map(({ conditionsString, ...combatant }) => combatant)
  }
  emit('update:modelValue', combatState)
}

const addCombatant = () => {
  const newCombatant: UICombatant = {
    id: `combatant_${Date.now()}`,
    name: `Combatant ${localCombat.value.combatants.length + 1}`,
    combatant_type: 'monster',
    initiative: 10,
    initiative_modifier: 0,
    current_hp: 10,
    max_hp: 10,
    armor_class: 10,
    conditions: [],
    is_player_controlled: false,
    is_incapacitated: false,
    has_taken_turn: false,
    // Monster-specific fields
    monster_type: 'goblin',
    challenge_rating: 0.25,
    size: 'Small',
    // UI fields
    conditionsString: ''
  }
  localCombat.value.combatants.push(newCombatant)
  emitUpdate()
}

const removeCombatant = (index: number) => {
  localCombat.value.combatants.splice(index, 1)
  // Adjust current turn index if needed
  if (localCombat.value.current_turn_index >= index && localCombat.value.current_turn_index > 0) {
    localCombat.value.current_turn_index--
  }
  emitUpdate()
}

const updateCombatantConditions = (index: number, event: Event) => {
  const target = event.target as HTMLInputElement
  const conditions = target.value
    .split(',')
    .map(c => c.trim())
    .filter(c => c.length > 0)
  localCombat.value.combatants[index].conditions = conditions
  
  // Update incapacitated status based on conditions
  const incapacitatingConditions = ['unconscious', 'paralyzed', 'petrified', 'stunned']
  localCombat.value.combatants[index].is_incapacitated = conditions.some(c => 
    incapacitatingConditions.includes(c.toLowerCase())
  )
  
  emitUpdate()
}
</script>

<style scoped>
.combat-configurator {
  background: #f8f9fa;
  padding: 1rem;
  border-radius: 6px;
  margin-bottom: 1rem;
}

.combat-configurator__title {
  margin: 0 0 1rem 0;
  font-size: 1.1rem;
  font-weight: 600;
  color: #333;
}

.combat-configurator__settings {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.combat-configurator__toggle {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  user-select: none;
}

.combat-configurator__toggle input {
  cursor: pointer;
}

.combat-configurator__details {
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  padding: 1rem;
}

.combat-configurator__field-group {
  display: flex;
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.combat-configurator__field {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  flex: 1;
}

.combat-configurator__field--small {
  flex: 0 0 auto;
  min-width: 100px;
}

.combat-configurator__field label {
  font-size: 0.85rem;
  font-weight: 500;
  color: #666;
}

.combat-configurator__input,
.combat-configurator__select {
  padding: 0.375rem 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 0.9rem;
}

.combat-configurator__separator {
  margin: 0 0.25rem;
  color: #999;
  align-self: flex-end;
  padding-bottom: 0.375rem;
}

.combat-configurator__combatants {
  border-top: 1px solid #e0e0e0;
  padding-top: 1rem;
}

.combat-configurator__combatants h6 {
  margin: 0 0 0.75rem 0;
  font-size: 1rem;
  font-weight: 600;
  color: #555;
}

.combat-configurator__combatant {
  background: #f8f9fa;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  padding: 0.75rem;
  margin-bottom: 0.75rem;
}

.combat-configurator__combatant-header {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}

.combat-configurator__input--name {
  flex: 1;
  font-weight: 500;
}

.combat-configurator__combatant-details {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.combat-configurator__button {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 4px;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s;
}

.combat-configurator__button--add {
  background: #17a2b8;
  color: white;
  margin-top: 0.5rem;
}

.combat-configurator__button--add:hover {
  background: #138496;
}

.combat-configurator__button--remove {
  background: #dc3545;
  color: white;
  padding: 0.25rem 0.5rem;
  font-size: 0.8rem;
}

.combat-configurator__button--remove:hover {
  background: #c82333;
}

.combat-configurator__monster-details {
  margin-top: 0.5rem;
}

.combat-configurator__monster-details summary {
  cursor: pointer;
  user-select: none;
  font-size: 0.9rem;
  color: #666;
  padding: 0.25rem 0;
}

.combat-configurator__monster-content {
  margin-top: 0.5rem;
  padding-top: 0.5rem;
  border-top: 1px solid #e0e0e0;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
</style>