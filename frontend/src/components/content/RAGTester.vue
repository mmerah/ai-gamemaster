<template>
  <AppCard class="rag-tester">
    <h3 class="text-2xl font-semibold mb-6 text-foreground">
      RAG System Tester
    </h3>

    <!-- Query Presets -->
    <QueryPresets :current-query="queryText" @apply-preset="applyPreset" />

    <!-- Content Pack Selection -->
    <BasePanel class="mb-6">
      <h4 class="text-lg font-semibold mb-4 text-foreground">Content Packs</h4>
      <div class="rag-tester__content-packs">
        <div
          v-for="pack in availableContentPacks"
          :key="pack.id"
          class="rag-tester__pack-item"
        >
          <label class="rag-tester__label">
            <input
              type="checkbox"
              class="rag-tester__checkbox"
              :checked="isPackActive(pack.id)"
              :disabled="pack.id === 'System'"
              @change="toggleContentPack(pack.id)"
            />
            <span>{{ pack.name }} ({{ pack.id }})</span>
          </label>
        </div>
      </div>
    </BasePanel>

    <!-- Basic Game Context -->
    <BasePanel class="mb-6">
      <h4 class="text-lg font-semibold mb-4 text-foreground">
        Basic Game Context
      </h4>
      <div class="rag-tester__context">
        <label class="rag-tester__label">
          <input
            v-model="contextOverride.in_combat"
            type="checkbox"
            class="rag-tester__checkbox"
          />
          <span>In Combat</span>
        </label>
        <div class="mt-4">
          <AppInput
            v-model="contextOverride.current_location"
            label="Current Location:"
            placeholder="e.g., Tavern, Dungeon..."
          />
        </div>
      </div>
    </BasePanel>

    <!-- Lore Selection -->
    <BasePanel v-if="availableLores.length > 0" class="mb-6">
      <h4 class="text-lg font-semibold mb-4 text-foreground">Active Lore</h4>
      <AppSelect v-model="activeLoreId">
        <option :value="null">No active lore</option>
        <option v-for="lore in availableLores" :key="lore.id" :value="lore.id">
          {{ lore.name || lore.id }}
        </option>
      </AppSelect>
    </BasePanel>

    <!-- Advanced Configuration (Collapsible) -->
    <details class="mb-6">
      <summary
        class="cursor-pointer p-4 bg-card rounded-lg font-semibold text-foreground hover:bg-accent hover:text-accent-foreground transition-colors"
      >
        Advanced Game State Configuration
      </summary>

      <div class="mt-4 space-y-4">
        <!-- Party Configuration -->
        <PartyConfigurator v-model="party" />

        <!-- Combat Configuration -->
        <CombatConfigurator v-model="combat" />

        <!-- World State Configuration -->
        <WorldStateConfigurator v-model="worldState" />
      </div>
    </details>

    <!-- Query Input -->
    <BasePanel class="mb-6">
      <h4 class="text-lg font-semibold mb-4 text-foreground">Test Query</h4>
      <AppTextarea
        v-model="queryText"
        placeholder="Enter a player action (e.g., 'I cast fireball at the goblin')"
        :rows="3"
      />
      <div class="flex gap-3 mt-4">
        <AppButton
          :disabled="!queryText.trim()"
          :is-loading="loading"
          @click="executeQuery"
        >
          {{ loading ? 'Testing...' : 'Test RAG Query' }}
        </AppButton>
        <AppButton
          variant="secondary"
          :disabled="loading"
          @click="clearConfiguration"
        >
          Clear/Reset
        </AppButton>
      </div>
    </BasePanel>

    <!-- Error Display -->
    <BasePanel
      v-if="error"
      class="mb-6 bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800"
    >
      <p class="text-red-600 dark:text-red-400">{{ error }}</p>
    </BasePanel>

    <!-- Results Display -->
    <BasePanel v-if="results" class="mb-6">
      <h4 class="text-lg font-semibold mb-4 text-foreground">RAG Results</h4>
      <div class="space-y-4">
        <div class="bg-background p-4 rounded">
          <h5 class="font-medium mb-2 text-foreground">Query Info:</h5>
          <pre class="text-sm text-foreground/80 overflow-x-auto">{{
            JSON.stringify(results.query_info, null, 2)
          }}</pre>
        </div>
        <div class="bg-background p-4 rounded">
          <h5 class="font-medium mb-2 text-foreground">Used Content Packs:</h5>
          <ul class="list-disc list-inside text-foreground/80">
            <li v-for="pack in results.used_content_packs" :key="pack">
              {{ pack }}
            </li>
          </ul>
        </div>
        <div class="bg-background p-4 rounded">
          <h5 class="font-medium mb-4 text-foreground">
            Retrieved Knowledge ({{ results.results.results.length }} items):
          </h5>
          <div
            v-for="(item, index) in results.results.results"
            :key="index"
            class="bg-card p-4 rounded mb-3 border border-border"
          >
            <div class="flex justify-between items-center mb-2">
              <strong class="text-foreground">{{ item.source }}</strong>
              <span class="text-sm text-foreground/60"
                >Score: {{ item.relevance_score.toFixed(3) }}</span
              >
            </div>
            <div class="text-foreground/80">{{ item.content }}</div>
            <details v-if="Object.keys(item.metadata).length > 0" class="mt-3">
              <summary
                class="cursor-pointer text-sm text-foreground/60 hover:text-foreground"
              >
                Metadata
              </summary>
              <pre
                class="mt-2 text-xs bg-background p-2 rounded overflow-x-auto"
                >{{ JSON.stringify(item.metadata, null, 2) }}</pre
              >
            </details>
          </div>
        </div>
        <div class="bg-background p-4 rounded">
          <details>
            <summary
              class="cursor-pointer font-medium text-foreground hover:text-accent"
            >
              Raw Response
            </summary>
            <pre class="mt-2 text-xs overflow-x-auto">{{
              JSON.stringify(results, null, 2)
            }}</pre>
          </details>
        </div>
      </div>
    </BasePanel>
  </AppCard>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useContentStore } from '@/stores/contentStore'
