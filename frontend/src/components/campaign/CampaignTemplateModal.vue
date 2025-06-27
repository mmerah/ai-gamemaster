<template>
  <AppModal :visible="visible" size="xl" @close="$emit('close')">
    <template #header>
      <h2 class="text-xl font-cinzel font-bold">
        {{ template ? 'Edit Campaign Template' : 'Create Campaign Template' }}
      </h2>
    </template>

    <!-- Tabs -->
    <AppTabs
      :tabs="tabs"
      :active-tab="activeTab"
      @update:active-tab="activeTab = $event"
    />

    <!-- Tab Content -->
    <form class="mt-6" @submit.prevent="handleSave">
      <!-- Basic Info Tab -->
      <div v-show="activeTab === 'basic'" class="space-y-6">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <!-- Left Column -->
          <div class="space-y-4">
            <!-- Template Name -->
            <AppInput
              v-model="formData.name"
              label="Template Name *"
              placeholder="Enter template name..."
              required
            />

            <!-- Description -->
            <AppTextarea
              v-model="formData.description"
              label="Description *"
              :rows="3"
              placeholder="Describe this campaign template..."
              required
            />

            <!-- Campaign Goal -->
            <AppTextarea
              v-model="formData.campaign_goal"
              label="Campaign Goal *"
              :rows="2"
              placeholder="What is the main objective?"
              required
            />

            <!-- Starting Location -->
            <AppFormSection title="Starting Location *">
              <AppInput
                v-model="formData.starting_location.name"
                placeholder="Location name..."
                required
                class="mb-2"
              />
              <AppTextarea
                v-model="formData.starting_location.description"
                :rows="2"
                placeholder="Location description..."
                required
              />
            </AppFormSection>

            <!-- Theme/Mood -->
            <AppInput
              v-model="formData.theme_mood"
              label="Theme & Mood"
              placeholder="e.g., Dark Fantasy, High Adventure..."
            />
          </div>

          <!-- Right Column -->
          <div class="space-y-4">
            <!-- Starting Level -->
            <AppNumberInput
              v-model="formData.starting_level"
              label="Starting Level *"
              :min="1"
              :max="20"
              required
            />

            <!-- Difficulty -->
            <AppSelect
              v-model="formData.difficulty"
              label="Difficulty *"
              :options="difficultyOptions"
              required
            />

            <!-- Starting Gold Range -->
            <AppFormSection title="Starting Gold Range">
              <div class="grid grid-cols-2 gap-2">
                <AppNumberInput
                  v-model="formData.starting_gold_range.min"
                  :min="0"
                  placeholder="Min"
                />
                <AppNumberInput
                  v-model="formData.starting_gold_range.max"
                  :min="0"
                  placeholder="Max"
                />
              </div>
            </AppFormSection>

            <!-- XP System -->
            <AppSelect
              v-model="formData.xp_system"
              label="XP System"
              :options="xpSystemOptions"
            />

            <!-- Tags -->
            <AppFormSection title="Tags">
              <AppInput
                v-model="tagsInput"
                placeholder="Enter tags separated by commas..."
                @blur="updateTags"
              />
              <div
                v-if="formData.tags.length > 0"
                class="flex flex-wrap gap-2 mt-2"
              >
                <BaseBadge
                  v-for="(tag, index) in formData.tags"
                  :key="index"
                  variant="default"
                  size="sm"
                  class="flex items-center"
                >
                  {{ tag }}
                  <button
                    type="button"
                    class="ml-1 text-accent hover:text-accent/80"
                    @click="removeTag(index)"
                  >
                    <svg
                      class="w-3 h-3"
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
                </BaseBadge>
              </div>
            </AppFormSection>
          </div>
        </div>

        <!-- Opening Narrative -->
        <AppTextarea
          v-model="formData.opening_narrative"
          label="Opening Narrative *"
          :rows="4"
          placeholder="Set the scene for your adventure..."
          required
        />

        <!-- Session Zero Notes -->
        <AppTextarea
          v-model="formData.session_zero_notes"
          label="Session Zero Notes"
          :rows="3"
          placeholder="Notes for campaign setup and player expectations..."
        />
      </div>

      <!-- NPCs & Quests Tab -->
      <div v-show="activeTab === 'npcs-quests'" class="space-y-6">
        <!-- NPCs Section -->
        <AppFormSection title="Initial NPCs">
          <template #actions>
            <AppButton
              type="button"
              variant="secondary"
              size="sm"
              @click="addNpc"
            >
              Add NPC
            </AppButton>
          </template>

          <div
            v-if="Object.keys(formData.initial_npcs).length === 0"
            class="text-foreground/60 text-sm italic"
          >
            No NPCs added yet
          </div>

          <div v-else class="space-y-3">
            <BasePanel
              v-for="(npc, npcId) in formData.initial_npcs"
              :key="npcId"
              class="p-4"
            >
              <div class="flex items-start justify-between">
                <div class="flex-1">
                  <h4 class="font-medium text-foreground">
                    {{ npc.name }}
                  </h4>
                  <p class="text-sm text-foreground/60 mt-1">
                    {{ npc.description }}
                  </p>
                  <p class="text-xs text-foreground/60 mt-2">
                    <span class="font-medium">Location:</span>
                    {{ npc.last_location }}
                  </p>
                </div>
                <div class="flex space-x-2 ml-4">
                  <button
                    type="button"
                    class="text-accent hover:text-accent/80"
                    @click="editNpc(npcId)"
                  >
                    <svg
                      class="w-4 h-4"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"
                      />
                    </svg>
                  </button>
                  <button
                    type="button"
                    class="text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300"
                    @click="removeNpc(npcId)"
                  >
                    <svg
                      class="w-4 h-4"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                      />
                    </svg>
                  </button>
                </div>
              </div>
            </BasePanel>
          </div>
        </AppFormSection>

        <!-- Quests Section -->
        <AppFormSection title="Initial Quests">
          <template #actions>
            <AppButton
              type="button"
              variant="secondary"
              size="sm"
              @click="addQuest"
            >
              Add Quest
            </AppButton>
          </template>

          <div
            v-if="Object.keys(formData.initial_quests).length === 0"
            class="text-foreground/60 text-sm italic"
          >
            No quests added yet
          </div>

          <div v-else class="space-y-3">
            <BasePanel
              v-for="(quest, questId) in formData.initial_quests"
              :key="questId"
              class="p-4"
            >
              <div class="flex items-start justify-between">
                <div class="flex-1">
                  <h4 class="font-medium text-foreground">
                    {{ quest.title }}
                  </h4>
                  <p class="text-sm text-foreground/60 mt-1">
                    {{ quest.description }}
                  </p>
                  <BaseBadge
                    :variant="getQuestVariant(quest.status)"
                    size="sm"
                    class="mt-2"
                  >
                    {{ quest.status }}
                  </BaseBadge>
                </div>
                <div class="flex space-x-2 ml-4">
                  <button
                    type="button"
                    class="text-accent hover:text-accent/80"
                    @click="editQuest(questId)"
                  >
                    <svg
                      class="w-4 h-4"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"
                      />
                    </svg>
                  </button>
                  <button
                    type="button"
                    class="text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300"
                    @click="removeQuest(questId)"
                  >
                    <svg
                      class="w-4 h-4"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                      />
                    </svg>
                  </button>
                </div>
              </div>
            </BasePanel>
          </div>
        </AppFormSection>
      </div>

      <!-- World & Rules Tab -->
      <div v-show="activeTab === 'world-rules'" class="space-y-6">
        <!-- World Lore Section -->
        <AppFormSection title="World Lore">
          <div class="space-y-2">
            <div class="flex gap-2">
              <AppInput
                v-model="newLoreItem"
                class="flex-1"
                placeholder="Add a piece of world lore..."
                @keyup.enter="addLoreItem"
              />
              <AppButton
                type="button"
                variant="secondary"
                :disabled="!newLoreItem.trim()"
                @click="addLoreItem"
              >
                Add
              </AppButton>
            </div>

            <div
              v-if="formData.world_lore.length === 0"
              class="text-foreground/60 text-sm italic"
            >
              No world lore added yet
            </div>

            <ul v-else class="space-y-2">
              <li
                v-for="(lore, index) in formData.world_lore"
                :key="index"
                class="flex items-start gap-2 bg-card p-2 rounded"
              >
                <span class="flex-1 text-sm">{{ lore }}</span>
                <button
                  type="button"
                  class="text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300"
                  @click="removeLoreItem(index)"
                >
                  <svg
                    class="w-4 h-4"
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
              </li>
            </ul>
          </div>
        </AppFormSection>

        <!-- House Rules Section -->
        <AppFormSection title="House Rules">
          <div class="space-y-3">
            <label class="flex items-center space-x-2 cursor-pointer">
              <input
                v-model="formData.house_rules.critical_hit_tables"
                type="checkbox"
                class="rounded text-primary focus:ring-primary"
              />
              <span class="text-sm">Use Critical Hit Tables</span>
            </label>

            <label class="flex items-center space-x-2 cursor-pointer">
              <input
                v-model="formData.house_rules.flanking_rules"
                type="checkbox"
                class="rounded text-primary focus:ring-primary"
              />
              <span class="text-sm">Use Flanking Rules</span>
            </label>

            <label class="flex items-center space-x-2 cursor-pointer">
              <input
                v-model="formData.house_rules.milestone_leveling"
                type="checkbox"
                class="rounded text-primary focus:ring-primary"
              />
              <span class="text-sm">Use Milestone Leveling</span>
            </label>

            <label class="flex items-center space-x-2 cursor-pointer">
              <input
                v-model="formData.house_rules.death_saves_public"
                type="checkbox"
                class="rounded text-primary focus:ring-primary"
              />
              <span class="text-sm">Make Death Saves Public</span>
            </label>
          </div>
        </AppFormSection>

        <!-- Allowed Races Section -->
        <AppFormSection title="Allowed Races">
          <div class="grid grid-cols-2 md:grid-cols-3 gap-3">
            <label
              v-for="race in availableRaces"
              :key="race"
              class="flex items-center space-x-2 cursor-pointer"
            >
              <input
                v-model="formData.allowed_races"
                :value="race"
                type="checkbox"
                class="rounded text-primary focus:ring-primary"
              />
              <span class="text-sm">{{ race }}</span>
            </label>
          </div>
        </AppFormSection>

        <!-- Allowed Classes Section -->
        <AppFormSection title="Allowed Classes">
          <div class="grid grid-cols-2 md:grid-cols-3 gap-3">
            <label
              v-for="cls in availableClasses"
              :key="cls"
              class="flex items-center space-x-2 cursor-pointer"
            >
              <input
                v-model="formData.allowed_classes"
                :value="cls"
                type="checkbox"
                class="rounded text-primary focus:ring-primary"
              />
              <span class="text-sm">{{ cls }}</span>
            </label>
          </div>
        </AppFormSection>
      </div>

      <!-- Settings Tab -->
      <div v-show="activeTab === 'settings'" class="space-y-6">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <!-- Ruleset -->
          <AppSelect
            v-model="formData.ruleset_id"
            label="Ruleset"
            :options="rulesetOptions"
          />

          <!-- Lore -->
          <AppSelect
            v-model="formData.lore_id"
            label="Lore Setting"
            :options="loreOptions"
          />

          <!-- World Map Path -->
          <AppInput
            v-model="formData.world_map_path"
            label="World Map Path"
            placeholder="/static/images/maps/example.jpg"
          />
        </div>

        <!-- TTS Settings -->
        <AppFormSection title="Text-to-Speech Settings" class="mt-6">
          <div class="space-y-4">
            <!-- Narration Enabled -->
            <label class="flex items-center space-x-2 cursor-pointer">
              <input
                v-model="formData.narration_enabled"
                type="checkbox"
                class="rounded text-primary focus:ring-primary"
              />
              <span class="text-sm">Enable TTS Narration by Default</span>
            </label>

            <!-- TTS Voice -->
            <AppSelect
              v-model="formData.tts_voice"
              label="Default TTS Voice"
              :options="ttsVoiceOptions"
            />
          </div>
        </AppFormSection>
      </div>
    </form>

    <template #footer>
      <div class="flex justify-end space-x-3">
        <AppButton type="button" variant="secondary" @click="$emit('close')">
          Cancel
        </AppButton>
        <AppButton type="button" @click="handleSave">
          {{ template ? 'Update' : 'Create' }} Template
        </AppButton>
      </div>
    </template>
  </AppModal>

  <!-- NPC Modal -->
  <AppModal :visible="showNpcModal" size="md" @close="closeNpcModal">
    <template #header>
      <h3 class="text-lg font-bold">{{ editingNpc ? 'Edit' : 'Add' }} NPC</h3>
    </template>

    <div class="space-y-4">
      <AppInput
        v-model="npcForm.name"
        label="Name *"
        placeholder="NPC name..."
      />
      <AppTextarea
        v-model="npcForm.description"
        label="Description *"
        :rows="3"
        placeholder="NPC description..."
      />
      <AppInput
        v-model="npcForm.last_location"
        label="Location *"
        placeholder="Where can this NPC be found?"
      />
    </div>

    <template #footer>
      <div class="flex justify-end space-x-3">
        <AppButton variant="secondary" @click="closeNpcModal">
          Cancel
        </AppButton>
        <AppButton @click="saveNpc">Save</AppButton>
      </div>
    </template>
  </AppModal>

  <!-- Quest Modal -->
  <AppModal :visible="showQuestModal" size="md" @close="closeQuestModal">
    <template #header>
      <h3 class="text-lg font-bold">
        {{ editingQuest ? 'Edit' : 'Add' }} Quest
      </h3>
    </template>

    <div class="space-y-4">
      <AppInput
        v-model="questForm.title"
        label="Title *"
        placeholder="Quest title..."
      />
      <AppTextarea
        v-model="questForm.description"
        label="Description *"
        :rows="3"
        placeholder="Quest description..."
      />
      <AppSelect
        v-model="questForm.status"
        label="Status"
        :options="questStatusOptions"
      />
    </div>

    <template #footer>
      <div class="flex justify-end space-x-3">
        <AppButton variant="secondary" @click="closeQuestModal">
          Cancel
        </AppButton>
        <AppButton @click="saveQuest">Save</AppButton>
      </div>
    </template>
  </AppModal>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import type {
  CampaignTemplateModel,
  CampaignOptionItem,
  NPCModel,
  QuestModel,
  LocationModel,
  HouseRulesModel,
  GoldRangeModel,
} from '../../types/unified'
import { campaignApi } from '@/services/campaignApi'
import { ttsApi } from '@/services/ttsApi'
import { useCampaignStore } from '@/stores/campaignStore'
import { logger } from '@/utils/logger'
import AppModal from '../base/AppModal.vue'
import AppButton from '../base/AppButton.vue'
import AppInput from '../base/AppInput.vue'
import AppTextarea from '../base/AppTextarea.vue'
import AppSelect from '../base/AppSelect.vue'
import AppTabs from '../base/AppTabs.vue'
import AppNumberInput from '../base/AppNumberInput.vue'
import AppFormSection from '../base/AppFormSection.vue'
import BaseBadge from '../base/BaseBadge.vue'
import BasePanel from '../base/BasePanel.vue'

