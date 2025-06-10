<template>
  <div class="configuration-screen min-h-screen bg-parchment">
    <!-- Header -->
    <div class="bg-primary-dark shadow-xl">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div class="flex items-center justify-between">
          <h1 class="text-3xl font-cinzel font-bold text-gold">
            Configuration
          </h1>
          <button
            @click="$router.push('/')"
            class="fantasy-button-secondary px-4 py-2"
          >
            <svg class="w-5 h-5 inline mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"></path>
            </svg>
            Back to Launch
          </button>
        </div>
      </div>
    </div>

    <!-- Main Content -->
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <!-- Tab Navigation -->
      <div class="border-b border-gold/20 mb-8" v-if="!loading && !error">
        <nav class="-mb-px flex space-x-8">
          <button
            v-for="tab in tabs"
            :key="tab.id"
            @click="activeTab = tab.id"
            :class="[
              'py-2 px-1 border-b-2 font-medium text-sm transition-colors',
              activeTab === tab.id
                ? 'border-gold text-gold'
                : 'border-transparent text-text-secondary hover:text-text-primary hover:border-gray-300'
            ]"
          >
            {{ tab.label }}
          </button>
        </nav>
      </div>
      <!-- Loading State -->
      <div v-if="loading" class="text-center py-12">
        <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-gold mb-4"></div>
        <p class="text-text-secondary font-crimson">Loading configuration...</p>
      </div>

      <!-- Error State -->
      <div v-else-if="error" class="fantasy-panel p-6 text-center">
        <p class="text-red-600 font-crimson">{{ error }}</p>
        <button @click="loadConfiguration" class="fantasy-button mt-4">
          Retry
        </button>
      </div>

      <!-- Configuration Sections -->
      <div v-else>
        <!-- Tab Content -->
        <div class="fantasy-panel">
          <!-- AI Settings Tab -->
          <div v-if="activeTab === 'ai'" class="space-y-4">
            <ConfigSection title="AI Configuration">
              <ConfigItem label="AI Provider" :value="config.AI_PROVIDER || 'Not configured'" />
              <ConfigItem label="Response Parsing Mode" :value="config.AI_RESPONSE_PARSING_MODE || 'Not configured'" />
              <ConfigItem label="Temperature" :value="config.AI_TEMPERATURE?.toString() || '0.7'" />
              <ConfigItem label="Max Tokens" :value="config.AI_MAX_TOKENS?.toString() || '4096'" />
              <ConfigItem label="Request Timeout" :value="config.AI_REQUEST_TIMEOUT ? `${config.AI_REQUEST_TIMEOUT}s` : '60s'" />
              <ConfigItem label="Max Retries" :value="config.AI_MAX_RETRIES?.toString() || '3'" />
              <ConfigItem label="Retry Delay" :value="config.AI_RETRY_DELAY ? `${config.AI_RETRY_DELAY}s` : '5s'" />
              <ConfigItem label="Retry Context Timeout" :value="config.AI_RETRY_CONTEXT_TIMEOUT ? `${config.AI_RETRY_CONTEXT_TIMEOUT}s` : '300s'" />
              <ConfigItem v-if="config.AI_PROVIDER === 'llamacpp_http'" label="Llama Server URL" :value="config.LLAMA_SERVER_URL || 'http://127.0.0.1:8080'" />
              <ConfigItem v-if="config.AI_PROVIDER === 'openrouter'" label="OpenRouter Model" :value="config.OPENROUTER_MODEL_NAME || 'Not configured'" />
              <ConfigItem v-if="config.AI_PROVIDER === 'openrouter'" label="OpenRouter Base URL" :value="config.OPENROUTER_BASE_URL || 'https://openrouter.ai/api/v1'" />
            </ConfigSection>
          </div>

          <!-- Storage Settings Tab -->
          <div v-if="activeTab === 'storage'" class="space-y-4">
            <ConfigSection title="Storage Configuration">
              <ConfigItem label="Game State Repository" :value="config.GAME_STATE_REPO_TYPE || 'memory'" />
              <ConfigItem label="Character Templates Directory" :value="config.CHARACTER_TEMPLATES_DIR || 'saves/character_templates'" />
              <ConfigItem label="Campaign Templates Directory" :value="config.CAMPAIGN_TEMPLATES_DIR || 'saves/campaign_templates'" />
              <ConfigItem label="Campaigns Directory" :value="config.CAMPAIGNS_DIR || 'saves/campaigns'" />
            </ConfigSection>
          </div>

          <!-- RAG Settings Tab -->
          <div v-if="activeTab === 'rag'" class="space-y-4">
            <ConfigSection title="RAG (Retrieval-Augmented Generation) Configuration">
              <ConfigItem label="RAG Enabled" :value="config.RAG_ENABLED ? 'Yes' : 'No'" :highlight="config.RAG_ENABLED" />
              <ConfigItem label="Max Results Per Query" :value="config.RAG_MAX_RESULTS_PER_QUERY?.toString() || '3'" />
              <ConfigItem label="Max Total Results" :value="config.RAG_MAX_TOTAL_RESULTS?.toString() || '8'" />
              <ConfigItem label="Embeddings Model" :value="config.RAG_EMBEDDINGS_MODEL || 'all-MiniLM-L6-v2'" />
              <ConfigItem label="Similarity Score Threshold" :value="config.RAG_SCORE_THRESHOLD?.toString() || '0.2'" />
              <ConfigItem label="Chunk Size" :value="config.RAG_CHUNK_SIZE?.toString() || '500'" />
              <ConfigItem label="Chunk Overlap" :value="config.RAG_CHUNK_OVERLAP?.toString() || '50'" />
              <ConfigItem label="Collection Name Prefix" :value="config.RAG_COLLECTION_NAME_PREFIX || 'ai_gamemaster'" />
              <ConfigItem label="Metadata Filtering" :value="config.RAG_METADATA_FILTERING_ENABLED ? 'Enabled' : 'Disabled'" />
              <ConfigItem label="Relevance Feedback" :value="config.RAG_RELEVANCE_FEEDBACK_ENABLED ? 'Enabled' : 'Disabled'" />
              <ConfigItem label="Cache TTL" :value="config.RAG_CACHE_TTL ? `${config.RAG_CACHE_TTL}s` : '3600s'" />
            </ConfigSection>
          </div>

          <!-- Game Settings Tab -->
          <div v-if="activeTab === 'game'" class="space-y-4">
            <ConfigSection title="Game Configuration">
              <ConfigItem label="Token Budget" :value="config.MAX_PROMPT_TOKENS_BUDGET?.toString() || '128000'" />
              <ConfigItem label="History Messages Limit" :value="config.LAST_X_HISTORY_MESSAGES?.toString() || '4'" />
              <ConfigItem label="Continuation Depth" :value="config.MAX_AI_CONTINUATION_DEPTH?.toString() || '20'" />
              <ConfigItem label="Tokens Per Message Overhead" :value="config.TOKENS_PER_MESSAGE_OVERHEAD?.toString() || '4'" />
              <ConfigItem label="Event Queue Size" :value="config.EVENT_QUEUE_MAX_SIZE === 0 ? '0 (unlimited)' : config.EVENT_QUEUE_MAX_SIZE?.toString() || '0 (unlimited)'" />
              <ConfigItem label="SSE Heartbeat Interval" :value="config.SSE_HEARTBEAT_INTERVAL ? `${config.SSE_HEARTBEAT_INTERVAL}s` : '30s'" />
              <ConfigItem label="SSE Event Timeout" :value="config.SSE_EVENT_TIMEOUT ? `${config.SSE_EVENT_TIMEOUT}s` : '1s'" />
            </ConfigSection>
          </div>

          <!-- System Settings Tab -->
          <div v-if="activeTab === 'system'" class="space-y-4">
            <ConfigSection title="System Configuration">
              <ConfigItem label="TTS Provider" :value="config.TTS_PROVIDER || 'disabled'" />
              <ConfigItem label="TTS Cache Directory" :value="config.TTS_CACHE_DIR_NAME || 'tts_cache'" />
              <ConfigItem label="Kokoro Language Code" :value="config.KOKORO_LANG_CODE || 'a'" />
              <ConfigItem label="Debug Mode" :value="config.FLASK_DEBUG ? 'Enabled' : 'Disabled'" :highlight="config.FLASK_DEBUG" />
              <ConfigItem label="Log Level" :value="config.LOG_LEVEL || 'INFO'" />
              <ConfigItem label="Log File" :value="config.LOG_FILE || 'dnd_ai_poc.log'" />
            </ConfigSection>
          </div>
        </div>
      </div>

      <!-- Note -->
      <div class="mt-8 fantasy-panel p-4 bg-amber-50/20">
        <p class="text-sm text-text-secondary font-crimson">
          <strong>Note:</strong> Configuration values are currently read-only. To modify settings, update your <code class="bg-primary-dark/10 px-1 rounded">.env</code> file and restart the server.
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, h } from 'vue'
import { useConfigStore } from '../stores/configStore'

