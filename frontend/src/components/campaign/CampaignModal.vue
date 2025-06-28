<template>
  <AppModal :visible="visible" size="lg" @close="$emit('close')">
    <template #header>
      <h2 class="text-xl font-cinzel font-bold text-theme-primary">
        {{ campaign ? 'Edit Campaign' : 'Create Campaign' }}
      </h2>
    </template>

    <form @submit.prevent="handleSave">
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <!-- Left Column -->
        <div class="space-y-4">
          <!-- Campaign Name -->
          <div>
            <label class="block text-sm font-medium text-theme-primary mb-1">
              Campaign Name *
            </label>
            <AppInput
              v-model="formData.name"
              type="text"
              required
              placeholder="Enter campaign name..."
            />
          </div>

          <!-- Description -->
          <div>
            <label class="block text-sm font-medium text-theme-primary mb-1">
              Description *
            </label>
            <AppTextarea
              v-model="formData.description"
              :rows="3"
              required
              placeholder="Describe your campaign..."
            />
          </div>

          <!-- Campaign Goal -->
          <div>
            <label class="block text-sm font-medium text-theme-primary mb-1">
              Campaign Goal *
            </label>
            <AppTextarea
              v-model="formData.campaign_goal"
              :rows="2"
              required
              placeholder="What is the main objective?"
            />
          </div>

          <!-- Starting Location -->
          <div>
            <label class="block text-sm font-medium text-theme-primary mb-1">
              Starting Location *
            </label>
            <AppInput
              v-model="formData.starting_location.name"
              type="text"
              required
              placeholder="Location name..."
              class="mb-2"
            />
            <AppTextarea
              v-model="formData.starting_location.description"
              :rows="2"
              required
              placeholder="Location description..."
            />
          </div>
        </div>

        <!-- Right Column -->
        <div class="space-y-4">
          <!-- Starting Level -->
          <div>
            <label class="block text-sm font-medium text-theme-primary mb-1">
              Starting Level *
            </label>
            <AppInput
              v-model.number="formData.starting_level"
              type="number"
              min="1"
              max="20"
              required
            />
          </div>

          <!-- Difficulty -->
          <div>
            <label class="block text-sm font-medium text-theme-primary mb-1">
              Difficulty *
            </label>
            <AppSelect
              v-model="formData.difficulty"
              :options="difficultyOptions"
              required
            />
          </div>

          <!-- Ruleset -->
          <div>
            <label class="block text-sm font-medium text-theme-primary mb-1">
              Ruleset
            </label>
            <AppSelect
              v-model="formData.ruleset_id"
              :options="rulesetOptions"
            />
          </div>

          <!-- Lore -->
          <div>
            <label class="block text-sm font-medium text-theme-primary mb-1">
              Lore Setting
            </label>
            <AppSelect v-model="formData.lore_id" :options="loreOptions" />
          </div>
        </div>
      </div>

      <!-- Opening Narrative -->
      <div class="mt-6">
        <label class="block text-sm font-medium text-theme-primary mb-1">
          Opening Narrative *
        </label>
        <AppTextarea
          v-model="formData.opening_narrative"
          :rows="4"
          required
          placeholder="Set the scene for your adventure..."
        />
      </div>

      <!-- Note about party selection -->
      <div
        class="mt-4 p-4 bg-theme-warn-bg/20 rounded-lg border border-theme-accent/20"
      >
        <p class="text-sm text-theme-secondary font-crimson">
          <strong>Note:</strong> This creates a blank campaign. To create a
          campaign with pre-selected characters and content, use the campaign
          templates feature.
        </p>
      </div>
    </form>

    <template #footer>
      <div class="flex justify-end space-x-3">
        <AppButton variant="secondary" @click="$emit('close')">
          Cancel
        </AppButton>
        <AppButton variant="primary" @click="handleSave">
          {{ campaign ? 'Update' : 'Create' }} Campaign
        </AppButton>
      </div>
    </template>
  </AppModal>
</template>

<script setup lang="ts">
import { ref, watch, Ref, onMounted } from 'vue'
import type {
  CampaignTemplateModel,
  CampaignInstanceModel,
  CampaignOptionItem,
} from '@/types/unified'
import AppModal from '@/components/base/AppModal.vue'
import AppInput from '@/components/base/AppInput.vue'
import AppTextarea from '@/components/base/AppTextarea.vue'
import AppSelect from '@/components/base/AppSelect.vue'
import AppButton from '@/components/base/AppButton.vue'
import { campaignApi } from '@/services/campaignApi'
import { logger } from '@/utils/logger'

