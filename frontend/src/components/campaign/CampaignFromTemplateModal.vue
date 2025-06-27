<template>
  <div
    v-if="visible"
    class="fixed inset-0 z-50 flex items-center justify-center p-4"
  >
    <!-- Backdrop -->
    <div
      class="absolute inset-0 bg-black bg-opacity-50"
      @click="$emit('close')"
    />

    <!-- Modal -->
    <AppCard size="xl" class="max-w-5xl w-full max-h-[90vh] overflow-y-auto">
      <!-- Header -->
      <div class="flex items-center justify-between mb-6">
        <h2 class="text-xl font-cinzel font-bold text-foreground">
          Create Campaign from Template
        </h2>
        <AppButton variant="secondary" size="sm" @click="$emit('close')">
          <svg
            class="w-5 h-5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </AppButton>
      </div>

      <!-- Template Info -->
      <BaseAlert v-if="template" variant="info" class="mb-6">
        <h3 class="font-cinzel font-semibold text-lg text-foreground mb-2">
          {{ template.name }}
        </h3>
        <p class="text-sm text-foreground/80 mb-2">
          {{ template.description }}
        </p>
        <div class="flex flex-wrap gap-4 text-xs text-foreground/70">
          <span v-if="template.starting_level">
            <strong>Starting Level:</strong> {{ template.starting_level }}
          </span>
          <span v-if="template.difficulty">
            <strong>Difficulty:</strong> {{ template.difficulty }}
          </span>
          <span v-if="template.theme_mood">
            <strong>Theme:</strong> {{ template.theme_mood }}
          </span>
        </div>
      </BaseAlert>

      <!-- Form -->
      <form @submit.prevent="handleCreate">
        <!-- Campaign Name -->
        <div class="mb-6">
          <AppInput
            v-model="formData.campaignName"
            label="Campaign Name *"
            :placeholder="`My ${template?.name || 'Campaign'}`"
            required
            hint="Give your campaign a unique name to distinguish it from other campaigns"
          />
        </div>

        <!-- Character Selection -->
        <div class="mb-6">
          <div class="flex items-center justify-between mb-3">
            <label class="text-sm font-medium text-foreground">
              Select Party Members *
            </label>
            <div class="text-xs text-foreground/60">
              {{ formData.selectedCharacters.length }}/6 selected
            </div>
          </div>

          <!-- Filters -->
          <div class="mb-4 space-y-3">
            <div class="grid grid-cols-1 md:grid-cols-4 gap-3">
              <AppInput
                v-model="characterFilters.search"
                placeholder="Search characters..."
                size="sm"
                class="md:col-span-2"
              />
              <AppSelect
                v-model="characterFilters.class"
                :options="classFilterOptions"
                placeholder="Filter by class"
                size="sm"
              />
              <AppSelect
                v-model="characterFilters.level"
                :options="levelFilterOptions"
                placeholder="Filter by level"
                size="sm"
              />
            </div>

            <!-- Content Pack Compatibility Filter -->
            <div class="flex items-center space-x-4">
              <label class="flex items-center space-x-2">
                <input
                  v-model="characterFilters.showOnlyCompatible"
                  type="checkbox"
                  class="rounded border-border text-primary focus:ring-2 focus:ring-primary"
                />
                <span class="text-sm text-foreground"
                  >Show only compatible characters</span
                >
              </label>
              <AppButton
                v-if="
                  characterFilters.showOnlyCompatible &&
                  templateContentPacks.length > 0
                "
                variant="secondary"
                size="sm"
                @click="showContentPackInfo = !showContentPackInfo"
              >
                <svg
                  class="w-4 h-4 mr-1"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
                Compatibility Info
              </AppButton>
            </div>

            <!-- Content Pack Compatibility Info -->
            <BaseAlert
              v-if="showContentPackInfo && templateContentPacks.length > 0"
              variant="info"
              class="text-sm"
            >
              <strong>Template Content Packs:</strong>
              <span class="ml-2">
                {{ templateContentPacks.join(', ') }}
              </span>
              <br />
              Characters are compatible if they use overlapping content packs.
            </BaseAlert>
          </div>

          <BaseLoader
            v-if="characterTemplatesLoading"
            size="lg"
            text="Loading character templates..."
          />

          <BaseAlert v-else-if="!characterTemplates.length" variant="warning">
            <strong>No character templates available.</strong>
            <br />
            Create character templates first to use them in campaigns.
          </BaseAlert>

          <div v-else-if="!filteredCharacters.length" class="text-center py-8">
            <p class="text-foreground/60">No characters match your filters.</p>
            <AppButton
              variant="secondary"
              size="sm"
              class="mt-2"
              @click="clearFilters"
            >
              Clear Filters
            </AppButton>
          </div>

          <div v-else class="space-y-3">
            <div
              v-for="character in filteredCharacters"
              :key="character.id"
              :class="[
                'p-4 rounded-lg border-2 cursor-pointer transition-all',
                isCharacterSelected(character.id)
                  ? 'border-primary bg-primary/5 shadow-md'
                  : 'border-border hover:border-border/60 bg-card',
              ]"
              @click="toggleCharacterSelection(character.id)"
            >
              <div class="flex items-start space-x-4">
                <!-- Selection Checkbox -->
                <div class="flex-shrink-0 mt-1">
                  <div
                    :class="[
                      'w-5 h-5 rounded border-2 flex items-center justify-center transition-colors',
                      isCharacterSelected(character.id)
                        ? 'border-primary bg-primary'
                        : 'border-border',
                    ]"
                  >
                    <svg
                      v-if="isCharacterSelected(character.id)"
                      class="w-3 h-3 text-primary-foreground"
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
                </div>

                <!-- Character Info -->
                <div class="flex-1 min-w-0">
                  <div class="flex items-start justify-between">
                    <div>
                      <h4 class="font-semibold text-foreground">
                        {{ character.name }}
                      </h4>
                      <p class="text-sm text-foreground/80">
                        Level {{ character.level }} {{ character.race }}
                        {{ character.char_class }}
                      </p>
                      <p class="text-sm text-foreground/60 mt-1">
                        {{ character.background }} •
                        {{ formatAlignment(character.alignment) }}
                      </p>
                    </div>

                    <!-- Compatibility Indicator -->
                    <div class="flex items-center space-x-2">
                      <div
                        v-if="
                          getCharacterCompatibility(character).level !==
                          'perfect'
                        "
                        :class="[
                          'px-2 py-1 rounded-full text-xs',
                          getCharacterCompatibility(character).level === 'good'
                            ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
                            : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
                        ]"
                      >
                        {{ getCharacterCompatibility(character).label }}
                      </div>
                    </div>
                  </div>

                  <!-- Content Packs -->
                  <div class="flex flex-wrap gap-1 mt-3">
                    <BaseBadge
                      v-for="packId in character.content_pack_ids || [
                        'dnd_5e_srd',
                      ]"
                      :key="packId"
                      :variant="
                        isContentPackUsedByTemplate(packId)
                          ? 'primary'
                          : 'secondary'
                      "
                      size="sm"
                    >
                      {{ getContentPackName(packId) }}
                    </BaseBadge>
                  </div>

                  <!-- Compatibility Details -->
                  <div
                    v-if="
                      getCharacterCompatibility(character).level !== 'perfect'
                    "
                    class="mt-2 text-xs text-foreground/60"
                  >
                    {{ getCharacterCompatibility(character).reason }}
                  </div>
                </div>
              </div>
            </div>
          </div>

          <p
            v-if="characterTemplates.length"
            class="text-xs text-foreground/60 mt-3"
          >
            Select 1-6 characters for your party. You can add more characters
            later.
          </p>
        </div>

        <!-- TTS Settings (Optional Override) -->
        <AppCard class="mb-6">
          <h4 class="font-medium text-sm text-foreground mb-3">
            Voice Narration Settings (Optional)
          </h4>
          <p class="text-xs text-foreground/60 mb-3">
            Override the default narration settings for this campaign. Leave
            unchecked to use template defaults.
          </p>

          <div class="space-y-3">
            <!-- Override Checkbox -->
            <div class="flex items-center">
              <input
                id="override-tts"
                v-model="formData.overrideTTS"
                type="checkbox"
                class="rounded border-border text-primary focus:ring-2 focus:ring-primary"
              />
              <label for="override-tts" class="ml-2 text-sm text-foreground">
                Override default voice settings
              </label>
            </div>

            <!-- TTS Settings (shown when override is checked) -->
            <div v-if="formData.overrideTTS" class="ml-6 space-y-3">
              <!-- Enable Narration -->
              <div class="flex items-center">
                <input
                  id="narration-enabled"
                  v-model="formData.narrationEnabled"
                  type="checkbox"
                  class="rounded border-border text-primary focus:ring-2 focus:ring-primary"
                />
                <label
                  for="narration-enabled"
                  class="ml-2 text-sm text-foreground"
                >
                  Enable voice narration
                </label>
              </div>

              <!-- Voice Selection -->
              <div v-if="formData.narrationEnabled">
                <AppSelect
                  v-model="formData.ttsVoice"
                  label="TTS Voice"
                  :options="ttsVoiceOptions"
                  size="sm"
                />
              </div>
            </div>
          </div>
        </AppCard>

        <!-- Actions -->
        <div
          class="flex justify-between items-center pt-4 border-t border-border/20"
        >
          <div class="text-sm text-foreground/60">
            <span v-if="formData.selectedCharacters.length === 0">
              No characters selected
            </span>
            <span v-else-if="formData.selectedCharacters.length === 1">
              1 character selected
            </span>
            <span v-else>
              {{ formData.selectedCharacters.length }} characters selected
            </span>
          </div>
          <div class="flex space-x-3">
            <AppButton variant="secondary" @click="$emit('close')">
              Cancel
            </AppButton>
            <AppButton
              type="submit"
              :disabled="
                !formData.campaignName ||
                formData.selectedCharacters.length === 0
              "
              @click="handleCreate"
            >
              Create Campaign
            </AppButton>
          </div>
        </div>
      </form>
    </AppCard>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { campaignApi } from '../../services/campaignApi'
