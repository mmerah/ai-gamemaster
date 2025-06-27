<template>
  <BasePanel class="query-presets mb-6">
    <h5 class="text-lg font-semibold mb-4 text-foreground">Query Presets</h5>

    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
      <!-- Combat Actions -->
      <AppCard variant="subtle" padding="sm">
        <h6 class="font-medium mb-2 text-foreground">Combat Actions</h6>
        <div class="flex flex-wrap gap-2">
          <AppButton
            v-for="preset in combatPresets"
            :key="preset.id"
            variant="secondary"
            size="sm"
            :title="preset.description"
            @click="applyPreset(preset)"
          >
            {{ preset.name }}
          </AppButton>
        </div>
      </AppCard>

      <!-- Skill Checks -->
      <AppCard variant="subtle" padding="sm">
        <h6 class="font-medium mb-2 text-foreground">Skill Checks</h6>
        <div class="flex flex-wrap gap-2">
          <AppButton
            v-for="preset in skillPresets"
            :key="preset.id"
            variant="secondary"
            size="sm"
            :title="preset.description"
            @click="applyPreset(preset)"
          >
            {{ preset.name }}
          </AppButton>
        </div>
      </AppCard>

      <!-- Spellcasting -->
      <AppCard variant="subtle" padding="sm">
        <h6 class="font-medium mb-2 text-foreground">Spellcasting</h6>
        <div class="flex flex-wrap gap-2">
          <AppButton
            v-for="preset in spellPresets"
            :key="preset.id"
            variant="secondary"
            size="sm"
            :title="preset.description"
            @click="applyPreset(preset)"
          >
            {{ preset.name }}
          </AppButton>
        </div>
      </AppCard>

      <!-- Social Interaction -->
      <AppCard variant="subtle" padding="sm">
        <h6 class="font-medium mb-2 text-foreground">Social Interaction</h6>
        <div class="flex flex-wrap gap-2">
          <AppButton
            v-for="preset in socialPresets"
            :key="preset.id"
            variant="secondary"
            size="sm"
            :title="preset.description"
            @click="applyPreset(preset)"
          >
            {{ preset.name }}
          </AppButton>
        </div>
      </AppCard>

      <!-- Equipment & Shopping -->
      <AppCard variant="subtle" padding="sm">
        <h6 class="font-medium mb-2 text-foreground">Equipment & Shopping</h6>
        <div class="flex flex-wrap gap-2">
          <AppButton
            v-for="preset in equipmentPresets"
            :key="preset.id"
            variant="secondary"
            size="sm"
            :title="preset.description"
            @click="applyPreset(preset)"
          >
            {{ preset.name }}
          </AppButton>
        </div>
      </AppCard>

      <!-- Rules & Character Info -->
      <AppCard variant="subtle" padding="sm">
        <h6 class="font-medium mb-2 text-foreground">Rules & Character Info</h6>
        <div class="flex flex-wrap gap-2">
          <AppButton
            v-for="preset in rulesPresets"
            :key="preset.id"
            variant="secondary"
            size="sm"
            :title="preset.description"
            @click="applyPreset(preset)"
          >
            {{ preset.name }}
          </AppButton>
        </div>
      </AppCard>
    </div>

    <!-- Custom Presets -->
    <AppCard variant="subtle" padding="sm">
      <h6 class="font-medium mb-3 text-foreground">Custom Presets</h6>
      <div class="flex gap-2 mb-3">
        <AppInput
          v-model="newPresetName"
          placeholder="Preset name"
          class="flex-1"
          @keyup.enter="saveCustomPreset"
        />
        <AppButton
          :disabled="!newPresetName || !currentQuery"
          @click="saveCustomPreset"
        >
          Save Current Query
        </AppButton>
      </div>
      <div v-if="customPresets.length > 0" class="flex flex-wrap gap-2">
        <div
          v-for="preset in customPresets"
          :key="preset.id"
          class="inline-flex items-center gap-1"
        >
          <AppButton
            variant="secondary"
            size="sm"
            :title="preset.query"
            @click="applyPreset(preset)"
          >
            {{ preset.name }}
          </AppButton>
          <AppButton
            variant="danger"
            size="sm"
            title="Remove preset"
            @click="removeCustomPreset(preset.id)"
          >
            ✕
          </AppButton>
        </div>
      </div>
    </AppCard>
  </BasePanel>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import type { QueryPreset } from '@/types/ui'
import BasePanel from '@/components/base/BasePanel.vue'
import AppCard from '@/components/base/AppCard.vue'
import AppButton from '@/components/base/AppButton.vue'
import AppInput from '@/components/base/AppInput.vue'

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
    gameStateOverrides: { in_combat: true, addCombatants: true },
  },
  {
    id: 'combat_2',
    name: 'Ranged Attack',
    query: 'I shoot my longbow at the orc archer',
    description: 'Ranged weapon attack',
    gameStateOverrides: { in_combat: true, addCombatants: true },
  },
  {
    id: 'combat_3',
    name: 'Multiple Targets',
    query: 'I want to attack both goblins with my greatsword',
    description: 'Attack multiple enemies',
    gameStateOverrides: { in_combat: true, addCombatants: true },
  },
  {
    id: 'combat_4',
    name: 'Defensive Action',
    query: 'I take the dodge action and move behind cover',
    description: 'Defensive combat action',
    gameStateOverrides: { in_combat: true },
  },
]

