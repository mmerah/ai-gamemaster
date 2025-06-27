<template>
  <AppModal
    :visible="visible"
    :title="currentStepTitle"
    size="xl"
    @close="handleClose"
  >
    <template #body>
      <!-- Progress Bar -->
      <div class="mb-6">
        <div class="flex items-center justify-between mb-2">
          <span class="text-sm text-foreground/60">
            Step {{ currentStep + 1 }} of {{ steps.length }}
          </span>
          <span class="text-sm font-medium text-foreground">
            {{ steps[currentStep].label }}
          </span>
        </div>
        <div class="w-full bg-card rounded-full h-2">
          <div
            class="bg-primary h-2 rounded-full transition-all duration-300"
            :style="{ width: `${((currentStep + 1) / steps.length) * 100}%` }"
          />
        </div>
      </div>

      <!-- Step Content -->
      <div class="min-h-[400px]">
        <!-- Step 1: Content Pack Selection -->
        <ContentPackSelectionStep
          v-if="currentStep === 0"
          v-model="formData.content_pack_ids"
          :available-content-packs="availableContentPacks"
          :loading-content-packs="contentPacksLoading"
        />

        <!-- Step 2: Basic Information -->
        <BasicInfoStep
          v-else-if="currentStep === 1"
          v-model="basicInfoData"
          :alignment-options="alignmentOptions"
          :background-options="backgroundOptions"
          :d5e-data-loading="d5eDataLoading"
          :fetched-background-details="fetchedBackgroundDetails"
          :fetching-background="fetchingDetails.background"
          :background-skills="backgroundSkills"
          :granted-tools="grantedTools"
        />

        <!-- Step 3: Race & Class Selection -->
        <RaceClassStep
          v-else-if="currentStep === 2"
          v-model="raceClassData"
          :race-options="raceOptions"
          :class-options="classOptions"
          :d5e-data-loading="d5eDataLoading"
          :selected-race-details="selectedRaceDetails"
          :selected-class-details="selectedClassDetails"
          :fetching-race="fetchingDetails.race"
          :fetching-class="fetchingDetails.class"
          :available-class-skills="availableClassSkills"
          :class-skill-choices="classSkillChoices"
        />

        <!-- Step 4: Ability Scores -->
        <AbilityScoresStep
          v-else-if="currentStep === 3"
          v-model="abilityScoreData"
        />

        <!-- Step 5: Skills & Proficiencies -->
        <SkillsProficienciesStep
          v-else-if="currentStep === 4"
          v-model="skillsData"
          :available-class-skills="availableClassSkills"
          :class-skill-choices="classSkillChoices"
          :background-skills="backgroundSkills"
          :can-choose-expertise="canChooseExpertise"
          :expertise-choices="expertiseChoices"
          :available-expertise-skills="availableExpertiseSkills"
          :granted-languages="grantedLanguages"
          :granted-tools="grantedTools"
        />

        <!-- Step 6: Equipment & Spells -->
        <SpellcastingStep
          v-else-if="currentStep === 5"
          v-model="equipmentSpellsData"
          :selected-class-details="selectedClassDetails"
          :fetched-background-details="fetchedBackgroundDetails"
          :is-spellcaster="isSpellcaster"
          :cantrips-known="cantripsKnown"
          :spells-known="spellsKnown"
          :class-equipment="classEquipment"
          :background-equipment="backgroundEquipment"
          :available-cantrips="availableCantrips"
          :available-first-level-spells="availableFirstLevelSpells"
          :loading-spells="loadingSpells"
        />

        <!-- Step 7: Review & Confirm -->
        <ReviewStep
          v-else-if="currentStep === 6"
          :character="reviewCharacterData"
          :content-packs="availableContentPacks"
          :race-options="raceOptions"
          :class-options="classOptions"
          :background-options="backgroundOptions"
          :alignment-options="alignmentOptions"
        />

        <!-- Steps 8+ placeholder -->
        <div v-else class="text-center py-8">
          <p class="text-foreground/60">This step is under construction...</p>
        </div>
      </div>
    </template>

    <template #footer>
      <div class="flex justify-between">
        <AppButton
          variant="secondary"
          :disabled="currentStep === 0"
          @click="previousStep"
        >
          Previous
        </AppButton>

        <div class="flex gap-2">
          <AppButton variant="secondary" @click="handleClose">
            Cancel
          </AppButton>

          <AppButton
            v-if="currentStep < steps.length - 1"
            :disabled="!canProceed"
            @click="nextStep"
          >
            Next
          </AppButton>

          <AppButton v-else :disabled="!canProceed" @click="saveCharacter">
            Create Character
          </AppButton>
        </div>
      </div>
    </template>
  </AppModal>