import { useContentStore } from '@/stores/contentStore'
import type {
  CampaignTemplateModel,
  CharacterTemplateModel,
} from '@/types/unified'
import AppInput from '@/components/base/AppInput.vue'
import AppSelect from '@/components/base/AppSelect.vue'
import { logger } from '@/utils/logger'
import AppButton from '@/components/base/AppButton.vue'
import AppCard from '@/components/base/AppCard.vue'
import BaseLoader from '@/components/base/BaseLoader.vue'
import BaseAlert from '@/components/base/BaseAlert.vue'
import BaseBadge from '@/components/base/BaseBadge.vue'

interface Props {
  visible: boolean
  template: CampaignTemplateModel
}

const props = defineProps<Props>()

const emit = defineEmits<{
  close: []
  create: [
    data: {
      templateId: string
      campaignName: string
      characterTemplateIds: string[]
      narrationEnabled?: boolean
      ttsVoice?: string
    },
  ]
}>()

// Local state for character templates
const characterTemplates = ref<CharacterTemplateModel[]>([])
const characterTemplatesLoading = ref(false)

// Content store for content pack data
const contentStore = useContentStore()

// Filter state
const characterFilters = ref({
  search: '',
  class: '',
  level: '',
  showOnlyCompatible: false,
})

const showContentPackInfo = ref(false)

