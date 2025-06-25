<template>
  <div v-if="visible" class="fixed inset-0 z-50 flex items-center justify-center p-4">
    <!-- Backdrop -->
    <div
      class="absolute inset-0 bg-black bg-opacity-50"
      @click="$emit('close')"
    />

    <!-- Modal -->
    <div class="relative bg-parchment rounded-lg shadow-xl max-w-6xl w-full max-h-[90vh] overflow-hidden flex flex-col">
      <div class="fantasy-panel flex flex-col h-full">
        <!-- Header -->
        <div class="flex items-center justify-between mb-6">
          <h2 class="text-xl font-cinzel font-bold text-text-primary">
            {{ template ? 'Edit Campaign Template' : 'Create Campaign Template' }}
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

        <!-- Tabs -->
        <div class="flex space-x-1 mb-4 border-b border-gold/20">
          <button
            v-for="tab in tabs"
            :key="tab.id"
            :class="[
              'px-4 py-2 font-medium text-sm transition-colors',
              activeTab === tab.id
                ? 'text-gold border-b-2 border-gold'
                : 'text-text-secondary hover:text-text-primary'
            ]"
            @click="activeTab = tab.id"
          >
            {{ tab.label }}
          </button>
        </div>

        <!-- Tab Content -->
        <div class="flex-1 overflow-y-auto">
          <form @submit.prevent="handleSave">
            <!-- Basic Info Tab -->
            <div v-show="activeTab === 'basic'" class="space-y-6">
              <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <!-- Left Column -->
                <div class="space-y-4">
                  <!-- Template Name -->
                  <div>
                    <label class="block text-sm font-medium text-text-primary mb-1">
                      Template Name *
                    </label>
                    <input
                      v-model="formData.name"
                      type="text"
                      required
                      class="fantasy-input w-full"
                      placeholder="Enter template name..."
                    >
                  </div>

                  <!-- Description -->
                  <div>
                    <label class="block text-sm font-medium text-text-primary mb-1">
                      Description *
                    </label>
                    <textarea
                      v-model="formData.description"
                      rows="3"
                      required
                      class="fantasy-input w-full resize-none"
                      placeholder="Describe this campaign template..."
                    />
                  </div>

                  <!-- Campaign Goal -->
                  <div>
                    <label class="block text-sm font-medium text-text-primary mb-1">
                      Campaign Goal *
                    </label>
                    <textarea
                      v-model="formData.campaign_goal"
                      rows="2"
                      required
                      class="fantasy-input w-full resize-none"
                      placeholder="What is the main objective?"
                    />
                  </div>

                  <!-- Starting Location -->
                  <div>
                    <label class="block text-sm font-medium text-text-primary mb-1">
                      Starting Location *
                    </label>
                    <input
                      v-model="formData.starting_location.name"
                      type="text"
                      required
                      class="fantasy-input w-full mb-2"
                      placeholder="Location name..."
                    >
                    <textarea
                      v-model="formData.starting_location.description"
                      rows="2"
                      required
                      class="fantasy-input w-full resize-none"
                      placeholder="Location description..."
                    />
                  </div>

                  <!-- Theme/Mood -->
                  <div>
                    <label class="block text-sm font-medium text-text-primary mb-1">
                      Theme & Mood
                    </label>
                    <input
                      v-model="formData.theme_mood"
                      type="text"
                      class="fantasy-input w-full"
                      placeholder="e.g., Dark Fantasy, High Adventure..."
                    >
                  </div>
                </div>

                <!-- Right Column -->
                <div class="space-y-4">
                  <!-- Starting Level -->
                  <div>
                    <label class="block text-sm font-medium text-text-primary mb-1">
                      Starting Level *
                    </label>
                    <input
                      v-model.number="formData.starting_level"
                      type="number"
                      min="1"
                      max="20"
                      required
                      class="fantasy-input w-full"
                    >
                  </div>

                  <!-- Difficulty -->
                  <div>
                    <label class="block text-sm font-medium text-text-primary mb-1">
                      Difficulty *
                    </label>
                    <select v-model="formData.difficulty" class="fantasy-input w-full" required>
                      <option value="easy">
                        Easy
                      </option>
                      <option value="normal">
                        Normal
                      </option>
                      <option value="hard">
                        Hard
                      </option>
                    </select>
                  </div>

                  <!-- Starting Gold Range -->
                  <div>
                    <label class="block text-sm font-medium text-text-primary mb-1">
                      Starting Gold Range
                    </label>
                    <div class="grid grid-cols-2 gap-2">
                      <input
                        v-model.number="formData.starting_gold_range.min"
                        type="number"
                        min="0"
                        placeholder="Min"
                        class="fantasy-input"
                      >
                      <input
                        v-model.number="formData.starting_gold_range.max"
                        type="number"
                        min="0"
                        placeholder="Max"
                        class="fantasy-input"
                      >
                    </div>
                  </div>

                  <!-- XP System -->
                  <div>
                    <label class="block text-sm font-medium text-text-primary mb-1">
                      XP System
                    </label>
                    <select v-model="formData.xp_system" class="fantasy-input w-full">
                      <option value="milestone">
                        Milestone
                      </option>
                      <option value="standard">
                        Standard
                      </option>
                      <option value="slow">
                        Slow Progression
                      </option>
                      <option value="fast">
                        Fast Progression
                      </option>
                    </select>
                  </div>

                  <!-- Tags -->
                  <div>
                    <label class="block text-sm font-medium text-text-primary mb-1">
                      Tags
                    </label>
                    <input
                      v-model="tagsInput"
                      type="text"
                      class="fantasy-input w-full"
                      placeholder="Enter tags separated by commas..."
                      @blur="updateTags"
                    >
                    <div v-if="formData.tags.length > 0" class="flex flex-wrap gap-2 mt-2">
                      <span
                        v-for="(tag, index) in formData.tags"
                        :key="index"
                        class="px-2 py-1 bg-gold/10 text-gold text-xs rounded-full flex items-center"
                      >
                        {{ tag }}
                        <button
                          type="button"
                          class="ml-1 text-gold hover:text-gold-light"
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
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Opening Narrative -->
              <div>
                <label class="block text-sm font-medium text-text-primary mb-1">
                  Opening Narrative *
                </label>
                <textarea
                  v-model="formData.opening_narrative"
                  rows="4"
                  required
                  class="fantasy-input w-full resize-none"
                  placeholder="Set the scene for your adventure..."
                />
              </div>

              <!-- Session Zero Notes -->
              <div>
                <label class="block text-sm font-medium text-text-primary mb-1">
                  Session Zero Notes
                </label>
                <textarea
                  v-model="formData.session_zero_notes"
                  rows="3"
                  class="fantasy-input w-full resize-none"
                  placeholder="Notes for campaign setup and player expectations..."
                />
              </div>
            </div>

            <!-- NPCs & Quests Tab -->
            <div v-show="activeTab === 'npcs-quests'" class="space-y-6">
              <!-- NPCs Section -->
              <div>
                <div class="flex items-center justify-between mb-4">
                  <h3 class="text-lg font-medium text-text-primary">
                    Initial NPCs
                  </h3>
                  <button
                    type="button"
                    class="fantasy-button-secondary text-sm"
                    @click="addNpc"
                  >
                    Add NPC
                  </button>
                </div>

                <div v-if="Object.keys(formData.initial_npcs).length === 0" class="text-text-secondary text-sm italic">
                  No NPCs added yet
                </div>

                <div v-else class="space-y-3">
                  <div
                    v-for="(npc, npcId) in formData.initial_npcs"
                    :key="npcId"
                    class="bg-parchment-light p-4 rounded-lg border border-gold/20"
                  >
                    <div class="flex items-start justify-between">
                      <div class="flex-1">
                        <h4 class="font-medium text-text-primary">
                          {{ npc.name }}
                        </h4>
                        <p class="text-sm text-text-secondary mt-1">
                          {{ npc.description }}
                        </p>
                        <p class="text-xs text-text-secondary mt-2">
                          <span class="font-medium">Location:</span> {{ npc.last_location }}
                        </p>
                      </div>
                      <div class="flex space-x-2 ml-4">
                        <button
                          type="button"
                          class="text-gold hover:text-gold-light"
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
                          class="text-red-600 hover:text-red-700"
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
                  </div>
                </div>
              </div>

              <!-- Quests Section -->
              <div>
                <div class="flex items-center justify-between mb-4">
                  <h3 class="text-lg font-medium text-text-primary">
                    Initial Quests
                  </h3>
                  <button
                    type="button"
                    class="fantasy-button-secondary text-sm"
                    @click="addQuest"
                  >
                    Add Quest
                  </button>
                </div>

                <div v-if="Object.keys(formData.initial_quests).length === 0" class="text-text-secondary text-sm italic">
                  No quests added yet
                </div>

                <div v-else class="space-y-3">
                  <div
                    v-for="(quest, questId) in formData.initial_quests"
                    :key="questId"
                    class="bg-parchment-light p-4 rounded-lg border border-gold/20"
                  >
                    <div class="flex items-start justify-between">
                      <div class="flex-1">
                        <h4 class="font-medium text-text-primary">
                          {{ quest.title }}
                        </h4>
                        <p class="text-sm text-text-secondary mt-1">
                          {{ quest.description }}
                        </p>
                        <span
                          :class="[
                            'inline-block mt-2 px-2 py-1 text-xs rounded-full',
                            quest.status === 'active' ? 'bg-green-100 text-green-800' :
                            quest.status === 'completed' ? 'bg-blue-100 text-blue-800' :
                            'bg-gray-100 text-gray-800'
                          ]"
                        >
                          {{ quest.status }}
                        </span>
                      </div>
                      <div class="flex space-x-2 ml-4">
                        <button
                          type="button"
                          class="text-gold hover:text-gold-light"
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
                          class="text-red-600 hover:text-red-700"
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
                  </div>
                </div>
              </div>
            </div>

            <!-- World & Rules Tab -->
            <div v-show="activeTab === 'world-rules'" class="space-y-6">
              <!-- World Lore Section -->
              <div>
                <h3 class="text-lg font-medium text-text-primary mb-4">
                  World Lore
                </h3>
                <div class="space-y-2">
                  <div class="flex gap-2">
                    <input
                      v-model="newLoreItem"
                      type="text"
                      class="fantasy-input flex-1"
                      placeholder="Add a piece of world lore..."
                      @keyup.enter="addLoreItem"
                    >
                    <button
                      type="button"
                      :disabled="!newLoreItem.trim()"
                      class="fantasy-button-secondary"
                      @click="addLoreItem"
                    >
                      Add
                    </button>
                  </div>

                  <div v-if="formData.world_lore.length === 0" class="text-text-secondary text-sm italic">
                    No world lore added yet
                  </div>

                  <ul v-else class="space-y-2">
                    <li
                      v-for="(lore, index) in formData.world_lore"
                      :key="index"
                      class="flex items-start gap-2 bg-parchment-light p-2 rounded"
                    >
                      <span class="flex-1 text-sm">{{ lore }}</span>
                      <button
                        type="button"
                        class="text-red-600 hover:text-red-700"
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
              </div>

              <!-- House Rules Section -->
              <div>
                <h3 class="text-lg font-medium text-text-primary mb-4">
                  House Rules
                </h3>
                <div class="space-y-3">
                  <label class="flex items-center space-x-2">
                    <input
                      v-model="formData.house_rules.critical_hit_tables"
                      type="checkbox"
                      class="rounded"
                    >
                    <span class="text-sm">Use Critical Hit Tables</span>
                  </label>

                  <label class="flex items-center space-x-2">
                    <input
                      v-model="formData.house_rules.flanking_rules"
                      type="checkbox"
                      class="rounded"
                    >
                    <span class="text-sm">Use Flanking Rules</span>
                  </label>

                  <label class="flex items-center space-x-2">
                    <input
                      v-model="formData.house_rules.milestone_leveling"
                      type="checkbox"
                      class="rounded"
                    >
                    <span class="text-sm">Use Milestone Leveling</span>
                  </label>

                  <label class="flex items-center space-x-2">
                    <input
                      v-model="formData.house_rules.death_saves_public"
                      type="checkbox"
                      class="rounded"
                    >
                    <span class="text-sm">Make Death Saves Public</span>
                  </label>
                </div>
              </div>

              <!-- Allowed Races Section -->
              <div>
                <h3 class="text-lg font-medium text-text-primary mb-4">
                  Allowed Races
                </h3>
                <div class="grid grid-cols-2 md:grid-cols-3 gap-3">
                  <label
                    v-for="race in availableRaces"
                    :key="race"
                    class="flex items-center space-x-2"
                  >
                    <input
                      v-model="formData.allowed_races"
                      :value="race"
                      type="checkbox"
                      class="rounded"
                    >
                    <span class="text-sm">{{ race }}</span>
                  </label>
                </div>
              </div>

              <!-- Allowed Classes Section -->
              <div>
                <h3 class="text-lg font-medium text-text-primary mb-4">
                  Allowed Classes
                </h3>
                <div class="grid grid-cols-2 md:grid-cols-3 gap-3">
                  <label
                    v-for="cls in availableClasses"
                    :key="cls"
                    class="flex items-center space-x-2"
                  >
                    <input
                      v-model="formData.allowed_classes"
                      :value="cls"
                      type="checkbox"
                      class="rounded"
                    >
                    <span class="text-sm">{{ cls }}</span>
                  </label>
                </div>
              </div>
            </div>

            <!-- Settings Tab -->
            <div v-show="activeTab === 'settings'" class="space-y-6">
              <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <!-- Ruleset -->
                <div>
                  <label class="block text-sm font-medium text-text-primary mb-1">
                    Ruleset
                  </label>
                  <select v-model="formData.ruleset_id" class="fantasy-input w-full">
                    <option value="dnd5e_standard">
                      D&D 5e Standard
                    </option>
                    <option value="dnd5e_homebrew">
                      D&D 5e with Homebrew
                    </option>
                  </select>
                </div>

                <!-- Lore -->
                <div>
                  <label class="block text-sm font-medium text-text-primary mb-1">
                    Lore Setting
                  </label>
                  <select v-model="formData.lore_id" class="fantasy-input w-full">
                    <option value="generic_fantasy">
                      Generic Fantasy
                    </option>
                    <option value="forgotten_realms">
                      Forgotten Realms
                    </option>
                    <option value="custom">
                      Custom
                    </option>
                  </select>
                </div>

                <!-- World Map Path -->
                <div>
                  <label class="block text-sm font-medium text-text-primary mb-1">
                    World Map Path
                  </label>
                  <input
                    v-model="formData.world_map_path"
                    type="text"
                    class="fantasy-input w-full"
                    placeholder="/static/images/maps/example.jpg"
                  >
                </div>
              </div>

              <!-- TTS Settings -->
              <div class="mt-6">
                <h3 class="text-lg font-medium text-text-primary mb-4">
                  Text-to-Speech Settings
                </h3>
                <div class="space-y-4">
                  <!-- Narration Enabled -->
                  <label class="flex items-center space-x-2">
                    <input
                      v-model="formData.narration_enabled"
                      type="checkbox"
                      class="rounded"
                    >
                    <span class="text-sm">Enable TTS Narration by Default</span>
                  </label>

                  <!-- TTS Voice -->
                  <div>
                    <label class="block text-sm font-medium text-text-primary mb-1">
                      Default TTS Voice
                    </label>
                    <select v-model="formData.tts_voice" class="fantasy-input w-full">
                      <option value="af_heart">
                        Heart (Female)
                      </option>
                      <option value="af_sarah">
                        Sarah (Female)
                      </option>
                      <option value="am_michael">
                        Michael (Male)
                      </option>
                      <option value="am_adam">
                        Adam (Male)
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
          </form>
        </div>

        <!-- Actions (outside scrollable area) -->
        <div class="flex justify-end space-x-3 mt-6 pt-4 border-t border-gold/20">
          <button
            type="button"
            class="fantasy-button-secondary"
            @click="$emit('close')"
          >
            Cancel
          </button>
          <button
            class="fantasy-button"
            @click="handleSave"
          >
            {{ template ? 'Update' : 'Create' }} Template
          </button>
        </div>
      </div>
    </div>

    <!-- NPC Modal -->
    <div v-if="showNpcModal" class="fixed inset-0 z-[60] flex items-center justify-center p-4">
      <div class="absolute inset-0 bg-black bg-opacity-50" @click="closeNpcModal" />
      <div class="relative bg-parchment rounded-lg shadow-xl max-w-md w-full p-6">
        <h3 class="text-lg font-bold mb-4">
          {{ editingNpc ? 'Edit' : 'Add' }} NPC
        </h3>
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-text-primary mb-1">Name *</label>
            <input
              v-model="npcForm.name"
              type="text"
              class="fantasy-input w-full"
              placeholder="NPC name..."
            >
          </div>
          <div>
            <label class="block text-sm font-medium text-text-primary mb-1">Description *</label>
            <textarea
              v-model="npcForm.description"
              rows="3"
              class="fantasy-input w-full resize-none"
              placeholder="NPC description..."
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-text-primary mb-1">Location *</label>
            <input
              v-model="npcForm.last_location"
              type="text"
              class="fantasy-input w-full"
              placeholder="Where can this NPC be found?"
            >
          </div>
        </div>
        <div class="flex justify-end space-x-3 mt-6">
          <button class="fantasy-button-secondary" @click="closeNpcModal">
            Cancel
          </button>
          <button class="fantasy-button" @click="saveNpc">
            Save
          </button>
        </div>
      </div>
    </div>

    <!-- Quest Modal -->
    <div v-if="showQuestModal" class="fixed inset-0 z-[60] flex items-center justify-center p-4">
      <div class="absolute inset-0 bg-black bg-opacity-50" @click="closeQuestModal" />
      <div class="relative bg-parchment rounded-lg shadow-xl max-w-md w-full p-6">
        <h3 class="text-lg font-bold mb-4">
          {{ editingQuest ? 'Edit' : 'Add' }} Quest
        </h3>
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-text-primary mb-1">Title *</label>
            <input
              v-model="questForm.title"
              type="text"
              class="fantasy-input w-full"
              placeholder="Quest title..."
            >
          </div>
          <div>
            <label class="block text-sm font-medium text-text-primary mb-1">Description *</label>
            <textarea
              v-model="questForm.description"
              rows="3"
              class="fantasy-input w-full resize-none"
              placeholder="Quest description..."
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-text-primary mb-1">Status</label>
            <select v-model="questForm.status" class="fantasy-input w-full">
              <option value="inactive">
                Inactive
              </option>
              <option value="active">
                Active
              </option>
              <option value="completed">
                Completed
              </option>
            </select>
          </div>
        </div>
        <div class="flex justify-end space-x-3 mt-6">
          <button class="fantasy-button-secondary" @click="closeQuestModal">
            Cancel
          </button>
          <button class="fantasy-button" @click="saveQuest">
            Save
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import type { CampaignTemplateModel, NPCModel, QuestModel, LocationModel, HouseRulesModel, GoldRangeModel } from '../../types/unified'

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
  { id: 'settings', label: 'Settings' }
]