</template>

<script setup lang="ts">
import { logger } from '@/utils/logger'
import { ref, computed, watch, onMounted } from 'vue'
import { useContentStore } from '@/stores/contentStore'
import { useD5eData } from '@/composables/useD5eData'
import {
  getRaceById,
  getClassById,
  getBackgroundById,
  getCantripsForClass,
  getFirstLevelSpellsForClass,
} from '@/services/d5eApi'
import type {
  CharacterTemplateModel,
  D5eRace,
  D5eClass,
  D5eBackground,
  APIReference,
} from '@/types/unified'
import { DEFAULT_ABILITY_SCORES, ALIGNMENTS } from '@/constants/character'

// Import all wizard step components
import ContentPackSelectionStep from './wizard-steps/ContentPackSelectionStep.vue'
import BasicInfoStep from './wizard-steps/BasicInfoStep.vue'
import RaceClassStep from './wizard-steps/RaceClassStep.vue'
import AbilityScoresStep from './wizard-steps/AbilityScoresStep.vue'
import SkillsProficienciesStep from './wizard-steps/SkillsProficienciesStep.vue'
import SpellcastingStep from './wizard-steps/SpellcastingStep.vue'
import ReviewStep from './wizard-steps/ReviewStep.vue'

// Import base components
import AppModal from '@/components/base/AppModal.vue'
import AppButton from '@/components/base/AppButton.vue'

interface Props {
  visible: boolean
  initialData?: Partial<CharacterTemplateModel>
}

const props = withDefaults(defineProps<Props>(), {
  visible: false,
  initialData: undefined,
})

const emit = defineEmits<{
  close: []
  save: [character: Partial<CharacterTemplateModel>]
}>()

// Stores
const contentStore = useContentStore()

// Form Data - Split into sections matching the step components
const formData = ref({
  name: '',
  content_pack_ids: ['dnd_5e_srd'] as string[],
  race: '',
  char_class: '',
  background: '',
  alignment: 'true_neutral',
  level: 1,
  ability_scores: { ...DEFAULT_ABILITY_SCORES },
  skills: [] as string[],
  expertises: [] as string[],
  cantrips: [] as string[],
  equipment: [] as string[],
  spells: [] as string[],
  backstory: '',
  ...props.initialData,
})

// Computed data models for each step
const basicInfoData = computed({
  get: () => ({
    name: formData.value.name,
    alignment: formData.value.alignment,
    background: formData.value.background,
    backstory: formData.value.backstory,
  }),
  set: value => {
    formData.value.name = value.name
    formData.value.alignment = value.alignment
    formData.value.background = value.background
    formData.value.backstory = value.backstory
  },
})

const raceClassData = computed({
  get: () => ({
    race: formData.value.race,
    char_class: formData.value.char_class,
    level: formData.value.level,
  }),
  set: value => {
    formData.value.race = value.race
    formData.value.char_class = value.char_class
    formData.value.level = value.level
  },
})

const abilityScoreData = computed({
  get: () => ({
    ability_score_method: abilityScoreMethod.value,
    ...formData.value.ability_scores,
  }),
  set: value => {
    const { ability_score_method, ...scores } = value
    abilityScoreMethod.value = ability_score_method
    formData.value.ability_scores =
      scores as typeof formData.value.ability_scores
  },
})

const skillsData = computed({
  get: () => ({
    class_skills: formData.value.skills,
    expertise: formData.value.expertises,
  }),
  set: value => {
    formData.value.skills = value.class_skills
    formData.value.expertises = value.expertise
  },
})

const equipmentSpellsData = computed({
  get: () => ({
    equipment_method: equipmentMethod.value,
    cantrips: formData.value.cantrips,
    spells: formData.value.spells,
  }),
  set: value => {
    equipmentMethod.value = value.equipment_method
    formData.value.cantrips = value.cantrips
    formData.value.spells = value.spells
  },
})

const reviewCharacterData = computed(() => ({
  name: formData.value.name,
  alignment: formData.value.alignment,
  background: formData.value.background,
  backstory: formData.value.backstory,
  race: formData.value.race,
  char_class: formData.value.char_class,
  level: formData.value.level,
  ability_scores: formData.value.ability_scores,
  skills: formData.value.skills,
  expertise: formData.value.expertises,
  cantrips: formData.value.cantrips,
  spells: formData.value.spells,
  content_pack_ids: formData.value.content_pack_ids,
}))

