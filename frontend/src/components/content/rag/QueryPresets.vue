<template>
  <div class="query-presets">
    <h5 class="query-presets__title">
      Query Presets
    </h5>
    
    <div class="query-presets__categories">
      <!-- Combat Actions -->
      <div class="query-presets__category">
        <h6>Combat Actions</h6>
        <div class="query-presets__preset-list">
          <button
            v-for="preset in combatPresets"
            :key="preset.id"
            @click="applyPreset(preset)"
            class="query-presets__preset"
            :title="preset.description"
          >
            {{ preset.name }}
          </button>
        </div>
      </div>
      
      <!-- Skill Checks -->
      <div class="query-presets__category">
        <h6>Skill Checks</h6>
        <div class="query-presets__preset-list">
          <button
            v-for="preset in skillPresets"
            :key="preset.id"
            @click="applyPreset(preset)"
            class="query-presets__preset"
            :title="preset.description"
          >
            {{ preset.name }}
          </button>
        </div>
      </div>
      
      <!-- Spellcasting -->
      <div class="query-presets__category">
        <h6>Spellcasting</h6>
        <div class="query-presets__preset-list">
          <button
            v-for="preset in spellPresets"
            :key="preset.id"
            @click="applyPreset(preset)"
            class="query-presets__preset"
            :title="preset.description"
          >
            {{ preset.name }}
          </button>
        </div>
      </div>
      
      <!-- Social Interaction -->
      <div class="query-presets__category">
        <h6>Social Interaction</h6>
        <div class="query-presets__preset-list">
          <button
            v-for="preset in socialPresets"
            :key="preset.id"
            @click="applyPreset(preset)"
            class="query-presets__preset"
            :title="preset.description"
          >
            {{ preset.name }}
          </button>
        </div>
      </div>
      
      <!-- Equipment & Shopping -->
      <div class="query-presets__category">
        <h6>Equipment & Shopping</h6>
        <div class="query-presets__preset-list">
          <button
            v-for="preset in equipmentPresets"
            :key="preset.id"
            @click="applyPreset(preset)"
            class="query-presets__preset"
            :title="preset.description"
          >
            {{ preset.name }}
          </button>
        </div>
      </div>
      
      <!-- Rules & Character Info -->
      <div class="query-presets__category">
        <h6>Rules & Character Info</h6>
        <div class="query-presets__preset-list">
          <button
            v-for="preset in rulesPresets"
            :key="preset.id"
            @click="applyPreset(preset)"
            class="query-presets__preset"
            :title="preset.description"
          >
            {{ preset.name }}
          </button>
        </div>
      </div>
    </div>
    
    <!-- Custom Presets -->
    <div class="query-presets__custom">
      <h6>Custom Presets</h6>
      <div class="query-presets__custom-controls">
        <input
          v-model="newPresetName"
          type="text"
          placeholder="Preset name"
          class="query-presets__input"
          @keyup.enter="saveCustomPreset"
        >
        <button
          @click="saveCustomPreset"
          :disabled="!newPresetName || !currentQuery"
          class="query-presets__button query-presets__button--save"
        >
          Save Current Query
        </button>
      </div>
      <div v-if="customPresets.length > 0" class="query-presets__preset-list">
        <div
          v-for="preset in customPresets"
          :key="preset.id"
          class="query-presets__custom-preset"
        >
          <button
            @click="applyPreset(preset)"
            class="query-presets__preset"
            :title="preset.query"
          >
            {{ preset.name }}
          </button>
          <button
            @click="removeCustomPreset(preset.id)"
            class="query-presets__button query-presets__button--remove"
            title="Remove preset"
          >
            ✕
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import type { QueryPreset } from '@/types/ui'

// Props
const props = defineProps<{
  currentQuery: string
}>()

// Emits
const emit = defineEmits<{
  applyPreset: [preset: QueryPreset]
}>()

// Local state
const newPresetName = ref('')
const customPresets = ref<QueryPreset[]>([])

