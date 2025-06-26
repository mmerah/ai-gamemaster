<template>
  <div class="party-configurator">
    <h5 class="party-configurator__title">
      Party Members
    </h5>
    
    <div class="party-configurator__members">
      <div 
        v-for="(member, index) in localParty" 
        :key="member.id" 
        class="party-configurator__member"
      >
        <div class="party-configurator__member-header">
          <input
            v-model="member.name"
            type="text"
            placeholder="Character name"
            class="party-configurator__input party-configurator__input--name"
            @input="emitUpdate"
          >
          <button
            @click="removeMember(index)"
            class="party-configurator__button party-configurator__button--remove"
            title="Remove character"
          >
            ✕
          </button>
        </div>
        
        <div class="party-configurator__member-details">
          <div class="party-configurator__field-group">
            <div class="party-configurator__field">
              <label>Class:</label>
              <input
                v-model="member.char_class"
                type="text"
                placeholder="e.g., Fighter, Wizard"
                class="party-configurator__input"
                @input="emitUpdate"
              >
            </div>
            <div class="party-configurator__field">
              <label>Race:</label>
              <input
                v-model="member.race"
                type="text"
                placeholder="e.g., Human, Elf"
                class="party-configurator__input"
                @input="emitUpdate"
              >
            </div>
            <div class="party-configurator__field party-configurator__field--small">
              <label>Level:</label>
              <input
                v-model.number="member.level"
                type="number"
                min="1"
                max="20"
                class="party-configurator__input"
                @input="emitUpdate"
              >
            </div>
          </div>
          
          <div class="party-configurator__field-group">
            <div class="party-configurator__field party-configurator__field--small">
              <label>HP:</label>
              <input
                v-model.number="member.current_hp"
                type="number"
                min="0"
                class="party-configurator__input"
                @input="emitUpdate"
              >
              <span class="party-configurator__separator">/</span>
              <input
                v-model.number="member.max_hp"
                type="number"
                min="1"
                class="party-configurator__input"
                @input="emitUpdate"
              >
            </div>
            <div class="party-configurator__field">
              <label>Conditions:</label>
              <input
                v-model="member.conditionsString"
                type="text"
                placeholder="e.g., poisoned, prone"
                class="party-configurator__input"
                @input="updateConditions(index, $event)"
              >
            </div>
          </div>
          
          <div class="party-configurator__field">
            <label>Equipment:</label>
            <textarea
              v-model="member.equipmentString"
              rows="2"
              placeholder="e.g., Longsword, Shield, Plate Armor"
              class="party-configurator__textarea"
              @input="updateEquipment(index, $event)"
            />
          </div>
          
          <details class="party-configurator__advanced">
            <summary>Advanced Settings</summary>
            <div class="party-configurator__advanced-content">
              <div class="party-configurator__field-group">
                <div class="party-configurator__field party-configurator__field--small">
                  <label>Gold:</label>
                  <input
                    v-model.number="member.gold"
                    type="number"
                    min="0"
                    class="party-configurator__input"
                    @input="emitUpdate"
                  >
                </div>
                <div class="party-configurator__field party-configurator__field--small">
                  <label>XP:</label>
                  <input
                    v-model.number="member.experience_points"
                    type="number"
                    min="0"
                    class="party-configurator__input"
                    @input="emitUpdate"
                  >
                </div>
                <div class="party-configurator__field party-configurator__field--small">
                  <label>Exhaustion:</label>
                  <input
                    v-model.number="member.exhaustion_level"
                    type="number"
                    min="0"
                    max="6"
                    class="party-configurator__input"
                    @input="emitUpdate"
                  >
                </div>
              </div>
              <div class="party-configurator__field">
                <label>Spell Slots Used (JSON):</label>
                <input
                  v-model="member.spellSlotsString"
                  type="text"
                  placeholder='{"1": 2, "2": 1}'
                  class="party-configurator__input"
                  @input="updateSpellSlots(index, $event)"
                >
              </div>
            </div>
          </details>
        </div>
      </div>
    </div>
    
    <button
      @click="addMember"
      class="party-configurator__button party-configurator__button--add"
    >
      + Add Party Member
    </button>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import type { CharacterInstanceModel } from '@/types/unified'

// Props
const props = defineProps<{
  modelValue: Record<string, CharacterInstanceModel>
}>()

// Emits
const emit = defineEmits<{
  'update:modelValue': [value: Record<string, CharacterInstanceModel>]
}>()

// Extended interface for UI convenience
interface UICharacterInstance extends CharacterInstanceModel {
  conditionsString: string
  equipmentString: string
  spellSlotsString: string
  char_class?: string
  race?: string
}

// Local state
const localParty = ref<UICharacterInstance[]>([])