// Wizard state
const currentStep = ref(0)
const errors = ref<Record<string, string>>({})

// Fetched D5E details
const fetchedRaceDetails = ref<D5eRace | null>(null)
const fetchedClassDetails = ref<D5eClass | null>(null)
const fetchedBackgroundDetails = ref<D5eBackground | null>(null)
const fetchingDetails = ref({
  race: false,
  class: false,
  background: false,
})

// Step definitions
const steps = [
  { id: 'content-packs', label: 'Content Selection' },
  { id: 'basic-info', label: 'Basic Information' },
  { id: 'race-class', label: 'Race & Class' },
  { id: 'abilities', label: 'Ability Scores' },
  { id: 'skills', label: 'Skills & Proficiencies' },
  { id: 'equipment', label: 'Equipment & Spells' },
  { id: 'review', label: 'Review & Confirm' },
]

// Content packs
const contentPacksLoading = ref(false)
const availableContentPacks = computed(() =>
  contentStore.contentPacks.filter(pack => pack.is_active !== false)
)

// D5E Data with content pack filtering
const {
  getRaceOptions,
  getClassOptions,
  getBackgroundOptions,
  isLoading: d5eDataLoading,
} = useD5eData({ contentPackIds: formData.value.content_pack_ids })

// Computed options from D5E data
const raceOptions = computed(() => getRaceOptions())
const classOptions = computed(() => getClassOptions())
const backgroundOptions = computed(() => getBackgroundOptions())

// Ability score methods
const abilityScoreMethod = ref<'point-buy' | 'standard-array' | 'roll'>(
  'point-buy'
)

// Equipment method
const equipmentMethod = ref<'standard' | 'gold'>('standard')

const alignmentOptions = ALIGNMENTS

// Computed properties
const currentStepTitle = computed(() => {
  return `Create Character - ${steps[currentStep.value].label}`
})

const selectedRaceDetails = computed(() => {
  return fetchedRaceDetails.value
})

const selectedClassDetails = computed(() => {
  return fetchedClassDetails.value
})

// Skills & Proficiencies computed properties
const availableClassSkills = computed(() => {
  if (!selectedClassDetails.value) {
    return []
  }

  // Extract skill choices from class proficiency choices
  const skillChoices = selectedClassDetails.value.proficiency_choices?.find(
    choice => choice.type === 'skills'
  )

  if (!skillChoices || !skillChoices.from_) {
    return []
  }

  // Convert APIReference array to options
  const options = skillChoices.from_.options as APIReference[] | undefined
  if (!options) {
    return []
  }

  return options.map(skill => ({
    value: skill.index,
    label: skill.name,
  }))
})

const classSkillChoices = computed(() => {
  if (!selectedClassDetails.value) {
    return 0
  }

  // Get the number of skill choices from proficiency choices
  const skillChoices = selectedClassDetails.value.proficiency_choices?.find(
    choice => choice.type === 'skills'
  )

  return skillChoices?.choose || 0
})

const backgroundSkills = computed(() => {
  if (!fetchedBackgroundDetails.value) {
    return []
  }

  // Get skill proficiencies from background
  const skills =
    fetchedBackgroundDetails.value.starting_proficiencies?.filter(prof =>
      prof.index.startsWith('skill-')
    ) || []

  return skills.map(skill => ({
    value: skill.index.replace('skill-', ''),
    label: skill.name,
  }))
})

const canChooseExpertise = computed(() => {
  if (!selectedClassDetails.value) {
    // Fallback to hardcoded check
    return (
      formData.value.char_class === 'rogue' ||
      formData.value.char_class === 'bard'
    )
  }

  // Check class features for expertise
  // This is a simplified check - in a real implementation,
  // we'd need to check specific class features
  return (
    selectedClassDetails.value.index === 'rogue' ||
    selectedClassDetails.value.index === 'bard'
  )
})

const expertiseChoices = computed(() => {
  if (!canChooseExpertise.value) {
    return 0
  }

  // Rogues and Bards typically get 2 expertise at level 1
  return 2
})

const availableExpertiseSkills = computed(() => {
  // Can only choose expertise in skills you're proficient in
  const classSkills = availableClassSkills.value.filter(skill =>
    formData.value.skills.includes(skill.value)
  )

  const allProficientSkills = [...classSkills, ...backgroundSkills.value]
  return allProficientSkills
})