// Predefined presets
const combatPresets: QueryPreset[] = [
  {
    id: 'combat_1',
    name: 'Attack with Weapon',
    query: 'I attack the goblin with my shortsword',
    description: 'Basic melee attack',
    gameStateOverrides: { in_combat: true, addCombatants: true }
  },
  {
    id: 'combat_2',
    name: 'Ranged Attack',
    query: 'I shoot my longbow at the orc archer',
    description: 'Ranged weapon attack',
    gameStateOverrides: { in_combat: true, addCombatants: true }
  },
  {
    id: 'combat_3',
    name: 'Multiple Targets',
    query: 'I want to attack both goblins with my greatsword',
    description: 'Attack multiple enemies',
    gameStateOverrides: { in_combat: true, addCombatants: true }
  },
  {
    id: 'combat_4',
    name: 'Defensive Action',
    query: 'I take the dodge action and move behind cover',
    description: 'Defensive combat action',
    gameStateOverrides: { in_combat: true }
  }
]

const skillPresets: QueryPreset[] = [
  {
    id: 'skill_1',
    name: 'Persuasion Check',
    query: 'I try to persuade the guard to let us pass',
    description: 'Social skill check'
  },
  {
    id: 'skill_2',
    name: 'Stealth Check',
    query: 'I attempt to sneak past the sleeping dragon',
    description: 'Stealth skill check'
  },
  {
    id: 'skill_3',
    name: 'Investigation',
    query: 'I search the room for hidden doors or traps',
    description: 'Investigation check'
  },
  {
    id: 'skill_4',
    name: 'Athletics Check',
    query: 'I try to climb the castle wall',
    description: 'Physical skill check'
  }
]

const spellPresets: QueryPreset[] = [
  {
    id: 'spell_1',
    name: 'Fireball',
    query: 'I cast fireball at the group of enemies',
    description: 'Area damage spell',
    gameStateOverrides: { in_combat: true, addCombatants: true }
  },
  {
    id: 'spell_2',
    name: 'Healing Spell',
    query: 'I cast cure wounds on the injured fighter',
    description: 'Healing spell',
    gameStateOverrides: { addPartyMembers: true }
  },
  {
    id: 'spell_3',
    name: 'Utility Spell',
    query: 'I cast detect magic to scan the room',
    description: 'Utility spell'
  },
  {
    id: 'spell_4',
    name: 'Buff Spell',
    query: 'I cast haste on our rogue before combat',
    description: 'Enhancement spell',
    gameStateOverrides: { addPartyMembers: true }
  }
]

const socialPresets: QueryPreset[] = [
  {
    id: 'social_1',
    name: 'Negotiate Price',
    query: 'I try to haggle with the merchant for a better price',
    description: 'Commerce interaction',
    gameStateOverrides: { current_location: 'Marketplace' }
  },
  {
    id: 'social_2',
    name: 'Gather Information',
    query: 'I ask the bartender about recent rumors',
    description: 'Information gathering',
    gameStateOverrides: { current_location: 'Tavern' }
  },
  {
    id: 'social_3',
    name: 'Intimidation',
    query: 'I intimidate the bandit to reveal their hideout',
    description: 'Intimidation check'
  },
  {
    id: 'social_4',
    name: 'Deception',
    query: 'I lie to the guard about our purpose here',
    description: 'Deception check'
  }
]

const equipmentPresets: QueryPreset[] = [
  {
    id: 'equip_1',
    name: 'Buy Weapon',
    query: 'I want to buy a longsword from the blacksmith',
    description: 'Purchase weapon',
    gameStateOverrides: { current_location: 'Blacksmith Shop' }
  },
  {
    id: 'equip_2',
    name: 'Sell Items',
    query: 'I want to sell these goblin weapons we found',
    description: 'Sell equipment'
  },
  {
    id: 'equip_3',
    name: 'Check Equipment',
    query: 'What equipment do I currently have?',
    description: 'Inventory check',
    gameStateOverrides: { addPartyMembers: true }
  },
  {
    id: 'equip_4',
    name: 'Identify Item',
    query: 'I examine the magical sword we found',
    description: 'Item identification'
  }
]

