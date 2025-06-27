<template>
  <AppModal
    :visible="visible"
    size="xl"
    title="Edit Character Template"
    @close="handleClose"
  >
    <!-- Tabs for navigation -->
    <AppTabs
      :tabs="tabs"
      :active-tab="activeTab"
      class="mb-6"
      @update:active-tab="activeTab = $event"
    />

    <!-- Tab Content -->
    <form @submit.prevent="saveCharacter">
      <!-- Basic Info Tab -->
      <div v-show="activeTab === 'basic'" class="space-y-4">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <AppInput
            v-model="formData.name"
            label="Character Name *"
            required
            placeholder="Enter character name"
          />
          <AppInput
            v-model="formData.alignment"
            label="Alignment"
            placeholder="e.g., Lawful Good"
          />
        </div>

        <AppTextarea
          v-model="formData.backstory"
          label="Backstory"
          :rows="4"
          placeholder="Tell us about your character's history..."
        />
      </div>

      <!-- Race & Class Tab -->
      <div v-show="activeTab === 'race-class'" class="space-y-4">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-foreground mb-1">
              Race *
            </label>
            <AppInput
              v-model="formData.race"
              required
              placeholder="Character race"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-foreground mb-1">
              Subrace
            </label>
            <AppInput
              v-model="formData.subrace"
              placeholder="Character subrace (if any)"
            />
          </div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-foreground mb-1">
              Class *
            </label>
            <AppInput
              v-model="formData.char_class"
              required
              placeholder="Character class"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-foreground mb-1">
              Subclass
            </label>
            <AppInput
              v-model="formData.subclass"
              placeholder="Character subclass (if any)"
            />
          </div>
        </div>

        <div>
          <label class="block text-sm font-medium text-foreground mb-1">
            Background *
          </label>
          <AppInput
            v-model="formData.background"
            required
            placeholder="Character background"
          />
        </div>
      </div>

      <!-- Abilities Tab -->
      <div v-show="activeTab === 'abilities'" class="space-y-4">
        <h3 class="text-lg font-medium text-foreground mb-3">Ability Scores</h3>
        <div class="grid grid-cols-2 md:grid-cols-3 gap-4">
          <div v-for="(value, key) in formData.base_stats" :key="key">
            <label class="block text-sm font-medium text-foreground mb-1">
              {{ key }}
            </label>
            <div class="flex items-center space-x-2">
              <AppInput
                v-model.number="formData.base_stats[key]"
                type="number"
                min="1"
                max="20"
                class="w-20"
              />
              <span class="text-sm text-foreground/60">
                ({{ getModifier(formData.base_stats[key]) >= 0 ? '+' : ''
                }}{{ getModifier(formData.base_stats[key]) }})
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Skills Tab -->
      <div v-show="activeTab === 'skills'" class="space-y-4">
        <h3 class="text-lg font-medium text-foreground mb-3">Proficiencies</h3>

        <div>
          <label class="block text-sm font-medium text-foreground mb-2">
            Skills
          </label>
          <div class="space-y-2">
            <div
              v-for="skill in formData.proficiencies.skills"
              :key="skill"
              class="flex items-center justify-between p-2 bg-card rounded"
            >
              <span>{{ skill }}</span>
              <AppButton
                type="button"
                variant="secondary"
                size="sm"
                @click="removeSkill(skill)"
              >
                Remove
              </AppButton>
            </div>
            <p
              v-if="formData.proficiencies.skills.length === 0"
              class="text-foreground/60 text-sm"
            >
              No skill proficiencies added yet
            </p>
          </div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-foreground mb-2">
              Languages
            </label>
            <div class="space-y-1">
              <span
                v-for="lang in formData.languages"
                :key="lang"
                class="inline-block mr-2 mb-1 px-2 py-1 bg-primary/10 text-primary rounded text-sm"
              >
                {{ lang }}
              </span>
              <p
                v-if="formData.languages.length === 0"
                class="text-foreground/60 text-sm"
              >
                No languages added yet
              </p>
            </div>
          </div>
        </div>
      </div>

      <!-- Equipment Tab -->
      <div v-show="activeTab === 'equipment'" class="space-y-4">
        <h3 class="text-lg font-medium text-foreground mb-3">
          Starting Equipment
        </h3>

        <div class="space-y-2">
          <div
            v-for="(item, index) in formData.starting_equipment"
            :key="index"
            class="flex items-center justify-between p-2 bg-card rounded"
          >
            <span>{{ item.name }} ({{ item.quantity }})</span>
            <AppButton
              type="button"
              variant="secondary"
              size="sm"
              @click="removeEquipment(index)"
            >
              Remove
            </AppButton>
          </div>
          <p
            v-if="formData.starting_equipment.length === 0"
            class="text-foreground/60 text-sm"
          >
            No starting equipment added yet
          </p>
        </div>

        <div>
          <label class="block text-sm font-medium text-foreground mb-1">
            Starting Gold
          </label>
          <AppInput
            v-model.number="formData.starting_gold"
            type="number"
            min="0"
            class="w-32"
          />
        </div>
      </div>

      <!-- Personality Tab -->
      <div v-show="activeTab === 'personality'" class="space-y-4">
        <AppTextarea
          v-model="formData.appearance"
          label="Appearance"
          :rows="3"
          placeholder="Describe your character's appearance..."
        />

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-foreground mb-2">
              Personality Traits
            </label>
            <div class="space-y-2">
              <div
                v-for="(trait, index) in formData.personality_traits"
                :key="index"
                class="flex items-center space-x-2"
              >
                <AppInput
                  v-model="formData.personality_traits[index]"
                  class="flex-1"
                  placeholder="Enter personality trait..."
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

          <div>
            <label class="block text-sm font-medium text-foreground mb-2">
              Ideals
            </label>
            <div class="space-y-2">
              <div
                v-for="(ideal, index) in formData.ideals"
                :key="index"
                class="flex items-center space-x-2"
              >
                <AppInput
                  v-model="formData.ideals[index]"
                  class="flex-1"
                  placeholder="Enter ideal..."
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
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-foreground mb-2">
              Bonds
            </label>
            <div class="space-y-2">
              <div
                v-for="(bond, index) in formData.bonds"
                :key="index"
                class="flex items-center space-x-2"
              >
                <AppInput
                  v-model="formData.bonds[index]"
                  class="flex-1"
                  placeholder="Enter bond..."
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

          <div>
            <label class="block text-sm font-medium text-foreground mb-2">
              Flaws
            </label>
            <div class="space-y-2">
              <div
                v-for="(flaw, index) in formData.flaws"
                :key="index"
                class="flex items-center space-x-2"
              >
                <AppInput
                  v-model="formData.flaws[index]"
                  class="flex-1"
                  placeholder="Enter flaw..."
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
      </div>
    </form>

    <template #footer>
      <div class="flex justify-end space-x-3">
        <AppButton variant="secondary" @click="handleClose"> Cancel </AppButton>
        <AppButton :disabled="!isValid" @click="saveCharacter">
          Save Changes
        </AppButton>
      </div>
    </template>
  </AppModal>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import type { CharacterTemplateModel } from '@/types/unified'