const grantedLanguages = computed(() => {
  const languages: string[] = []

  // Get languages from race
  if (selectedRaceDetails.value?.languages) {
    selectedRaceDetails.value.languages.forEach(lang => {
      languages.push(lang.name)
    })
  }

  // Get languages from background language options (if any)
  // Note: D5eBackground has language_options, not direct languages
  // This would require fetching available languages from the options
  // For now, we'll skip background languages

  // Default to Common if no languages found
  if (languages.length === 0) {
    languages.push('Common')
  }

  return languages
})

const grantedTools = computed(() => {
  if (!fetchedBackgroundDetails.value) {
    return []
  }

  // Get tool proficiencies from background
  const tools =
    fetchedBackgroundDetails.value.starting_proficiencies?.filter(
      prof => prof.index.includes('tools') || prof.index.includes('kit')
    ) || []

  return tools.map(tool => tool.name)
})

// Equipment computed properties
const classEquipment = computed(() => {
  if (
    !selectedClassDetails.value ||
    !selectedClassDetails.value.starting_equipment
  ) {
    return []
  }

  // Extract equipment names from starting equipment
  const equipment: string[] = []

  selectedClassDetails.value.starting_equipment.forEach(item => {
    if ('equipment' in item && item.equipment) {
      equipment.push(item.equipment.name)
    } else if ('equipment_option' in item && item.equipment_option) {
      // For equipment options, just show a generic description
      equipment.push(item.equipment_option.desc || 'Equipment choice')
    }
  })

  return equipment
})

const backgroundEquipment = computed(() => {
  if (
    !fetchedBackgroundDetails.value ||
    !fetchedBackgroundDetails.value.starting_equipment
  ) {
    return []
  }

  // Extract equipment names from starting equipment
  const equipment: string[] = []

  fetchedBackgroundDetails.value.starting_equipment.forEach(item => {
    if ('equipment' in item && item.equipment) {
      equipment.push(item.equipment.name)
    } else if ('equipment_option' in item && item.equipment_option) {
      // For equipment options, just show a generic description
      equipment.push(item.equipment_option.desc || 'Equipment choice')
    }
  })

  return equipment
})

// Spellcasting computed properties
const isSpellcaster = computed(() => {
  if (!selectedClassDetails.value) {
    // Fallback to hardcoded check
    const spellcastingClasses = [
      'wizard',
      'sorcerer',
      'cleric',
      'druid',
      'bard',
      'warlock',
    ]
    return spellcastingClasses.includes(formData.value.char_class)
  }

  // Check if class has spellcasting feature
  return !!selectedClassDetails.value.spellcasting
})

const cantripsKnown = computed(() => {
  if (!isSpellcaster.value || !selectedClassDetails.value) return 0

  // Get cantrips known from spellcasting info
  const spellcasting = selectedClassDetails.value.spellcasting

  if (!spellcasting) return 0

  // For most classes, cantrips known is in the spellcasting info
  // This is a simplified implementation - real data would come from class tables
  switch (selectedClassDetails.value.index) {
    case 'wizard':
    case 'cleric':
    case 'druid':
      return 3 // These classes typically start with 3 cantrips
    case 'sorcerer':
    case 'warlock':
      return 2 // These classes typically start with 2 cantrips
    case 'bard':
      return 2 // Bards start with 2 cantrips
    default:
      return 2
  }
})

const spellsKnown = computed(() => {
  if (!isSpellcaster.value || !selectedClassDetails.value) return 0

  // Spells known varies by class
  // This is a simplified implementation
  switch (selectedClassDetails.value.index) {
    case 'wizard':
      return 6 // Wizards start with 6 spells in spellbook
    case 'sorcerer':
    case 'bard':
      return 2 // Sorcerers and Bards know 2 spells at level 1
    case 'cleric':
    case 'druid':
      // Clerics and Druids prepare spells, not "know" them
      // But for character creation, let them pick some
      return (
        1 +
        (selectedClassDetails.value.spellcasting?.spellcasting_ability
          ?.index === 'wis'
          ? 2
          : 0)
      )
    case 'warlock':
      return 2 // Warlocks know 2 spells at level 1
    default:
      return 2
  }
})

// Reactive state for spell lists
const availableCantrips = ref<Array<{ value: string; label: string }>>([])
const availableFirstLevelSpells = ref<Array<{ value: string; label: string }>>(
  []
)
const loadingSpells = ref(false)