interface Props {
  visible: boolean
  template: CampaignTemplateModel | null
}

const props = defineProps<Props>()

const emit = defineEmits(['close', 'save'])

// Tab state
const activeTab = ref('basic')
const tabs = [
  { id: 'basic', label: 'Basic Info' },
  { id: 'npcs-quests', label: 'NPCs & Quests' },
  { id: 'world-rules', label: 'World & Rules' },
  { id: 'settings', label: 'Settings' },
]

const formData = ref({
  name: '',
  description: '',
  campaign_goal: '',
  starting_location: {
    name: '',
    description: '',
  } as LocationModel,
  opening_narrative: '',
  starting_level: 1,
  difficulty: 'normal',
  ruleset_id: 'dnd5e_standard',
  lore_id: 'generic_fantasy',
  theme_mood: '',
  xp_system: 'milestone',
  session_zero_notes: '',
  tags: [] as string[],
  // New unified model fields
  initial_npcs: {} as Record<string, NPCModel>,
  initial_quests: {} as Record<string, QuestModel>,
  world_lore: [] as string[],
  house_rules: {
    critical_hit_tables: false,
    flanking_rules: false,
    milestone_leveling: true,
    death_saves_public: false,
  } as HouseRulesModel,
  allowed_races: [] as string[],
  allowed_classes: [] as string[],
  starting_gold_range: {
    min: 0,
    max: 0,
  } as GoldRangeModel,
  world_map_path: '',
  // TTS Settings
  narration_enabled: false,
  tts_voice: 'af_heart',
})