const formData = ref({
  name: '',
  description: '',
  campaign_goal: '',
  starting_location: {
    name: '',
    description: ''
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
    death_saves_public: false
  } as HouseRulesModel,
  allowed_races: [] as string[],
  allowed_classes: [] as string[],
  starting_gold_range: {
    min: 0,
    max: 0
  } as GoldRangeModel,
  world_map_path: '',
  // TTS Settings
  narration_enabled: false,
  tts_voice: 'af_heart'
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
  last_location: ''
})

const questForm = ref({
  id: '',
  title: '',
  description: '',
  status: 'inactive'
})

// State for world lore
const newLoreItem = ref('')

// Available races and classes
const availableRaces = ['Human', 'Elf', 'Dwarf', 'Halfling', 'Gnome', 'Half-Elf', 'Half-Orc', 'Tiefling', 'Dragonborn']
const availableClasses = ['Fighter', 'Wizard', 'Cleric', 'Rogue', 'Ranger', 'Paladin', 'Barbarian', 'Sorcerer', 'Warlock', 'Druid', 'Monk', 'Bard']

watch(() => props.template, (newTemplate) => {
  if (newTemplate) {
    formData.value = {
      name: newTemplate.name || '',
      description: newTemplate.description || '',
      campaign_goal: newTemplate.campaign_goal || '',
      starting_location: {
        name: newTemplate.starting_location?.name || '',
        description: newTemplate.starting_location?.description || ''
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
        death_saves_public: false
      },
      allowed_races: newTemplate.allowed_races || [],
      allowed_classes: newTemplate.allowed_classes || [],
      starting_gold_range: newTemplate.starting_gold_range || { min: 0, max: 0 },
      world_map_path: newTemplate.world_map_path || '',
      // TTS Settings
      narration_enabled: newTemplate.narration_enabled ?? false,
      tts_voice: newTemplate.tts_voice || 'af_heart'
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
        description: ''
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
        death_saves_public: false
      },
      allowed_races: [],
      allowed_classes: [],
      starting_gold_range: { min: 0, max: 0 },
      world_map_path: '',
      // TTS Settings
      narration_enabled: false,
      tts_voice: 'af_heart'
    }
    tagsInput.value = ''
  }
  // Reset tab to basic when opening modal
  activeTab.value = 'basic'
}, { immediate: true })

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
    last_location: ''
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
  if (!npcForm.value.name || !npcForm.value.description || !npcForm.value.last_location) {
    alert('Please fill in all required fields')
    return
  }

  const npcId = editingNpc.value || npcForm.value.id || `npc_${Date.now()}`
  formData.value.initial_npcs[npcId] = {
    id: npcId,
    name: npcForm.value.name,
    description: npcForm.value.description,
    last_location: npcForm.value.last_location
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
    status: 'inactive'
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

  const questId = editingQuest.value || questForm.value.id || `quest_${Date.now()}`
  formData.value.initial_quests[questId] = {
    id: questId,
    title: questForm.value.title,
    description: questForm.value.description,
    status: questForm.value.status
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

function handleSave() {
  updateTags() // Ensure tags are updated before saving
  emit('save', { ...formData.value })
}
</script>
