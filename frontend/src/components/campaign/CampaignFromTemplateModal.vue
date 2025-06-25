<template>
  <div v-if="visible" class="fixed inset-0 z-50 flex items-center justify-center p-4">
    <!-- Backdrop -->
    <div
      class="absolute inset-0 bg-black bg-opacity-50"
      @click="$emit('close')"
    />

    <!-- Modal -->
    <div class="relative bg-parchment rounded-lg shadow-xl max-w-5xl w-full max-h-[90vh] overflow-y-auto">
      <div class="fantasy-panel">
        <!-- Header -->
        <div class="flex items-center justify-between mb-6">
          <h2 class="text-xl font-cinzel font-bold text-text-primary">
            Create Campaign from Template
          </h2>
          <button
            class="text-text-secondary hover:text-text-primary"
            @click="$emit('close')"
          >
            <svg
              class="w-6 h-6"
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
          </button>
        </div>

        <!-- Template Info -->
        <div v-if="template" class="mb-6 p-4 bg-amber-50/20 rounded-lg border border-gold/20">
          <h3 class="font-cinzel font-semibold text-lg text-text-primary mb-2">
            {{ template.name }}
          </h3>
          <p class="text-sm text-text-secondary mb-2">
            {{ template.description }}
          </p>
          <div class="flex flex-wrap gap-4 text-xs text-text-secondary">
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
        </div>

        <!-- Form -->
        <form @submit.prevent="handleCreate">
          <!-- Campaign Name -->
          <div class="mb-6">
            <label class="block text-sm font-medium text-text-primary mb-1">
              Campaign Name *
            </label>
            <input
              v-model="formData.campaignName"
              type="text"
              required
              class="fantasy-input w-full"
              :placeholder="`My ${template?.name || 'Campaign'}`"
            >
            <p class="text-xs text-text-secondary mt-1">
              Give your campaign a unique name to distinguish it from other campaigns
            </p>
          </div>

          <!-- Character Selection -->
          <div class="mb-6">
            <label class="block text-sm font-medium text-text-primary mb-3">
              Select Party Members *
            </label>

            <div v-if="characterTemplatesLoading" class="text-center py-8">
              <div class="spinner" />
              <p class="text-text-secondary mt-2">
                Loading character templates...
              </p>
            </div>

            <div v-else-if="!characterTemplates.length" class="text-center py-8 bg-amber-50/10 rounded-lg border border-gold/10">
              <p class="text-text-secondary">
                No character templates available.
              </p>
              <p class="text-sm text-text-secondary mt-2">
                Create character templates first to use them in campaigns.
              </p>
            </div>

            <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <div
                v-for="character in characterTemplates"
                :key="character.id"
                :class="[
                  'p-4 rounded-lg border-2 cursor-pointer transition-all',
                  isCharacterSelected(character.id)
                    ? 'border-gold bg-gold/10 shadow-md'
                    : 'border-secondary/20 hover:border-secondary/40 bg-white/5'
                ]"
                @click="toggleCharacterSelection(character.id)"
              >
                <div class="flex items-start space-x-3">
                  <div class="flex-shrink-0 mt-1">
                    <div
                      :class="[
                        'w-5 h-5 rounded border-2 flex items-center justify-center transition-colors',
                        isCharacterSelected(character.id)
                          ? 'border-gold bg-gold'
                          : 'border-secondary/40'
                      ]"
                    >
                      <svg
                        v-if="isCharacterSelected(character.id)"
                        class="w-3 h-3 text-white"
                        fill="currentColor"
                        viewBox="0 0 20 20"
                      >
                        <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
                      </svg>
                    </div>
                  </div>
                  <div class="flex-1 min-w-0">
                    <h4 class="font-semibold text-text-primary truncate">
                      {{ character.name }}
                    </h4>
                    <p class="text-xs text-text-secondary">
                      Level {{ character.level }} {{ character.race }} {{ character.char_class }}
                    </p>
                    <p v-if="character.background" class="text-xs text-text-secondary/70 mt-1">
                      {{ character.background }}
                    </p>
                    <p v-if="character.alignment" class="text-xs text-text-secondary/70">
                      {{ character.alignment }}
                    </p>
                  </div>
                </div>
              </div>
            </div>

            <p v-if="characterTemplates.length" class="text-xs text-text-secondary mt-3">
              Select 1-6 characters for your party. You can add more characters later.
            </p>
          </div>

          <!-- TTS Settings (Optional Override) -->
          <div class="mb-6 p-4 bg-amber-50/10 rounded-lg border border-gold/10">
            <h4 class="font-medium text-sm text-text-primary mb-3">
              Voice Narration Settings (Optional)
            </h4>
            <p class="text-xs text-text-secondary mb-3">
              Override the default narration settings for this campaign. Leave unchecked to use template defaults.
            </p>

            <div class="space-y-3">
              <!-- Override Checkbox -->
              <div class="flex items-center">
                <input
                  id="override-tts"
                  v-model="formData.overrideTTS"
                  type="checkbox"
                  class="rounded border-brown-400 text-gold focus:ring-gold"
                >
                <label for="override-tts" class="ml-2 text-sm text-text-primary">
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
                    class="rounded border-brown-400 text-gold focus:ring-gold"
                  >
                  <label for="narration-enabled" class="ml-2 text-sm text-text-primary">
                    Enable voice narration
                  </label>
                </div>

                <!-- Voice Selection -->
                <div v-if="formData.narrationEnabled">
                  <label class="block text-xs font-medium text-text-primary mb-1">
                    TTS Voice
                  </label>
                  <select
                    v-model="formData.ttsVoice"
                    class="fantasy-input w-full text-sm"
                  >
                    <option value="af_heart">
                      Heart (Female)
                    </option>
                    <option value="af_bella">
                      Bella (Female)
                    </option>
                    <option value="af_sarah">
                      Sarah (Female)
                    </option>
                    <option value="am_adam">
                      Adam (Male)
                    </option>
                    <option value="am_michael">
                      Michael (Male)
                    </option>
                    <option value="bf_emma">
                      Emma (British Female)
                    </option>
                    <option value="bm_george">
                      George (British Male)
                    </option>
                  </select>
                </div>
              </div>
            </div>
          </div>

          <!-- Actions -->
          <div class="flex justify-between items-center pt-4 border-t border-gold/20">
            <div class="text-sm text-text-secondary">
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
              <button
                type="button"
                class="fantasy-button-secondary"
                @click="$emit('close')"
              >
                Cancel
              </button>
              <button
                type="submit"
                :disabled="!formData.campaignName || formData.selectedCharacters.length === 0"
                class="fantasy-button"
              >
                Create Campaign
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { campaignApi } from '../../services/campaignApi'

