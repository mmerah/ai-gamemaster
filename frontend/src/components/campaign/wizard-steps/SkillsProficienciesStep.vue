<template>
  <div class="space-y-6">
    <h3 class="text-lg font-semibold text-foreground">
      Skills & Proficiencies
    </h3>

    <!-- Class Skills -->
    <AppFormSection
      v-if="availableClassSkills.length > 0"
      title="Class Skills"
      :description="`Choose ${classSkillChoices} skill${classSkillChoices !== 1 ? 's' : ''} from your class`"
    >
      <AppCheckboxGroup
        :model-value="modelValue.class_skills"
        :options="availableClassSkills"
        :max-selections="classSkillChoices"
        columns="2"
        @update:model-value="
          value =>
            emit('update:modelValue', { ...modelValue, class_skills: value })
        "
      />
    </AppFormSection>

    <!-- Background Skills -->
    <AppFormSection
      v-if="backgroundSkills.length > 0"
      title="Background Skills"
      description="These skills are granted by your background"
    >
      <div class="grid grid-cols-2 gap-3">
        <div
          v-for="skill in backgroundSkills"
          :key="skill.value"
          class="flex items-center space-x-2 text-sm"
        >
          <div
            class="w-4 h-4 rounded bg-primary/20 flex items-center justify-center"
          >
            <svg
              class="w-3 h-3 text-primary"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fill-rule="evenodd"
                d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                clip-rule="evenodd"
              />
            </svg>
          </div>
          <span class="text-foreground">{{ skill.label }}</span>
        </div>
      </div>
    </AppFormSection>

    <!-- Expertise -->
    <AppFormSection
      v-if="canChooseExpertise && availableExpertiseSkills.length > 0"
      title="Expertise"
      :description="`Choose ${expertiseChoices} skill${expertiseChoices !== 1 ? 's' : ''} to gain expertise (double proficiency bonus)`"
    >
      <AppCheckboxGroup
        :model-value="modelValue.expertise"
        :options="availableExpertiseSkills"
        :max-selections="expertiseChoices"
        columns="2"
        @update:model-value="
          value =>
            emit('update:modelValue', { ...modelValue, expertise: value })
        "
      />
    </AppFormSection>

    <!-- Languages -->
    <AppFormSection
      v-if="grantedLanguages.length > 0"
      title="Languages"
      description="Languages known from race and background"
    >
      <div class="flex flex-wrap gap-2">
        <BaseBadge
          v-for="language in grantedLanguages"
          :key="language"
          variant="default"
        >
          {{ language }}
        </BaseBadge>
      </div>
    </AppFormSection>

    <!-- Tool Proficiencies -->
    <AppFormSection
      v-if="grantedTools.length > 0"
      title="Tool Proficiencies"
      description="Tool proficiencies from class and background"
    >
      <div class="flex flex-wrap gap-2">
        <BaseBadge v-for="tool in grantedTools" :key="tool" variant="secondary">
          {{ tool }}
        </BaseBadge>
      </div>
    </AppFormSection>

    <!-- Armor & Weapon Proficiencies -->
    <AppFormSection
      v-if="armorProficiencies.length > 0 || weaponProficiencies.length > 0"
      title="Combat Proficiencies"
      collapsible
      :collapsed="true"
    >
      <div class="space-y-3">
        <div v-if="armorProficiencies.length > 0">
          <h5 class="font-medium text-foreground text-sm mb-2">Armor</h5>
          <div class="flex flex-wrap gap-2">
            <BaseBadge
              v-for="armor in armorProficiencies"
              :key="armor"
              variant="default"
            >
              {{ armor }}
            </BaseBadge>
          </div>
        </div>

        <div v-if="weaponProficiencies.length > 0">
          <h5 class="font-medium text-foreground text-sm mb-2">Weapons</h5>
          <div class="flex flex-wrap gap-2">
            <BaseBadge
              v-for="weapon in weaponProficiencies"
              :key="weapon"
              variant="default"
            >
              {{ weapon }}
            </BaseBadge>
          </div>
        </div>
      </div>
    </AppFormSection>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import AppFormSection from '@/components/base/AppFormSection.vue'
import AppCheckboxGroup from '@/components/base/AppCheckboxGroup.vue'
import BaseBadge from '@/components/base/BaseBadge.vue'

export interface SkillsProficienciesStepProps {
  modelValue: {
    class_skills: string[]
    expertise: string[]
  }
  availableClassSkills: Array<{ value: string; label: string }>
  classSkillChoices: number
  backgroundSkills: Array<{ value: string; label: string }>
  canChooseExpertise: boolean
  expertiseChoices: number
  availableExpertiseSkills: Array<{ value: string; label: string }>
  grantedLanguages: string[]
  grantedTools: string[]
  armorProficiencies?: string[]
  weaponProficiencies?: string[]
}

const props = withDefaults(defineProps<SkillsProficienciesStepProps>(), {
  armorProficiencies: () => [],
  weaponProficiencies: () => [],
})

const emit = defineEmits<{
  'update:modelValue': [value: SkillsProficienciesStepProps['modelValue']]
}>()
</script>
