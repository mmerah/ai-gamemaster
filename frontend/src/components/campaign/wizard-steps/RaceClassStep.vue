<template>
  <div class="space-y-6">
    <h3 class="text-lg font-semibold text-foreground">Race & Class</h3>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <!-- Race Selection -->
      <AppFormSection title="Race" :collapsed="false">
        <AppSelect
          v-model="localRace"
          label="Choose your race"
          :options="raceOptions"
          placeholder="Select a race"
          required
          :error="errors.race"
        />

        <div v-if="selectedRaceDetails" class="mt-4 p-4 bg-card rounded-lg">
          <BaseLoader v-if="fetchingRace" size="sm" />
          <div v-else>
            <h4 class="font-semibold text-foreground mb-2">
              {{ selectedRaceDetails.name }} Traits
            </h4>
            <ul class="text-sm text-foreground/60 space-y-1">
              <li>Size: {{ selectedRaceDetails.size }}</li>
              <li>Speed: {{ selectedRaceDetails.speed }} feet</li>
              <li
                v-if="
                  selectedRaceDetails.ability_bonuses &&
                  selectedRaceDetails.ability_bonuses.length > 0
                "
              >
                Ability Bonuses:
                {{
                  selectedRaceDetails.ability_bonuses
                    .map(b => `${b.ability_score.name} +${b.bonus}`)
                    .join(', ')
                }}
              </li>
              <li
                v-if="
                  selectedRaceDetails.languages &&
                  selectedRaceDetails.languages.length > 0
                "
              >
                Languages:
                {{ selectedRaceDetails.languages.map(l => l.name).join(', ') }}
              </li>
              <li
                v-for="trait in selectedRaceDetails.traits || []"
                :key="trait.index"
              >
                • {{ trait.name }}
              </li>
            </ul>
          </div>
        </div>
      </AppFormSection>

      <!-- Class Selection -->
      <AppFormSection title="Class" :collapsed="false">
        <AppSelect
          v-model="localClass"
          label="Choose your class"
          :options="classOptions"
          placeholder="Select a class"
          required
          :error="errors.char_class"
        />

        <AppNumberInput
          v-model="localLevel"
          label="Starting Level"
          :min="1"
          :max="20"
          class="mt-4"
        />

        <div v-if="selectedClassDetails" class="mt-4 p-4 bg-card rounded-lg">
          <BaseLoader v-if="fetchingClass" size="sm" />
          <div v-else>
            <h4 class="font-semibold text-foreground mb-2">
              {{ selectedClassDetails.name }} Features
            </h4>
            <ul class="text-sm text-foreground/60 space-y-1">
              <li>Hit Die: d{{ selectedClassDetails.hit_die }}</li>
              <li
                v-if="
                  selectedClassDetails.saving_throws &&
                  selectedClassDetails.saving_throws.length > 0
                "
              >
                Saving Throws:
                {{
                  selectedClassDetails.saving_throws.map(s => s.name).join(', ')
                }}
              </li>
              <li
                v-if="
                  selectedClassDetails.proficiencies &&
                  selectedClassDetails.proficiencies.length > 0
                "
              >
                Proficiencies:
                {{
                  selectedClassDetails.proficiencies
                    .slice(0, 3)
                    .map(p => p.name)
                    .join(', ')
                }}{{
                  selectedClassDetails.proficiencies.length > 3 ? '...' : ''
                }}
              </li>
              <li
                v-if="
                  selectedClassDetails.proficiency_choices &&
                  selectedClassDetails.proficiency_choices.length > 0
                "
              >
                Skill Choices: Choose {{ classSkillChoices }} from
                {{ availableClassSkills }} options
              </li>
              <li v-if="selectedClassDetails.spellcasting">
                Spellcasting:
                {{
                  selectedClassDetails.spellcasting.spellcasting_ability
                    ?.name || 'Yes'
                }}
              </li>
              <li
                v-if="
                  selectedClassDetails.starting_equipment &&
                  selectedClassDetails.starting_equipment.length > 0
                "
              >
                Starting Equipment:
                {{ selectedClassDetails.starting_equipment.length }} items
              </li>
            </ul>
          </div>
        </div>
      </AppFormSection>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { D5eRace, D5eClass } from '@/types/unified'
import AppSelect from '@/components/base/AppSelect.vue'
import AppNumberInput from '@/components/base/AppNumberInput.vue'
import AppFormSection from '@/components/base/AppFormSection.vue'
import BaseLoader from '@/components/base/BaseLoader.vue'

export interface RaceClassStepProps {
  modelValue: {
    race: string
    char_class: string
    level: number
  }
  raceOptions: Array<{ value: string; label: string; _source?: string }>
  classOptions: Array<{ value: string; label: string; _source?: string }>
  selectedRaceDetails: D5eRace | null
  selectedClassDetails: D5eClass | null
  fetchingRace: boolean
  fetchingClass: boolean
  classSkillChoices?: number
  availableClassSkills?: number
  errors?: Record<string, string>
}

const props = withDefaults(defineProps<RaceClassStepProps>(), {
  errors: () => ({}),
  classSkillChoices: 0,
  availableClassSkills: 0,
})

const emit = defineEmits<{
  'update:modelValue': [value: RaceClassStepProps['modelValue']]
}>()

// Create computed properties for two-way binding
const localRace = computed({
  get: () => props.modelValue.race,
  set: value => emit('update:modelValue', { ...props.modelValue, race: value }),
})

const localClass = computed({
  get: () => props.modelValue.char_class,
  set: value =>
    emit('update:modelValue', { ...props.modelValue, char_class: value }),
})

const localLevel = computed({
  get: () => props.modelValue.level,
  set: value =>
    emit('update:modelValue', { ...props.modelValue, level: value }),
})
</script>
