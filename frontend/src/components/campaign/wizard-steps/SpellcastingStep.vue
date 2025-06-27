<template>
  <div class="space-y-6">
    <h3 class="text-lg font-semibold text-foreground">Equipment & Spells</h3>

    <!-- Equipment Selection -->
    <AppFormSection title="Starting Equipment" collapsible :collapsed="false">
      <div class="space-y-4">
        <div class="flex items-center space-x-4">
          <label class="flex items-center space-x-2">
            <input
              v-model="equipmentMethod"
              type="radio"
              value="standard"
              class="text-primary focus:ring-primary"
            />
            <span class="text-foreground">Standard Equipment</span>
          </label>
          <label class="flex items-center space-x-2">
            <input
              v-model="equipmentMethod"
              type="radio"
              value="gold"
              class="text-primary focus:ring-primary"
            />
            <span class="text-foreground">Starting Gold</span>
          </label>
        </div>

        <div v-if="equipmentMethod === 'standard'" class="space-y-3">
          <div v-if="classEquipment.length > 0">
            <h5 class="font-medium text-foreground text-sm mb-2">
              Class Equipment
            </h5>
            <ul
              class="list-disc list-inside text-sm text-foreground/60 space-y-1"
            >
              <li v-for="item in classEquipment" :key="item">
                {{ item }}
              </li>
            </ul>
          </div>

          <div v-if="backgroundEquipment.length > 0">
            <h5 class="font-medium text-foreground text-sm mb-2">
              Background Equipment
            </h5>
            <ul
              class="list-disc list-inside text-sm text-foreground/60 space-y-1"
            >
              <li v-for="item in backgroundEquipment" :key="item">
                {{ item }}
              </li>
            </ul>
          </div>
        </div>

        <div v-else class="space-y-3">
          <BaseAlert type="info">
            Starting gold varies by class. Roll for gold after character
            creation.
          </BaseAlert>
        </div>
      </div>
    </AppFormSection>

    <!-- Spell Selection -->
    <AppFormSection
      v-if="isSpellcaster"
      title="Spell Selection"
      collapsible
      :collapsed="false"
    >
      <div v-if="loadingSpells" class="text-center py-8">
        <BaseLoader size="md" />
        <p class="text-foreground/60 mt-2">Loading spell lists...</p>
      </div>

      <div v-else class="space-y-4">
        <!-- Cantrips -->
        <div v-if="cantripsKnown > 0" class="space-y-3">
          <h5 class="font-medium text-foreground">
            Cantrips
            <span class="text-xs text-foreground/60 ml-2">
              (Choose {{ cantripsKnown }})
            </span>
          </h5>
          <AppCheckboxGroup
            :model-value="modelValue.cantrips"
            :options="availableCantrips"
            :max-selections="cantripsKnown"
            columns="2"
            @update:model-value="
              value =>
                emit('update:modelValue', { ...modelValue, cantrips: value })
            "
          />
          <p
            v-if="availableCantrips.length === 0"
            class="text-sm text-foreground/60"
          >
            No cantrips available for this class.
          </p>
        </div>

        <!-- 1st Level Spells -->
        <div v-if="spellsKnown > 0" class="space-y-3">
          <h5 class="font-medium text-foreground">
            1st Level Spells
            <span class="text-xs text-foreground/60 ml-2">
              (Choose {{ spellsKnown }})
            </span>
          </h5>
          <AppCheckboxGroup
            :model-value="modelValue.spells"
            :options="availableFirstLevelSpells"
            :max-selections="spellsKnown"
            columns="2"
            @update:model-value="
              value =>
                emit('update:modelValue', { ...modelValue, spells: value })
            "
          />
          <p
            v-if="availableFirstLevelSpells.length === 0"
            class="text-sm text-foreground/60"
          >
            No 1st level spells available for this class.
          </p>
        </div>
      </div>
    </AppFormSection>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import type { D5eClass, D5eBackground } from '@/types/unified'
import AppFormSection from '@/components/base/AppFormSection.vue'
import AppCheckboxGroup from '@/components/base/AppCheckboxGroup.vue'
import BaseAlert from '@/components/base/BaseAlert.vue'
import BaseLoader from '@/components/base/BaseLoader.vue'

export interface SpellcastingStepProps {
  modelValue: {
    equipment_method: 'standard' | 'gold'
    cantrips: string[]
    spells: string[]
  }
  selectedClassDetails: D5eClass | null
  fetchedBackgroundDetails: D5eBackground | null
  isSpellcaster: boolean
  cantripsKnown: number
  spellsKnown: number
  classEquipment: string[]
  backgroundEquipment: string[]
  availableCantrips: Array<{ value: string; label: string }>
  availableFirstLevelSpells: Array<{ value: string; label: string }>
  loadingSpells: boolean
}

const props = defineProps<SpellcastingStepProps>()

const emit = defineEmits<{
  'update:modelValue': [value: SpellcastingStepProps['modelValue']]
}>()

// Local equipment method ref
const equipmentMethod = computed({
  get: () => props.modelValue.equipment_method,
  set: value => {
    emit('update:modelValue', {
      ...props.modelValue,
      equipment_method: value,
    })
  },
})
</script>