// Define ConfigSection component
const ConfigSection = {
  props: ['title'],
  setup(props, { slots }) {
    return () => h('div', [
      h('h2', {
        class: 'text-xl font-cinzel font-semibold text-text-primary mb-6 pb-3 border-b border-gold/30'
      }, props.title),
      h('div', { class: 'space-y-4' }, slots.default?.())
    ])
  }
}

// Define ConfigItem component
const ConfigItem = {
  props: {
    label: String,
    value: String,
    highlight: Boolean
  },
  setup(props) {
    return () => h('div', {
      class: 'flex justify-between items-center py-2 border-b border-gold/10 last:border-0'
    }, [
      h('span', { class: 'text-text-secondary font-crimson' }, `${props.label}:`),
      h('span', {
        class: [
          'text-text-primary font-semibold',
          props.highlight === true ? 'text-green-600' : '',
          props.highlight === false ? 'text-amber-600' : ''
        ].filter(Boolean).join(' ')
      }, props.value)
    ])
  }
}

// Store
const configStore = useConfigStore()

// State
const loading = ref(true)
const error = ref(null)
const activeTab = ref('ai')

// Tab definitions
const tabs = [
  { id: 'ai', label: 'AI Settings' },
  { id: 'storage', label: 'Storage' },
  { id: 'rag', label: 'RAG Settings' },
  { id: 'game', label: 'Game Settings' },
  { id: 'system', label: 'System' }
]

// Use computed to reactively access the store's configuration
const config = computed(() => configStore.configuration)

// Load configuration on mount
onMounted(() => {
  loadConfiguration()
})

async function loadConfiguration() {
  loading.value = true
  error.value = null

  try {
    await configStore.loadConfiguration()
    console.log('Configuration loaded:', configStore.configuration)
  } catch (err) {
    error.value = 'Failed to load configuration. Please try again.'
    console.error('Configuration load error:', err)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.configuration-screen {
  min-height: 100vh;
}

code {
  font-family: 'Courier New', monospace;
}
</style>