const tagsInput = ref('')

// State for adding NPCs/Quests
const showNpcModal = ref(false)
const showQuestModal = ref(false)
const editingNpc = ref<string | null>(null)
const editingQuest = ref<string | null>(null)

const npcForm = ref({
  id: '',
  name: '',
  description: '',
  last_location: '',
})

const questForm = ref({
  id: '',
  title: '',
  description: '',
  status: 'inactive',
})

// State for world lore
const newLoreItem = ref('')

// Available races and classes - loaded from API
const availableRaces = ref<string[]>([])
const availableClasses = ref<string[]>([])
const d5eDataLoading = ref(false)

// Select options
// Options for select dropdowns - fetch from API
const difficultyOptions = ref<CampaignOptionItem[]>([])
const loreOptions = ref<CampaignOptionItem[]>([])

const xpSystemOptions = [
  { label: 'Milestone', value: 'milestone' },
  { label: 'Standard', value: 'standard' },
  { label: 'Slow Progression', value: 'slow' },
  { label: 'Fast Progression', value: 'fast' },
]

const rulesetOptions = [
  { label: 'D&D 5e Standard', value: 'dnd5e_standard' },
  { label: 'D&D 5e with Homebrew', value: 'dnd5e_homebrew' },
]

// TTS voice options - loaded from API
const ttsVoiceOptions = ref<{ label: string; value: string }[]>([])

