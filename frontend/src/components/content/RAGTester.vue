<template>
  <div class="rag-tester">
    <h3 class="rag-tester__title">
      RAG System Tester
    </h3>
    
    <!-- Content Pack Selection -->
    <div class="rag-tester__section">
      <h4 class="rag-tester__section-title">
        Content Packs
      </h4>
      <div class="rag-tester__content-packs">
        <div v-for="pack in availableContentPacks" :key="pack.id" class="rag-tester__pack-item">
          <label class="rag-tester__label">
            <input 
              type="checkbox"
              class="rag-tester__checkbox"
              :checked="isPackActive(pack.id)"
              :disabled="pack.id === 'System'"
              @change="toggleContentPack(pack.id)"
            >
            <span>{{ pack.name }} ({{ pack.id }})</span>
          </label>
        </div>
      </div>
    </div>
    
    <!-- Game Context Override -->
    <div class="rag-tester__section">
      <h4 class="rag-tester__section-title">
        Game Context
      </h4>
      <div class="rag-tester__context">
        <label class="rag-tester__label">
          <input 
            v-model="contextOverride.in_combat"
            type="checkbox"
            class="rag-tester__checkbox"
          >
          <span>In Combat</span>
        </label>
        <div class="rag-tester__field">
          <label class="rag-tester__field-label">Current Location:</label>
          <input 
            v-model="contextOverride.current_location"
            type="text"
            placeholder="e.g., Tavern, Dungeon..."
            class="rag-tester__input"
          >
        </div>
      </div>
    </div>
    
    <!-- Lore Selection -->
    <div v-if="availableLores.length > 0" class="rag-tester__section">
      <h4 class="rag-tester__section-title">
        Active Lore
      </h4>
      <div class="rag-tester__lores">
        <select v-model="activeLoreId" class="rag-tester__select">
          <option :value="null">
            No active lore
          </option>
          <option v-for="lore in availableLores" :key="lore.id" :value="lore.id">
            {{ lore.name || lore.id }}
          </option>
        </select>
      </div>
    </div>
    
    <!-- Query Input -->
    <div class="rag-tester__section">
      <h4 class="rag-tester__section-title">
        Test Query
      </h4>
      <div class="rag-tester__query">
        <textarea 
          v-model="queryText" 
          placeholder="Enter a player action (e.g., 'I cast fireball at the goblin')"
          rows="3"
          class="rag-tester__textarea"
        />
        <button 
          @click="executeQuery" 
          :disabled="loading || !queryText.trim()"
          class="rag-tester__button"
        >
          {{ loading ? 'Testing...' : 'Test RAG Query' }}
        </button>
      </div>
    </div>
    
    <!-- Error Display -->
    <div v-if="error" class="rag-tester__error">
      <p>{{ error }}</p>
    </div>
    
    <!-- Results Display -->
    <div v-if="results" class="rag-tester__section">
      <h4 class="rag-tester__section-title">
        RAG Results
      </h4>
      <div class="rag-tester__results">
        <div class="rag-tester__results-info">
          <h5>Query Info:</h5>
          <pre>{{ JSON.stringify(results.query_info, null, 2) }}</pre>
        </div>
        <div class="rag-tester__results-packs">
          <h5>Used Content Packs:</h5>
          <ul>
            <li v-for="pack in results.used_content_packs" :key="pack">{{ pack }}</li>
          </ul>
        </div>
        <div class="rag-tester__results-knowledge">
          <h5>Retrieved Knowledge ({{ results.results.results.length }} items):</h5>
          <div v-for="(item, index) in results.results.results" :key="index" class="rag-tester__knowledge-item">
            <div class="rag-tester__knowledge-header">
              <strong>{{ item.source }}</strong>
              <span class="rag-tester__score">Score: {{ item.relevance_score.toFixed(3) }}</span>
            </div>
            <div class="rag-tester__knowledge-content">{{ item.content }}</div>
            <details v-if="Object.keys(item.metadata).length > 0" class="rag-tester__metadata">
              <summary>Metadata</summary>
              <pre>{{ JSON.stringify(item.metadata, null, 2) }}</pre>
            </details>
          </div>
        </div>
        <div class="rag-tester__results-raw">
          <details>
            <summary>Raw Response</summary>
            <pre>{{ JSON.stringify(results, null, 2) }}</pre>
          </details>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useContentStore } from '@/stores/contentStore'
import { useCampaignStore } from '@/stores/campaignStore'
import { contentApi } from '@/services/contentApi'
import type { RAGQueryResponse } from '@/types/unified'

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
  current_location: ''
})
const activeLoreId = ref<string | null>(null)

// Computed
const availableContentPacks = computed(() => contentStore.contentPacks)
// State for lores
const availableLores = ref<Array<{ id: string; name: string; file_path: string }>>([])

// Load available lores
const loadAvailableLores = async () => {
  try {
    // Load lores from the lores.json file
    const response = await fetch('/src/assets/data/knowledge/lores.json')
    if (!response.ok) {
      // Try alternative path
      const altResponse = await fetch('/app/content/data/knowledge/lores.json')
      if (altResponse.ok) {
        availableLores.value = await altResponse.json()
      }
    } else {
      availableLores.value = await response.json()
    }
  } catch (error) {
    console.warn('Could not load lores.json, using hardcoded values')
    // Fallback to hardcoded lores if file not found
    availableLores.value = [
      {
        id: "generic_fantasy",
        name: "Generic Fantasy Lore",
        file_path: "knowledge/lore/generic_fantasy_lore.json"
      },
      {
        id: "world_of_eldoria", 
        name: "World of Eldoria",
        file_path: "knowledge/lore/world_of_eldoria_lore.json"
      }
    ]
  }
}