import { useCampaignStore } from '@/stores/campaignStore'
import { contentApi } from '@/services/contentApi'
import type {
  RAGQueryResponse,
  CharacterInstanceModel,
  CombatStateModel,
  NPCModel,
  QuestModel,
} from '@/types/unified'
import type { QueryPreset } from '@/types/ui'
import PartyConfigurator from './rag/PartyConfigurator.vue'
import CombatConfigurator from './rag/CombatConfigurator.vue'
import WorldStateConfigurator from './rag/WorldStateConfigurator.vue'
import QueryPresets from './rag/QueryPresets.vue'
import AppCard from '@/components/base/AppCard.vue'
import BasePanel from '@/components/base/BasePanel.vue'
import AppButton from '@/components/base/AppButton.vue'
import AppInput from '@/components/base/AppInput.vue'
import AppTextarea from '@/components/base/AppTextarea.vue'
import AppSelect from '@/components/base/AppSelect.vue'

const contentStore = useContentStore()
const campaignStore = useCampaignStore()

// State
const queryText = ref('')
const loading = ref(false)
const error = ref<string | null>(null)
const results = ref<RAGQueryResponse | null>(null)
const activeContentPacks = ref<string[]>(['System'])
const contextOverride = ref({
  in_combat: false,
  current_location: '',
})
const activeLoreId = ref<string | null>(null)

// Advanced configuration state
const party = ref<Record<string, CharacterInstanceModel>>({})
const combat = ref<CombatStateModel>({
  is_active: false,
  combatants: [],
  current_turn_index: -1,
  round_number: 1,
  current_turn_instruction_given: false,
})
const worldState = ref({
  campaign_goal: '',
  known_npcs: {} as Record<string, NPCModel>,
  active_quests: {} as Record<string, QuestModel>,
  world_lore: [] as string[],
  event_summary: [] as string[],
  session_count: 0,
  active_ruleset_id: undefined as string | undefined,
})

