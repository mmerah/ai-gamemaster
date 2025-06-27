<template>
  <div class="space-y-6">
    <h3 class="text-lg font-semibold text-foreground">
      Personality & Background
    </h3>

    <!-- Appearance -->
    <div>
      <AppTextarea
        :model-value="modelValue.appearance"
        label="Appearance"
        :rows="3"
        placeholder="Describe your character's appearance..."
        @update:model-value="updateField('appearance', $event)"
      />
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <!-- Personality Traits -->
      <div>
        <label class="block text-sm font-medium text-foreground mb-2">
          Personality Traits
        </label>
        <div class="space-y-2">
          <div
            v-for="(trait, index) in modelValue.personality_traits"
            :key="index"
            class="flex items-center space-x-2"
          >
            <AppInput
              :model-value="trait"
              class="flex-1"
              placeholder="Enter personality trait..."
              @update:model-value="updatePersonalityTrait(index, $event)"
            />
            <AppButton
              type="button"
              variant="secondary"
              size="sm"
              @click="removePersonalityTrait(index)"
            >
              Remove
            </AppButton>
          </div>
          <AppButton
            type="button"
            variant="secondary"
            size="sm"
            @click="addPersonalityTrait"
          >
            Add Trait
          </AppButton>
        </div>
      </div>

      <!-- Ideals -->
      <div>
        <label class="block text-sm font-medium text-foreground mb-2">
          Ideals
        </label>
        <div class="space-y-2">
          <div
            v-for="(ideal, index) in modelValue.ideals"
            :key="index"
            class="flex items-center space-x-2"
          >
            <AppInput
              :model-value="ideal"
              class="flex-1"
              placeholder="Enter ideal..."
              @update:model-value="updateIdeal(index, $event)"
            />
            <AppButton
              type="button"
              variant="secondary"
              size="sm"
              @click="removeIdeal(index)"
            >
              Remove
            </AppButton>
          </div>
          <AppButton
            type="button"
            variant="secondary"
            size="sm"
            @click="addIdeal"
          >
            Add Ideal
          </AppButton>
        </div>
      </div>

      <!-- Bonds -->
      <div>
        <label class="block text-sm font-medium text-foreground mb-2">
          Bonds
        </label>
        <div class="space-y-2">
          <div
            v-for="(bond, index) in modelValue.bonds"
            :key="index"
            class="flex items-center space-x-2"
          >
            <AppInput
              :model-value="bond"
              class="flex-1"
              placeholder="Enter bond..."
              @update:model-value="updateBond(index, $event)"
            />
            <AppButton
              type="button"
              variant="secondary"
              size="sm"
              @click="removeBond(index)"
            >
              Remove
            </AppButton>
          </div>
          <AppButton
            type="button"
            variant="secondary"
            size="sm"
            @click="addBond"
          >
            Add Bond
          </AppButton>
        </div>
      </div>

      <!-- Flaws -->
      <div>
        <label class="block text-sm font-medium text-foreground mb-2">
          Flaws
        </label>
        <div class="space-y-2">
          <div
            v-for="(flaw, index) in modelValue.flaws"
            :key="index"
            class="flex items-center space-x-2"
          >
            <AppInput
              :model-value="flaw"
              class="flex-1"
              placeholder="Enter flaw..."
              @update:model-value="updateFlaw(index, $event)"
            />
            <AppButton
              type="button"
              variant="secondary"
              size="sm"
              @click="removeFlaw(index)"
            >
              Remove
            </AppButton>
          </div>
          <AppButton
            type="button"
            variant="secondary"
            size="sm"
            @click="addFlaw"
          >
            Add Flaw
          </AppButton>
        </div>
      </div>
    </div>

    <!-- Backstory -->
    <div>
      <AppTextarea
        :model-value="modelValue.backstory"
        label="Backstory"
        :rows="4"
        placeholder="Tell your character's story..."
        @update:model-value="updateField('backstory', $event)"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import AppButton from '@/components/base/AppButton.vue'
import AppInput from '@/components/base/AppInput.vue'
import AppTextarea from '@/components/base/AppTextarea.vue'

export interface PersonalityStepProps {
  modelValue: {
    appearance: string
    personality_traits: string[]
    ideals: string[]
    bonds: string[]
    flaws: string[]
    backstory: string
  }
}

const props = defineProps<PersonalityStepProps>()

const emit = defineEmits<{
  'update:modelValue': [value: PersonalityStepProps['modelValue']]
}>()

function updateField(
  field: keyof PersonalityStepProps['modelValue'],
  value: string
) {
  emit('update:modelValue', {
    ...props.modelValue,
    [field]: value,
  })
}

function updatePersonalityTrait(index: number, value: string) {
  const traits = [...props.modelValue.personality_traits]
  traits[index] = value
  emit('update:modelValue', {
    ...props.modelValue,
    personality_traits: traits,
  })
}

function addPersonalityTrait() {
  emit('update:modelValue', {
    ...props.modelValue,
    personality_traits: [...props.modelValue.personality_traits, ''],
  })
}

function removePersonalityTrait(index: number) {
  const traits = [...props.modelValue.personality_traits]
  traits.splice(index, 1)
  emit('update:modelValue', {
    ...props.modelValue,
    personality_traits: traits,
  })
}

function updateIdeal(index: number, value: string) {
  const ideals = [...props.modelValue.ideals]
  ideals[index] = value
  emit('update:modelValue', {
    ...props.modelValue,
    ideals: ideals,
  })
}

function addIdeal() {
  emit('update:modelValue', {
    ...props.modelValue,
    ideals: [...props.modelValue.ideals, ''],
  })
}

function removeIdeal(index: number) {
  const ideals = [...props.modelValue.ideals]
  ideals.splice(index, 1)
  emit('update:modelValue', {
    ...props.modelValue,
    ideals: ideals,
  })
}

function updateBond(index: number, value: string) {
  const bonds = [...props.modelValue.bonds]
  bonds[index] = value
  emit('update:modelValue', {
    ...props.modelValue,
    bonds: bonds,
  })
}

function addBond() {
  emit('update:modelValue', {
    ...props.modelValue,
    bonds: [...props.modelValue.bonds, ''],
  })
}

function removeBond(index: number) {
  const bonds = [...props.modelValue.bonds]
  bonds.splice(index, 1)
  emit('update:modelValue', {
    ...props.modelValue,
    bonds: bonds,
  })
}

function updateFlaw(index: number, value: string) {
  const flaws = [...props.modelValue.flaws]
  flaws[index] = value
  emit('update:modelValue', {
    ...props.modelValue,
    flaws: flaws,
  })
}

function addFlaw() {
  emit('update:modelValue', {
    ...props.modelValue,
    flaws: [...props.modelValue.flaws, ''],
  })
}

function removeFlaw(index: number) {
  const flaws = [...props.modelValue.flaws]
  flaws.splice(index, 1)
  emit('update:modelValue', {
    ...props.modelValue,
    flaws: flaws,
  })
}
</script>