import AppModal from '@/components/base/AppModal.vue'
import AppButton from '@/components/base/AppButton.vue'
import AppInput from '@/components/base/AppInput.vue'
import AppTextarea from '@/components/base/AppTextarea.vue'
import AppTabs from '@/components/base/AppTabs.vue'

interface Props {
  visible: boolean
  character: CharacterTemplateModel | null
}

interface Emits {
  (e: 'close'): void
  (e: 'save', character: CharacterTemplateModel): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// Tab configuration
const tabs = [
  { id: 'basic', label: 'Basic Info' },
  { id: 'race-class', label: 'Race & Class' },
  { id: 'abilities', label: 'Abilities' },
  { id: 'skills', label: 'Skills' },
  { id: 'equipment', label: 'Equipment' },
  { id: 'personality', label: 'Personality' },
]

const activeTab = ref('basic')

// Form data
const formData = ref<CharacterTemplateModel>({
  version: 1,
  id: '',
  name: '',
  race: '',
  subrace: '',
  char_class: '',
  subclass: '',
  level: 1,
  background: '',
  alignment: '',
  base_stats: {
    STR: 10,
    DEX: 10,
    CON: 10,
    INT: 10,
    WIS: 10,
    CHA: 10,
  },
  proficiencies: {
    armor: [],
    weapons: [],
    tools: [],
    saving_throws: [],
    skills: [],
  },
  languages: [],
  racial_traits: [],
  class_features: [],
  feats: [],
  spells_known: [],
  cantrips_known: [],
  starting_equipment: [],
  starting_gold: 0,
  personality_traits: [],
  ideals: [],
  bonds: [],
  flaws: [],
  appearance: '',
  backstory: '',
  content_pack_ids: ['dnd_5e_srd'],
})

// Watch for character prop changes
watch(
  () => props.character,
  newCharacter => {
    if (newCharacter) {
      // Deep copy the character data
      formData.value = JSON.parse(
        JSON.stringify(newCharacter)
      ) as CharacterTemplateModel
    }
  },
  { immediate: true }
)

// Computed properties
const isValid = computed(() => {
  return (
    formData.value.name &&
    formData.value.race &&
    formData.value.char_class &&
    formData.value.background
  )
})

// Helper functions
function getModifier(score: number): number {
  return Math.floor((score - 10) / 2)
}

function removeSkill(skill: string) {
  const index = formData.value.proficiencies.skills.indexOf(skill)
  if (index > -1) {
    formData.value.proficiencies.skills.splice(index, 1)
  }
}

function removeEquipment(index: number) {
  formData.value.starting_equipment.splice(index, 1)
}

// Personality management functions
function addPersonalityTrait() {
  formData.value.personality_traits.push('')
}

function removePersonalityTrait(index: number) {
  formData.value.personality_traits.splice(index, 1)
}

function addIdeal() {
  formData.value.ideals.push('')
}

function removeIdeal(index: number) {
  formData.value.ideals.splice(index, 1)
}

function addBond() {
  formData.value.bonds.push('')
}

function removeBond(index: number) {
  formData.value.bonds.splice(index, 1)
}

function addFlaw() {
  formData.value.flaws.push('')
}

function removeFlaw(index: number) {
  formData.value.flaws.splice(index, 1)
}

function handleClose() {
  emit('close')
}

function saveCharacter() {
  if (!isValid.value) return

  // Update last_modified timestamp
  formData.value.last_modified = new Date().toISOString()

  emit('save', formData.value)
}
</script>