// Computed
const availableContentPacks = computed(() => contentStore.contentPacks)
// State for lores
const availableLores = ref<
  Array<{ id: string; name: string; file_path: string }>
>([])

// Load available lores
const loadAvailableLores = async () => {
  try {
    // Load lores from the lores.json file
    const response = await fetch('/src/assets/data/knowledge/lores.json')
    if (!response.ok) {
      // Try alternative path
      const altResponse = await fetch('/app/content/data/knowledge/lores.json')
      if (altResponse.ok) {
        availableLores.value = (await altResponse.json()) as Array<{
          id: string
          name: string
          file_path: string
        }>
      }
    } else {
      availableLores.value = (await response.json()) as Array<{
        id: string
        name: string
        file_path: string
      }>
    }
  } catch (error) {
    console.warn('Could not load lores.json, using hardcoded values')
    // Fallback to hardcoded lores if file not found
    availableLores.value = [
      {
        id: 'generic_fantasy',
        name: 'Generic Fantasy Lore',
        file_path: 'knowledge/lore/generic_fantasy_lore.json',
      },
      {
        id: 'world_of_eldoria',
        name: 'World of Eldoria',
        file_path: 'knowledge/lore/world_of_eldoria_lore.json',
      },
    ]
  }
}

const currentCampaignId = computed(() => {
  // Try to get current campaign ID from the store
  // If not available, return null (API will use defaults)
  return (
    campaignStore.activeCampaign?.id || campaignStore.campaigns[0]?.id || null
  )
})

// Methods
const isPackActive = (packId: string) => {
  return activeContentPacks.value.includes(packId)
}

const toggleContentPack = (packId: string) => {
  if (packId === 'System') return // System pack is always active

  const index = activeContentPacks.value.indexOf(packId)
  if (index > -1) {
    activeContentPacks.value.splice(index, 1)
  } else {
    activeContentPacks.value.push(packId)
  }
}

// Apply preset from QueryPresets component
const applyPreset = (preset: QueryPreset) => {
  queryText.value = preset.query

  // Apply game state overrides if present
  if (preset.gameStateOverrides) {
    if (preset.gameStateOverrides.in_combat !== undefined) {
      contextOverride.value.in_combat = preset.gameStateOverrides.in_combat
      combat.value.is_active = preset.gameStateOverrides.in_combat
    }

    if (preset.gameStateOverrides.current_location) {
      contextOverride.value.current_location =
        preset.gameStateOverrides.current_location
    }

    if (
      preset.gameStateOverrides.addCombatants &&
      combat.value.combatants.length === 0
    ) {
      // Add sample combatants
      combat.value.combatants = [
        {
          id: 'combatant_1',
          name: 'Goblin',
          combatant_type: 'monster',
          initiative: 15,
          initiative_modifier: 2,
          current_hp: 7,
          max_hp: 7,
          armor_class: 15,
          conditions: [],
          is_player_controlled: false,
          is_incapacitated: false,
          has_taken_turn: false,
          monster_type: 'goblin',
          challenge_rating: 0.25,
          size: 'Small',
        },
        {
          id: 'combatant_2',
          name: 'Orc',
          combatant_type: 'monster',
          initiative: 10,
          initiative_modifier: 1,
          current_hp: 15,
          max_hp: 15,
          armor_class: 13,
          conditions: [],
          is_player_controlled: false,
          is_incapacitated: false,
          has_taken_turn: false,
          monster_type: 'orc',
          challenge_rating: 0.5,
          size: 'Medium',
        },
      ]
    }

    if (
      preset.gameStateOverrides.addPartyMembers &&
      Object.keys(party.value).length === 0
    ) {
      // Add sample party member
      party.value = {
        char_sample: {
          version: 1,
          id: 'char_sample',
          name: 'Test Fighter',
          template_id: 'test_template',
          campaign_id: 'test_campaign',
          current_hp: 12,
          max_hp: 12,
          temp_hp: 0,
          experience_points: 0,
          level: 1,
          spell_slots_used: {},
          hit_dice_used: 0,
          death_saves: { successes: 0, failures: 0 },
          inventory: [
            { id: 'item_1', name: 'Longsword', description: '', quantity: 1 },
            { id: 'item_2', name: 'Chain Mail', description: '', quantity: 1 },
          ],
          gold: 10,
          conditions: [],
          exhaustion_level: 0,
          notes: '',
          achievements: [],
          relationships: {},
          last_played: new Date().toISOString(),
        },
      }
    }
  }
}