// Props interface
interface Props {
  visible: boolean
  campaign?: CampaignTemplateModel | CampaignInstanceModel | null
  template?: CampaignTemplateModel | null // Template to create instance from
}

// Emits interface
interface Emits {
  (e: 'close'): void
  (e: 'save', data: Partial<CampaignTemplateModel>): void
}

// Form data interface
interface FormData {
  name: string
  description: string
  campaign_goal: string
  starting_location: {
    name: string
    description: string
  }
  opening_narrative: string
  starting_level: number
  difficulty: string
  ruleset_id: string
  lore_id: string
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const formData: Ref<FormData> = ref({
  name: '',
  description: '',
  campaign_goal: '',
  starting_location: {
    name: '',
    description: '',
  },
  opening_narrative: '',
  starting_level: 1,
  difficulty: 'normal',
  ruleset_id: 'dnd5e_standard',
  lore_id: 'generic_fantasy',
})

// Options for select dropdowns - loaded from API
const difficultyOptions = ref<CampaignOptionItem[]>([])
const loreOptions = ref<CampaignOptionItem[]>([])
const rulesetOptions = ref<CampaignOptionItem[]>([])

// Fetch campaign options on mount
onMounted(async () => {
  try {
    const response = await campaignApi.getCampaignOptions()
    difficultyOptions.value = response.data.difficulties || []
    loreOptions.value = response.data.lores || []
    rulesetOptions.value = response.data.rulesets || []
  } catch (error) {
    logger.error('Failed to fetch campaign options:', error)
    // Fallback to defaults if API fails
    difficultyOptions.value = [
      { value: 'easy', label: 'Easy' },
      { value: 'normal', label: 'Normal' },
      { value: 'hard', label: 'Hard' },
    ]
    loreOptions.value = [{ value: 'generic_fantasy', label: 'Generic Fantasy' }]
    rulesetOptions.value = [
      { value: 'dnd5e_standard', label: 'D&D 5e Standard' },
      { value: 'dnd5e_homebrew', label: 'D&D 5e with Homebrew' },
    ]
  }
})

watch(
  () => props.campaign,
  newCampaign => {
    if (newCampaign && 'description' in newCampaign) {
      // This is a CampaignTemplateModel
      formData.value = {
        name: newCampaign.name || '',
        description: newCampaign.description || '',
        campaign_goal: newCampaign.campaign_goal || '',
        starting_location: {
          name: newCampaign.starting_location?.name || '',
          description: newCampaign.starting_location?.description || '',
        },
        opening_narrative: newCampaign.opening_narrative || '',
        starting_level: newCampaign.starting_level || 1,
        difficulty: newCampaign.difficulty || 'normal',
        ruleset_id: newCampaign.ruleset_id || 'dnd5e_standard',
        lore_id: newCampaign.lore_id || 'generic_fantasy',
      }
    } else {
      // Reset to defaults for new campaign
      formData.value = {
        name: '',
        description: '',
        campaign_goal: '',
        starting_location: {
          name: '',
          description: '',
        },
        opening_narrative: '',
        starting_level: 1,
        difficulty: 'normal',
        ruleset_id: 'dnd5e_standard',
        lore_id: 'generic_fantasy',
      }
    }
  },
  { immediate: true }
)

// Watch template prop for creating instance from template
watch(
  () => props.template,
  newTemplate => {
    if (newTemplate && !props.campaign) {
      // Inherit data from template when creating a new instance
      formData.value = {
        name: '', // User must provide a unique name
        description: newTemplate.description || '',
        campaign_goal: newTemplate.campaign_goal || '',
        starting_location: {
          name: newTemplate.starting_location?.name || '',
          description: newTemplate.starting_location?.description || '',
        },
        opening_narrative: newTemplate.opening_narrative || '',
        starting_level: newTemplate.starting_level || 1,
        difficulty: newTemplate.difficulty || 'normal',
        ruleset_id: newTemplate.ruleset_id || 'dnd5e_standard',
        lore_id: newTemplate.lore_id || 'generic_fantasy',
      }
    }
  },
  { immediate: true }
)

function handleSave() {
  // Ensure we only emit the fields that are part of the template model
  const saveData: Partial<CampaignTemplateModel> = {
    name: formData.value.name,
    description: formData.value.description,
    campaign_goal: formData.value.campaign_goal,
    starting_location: formData.value.starting_location,
    opening_narrative: formData.value.opening_narrative,
    starting_level: formData.value.starting_level,
    difficulty: formData.value.difficulty,
    ruleset_id: formData.value.ruleset_id,
    lore_id: formData.value.lore_id,
  }
  emit('save', saveData)
}
</script>