const skillPresets: QueryPreset[] = [
  {
    id: 'skill_1',
    name: 'Persuasion Check',
    query: 'I try to persuade the guard to let us pass',
    description: 'Social skill check',
  },
  {
    id: 'skill_2',
    name: 'Stealth Check',
    query: 'I attempt to sneak past the sleeping dragon',
    description: 'Stealth skill check',
  },
  {
    id: 'skill_3',
    name: 'Investigation',
    query: 'I search the room for hidden doors or traps',
    description: 'Investigation check',
  },
  {
    id: 'skill_4',
    name: 'Athletics Check',
    query: 'I try to climb the castle wall',
    description: 'Physical skill check',
  },
]

const spellPresets: QueryPreset[] = [
  {
    id: 'spell_1',
    name: 'Fireball',
    query: 'I cast fireball at the group of enemies',
    description: 'Area damage spell',
    gameStateOverrides: { in_combat: true, addCombatants: true },
  },
  {
    id: 'spell_2',
    name: 'Healing Spell',
    query: 'I cast cure wounds on the injured fighter',
    description: 'Healing spell',
    gameStateOverrides: { addPartyMembers: true },
  },
  {
    id: 'spell_3',
    name: 'Utility Spell',
    query: 'I cast detect magic to scan the room',
    description: 'Utility spell',
  },
  {
    id: 'spell_4',
    name: 'Buff Spell',
    query: 'I cast haste on our rogue before combat',
    description: 'Enhancement spell',
    gameStateOverrides: { addPartyMembers: true },
  },
]

const socialPresets: QueryPreset[] = [
  {
    id: 'social_1',
    name: 'Negotiate Price',
    query: 'I try to haggle with the merchant for a better price',
    description: 'Commerce interaction',
    gameStateOverrides: { current_location: 'Marketplace' },
  },
  {
    id: 'social_2',
    name: 'Gather Information',
    query: 'I ask the bartender about recent rumors',
    description: 'Information gathering',
    gameStateOverrides: { current_location: 'Tavern' },
  },
  {
    id: 'social_3',
    name: 'Intimidation',
    query: 'I intimidate the bandit to reveal their hideout',
    description: 'Intimidation check',
  },
  {
    id: 'social_4',
    name: 'Deception',
    query: 'I lie to the guard about our purpose here',
    description: 'Deception check',
  },
]

const equipmentPresets: QueryPreset[] = [
  {
    id: 'equip_1',
    name: 'Buy Weapon',
    query: 'I want to buy a longsword from the blacksmith',
    description: 'Purchase weapon',
    gameStateOverrides: { current_location: 'Blacksmith Shop' },
  },
  {
    id: 'equip_2',
    name: 'Sell Items',
    query: 'I want to sell these goblin weapons we found',
    description: 'Sell equipment',
  },
  {
    id: 'equip_3',
    name: 'Check Equipment',
    query: 'What equipment do I currently have?',
    description: 'Inventory check',
    gameStateOverrides: { addPartyMembers: true },
  },
  {
    id: 'equip_4',
    name: 'Identify Item',
    query: 'I examine the magical sword we found',
    description: 'Item identification',
  },
]

const rulesPresets: QueryPreset[] = [
  {
    id: 'rules_1',
    name: 'Class Features',
    query: 'What abilities does a level 5 fighter have?',
    description: 'Class information lookup',
  },
  {
    id: 'rules_2',
    name: 'Spell Details',
    query: 'How does counterspell work?',
    description: 'Spell rules lookup',
  },
  {
    id: 'rules_3',
    name: 'Condition Rules',
    query: 'What happens when someone is paralyzed?',
    description: 'Condition rules',
  },
  {
    id: 'rules_4',
    name: 'Race Features',
    query: 'What are the traits of a hill dwarf?',
    description: 'Race information',
  },
  {
    id: 'rules_5',
    name: 'Multiclassing',
    query: 'What are the requirements for multiclassing into wizard?',
    description: 'Multiclassing rules',
  },
  {
    id: 'rules_6',
    name: 'Level Progression',
    query: 'What do rogues get when they reach level 3?',
    description: 'Level progression info',
  },
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
    query: props.currentQuery,
  }

  customPresets.value.push(newPreset)
  localStorage.setItem(
    'ragTesterCustomPresets',
    JSON.stringify(customPresets.value)
  )
  newPresetName.value = ''
}

const removeCustomPreset = (id: string) => {
  customPresets.value = customPresets.value.filter(p => p.id !== id)
  localStorage.setItem(
    'ragTesterCustomPresets',
    JSON.stringify(customPresets.value)
  )
}

// Load custom presets on mount
onMounted(() => {
  const saved = localStorage.getItem('ragTesterCustomPresets')
  if (saved) {
    try {
      customPresets.value = JSON.parse(saved) as QueryPreset[]
    } catch (e) {
      console.error('Failed to load custom presets:', e)
    }
  }
})
</script>

<style scoped>
.query-presets {
  /* Component-specific styles if needed */
}
</style>
