<template>
  <div class="space-y-6">
    <h3 class="text-lg font-semibold text-foreground">Basic Information</h3>

    <div class="space-y-4">
      <AppInput
        v-model="localName"
        label="Character Name"
        placeholder="Enter character name"
        required
        :error="errors.name"
      />

      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <AppSelect
          v-model="localAlignment"
          label="Alignment"
          :options="alignmentOptions"
          placeholder="Select alignment"
          required
          :error="errors.alignment"
        />

        <AppSelect
          v-model="localBackground"
          label="Background"
          :options="backgroundOptions"
          placeholder="Select background"
          required
          :error="errors.background"
        >
          <template #option="{ option }">
            <div class="flex items-center justify-between">
              <span>{{ option.label }}</span>
              <BaseBadge v-if="option._source" size="sm" variant="secondary">
                {{ option._source }}
              </BaseBadge>
            </div>
          </template>
        </AppSelect>
      </div>

      <div v-if="fetchedBackgroundDetails" class="mt-4 p-4 bg-card rounded-lg">
        <BaseLoader v-if="fetchingBackground" size="sm" />
        <div v-else>
          <h4 class="font-semibold text-foreground mb-2">
            {{ fetchedBackgroundDetails.name }}
          </h4>
          <ul class="text-sm text-foreground/60 space-y-1">
            <li v-if="fetchedBackgroundDetails.feature">
              Feature: {{ fetchedBackgroundDetails.feature.name }}
            </li>
            <li v-if="backgroundSkills.length > 0">
              Skills: {{ backgroundSkills.map(s => s.label).join(', ') }}
            </li>
            <li v-if="backgroundTools.length > 0">
              Tools: {{ backgroundTools.join(', ') }}
            </li>
            <li
              v-if="
                fetchedBackgroundDetails.languages &&
                fetchedBackgroundDetails.languages.length > 0
              "
            >
              Languages:
              {{
                fetchedBackgroundDetails.languages.map(l => l.name).join(', ')
              }}
            </li>
            <li
              v-if="
                fetchedBackgroundDetails.starting_equipment &&
                fetchedBackgroundDetails.starting_equipment.length > 0
              "
            >
              Equipment:
              {{ fetchedBackgroundDetails.starting_equipment.length }} items
            </li>
          </ul>
        </div>
      </div>

      <AppTextarea
        v-model="localBackstory"
        label="Backstory (Optional)"
        placeholder="Tell us about your character's background..."
        rows="4"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, watch } from 'vue'
import type { D5eBackground } from '@/types/unified'
import AppInput from '@/components/base/AppInput.vue'
import AppSelect from '@/components/base/AppSelect.vue'
import AppTextarea from '@/components/base/AppTextarea.vue'
import BaseBadge from '@/components/base/BaseBadge.vue'
import BaseLoader from '@/components/base/BaseLoader.vue'

export interface BasicInfoStepProps {
  modelValue: {
    name: string
    alignment: string
    background: string
    backstory: string
  }
  alignmentOptions: Array<{ value: string; label: string }>
  backgroundOptions: Array<{ value: string; label: string; _source?: string }>
  fetchedBackgroundDetails: D5eBackground | null
  fetchingBackground: boolean
  backgroundSkills: Array<{ value: string; label: string }>
  backgroundTools: string[]
  errors?: Record<string, string>
}

const props = withDefaults(defineProps<BasicInfoStepProps>(), {
  errors: () => ({}),
})

const emit = defineEmits<{
  'update:modelValue': [value: BasicInfoStepProps['modelValue']]
}>()

// Create computed properties for two-way binding
const localName = computed({
  get: () => props.modelValue.name,
  set: value => emit('update:modelValue', { ...props.modelValue, name: value }),
})

const localAlignment = computed({
  get: () => props.modelValue.alignment,
  set: value =>
    emit('update:modelValue', { ...props.modelValue, alignment: value }),
})

const localBackground = computed({
  get: () => props.modelValue.background,
  set: value =>
    emit('update:modelValue', { ...props.modelValue, background: value }),
})

const localBackstory = computed({
  get: () => props.modelValue.backstory,
  set: value =>
    emit('update:modelValue', { ...props.modelValue, backstory: value }),
})
</script>