// Clear/Reset all configuration
const clearConfiguration = () => {
  // Clear query and results
  queryText.value = ''
  error.value = null
  results.value = null

  // Reset context override
  contextOverride.value = {
    in_combat: false,
    current_location: '',
  }

  // Reset active lore
  activeLoreId.value = null

  // Reset content packs to default (System only)
  activeContentPacks.value = ['System']

  // Reset advanced configuration
  party.value = {}
  combat.value = {
    is_active: false,
    combatants: [],
    current_turn_index: -1,
    round_number: 1,
    current_turn_instruction_given: false,
  }
  worldState.value = {
    campaign_goal: '',
    known_npcs: {},
    active_quests: {},
    world_lore: [],
    event_summary: [],
    session_count: 0,
    active_ruleset_id: undefined,
  }
}

const executeQuery = async () => {
  if (!queryText.value.trim()) return

  loading.value = true
  error.value = null
  results.value = null

  try {
    const response = await contentApi.queryRAG({
      query: queryText.value,
      campaign_id: currentCampaignId.value || undefined, // Convert null to undefined
      max_results: 10, // Default max results
      override_content_packs: activeContentPacks.value,
      override_game_state: {
        // Required fields for GameStateModel
        version: 1,
        party: party.value,
        current_location:
          contextOverride.value.current_location &&
          contextOverride.value.current_location.trim()
            ? {
                name: contextOverride.value.current_location.trim(),
                description: '',
              }
            : {
                name: 'Testing Environment',
                description: 'A neutral testing environment',
              },
        chat_history: [],
        pending_player_dice_requests: [],
        combat: combat.value,
        campaign_goal: worldState.value.campaign_goal || '',
        known_npcs: worldState.value.known_npcs,
        active_quests: worldState.value.active_quests,
        world_lore: worldState.value.world_lore,
        event_summary: worldState.value.event_summary,
        session_count: worldState.value.session_count,
        in_combat: contextOverride.value.in_combat || combat.value.is_active,
        narration_enabled: false,
        tts_voice: 'shimmer',
        content_pack_priority: activeContentPacks.value,
        // Add campaign_id so lore can be loaded properly
        campaign_id: currentCampaignId.value || 'test_campaign',
        // Optional fields
        active_lore_id: activeLoreId.value || undefined,
        active_ruleset_id: worldState.value.active_ruleset_id || undefined,
      },
    })

    results.value = response.data
  } catch (err) {
    console.error('RAG query error:', err)
    // Handle axios errors
    if (err && typeof err === 'object' && 'response' in err) {
      const axiosError = err as { response?: { data?: { detail?: string } } }
      error.value =
        axiosError.response?.data?.detail || 'Failed to execute RAG query'
    } else if (err instanceof Error) {
      error.value = 'Failed to execute RAG query: ' + err.message
    } else {
      error.value = 'Failed to execute RAG query'
    }
  } finally {
    loading.value = false
  }
}

// Load content packs on mount
onMounted(async () => {
  if (contentStore.contentPacks.length === 0) {
    await contentStore.loadContentPacks()
  }

  // Initialize with all active packs
  activeContentPacks.value = contentStore.activePacks.map(pack => pack.id)

  // Load available lores
  await loadAvailableLores()
})
</script>

<style scoped>
.rag-tester {
  max-width: 100%;
}

.rag-tester__content-packs,
.rag-tester__context {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.rag-tester__pack-item {
  display: flex;
  align-items: center;
}

.rag-tester__label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  user-select: none;
}

.rag-tester__checkbox {
  cursor: pointer;
}
</style>
