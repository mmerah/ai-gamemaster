<template>
  <BasePanel class="party-configurator">
    <h5 class="text-lg font-semibold mb-4 text-foreground">Party Members</h5>

    <div class="space-y-4">
      <AppCard
        v-for="(member, index) in localParty"
        :key="member.id"
        variant="subtle"
        padding="sm"
      >
        <div class="flex gap-2 mb-3">
          <AppInput
            v-model="member.name"
            placeholder="Character name"
            class="flex-1 font-medium"
            @input="emitUpdate"
          />
          <AppButton
            variant="danger"
            size="sm"
            title="Remove character"
            @click="removeMember(index)"
          >
            ✕
          </AppButton>
        </div>

        <div class="space-y-3">
          <div class="grid grid-cols-3 gap-3">
            <AppInput
              v-model="member.char_class"
              label="Class:"
              placeholder="e.g., Fighter, Wizard"
              @input="emitUpdate"
            />
            <AppInput
              v-model="member.race"
              label="Race:"
              placeholder="e.g., Human, Elf"
              @input="emitUpdate"
            />
            <AppInput
              v-model.number="member.level"
              label="Level:"
              type="number"
              :min="1"
              :max="20"
              @input="emitUpdate"
            />
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-sm font-medium text-foreground mb-1"
                >HP:</label
              >
              <div class="flex items-center gap-2">
                <AppInput
                  v-model.number="member.current_hp"
                  type="number"
                  :min="0"
                  @input="emitUpdate"
                />
                <span class="text-foreground/60">/</span>
                <AppInput
                  v-model.number="member.max_hp"
                  type="number"
                  :min="1"
                  @input="emitUpdate"
                />
              </div>
            </div>
            <AppInput
              v-model="member.conditionsString"
              label="Conditions:"
              placeholder="e.g., poisoned, prone"
              @input="updateConditions(index, $event)"
            />
          </div>

          <AppTextarea
            v-model="member.equipmentString"
            label="Equipment:"
            :rows="2"
            placeholder="e.g., Longsword, Shield, Plate Armor"
            @input="updateEquipment(index, $event)"
          />

          <details class="mt-3">
            <summary
              class="cursor-pointer text-sm text-foreground/60 hover:text-foreground"
            >
              Advanced Settings
            </summary>
            <div class="mt-3 space-y-3 pl-4">
              <div class="grid grid-cols-3 gap-3">
                <AppInput
                  v-model.number="member.gold"
                  label="Gold:"
                  type="number"
                  :min="0"
                  @input="emitUpdate"
                />
                <AppInput
                  v-model.number="member.experience_points"
                  label="XP:"
                  type="number"
                  :min="0"
                  @input="emitUpdate"
                />
                <AppInput
                  v-model.number="member.exhaustion_level"
                  label="Exhaustion:"
                  type="number"
                  :min="0"
                  :max="6"
                  @input="emitUpdate"
                />
              </div>
              <AppInput
                v-model="member.spellSlotsString"
                label="Spell Slots Used (JSON):"
                placeholder='{"1": 2, "2": 1}'
                @input="updateSpellSlots(index, $event)"
              />
            </div>
          </details>
        </div>
      </AppCard>

      <AppButton variant="secondary" @click="addMember">
        + Add Party Member
      </AppButton>
    </div>
  </BasePanel>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import type { CharacterInstanceModel } from '@/types/unified'
import BasePanel from '@/components/base/BasePanel.vue'
import AppCard from '@/components/base/AppCard.vue'
import AppButton from '@/components/base/AppButton.vue'
import AppInput from '@/components/base/AppInput.vue'
import AppTextarea from '@/components/base/AppTextarea.vue'

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
watch(
  () => props.modelValue,
  newValue => {
    localParty.value = Object.values(newValue).map(char => ({
      ...char,
      char_class: 'Fighter', // Default class
      race: 'Human', // Default race
      conditionsString: char.conditions.join(', '),
      equipmentString: char.inventory.map(item => item.name).join(', '),
      spellSlotsString: JSON.stringify(char.spell_slots_used),
    }))
  },
  { immediate: true }
)

// Methods
const emitUpdate = () => {
  const partyDict: Record<string, CharacterInstanceModel> = {}
  localParty.value.forEach(member => {
    const {
      conditionsString,
      equipmentString,
      spellSlotsString,
      char_class,
      race,
      ...baseChar
    } = member
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
    spellSlotsString: '{}',
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
      quantity: 1,
    }))
  localParty.value[index].inventory = items
  emitUpdate()
}

const updateSpellSlots = (index: number, event: Event) => {
  const target = event.target as HTMLInputElement
  try {
    const slots = JSON.parse(target.value || '{}') as Record<string, number>
    localParty.value[index].spell_slots_used = slots
    emitUpdate()
  } catch {
    // Invalid JSON, ignore
  }
}
</script>

<style scoped>
.party-configurator {
  margin-bottom: 1rem;
}
</style>
