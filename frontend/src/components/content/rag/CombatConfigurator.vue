<template>
  <BasePanel class="combat-configurator">
    <h5 class="text-lg font-semibold mb-4 text-foreground">Combat State</h5>

    <div class="space-y-4">
      <label class="flex items-center gap-2 cursor-pointer">
        <input
          v-model="localCombat.is_active"
          type="checkbox"
          class="cursor-pointer"
          @change="emitUpdate"
        />
        <span class="text-foreground">Combat Active</span>
      </label>

      <div v-if="localCombat.is_active" class="space-y-4">
        <AppCard variant="subtle" padding="sm">
          <div class="grid grid-cols-2 gap-4">
            <AppInput
              v-model.number="localCombat.round_number"
              label="Round:"
              type="number"
              :min="1"
              @input="emitUpdate"
            />
            <AppSelect
              v-model.number="localCombat.current_turn_index"
              label="Current Turn:"
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
            </AppSelect>
          </div>
        </AppCard>

        <div class="space-y-4">
          <h6 class="font-medium text-foreground">Combatants</h6>
          <div
            v-for="(combatant, index) in localCombat.combatants"
            :key="combatant.id"
            class="space-y-3"
          >
            <AppCard variant="subtle" padding="sm">
              <div class="flex gap-2 mb-3">
                <AppInput
                  v-model="combatant.name"
                  placeholder="Combatant name"
                  class="flex-1"
                  @input="emitUpdate"
                />
                <AppButton
                  variant="danger"
                  size="sm"
                  title="Remove combatant"
                  @click="removeCombatant(index)"
                >
                  ✕
                </AppButton>
              </div>

              <div class="space-y-3">
                <div class="grid grid-cols-3 gap-3">
                  <AppSelect
                    v-model="combatant.combatant_type"
                    label="Type:"
                    @change="
                      () => {
                        combatant.is_player =
                          combatant.combatant_type === 'player'
                        emitUpdate()
                      }
                    "
                  >
                    <option value="player">Player</option>
                    <option value="monster">Monster</option>
                    <option value="npc">NPC</option>
                  </AppSelect>
                  <AppInput
                    v-model.number="combatant.initiative"
                    label="Initiative:"
                    type="number"
                    @input="emitUpdate"
                  />
                  <AppInput
                    v-model.number="combatant.initiative_modifier"
                    label="Init Mod:"
                    type="number"
                    @input="emitUpdate"
                  />
                </div>

                <div class="grid grid-cols-2 gap-3">
                  <div>
                    <label
                      class="block text-sm font-medium text-foreground mb-1"
                      >HP:</label
                    >
                    <div class="flex items-center gap-2">
                      <AppInput
                        v-model.number="combatant.current_hp"
                        type="number"
                        :min="0"
                        @input="emitUpdate"
                      />
                      <span class="text-foreground/60">/</span>
                      <AppInput
                        v-model.number="combatant.max_hp"
                        type="number"
                        :min="1"
                        @input="emitUpdate"
                      />
                    </div>
                  </div>
                  <AppInput
                    v-model.number="combatant.armor_class"
                    label="AC:"
                    type="number"
                    :min="0"
                    @input="emitUpdate"
                  />
                </div>

                <AppInput
                  v-model="combatant.conditionsString"
                  label="Conditions:"
                  placeholder="e.g., stunned, prone"
                  @input="updateCombatantConditions(index, $event)"
                />

                <details
                  v-if="combatant.combatant_type === 'monster'"
                  class="mt-3"
                >
                  <summary
                    class="cursor-pointer text-sm text-foreground/60 hover:text-foreground"
                  >
                    Monster Details
                  </summary>
                  <div class="mt-3 space-y-3 pl-4">
                    <AppInput
                      v-model="combatant.monster_type"
                      label="Monster Type:"
                      placeholder="e.g., goblin, orc"
                      @input="emitUpdate"
                    />
                    <div class="grid grid-cols-2 gap-3">
                      <AppInput
                        v-model.number="combatant.challenge_rating"
                        label="CR:"
                        type="number"
                        :min="0"
                        :step="0.125"
                        @input="emitUpdate"
                      />
                      <AppSelect
                        v-model="combatant.size"
                        label="Size:"
                        @change="emitUpdate"
                      >
                        <option value="Tiny">Tiny</option>
                        <option value="Small">Small</option>
                        <option value="Medium">Medium</option>
                        <option value="Large">Large</option>
                        <option value="Huge">Huge</option>
                        <option value="Gargantuan">Gargantuan</option>
                      </AppSelect>
                    </div>
                  </div>
                </details>
              </div>
            </AppCard>
          </div>

          <AppButton variant="secondary" @click="addCombatant">
            + Add Combatant
          </AppButton>
        </div>
      </div>
    </div>
  </BasePanel>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import type { CombatStateModel, CombatantModel } from '@/types/unified'
import BasePanel from '@/components/base/BasePanel.vue'
import AppCard from '@/components/base/AppCard.vue'
import AppButton from '@/components/base/AppButton.vue'
import AppInput from '@/components/base/AppInput.vue'
import AppSelect from '@/components/base/AppSelect.vue'

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
  // Extended UI fields (not sent to backend)
  combatant_type?: string
  monster_type?: string
  challenge_rating?: number
  size?: string
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
  current_turn_instruction_given: false,
})

// Initialize from props
watch(
  () => props.modelValue,
  newValue => {
    localCombat.value = {
      ...newValue,
      combatants: newValue.combatants.map(c => ({
        ...c,
        conditionsString: c.conditions?.join(', ') || '',
        combatant_type: c.is_player ? 'player' : 'monster',
      })),
    }
  },
  { immediate: true }
)

// Methods
const emitUpdate = () => {
  const combatState: CombatStateModel = {
    ...localCombat.value,
    combatants: localCombat.value.combatants.map(
      ({
        conditionsString,
        combatant_type,
        monster_type,
        challenge_rating,
        size,
        ...combatant
      }) => ({
        id: combatant.id,
        name: combatant.name,
        initiative: combatant.initiative,
        initiative_modifier: combatant.initiative_modifier,
        current_hp: combatant.current_hp,
        max_hp: combatant.max_hp,
        armor_class: combatant.armor_class,
        conditions: combatant.conditions,
        is_player: combatant.is_player,
      })
    ),
  }
  emit('update:modelValue', combatState)
}

const addCombatant = () => {
  const newCombatant: UICombatant = {
    id: `combatant_${Date.now()}`,
    name: `Combatant ${localCombat.value.combatants.length + 1}`,
    initiative: 10,
    initiative_modifier: 0,
    current_hp: 10,
    max_hp: 10,
    armor_class: 10,
    conditions: [],
    is_player: false,
    // UI fields for local editing only
    conditionsString: '',
    // Extended fields for UI display
    combatant_type: 'monster',
    monster_type: 'goblin',
    challenge_rating: 0.25,
    size: 'Small',
  }
  localCombat.value.combatants.push(newCombatant)
  emitUpdate()
}

const removeCombatant = (index: number) => {
  localCombat.value.combatants.splice(index, 1)
  // Adjust current turn index if needed
  if (
    localCombat.value.current_turn_index >= index &&
    localCombat.value.current_turn_index > 0
  ) {
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
  const incapacitatingConditions = [
    'unconscious',
    'paralyzed',
    'petrified',
    'stunned',
  ]
  localCombat.value.combatants[index].is_incapacitated = conditions.some(c =>
    incapacitatingConditions.includes(c.toLowerCase())
  )

  emitUpdate()
}
</script>

<style scoped>
.combat-configurator {
  margin-bottom: 1rem;
}
</style>