interface FormData {
  campaignName: string
  selectedCharacters: string[]
  overrideTTS: boolean
  narrationEnabled: boolean
  ttsVoice: string
}

const formData = ref<FormData>({
  campaignName: '',
  selectedCharacters: [],
  overrideTTS: false,
  narrationEnabled: false,
  ttsVoice: 'af_heart',
})

// Computed properties for filtering and compatibility
const templateContentPacks = computed<string[]>(() => {
  if (!props.template) return []

  // Use template's content_pack_ids directly
  return props.template.content_pack_ids || []
})

const classFilterOptions = computed(() => {
  const classes = [
    ...new Set(characterTemplates.value.map(c => c.char_class).filter(Boolean)),
  ]
  return [
    { value: '', label: 'All Classes' },
    ...classes.map(cls => ({ value: cls, label: cls })),
  ]
})

const levelFilterOptions = computed(() => {
  const levels = [
    ...new Set(characterTemplates.value.map(c => c.level).filter(Boolean)),
  ].sort((a, b) => a - b)
  return [
    { value: '', label: 'All Levels' },
    ...levels.map(level => ({
      value: level.toString(),
      label: `Level ${level}`,
    })),
  ]
})

const ttsVoiceOptions = [
  { value: 'af_heart', label: 'Heart (Female)' },
  { value: 'af_bella', label: 'Bella (Female)' },
  { value: 'af_sarah', label: 'Sarah (Female)' },
  { value: 'am_adam', label: 'Adam (Male)' },
  { value: 'am_michael', label: 'Michael (Male)' },
  { value: 'bf_emma', label: 'Emma (British Female)' },
  { value: 'bm_george', label: 'George (British Male)' },
]

const filteredCharacters = computed(() => {
  let filtered = characterTemplates.value

  // Search filter
  if (characterFilters.value.search) {
    const search = characterFilters.value.search.toLowerCase()
    filtered = filtered.filter(
      char =>
        char.name.toLowerCase().includes(search) ||
        char.race?.toLowerCase().includes(search) ||
        char.char_class?.toLowerCase().includes(search) ||
        char.background?.toLowerCase().includes(search)
    )
  }

  // Class filter
  if (characterFilters.value.class) {
    filtered = filtered.filter(
      char => char.char_class === characterFilters.value.class
    )
  }

  // Level filter
  if (characterFilters.value.level) {
    const level = parseInt(characterFilters.value.level)
    filtered = filtered.filter(char => char.level === level)
  }

  // Compatibility filter
  if (characterFilters.value.showOnlyCompatible) {
    filtered = filtered.filter(char => {
      const compatibility = getCharacterCompatibility(char)
      return compatibility.level === 'perfect' || compatibility.level === 'good'
    })
  }

  return filtered
})