// Initialize from props
watch(() => props.modelValue, (newValue) => {
  localParty.value = Object.values(newValue).map(char => ({
    ...char,
    char_class: 'Fighter', // Default class
    race: 'Human', // Default race
    conditionsString: char.conditions.join(', '),
    equipmentString: char.inventory.map(item => item.name).join(', '),
    spellSlotsString: JSON.stringify(char.spell_slots_used)
  }))
}, { immediate: true })

// Methods
const emitUpdate = () => {
  const partyDict: Record<string, CharacterInstanceModel> = {}
  localParty.value.forEach(member => {
    const { conditionsString, equipmentString, spellSlotsString, char_class, race, ...baseChar } = member
    partyDict[member.id] = baseChar
  })
  emit('update:modelValue', partyDict)
}

const addMember = () => {
  const newId = `char_${Date.now()}`
  const newMember: UICharacterInstance = {
    version: 1,
    id: newId,
    name: `Character ${localParty.value.length + 1}`,
    template_id: 'test_template',
    campaign_id: 'test_campaign',
    current_hp: 10,
    max_hp: 10,
    temp_hp: 0,
    experience_points: 0,
    level: 1,
    spell_slots_used: {},
    hit_dice_used: 0,
    death_saves: { successes: 0, failures: 0 },
    inventory: [],
    gold: 0,
    conditions: [],
    exhaustion_level: 0,
    notes: '',
    achievements: [],
    relationships: {},
    last_played: new Date().toISOString(),
    // UI fields
    char_class: 'Fighter',
    race: 'Human',
    conditionsString: '',
    equipmentString: '',
    spellSlotsString: '{}'
  }
  localParty.value.push(newMember)
  emitUpdate()
}

const removeMember = (index: number) => {
  localParty.value.splice(index, 1)
  emitUpdate()
}

const updateConditions = (index: number, event: Event) => {
  const target = event.target as HTMLInputElement
  const conditions = target.value
    .split(',')
    .map(c => c.trim())
    .filter(c => c.length > 0)
  localParty.value[index].conditions = conditions
  emitUpdate()
}

const updateEquipment = (index: number, event: Event) => {
  const target = event.target as HTMLTextAreaElement
  const items = target.value
    .split(',')
    .map(name => name.trim())
    .filter(name => name.length > 0)
    .map((name, i) => ({
      id: `item_${Date.now()}_${i}`,
      name,
      description: '',
      quantity: 1
    }))
  localParty.value[index].inventory = items
  emitUpdate()
}

const updateSpellSlots = (index: number, event: Event) => {
  const target = event.target as HTMLInputElement
  try {
    const slots = JSON.parse(target.value || '{}')
    localParty.value[index].spell_slots_used = slots
    emitUpdate()
  } catch {
    // Invalid JSON, ignore
  }
}
</script>

<style scoped>
.party-configurator {
  background: #f8f9fa;
  padding: 1rem;
  border-radius: 6px;
  margin-bottom: 1rem;
}

.party-configurator__title {
  margin: 0 0 1rem 0;
  font-size: 1.1rem;
  font-weight: 600;
  color: #333;
}

.party-configurator__members {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.party-configurator__member {
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  padding: 1rem;
}

.party-configurator__member-header {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
}

.party-configurator__input--name {
  flex: 1;
  font-weight: 500;
}

.party-configurator__member-details {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.party-configurator__field-group {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.party-configurator__field {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  flex: 1;
  min-width: 120px;
}

.party-configurator__field--small {
  flex: 0 0 auto;
  min-width: 80px;
}

.party-configurator__field label {
  font-size: 0.85rem;
  font-weight: 500;
  color: #666;
}

.party-configurator__input,
.party-configurator__textarea {
  padding: 0.375rem 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 0.9rem;
}

.party-configurator__textarea {
  resize: vertical;
  min-height: 50px;
}

.party-configurator__separator {
  margin: 0 0.25rem;
  color: #999;
  align-self: flex-end;
  padding-bottom: 0.375rem;
}

.party-configurator__button {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 4px;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s;
}

.party-configurator__button--add {
  background: #28a745;
  color: white;
  margin-top: 1rem;
}

.party-configurator__button--add:hover {
  background: #218838;
}

.party-configurator__button--remove {
  background: #dc3545;
  color: white;
  padding: 0.25rem 0.5rem;
  font-size: 0.8rem;
}

.party-configurator__button--remove:hover {
  background: #c82333;
}

.party-configurator__advanced {
  margin-top: 0.5rem;
}

.party-configurator__advanced summary {
  cursor: pointer;
  user-select: none;
  font-size: 0.9rem;
  color: #666;
  padding: 0.25rem 0;
}

.party-configurator__advanced-content {
  margin-top: 0.75rem;
  padding-top: 0.75rem;
  border-top: 1px solid #e0e0e0;
}
</style>