const rulesPresets: QueryPreset[] = [
  {
    id: 'rules_1',
    name: 'Class Features',
    query: 'What abilities does a level 5 fighter have?',
    description: 'Class information lookup'
  },
  {
    id: 'rules_2',
    name: 'Spell Details',
    query: 'How does counterspell work?',
    description: 'Spell rules lookup'
  },
  {
    id: 'rules_3',
    name: 'Condition Rules',
    query: 'What happens when someone is paralyzed?',
    description: 'Condition rules'
  },
  {
    id: 'rules_4',
    name: 'Race Features',
    query: 'What are the traits of a hill dwarf?',
    description: 'Race information'
  },
  {
    id: 'rules_5',
    name: 'Multiclassing',
    query: 'What are the requirements for multiclassing into wizard?',
    description: 'Multiclassing rules'
  },
  {
    id: 'rules_6',
    name: 'Level Progression',
    query: 'What do rogues get when they reach level 3?',
    description: 'Level progression info'
  }
]

// Methods
const applyPreset = (preset: QueryPreset) => {
  emit('applyPreset', preset)
}

const saveCustomPreset = () => {
  if (!newPresetName.value || !props.currentQuery) return
  
  const newPreset: QueryPreset = {
    id: `custom_${Date.now()}`,
    name: newPresetName.value,
    query: props.currentQuery
  }
  
  customPresets.value.push(newPreset)
  localStorage.setItem('ragTesterCustomPresets', JSON.stringify(customPresets.value))
  newPresetName.value = ''
}

const removeCustomPreset = (id: string) => {
  customPresets.value = customPresets.value.filter(p => p.id !== id)
  localStorage.setItem('ragTesterCustomPresets', JSON.stringify(customPresets.value))
}

// Load custom presets on mount
onMounted(() => {
  const saved = localStorage.getItem('ragTesterCustomPresets')
  if (saved) {
    try {
      customPresets.value = JSON.parse(saved)
    } catch (e) {
      console.error('Failed to load custom presets:', e)
    }
  }
})
</script>

<style scoped>
.query-presets {
  background: #f8f9fa;
  padding: 1rem;
  border-radius: 6px;
  margin-bottom: 1rem;
}

.query-presets__title {
  margin: 0 0 1rem 0;
  font-size: 1.1rem;
  font-weight: 600;
  color: #333;
}

.query-presets__categories {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.query-presets__category {
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  padding: 0.75rem;
}

.query-presets__category h6 {
  margin: 0 0 0.5rem 0;
  font-size: 0.95rem;
  font-weight: 600;
  color: #555;
}

.query-presets__preset-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.query-presets__preset {
  padding: 0.375rem 0.75rem;
  background: #e9ecef;
  border: 1px solid #dee2e6;
  border-radius: 4px;
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.2s;
}

.query-presets__preset:hover {
  background: #007bff;
  color: white;
  border-color: #007bff;
}

.query-presets__custom {
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  padding: 1rem;
}

.query-presets__custom h6 {
  margin: 0 0 0.75rem 0;
  font-size: 0.95rem;
  font-weight: 600;
  color: #555;
}

.query-presets__custom-controls {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
}

.query-presets__input {
  flex: 1;
  padding: 0.375rem 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 0.9rem;
}

.query-presets__button {
  padding: 0.375rem 0.75rem;
  border: none;
  border-radius: 4px;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s;
}

.query-presets__button--save {
  background: #28a745;
  color: white;
}

.query-presets__button--save:hover:not(:disabled) {
  background: #218838;
}

.query-presets__button--save:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.query-presets__custom-preset {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
}

.query-presets__button--remove {
  background: #dc3545;
  color: white;
  padding: 0.25rem 0.5rem;
  font-size: 0.75rem;
}

.query-presets__button--remove:hover {
  background: #c82333;
}
</style>