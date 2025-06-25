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
            class="fantasy-button-secondary px-4 py-2"
            @click="$router.push('/')"
          >
            <svg
              class="w-5 h-5 inline mr-2"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M10 19l-7-7m0 0l7-7m-7 7h18"
              />
            </svg>
            Back to Launch
          </button>
        </div>
      </div>
    </div>

    <!-- Main Content -->
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <!-- Tab Navigation -->
      <div v-if="!loading && !error" class="border-b border-gold/20 mb-8">
        <nav class="-mb-px flex space-x-8">
          <button
            v-for="tab in tabs"
            :key="tab.id"
            :class="[
              'py-2 px-1 border-b-2 font-medium text-sm transition-colors',
              activeTab === tab.id
                ? 'border-gold text-gold'
                : 'border-transparent text-text-secondary hover:text-text-primary hover:border-gray-300'
            ]"
            @click="activeTab = tab.id"
          >
            {{ tab.label }}
          </button>
        </nav>
      </div>
      <!-- Loading State -->
      <div v-if="loading" class="text-center py-12">
        <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-gold mb-4" />
        <p class="text-text-secondary font-crimson">
          Loading configuration...
        </p>
      </div>

      <!-- Error State -->
      <div v-else-if="error" class="fantasy-panel p-6 text-center">
        <p class="text-red-600 font-crimson">
          {{ error }}
        </p>
        <button class="fantasy-button mt-4" @click="loadConfiguration">
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
              <ConfigItem label="AI Provider" :value="config.ai?.provider || 'Not configured'" />
              <ConfigItem label="Response Parsing Mode" :value="config.ai?.response_parsing_mode || 'Not configured'" />
              <ConfigItem label="Temperature" :value="config.ai?.temperature?.toString() || 'Not configured'" />
              <ConfigItem label="Max Tokens" :value="config.ai?.max_tokens?.toString() || 'Not configured'" />
              <ConfigItem label="Request Timeout" :value="config.ai?.request_timeout ? `${config.ai.request_timeout}s` : 'Not configured'" />
              <ConfigItem label="Max Retries" :value="config.ai?.max_retries?.toString() || 'Not configured'" />
              <ConfigItem label="Retry Delay" :value="config.ai?.retry_delay ? `${config.ai.retry_delay}s` : 'Not configured'" />
              <ConfigItem label="Retry Context Timeout" :value="config.ai?.retry_context_timeout ? `${config.ai.retry_context_timeout}s` : 'Not configured'" />
              <ConfigItem v-if="config.ai?.provider === 'llamacpp_http'" label="Llama Server URL" :value="config.ai?.llama_server_url || 'Not configured'" />
              <ConfigItem v-if="config.ai?.provider === 'openrouter'" label="OpenRouter Model" :value="config.ai?.openrouter_model_name || 'Not configured'" />
              <ConfigItem v-if="config.ai?.provider === 'openrouter'" label="OpenRouter Base URL" :value="config.ai?.openrouter_base_url || 'Not configured'" />
            </ConfigSection>
          </div>

          <!-- Storage Settings Tab -->
          <div v-if="activeTab === 'storage'" class="space-y-4">
            <ConfigSection title="Storage Configuration">
              <ConfigItem label="Game State Repository" :value="config.storage?.game_state_repo_type || 'Not configured'" />
              <ConfigItem label="Character Templates Directory" :value="config.storage?.character_templates_dir || 'Not configured'" />
              <ConfigItem label="Campaign Templates Directory" :value="config.storage?.campaign_templates_dir || 'Not configured'" />
              <ConfigItem label="Campaigns Directory" :value="config.storage?.campaigns_dir || 'Not configured'" />
            </ConfigSection>
          </div>

          <!-- RAG Settings Tab -->
          <div v-if="activeTab === 'rag'" class="space-y-4">
            <ConfigSection title="RAG (Retrieval-Augmented Generation) Configuration">
              <ConfigItem label="RAG Enabled" :value="config.rag?.enabled !== undefined ? (config.rag.enabled ? 'Yes' : 'No') : 'Not configured'" :highlight="config.rag?.enabled" />
              <ConfigItem label="Max Results Per Query" :value="config.rag?.max_results_per_query?.toString() || 'Not configured'" />
              <ConfigItem label="Max Total Results" :value="config.rag?.max_total_results?.toString() || 'Not configured'" />
              <ConfigItem label="Embeddings Model" :value="config.rag?.embeddings_model || 'Not configured'" />
              <ConfigItem label="Similarity Score Threshold" :value="config.rag?.score_threshold?.toString() || 'Not configured'" />
              <ConfigItem label="Chunk Size" :value="config.rag?.chunk_size?.toString() || 'Not configured'" />
              <ConfigItem label="Chunk Overlap" :value="config.rag?.chunk_overlap?.toString() || 'Not configured'" />
              <ConfigItem label="Collection Name Prefix" :value="config.rag?.collection_name_prefix || 'Not configured'" />
              <ConfigItem label="Metadata Filtering" :value="config.rag?.metadata_filtering_enabled !== undefined ? (config.rag.metadata_filtering_enabled ? 'Enabled' : 'Disabled') : 'Not configured'" />
              <ConfigItem label="Relevance Feedback" :value="config.rag?.relevance_feedback_enabled !== undefined ? (config.rag.relevance_feedback_enabled ? 'Enabled' : 'Disabled') : 'Not configured'" />
              <ConfigItem label="Cache TTL" :value="config.rag?.cache_ttl ? `${config.rag.cache_ttl}s` : 'Not configured'" />
            </ConfigSection>
          </div>

          <!-- Game Settings Tab -->
          <div v-if="activeTab === 'game'" class="space-y-4">
            <ConfigSection title="Game Configuration">
              <ConfigItem label="Token Budget" :value="config.prompt?.max_tokens_budget?.toString() || 'Not configured'" />
              <ConfigItem label="Last History Messages" :value="config.prompt?.last_x_history_messages?.toString() || 'Not configured'" />
              <ConfigItem label="Continuation Depth" :value="config.ai?.max_continuation_depth?.toString() || 'Not configured'" />
              <ConfigItem label="Tokens Per Message Overhead" :value="config.prompt?.tokens_per_message_overhead?.toString() || 'Not configured'" />
              <ConfigItem label="Event Queue Size" :value="config.system?.event_queue_max_size === 0 ? '0 (unlimited)' : config.system?.event_queue_max_size?.toString() || 'Not configured'" />
              <ConfigItem label="SSE Heartbeat Interval" :value="config.sse?.heartbeat_interval ? `${config.sse.heartbeat_interval}s` : 'Not configured'" />
              <ConfigItem label="SSE Event Timeout" :value="config.sse?.event_timeout ? `${config.sse.event_timeout}s` : 'Not configured'" />
            </ConfigSection>
          </div>

          <!-- System Settings Tab -->
          <div v-if="activeTab === 'system'" class="space-y-4">
            <ConfigSection title="System Configuration">
              <ConfigItem label="TTS Provider" :value="config.tts?.provider || 'Not configured'" />
              <ConfigItem label="TTS Cache Directory" :value="config.tts?.cache_dir_name || 'Not configured'" />
              <ConfigItem label="Kokoro Language Code" :value="config.tts?.kokoro_lang_code || 'Not configured'" />
              <ConfigItem label="Debug Mode" :value="config.system?.debug ? 'Enabled' : 'Disabled'" :highlight="config.system?.debug" />
              <ConfigItem label="Log Level" :value="config.system?.log_level || 'Not configured'" />
              <ConfigItem label="Log File" :value="config.system?.log_file || 'Not configured'" />
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