// Watch for class changes to load spell lists
watch(
  [() => formData.value.char_class, () => formData.value.content_pack_ids],
  async ([newClass, contentPacks]) => {
    if (!newClass || !isSpellcaster.value) {
      availableCantrips.value = []
      availableFirstLevelSpells.value = []
      return
    }

    loadingSpells.value = true
    try {
      // Fetch cantrips
      const cantrips = await getCantripsForClass(
        newClass,
        contentPacks as string[]
      )
      availableCantrips.value = cantrips.map(spell => ({
        value: spell.index,
        label: spell.name,
      }))

      // Fetch 1st level spells
      const firstLevel = await getFirstLevelSpellsForClass(
        newClass,
        contentPacks as string[]
      )
      availableFirstLevelSpells.value = firstLevel.map(spell => ({
        value: spell.index,
        label: spell.name,
      }))
    } catch (error) {
      logger.error('Failed to load spell lists:', error)
      availableCantrips.value = []
      availableFirstLevelSpells.value = []
    } finally {
      loadingSpells.value = false
    }
  },
  { immediate: true }
)

// Validation
const canProceed = computed(() => {
  switch (currentStep.value) {
    case 0: // Content packs
      return formData.value.content_pack_ids.length > 0

    case 1: // Basic info
      return (
        formData.value.name.trim().length > 0 && formData.value.alignment !== ''
      )

    case 2: // Race & Class
      return formData.value.race !== '' && formData.value.char_class !== ''

    case 3: // Ability scores
      // Validation is handled within the AbilityScoresStep component
      return true

    case 4: // Skills & Proficiencies
      return formData.value.skills.length >= classSkillChoices.value

    case 5: // Equipment & Spells
      if (isSpellcaster.value) {
        return (
          formData.value.cantrips.length >= cantripsKnown.value &&
          formData.value.spells.length >= spellsKnown.value
        )
      }
      return true

    case 6: // Review
      // Check all required fields are filled
      return (
        formData.value.name.trim().length > 0 &&
        formData.value.race !== '' &&
        formData.value.char_class !== '' &&
        formData.value.content_pack_ids.length > 0
      )

    default:
      return true
  }
})

// Methods
function handleClose() {
  if (
    confirm(
      'Are you sure you want to cancel character creation? All progress will be lost.'
    )
  ) {
    emit('close')
  }
}

function nextStep() {
  if (canProceed.value && currentStep.value < steps.length - 1) {
    currentStep.value++
  }
}

function previousStep() {
  if (currentStep.value > 0) {
    currentStep.value--
  }
}

async function saveCharacter() {
  if (!canProceed.value) return

  // Transform form data to match CharacterTemplateModel
  const characterData: Partial<CharacterTemplateModel> = {
    ...formData.value,
    // Add any additional transformations needed
  }

  emit('save', characterData)
}

// Load content packs on mount
onMounted(async () => {
  contentPacksLoading.value = true
  try {
    await contentStore.loadContentPacks()
  } finally {
    contentPacksLoading.value = false
  }
})

// Watch for race selection changes
watch(
  () => formData.value.race,
  async newRace => {
    if (!newRace) {
      fetchedRaceDetails.value = null
      return
    }

    fetchingDetails.value.race = true
    try {
      fetchedRaceDetails.value = await getRaceById(
        newRace,
        formData.value.content_pack_ids
      )
    } catch (error) {
      logger.error('Failed to fetch race details:', error)
      fetchedRaceDetails.value = null
    } finally {
      fetchingDetails.value.race = false
    }
  }
)

// Watch for class selection changes
watch(
  () => formData.value.char_class,
  async newClass => {
    if (!newClass) {
      fetchedClassDetails.value = null
      return
    }

    fetchingDetails.value.class = true
    try {
      fetchedClassDetails.value = await getClassById(
        newClass,
        formData.value.content_pack_ids
      )
    } catch (error) {
      logger.error('Failed to fetch class details:', error)
      fetchedClassDetails.value = null
    } finally {
      fetchingDetails.value.class = false
    }
  }
)

// Watch for background selection changes
watch(
  () => formData.value.background,
  async newBackground => {
    if (!newBackground) {
      fetchedBackgroundDetails.value = null
      return
    }

    fetchingDetails.value.background = true
    try {
      fetchedBackgroundDetails.value = await getBackgroundById(
        newBackground,
        formData.value.content_pack_ids
      )
    } catch (error) {
      logger.error('Failed to fetch background details:', error)
      fetchedBackgroundDetails.value = null
    } finally {
      fetchingDetails.value.background = false
    }
  }
)
</script>