const props = defineProps({
  visible: {
    type: Boolean,
    required: true
  },
  template: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['close', 'create'])

// Local state for character templates
const characterTemplates = ref([])
const characterTemplatesLoading = ref(false)

const formData = ref({
  campaignName: '',
  selectedCharacters: [],
  overrideTTS: false,
  narrationEnabled: false,
  ttsVoice: 'af_heart'
})

// Function to load character templates
async function loadCharacterTemplates() {
  characterTemplatesLoading.value = true
  try {
    const response = await campaignApi.getTemplates()
    characterTemplates.value = response.data || []
  } catch (error) {
    console.error('Failed to load character templates:', error)
    characterTemplates.value = []
  } finally {
    characterTemplatesLoading.value = false
  }
}

// Load character templates when modal opens
onMounted(() => {
  if (props.visible) {
    loadCharacterTemplates()
  }
})

// Reset form when modal opens
watch(() => props.visible, (newVal) => {
  if (newVal) {
    formData.value = {
      campaignName: '',
      selectedCharacters: [],
      overrideTTS: false,
      narrationEnabled: false,
      ttsVoice: 'af_heart'
    }
    // Load character templates if not already loaded
    if (!characterTemplates.value.length && !characterTemplatesLoading.value) {
      loadCharacterTemplates()
    }
  }
})

function toggleCharacterSelection(characterId) {
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

function isCharacterSelected(characterId) {
  return formData.value.selectedCharacters.includes(characterId)
}

function handleCreate() {
  if (!formData.value.campaignName || formData.value.selectedCharacters.length === 0) {
    return
  }

  const createData = {
    templateId: props.template.id,
    campaignName: formData.value.campaignName,
    characterTemplateIds: formData.value.selectedCharacters
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