const currentCampaignId = computed(() => {
  // Try to get current campaign ID from the store
  // If not available, return null (API will use defaults)
  return campaignStore.activeCampaign?.id || campaignStore.campaigns[0]?.id || null
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


const executeQuery = async () => {
  if (!queryText.value.trim()) return
  
  loading.value = true
  error.value = null
  results.value = null
  
  try {
    const response = await contentApi.queryRAG({
      query: queryText.value,
      campaign_id: currentCampaignId.value || undefined,  // Convert null to undefined
      max_results: 10,  // Default max results
      override_content_packs: activeContentPacks.value,
      override_game_state: {
        // Required fields for GameStateModel
        version: 1,
        party: {},
        current_location: contextOverride.value.current_location ? {
          name: contextOverride.value.current_location,
          description: ''
        } : {
          name: 'Testing Environment',
          description: 'A neutral testing environment'
        },
        chat_history: [],
        pending_player_dice_requests: [],
        combat: {
          is_active: false,
          combatants: [],
          current_turn_index: 0,
          round_number: 1,
          current_turn_instruction_given: false
        },
        campaign_goal: '',
        known_npcs: {},
        active_quests: {},
        world_lore: [],
        event_summary: [],
        session_count: 0,
        in_combat: contextOverride.value.in_combat,
        narration_enabled: false,
        tts_voice: 'shimmer',
        content_pack_priority: activeContentPacks.value,
        // Add campaign_id so lore can be loaded properly
        campaign_id: currentCampaignId.value || 'test_campaign',
        // Optional fields
        active_lore_id: activeLoreId.value || undefined
      }
    })
    
    results.value = response.data
  } catch (err) {
    console.error('RAG query error:', err)
    // Handle axios errors
    if (err && typeof err === 'object' && 'response' in err) {
      const axiosError = err as { response?: { data?: { detail?: string } } }
      error.value = axiosError.response?.data?.detail || 'Failed to execute RAG query'
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
  padding: 1.5rem;
  background: #f8f9fa;
  border-radius: 8px;
  max-width: 100%;
  margin: 0 auto;
}

.rag-tester__title {
  font-size: 1.5rem;
  font-weight: 600;
  margin-bottom: 1.5rem;
  color: #333;
}

.rag-tester__section {
  margin-bottom: 2rem;
  background: white;
  padding: 1.25rem;
  border-radius: 6px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.rag-tester__section-title {
  font-size: 1.1rem;
  font-weight: 600;
  margin-bottom: 1rem;
  color: #555;
}

.rag-tester__content-packs,
.rag-tester__lores {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.rag-tester__pack-item,
.rag-tester__lore-item {
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

.rag-tester__context {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.rag-tester__field {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.rag-tester__field-label {
  font-weight: 500;
  color: #666;
}

.rag-tester__input,
.rag-tester__select {
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 0.95rem;
}

.rag-tester__query {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.rag-tester__textarea {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 0.95rem;
  resize: vertical;
  min-height: 80px;
}

.rag-tester__button {
  padding: 0.75rem 1.5rem;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s;
  align-self: flex-start;
}

.rag-tester__button:hover:not(:disabled) {
  background: #0056b3;
}

.rag-tester__button:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.rag-tester__error {
  background: #f8d7da;
  color: #721c24;
  padding: 1rem;
  border-radius: 4px;
  margin-bottom: 1rem;
}

.rag-tester__results {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.rag-tester__results-info,
.rag-tester__results-packs,
.rag-tester__results-knowledge,
.rag-tester__results-raw {
  background: #f8f9fa;
  padding: 1rem;
  border-radius: 4px;
}

.rag-tester__results h5 {
  margin-top: 0;
  margin-bottom: 0.75rem;
  color: #555;
}

.rag-tester__results pre {
  background: #e9ecef;
  padding: 0.75rem;
  border-radius: 4px;
  overflow-x: auto;
  font-size: 0.85rem;
  margin: 0;
}

.rag-tester__knowledge-item {
  background: white;
  padding: 1rem;
  border-radius: 4px;
  margin-bottom: 0.75rem;
  border: 1px solid #e0e0e0;
}

.rag-tester__knowledge-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.rag-tester__score {
  font-size: 0.85rem;
  color: #666;
}

.rag-tester__knowledge-content {
  font-size: 0.95rem;
  line-height: 1.5;
  color: #333;
}

.rag-tester__metadata {
  margin-top: 0.75rem;
  font-size: 0.85rem;
}

.rag-tester__metadata summary {
  cursor: pointer;
  user-select: none;
  color: #666;
}

.rag-tester__metadata pre {
  margin-top: 0.5rem;
  background: #f5f5f5;
  font-size: 0.8rem;
}

details {
  margin-top: 0.5rem;
}

details summary {
  cursor: pointer;
  user-select: none;
  font-weight: 500;
  color: #666;
}
</style>