const questStatusOptions = [
  { label: 'Inactive', value: 'inactive' },
  { label: 'Active', value: 'active' },
  { label: 'Completed', value: 'completed' },
]

// Helper function for quest badge variant
function getQuestVariant(status: string): 'success' | 'info' | 'default' {
  switch (status) {
    case 'active':
      return 'success'
    case 'completed':
      return 'info'
    default:
      return 'default'
  }
}

watch(
  () => props.template,
  newTemplate => {
    if (newTemplate) {
      formData.value = {
        name: newTemplate.name || '',
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
        theme_mood: newTemplate.theme_mood || '',
        xp_system: newTemplate.xp_system || 'milestone',
        session_zero_notes: newTemplate.session_zero_notes || '',
        tags: newTemplate.tags || [],
        // New fields
        initial_npcs: newTemplate.initial_npcs || {},
        initial_quests: newTemplate.initial_quests || {},
        world_lore: newTemplate.world_lore || [],
        house_rules: newTemplate.house_rules || {
          critical_hit_tables: false,
          flanking_rules: false,
          milestone_leveling: true,
          death_saves_public: false,
        },
        allowed_races: newTemplate.allowed_races || [],
        allowed_classes: newTemplate.allowed_classes || [],
        starting_gold_range: newTemplate.starting_gold_range || {
          min: 0,
          max: 0,
        },
        world_map_path: newTemplate.world_map_path || '',
        // TTS Settings
        narration_enabled: newTemplate.narration_enabled ?? false,
        tts_voice: newTemplate.tts_voice || 'af_heart',
      }
      tagsInput.value = formData.value.tags.join(', ')
    } else {
      // Reset to defaults for new template
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
        theme_mood: '',
        xp_system: 'milestone',
        session_zero_notes: '',
        tags: [],
        // New fields
        initial_npcs: {},
        initial_quests: {},
        world_lore: [],
        house_rules: {
          critical_hit_tables: false,
          flanking_rules: false,
          milestone_leveling: true,
          death_saves_public: false,
        },
        allowed_races: [],
        allowed_classes: [],
        starting_gold_range: { min: 0, max: 0 },
        world_map_path: '',
        // TTS Settings
        narration_enabled: false,
        tts_voice: 'af_heart',
      }
      tagsInput.value = ''
    }
    // Reset tab to basic when opening modal
    activeTab.value = 'basic'
  },
  { immediate: true }
)