// Helper functions
function formatAlignment(alignment: string): string {
  if (!alignment) return ''
  return alignment
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

function getContentPackName(packId: string): string {
  const pack = contentStore.contentPacks.find(p => p.id === packId)
  return pack?.name || packId
}

function isContentPackUsedByTemplate(packId: string): boolean {
  return templateContentPacks.value.includes(packId)
}

interface CompatibilityResult {
  level: 'perfect' | 'good' | 'poor'
  label: string
  reason: string
}

function getCharacterCompatibility(
  character: CharacterTemplateModel
): CompatibilityResult {
  const charPacks = character.content_pack_ids || ['dnd_5e_srd']
  const templatePacks = templateContentPacks.value

  // If template has no specific content packs, all characters are compatible
  if (templatePacks.length === 0) {
    return {
      level: 'perfect',
      label: 'Compatible',
      reason: '',
    }
  }

  // Check for overlap
  const overlap = charPacks.filter(packId => templatePacks.includes(packId))
  const overlapRatio =
    overlap.length / Math.max(charPacks.length, templatePacks.length)

  if (overlapRatio === 1) {
    return {
      level: 'perfect',
      label: 'Perfect Match',
      reason: '',
    }
  } else if (overlapRatio >= 0.5 || overlap.length > 0) {
    return {
      level: 'good',
      label: 'Mostly Compatible',
      reason: `Shares ${overlap.length} content pack(s) with template`,
    }
  } else {
    return {
      level: 'poor',
      label: 'Incompatible',
      reason: 'No overlapping content packs with template',
    }
  }
}

function clearFilters(): void {
  characterFilters.value = {
    search: '',
    class: '',
    level: '',
    showOnlyCompatible: false,
  }
}

// Function to load character templates
async function loadCharacterTemplates() {
  characterTemplatesLoading.value = true
  try {
    const response = await campaignApi.getTemplates()
    characterTemplates.value = response.data || []
  } catch (error) {
    logger.error('Failed to load character templates:', error)
    characterTemplates.value = []
  } finally {
    characterTemplatesLoading.value = false
  }
}

// Load character templates and content packs when modal opens
onMounted(async () => {
  if (props.visible) {
    await Promise.all([
      loadCharacterTemplates(),
      contentStore.loadContentPacks(),
    ])
  }
})

// Reset form when modal opens
watch(
  () => props.visible,
  async newVal => {
    if (newVal) {
      formData.value = {
        campaignName: '',
        selectedCharacters: [],
        overrideTTS: false,
        narrationEnabled: false,
        ttsVoice: 'af_heart',
      }

      // Reset filters
      clearFilters()
      showContentPackInfo.value = false

      // Load character templates and content packs if not already loaded
      if (
        !characterTemplates.value.length &&
        !characterTemplatesLoading.value
      ) {
        await Promise.all([
          loadCharacterTemplates(),
          contentStore.loadContentPacks(),
        ])
      }
    }
  }
)

function toggleCharacterSelection(characterId: string): void {
  const index = formData.value.selectedCharacters.indexOf(characterId)
  if (index > -1) {
    formData.value.selectedCharacters.splice(index, 1)
  } else {
    // Limit to 6 characters
    if (formData.value.selectedCharacters.length < 6) {
      formData.value.selectedCharacters.push(characterId)
    }
  }
}

function isCharacterSelected(characterId: string): boolean {
  return formData.value.selectedCharacters.includes(characterId)
}

function handleCreate(): void {
  if (
    !formData.value.campaignName ||
    formData.value.selectedCharacters.length === 0
  ) {
    return
  }

  const createData = {
    templateId: props.template.id,
    campaignName: formData.value.campaignName,
    characterTemplateIds: formData.value.selectedCharacters,
    narrationEnabled: undefined as boolean | undefined,
    ttsVoice: undefined as string | undefined,
  }

  // Only include TTS overrides if the user opted to override
  if (formData.value.overrideTTS) {
    createData.narrationEnabled = formData.value.narrationEnabled
    createData.ttsVoice = formData.value.ttsVoice
  }

  emit('create', createData)
}
</script>

<style scoped>
.spinner {
  @apply inline-block w-8 h-8 border-4 border-gold border-t-transparent rounded-full animate-spin;
}
</style>