function updateTags() {
  if (tagsInput.value.trim()) {
    formData.value.tags = tagsInput.value
      .split(',')
      .map(tag => tag.trim())
      .filter(tag => tag.length > 0)
  }
}

function removeTag(index: number) {
  formData.value.tags.splice(index, 1)
  tagsInput.value = formData.value.tags.join(', ')
}

// NPC Management
function addNpc() {
  editingNpc.value = null
  npcForm.value = {
    id: '',
    name: '',
    description: '',
    last_location: '',
  }
  showNpcModal.value = true
}

function editNpc(npcId: string) {
  const npc = formData.value.initial_npcs[npcId]
  if (npc) {
    editingNpc.value = npcId
    npcForm.value = { ...npc }
    showNpcModal.value = true
  }
}

function removeNpc(npcId: string) {
  delete formData.value.initial_npcs[npcId]
}

function closeNpcModal() {
  showNpcModal.value = false
  editingNpc.value = null
}

function saveNpc() {
  if (
    !npcForm.value.name ||
    !npcForm.value.description ||
    !npcForm.value.last_location
  ) {
    alert('Please fill in all required fields')
    return
  }

  const npcId = editingNpc.value || npcForm.value.id || `npc_${Date.now()}`
  formData.value.initial_npcs[npcId] = {
    id: npcId,
    name: npcForm.value.name,
    description: npcForm.value.description,
    last_location: npcForm.value.last_location,
  }

  closeNpcModal()
}

// Quest Management
function addQuest() {
  editingQuest.value = null
  questForm.value = {
    id: '',
    title: '',
    description: '',
    status: 'inactive',
  }
  showQuestModal.value = true
}

function editQuest(questId: string) {
  const quest = formData.value.initial_quests[questId]
  if (quest) {
    editingQuest.value = questId
    questForm.value = { ...quest }
    showQuestModal.value = true
  }
}

function removeQuest(questId: string) {
  delete formData.value.initial_quests[questId]
}

function closeQuestModal() {
  showQuestModal.value = false
  editingQuest.value = null
}

function saveQuest() {
  if (!questForm.value.title || !questForm.value.description) {
    alert('Please fill in all required fields')
    return
  }

  const questId =
    editingQuest.value || questForm.value.id || `quest_${Date.now()}`
  formData.value.initial_quests[questId] = {
    id: questId,
    title: questForm.value.title,
    description: questForm.value.description,
    status: questForm.value.status,
  }

  closeQuestModal()
}

// World Lore Management
function addLoreItem() {
  if (newLoreItem.value.trim()) {
    formData.value.world_lore.push(newLoreItem.value.trim())
    newLoreItem.value = ''
  }
}

function removeLoreItem(index: number) {
  formData.value.world_lore.splice(index, 1)
}

// Get campaign store instance
const campaignStore = useCampaignStore()

// Fetch campaign options, TTS voices, and D5e data on mount
onMounted(async () => {
  // Fetch campaign options
  try {
    const response = await campaignApi.getCampaignOptions()
    difficultyOptions.value = response.data.difficulties
    loreOptions.value = response.data.lores
  } catch (error) {
    logger.error('Failed to fetch campaign options:', error)
    // Fallback to defaults if API fails
    difficultyOptions.value = [
      { value: 'easy', label: 'Easy' },
      { value: 'normal', label: 'Normal' },
      { value: 'hard', label: 'Hard' },
    ]
    loreOptions.value = [{ value: 'generic_fantasy', label: 'Generic Fantasy' }]
  }

  // Fetch TTS voices
  try {
    const voicesResponse = await ttsApi.getVoices()
    ttsVoiceOptions.value = voicesResponse.data.voices.map(voice => ({
      label: `${voice.name}${voice.gender ? ` (${voice.gender})` : ''}`,
      value: voice.id,
    }))
  } catch (error) {
    logger.error('Failed to fetch TTS voices:', error)
    // Fallback to basic options if API fails
    ttsVoiceOptions.value = [{ label: 'Default Voice', value: 'default' }]
  }

  // Fetch D5e data (races and classes)
  d5eDataLoading.value = true
  try {
    // Load character creation options which includes races and classes
    const creationOptions = await campaignStore.loadCharacterCreationOptions()

    // Extract race names
    if (creationOptions.races) {
      availableRaces.value = creationOptions.races.map(race => race.name)
    }

    // Extract class names
    if (creationOptions.classes) {
      availableClasses.value = creationOptions.classes.map(clazz => clazz.name)
    }
  } catch (error) {
    logger.error('Failed to fetch D5e data:', error)
    // Fallback to empty arrays if API fails
    availableRaces.value = []
    availableClasses.value = []
  } finally {
    d5eDataLoading.value = false
  }
})

function handleSave() {
  updateTags() // Ensure tags are updated before saving
  emit('save', { ...formData.value })
}
</script>
