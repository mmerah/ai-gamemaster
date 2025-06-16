<template>
  <div class="min-h-screen bg-parchment p-4">
    <div class="max-w-7xl mx-auto">
      <!-- Header -->
      <div class="bg-parchment rounded-lg shadow-lg p-6 mb-6">
        <div class="flex items-center justify-between mb-4">
          <div>
            <h1 class="text-3xl font-cinzel font-bold text-text-primary mb-2">
              {{ pack?.name || 'Loading...' }}
            </h1>
            <p v-if="pack" class="text-text-secondary">
              {{ pack.description || 'No description available' }}
            </p>
          </div>
          <button
            @click="$router.push('/content')"
            class="fantasy-button-secondary"
          >
            <svg class="w-5 h-5 mr-2 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"></path>
            </svg>
            Back to Content Manager
          </button>
        </div>

        <!-- Pack Info -->
        <div v-if="pack" class="grid grid-cols-1 md:grid-cols-4 gap-4 text-sm">
          <div>
            <span class="font-semibold text-text-secondary">Version:</span>
            <span class="ml-2">{{ pack.version }}</span>
          </div>
          <div>
            <span class="font-semibold text-text-secondary">Author:</span>
            <span class="ml-2">{{ pack.author || 'Unknown' }}</span>
          </div>
          <div>
            <span class="font-semibold text-text-secondary">Status:</span>
            <span class="ml-2">
              <span :class="[
                'px-2 py-1 rounded-full text-xs font-medium',
                pack.is_active 
                  ? 'bg-green-100 text-green-800' 
                  : 'bg-gray-100 text-gray-800'
              ]">
                {{ pack.is_active ? 'Active' : 'Inactive' }}
              </span>
            </span>
          </div>
          <div>
            <span class="font-semibold text-text-secondary">Total Items:</span>
            <span class="ml-2">{{ totalItems }}</span>
          </div>
        </div>
      </div>

      <!-- Content Filters -->
      <div class="bg-parchment rounded-lg shadow-lg p-6 mb-6">
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <!-- Content Type Filter -->
          <div>
            <label for="content-type-filter" class="block text-sm font-medium text-text-primary mb-2">
              Content Type
            </label>
            <select
              id="content-type-filter"
              v-model="selectedType"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold"
            >
              <option value="">All Content Types</option>
              <option v-for="(count, type) in contentCounts" :key="type" :value="type">
                {{ formatContentType(type) }} ({{ count }})
              </option>
            </select>
          </div>

          <!-- Search Filter -->
          <div class="md:col-span-2">
            <label for="search-filter" class="block text-sm font-medium text-text-primary mb-2">
              Search
            </label>
            <input
              id="search-filter"
              v-model="searchQuery"
              type="text"
              placeholder="Search by name..."
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold"
            />
          </div>
        </div>
      </div>

      <!-- Content Display -->
      <div v-if="loading" class="bg-parchment rounded-lg shadow-lg p-6">
        <div class="flex justify-center items-center py-12">
          <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-gold"></div>
        </div>
      </div>

      <div v-else-if="error" class="bg-parchment rounded-lg shadow-lg p-6">
        <div class="text-center py-12">
          <p class="text-red-600 mb-4">{{ error }}</p>
          <button @click="loadPackDetails" class="fantasy-button">
            Try Again
          </button>
        </div>
      </div>

      <div v-else-if="!pack" class="bg-parchment rounded-lg shadow-lg p-6">
        <div class="text-center py-12">
          <p class="text-gray-600">Content pack not found</p>
        </div>
      </div>

      <div v-else class="bg-parchment rounded-lg shadow-lg p-6">
        <!-- No Content Message -->
        <div v-if="contentItems.length === 0" class="text-center py-12">
          <svg class="mx-auto h-12 w-12 text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
          </svg>
          <p class="text-gray-600 mb-4">This content pack is empty</p>
          <p class="text-sm text-gray-500">Upload content to get started</p>
        </div>

        <!-- Content Sections -->
        <div v-else class="space-y-6">
          <div v-for="(items, type) in groupedContent" :key="type" class="border-t pt-6 first:border-t-0 first:pt-0">
            <h3 class="text-xl font-cinzel font-semibold text-text-primary mb-4">
              {{ formatContentType(type) }}
              <span class="text-sm font-normal text-text-secondary ml-2">({{ items.length }})</span>
            </h3>

            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <div
                v-for="item in items"
                :key="item.index"
                @click="showItemDetails(item)"
                class="border border-gray-300 rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer hover:border-gold"
              >
                <h4 class="font-semibold text-text-primary mb-2">{{ item.name }}</h4>
                
                <!-- Type-specific info -->
                <div class="text-sm text-text-secondary space-y-1">
                  <!-- Spell-specific -->
                  <template v-if="type === 'spells' && item.level !== undefined">
                    <p>Level: {{ item.level === 0 ? 'Cantrip' : item.level }}</p>
                    <p v-if="item.school">School: {{ item.school.name || item.school }}</p>
                  </template>

                  <!-- Monster-specific -->
                  <template v-else-if="type === 'monsters'">
                    <p v-if="item.challenge_rating">CR: {{ item.challenge_rating }}</p>
                    <p v-if="item.type">Type: {{ item.type }}</p>
                  </template>

                  <!-- Equipment-specific -->
                  <template v-else-if="type === 'equipment'">
                    <p v-if="item.equipment_category">Category: {{ item.equipment_category.name || item.equipment_category }}</p>
                    <p v-if="item.cost">Cost: {{ item.cost.quantity }} {{ item.cost.unit }}</p>
                  </template>

                  <!-- Class-specific -->
                  <template v-else-if="type === 'classes'">
                    <p v-if="item.hit_die">Hit Die: d{{ item.hit_die }}</p>
                  </template>

                  <!-- Race-specific -->
                  <template v-else-if="type === 'races'">
                    <p v-if="item.size">Size: {{ item.size }}</p>
                    <p v-if="item.speed">Speed: {{ item.speed }} ft.</p>
                  </template>

                  <!-- Default info -->
                  <p v-if="item.desc" class="line-clamp-2 text-xs mt-2">
                    {{ Array.isArray(item.desc) ? item.desc[0] : item.desc }}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <!-- Item Detail Modal -->
    <div v-if="selectedItem" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" @click.self="selectedItem = null">
      <div class="bg-parchment rounded-lg shadow-xl max-w-4xl w-full mx-4 max-h-[90vh] overflow-hidden flex flex-col">
        <div class="p-6 border-b border-gray-300">
          <div class="flex items-center justify-between">
            <h2 class="text-2xl font-cinzel font-bold text-text-primary">
              {{ selectedItem.name }}
            </h2>
            <button
              @click="selectedItem = null"
              class="text-text-secondary hover:text-text-primary transition-colors"
            >
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
              </svg>
            </button>
          </div>
        </div>
        
        <div class="flex-1 overflow-y-auto p-6">
          <div class="space-y-4">
            <!-- Dynamic Field Display -->
            <div v-for="(value, key) in getItemDisplayFields(selectedItem)" :key="key" class="border-b pb-3 last:border-b-0">
              <h4 class="font-semibold text-text-primary capitalize mb-1">
                {{ formatFieldName(key) }}
              </h4>
              <div class="text-text-secondary">
                <!-- Handle different value types -->
                <template v-if="Array.isArray(value)">
                  <ul class="list-disc list-inside space-y-1">
                    <li v-for="(item, index) in value" :key="index">
                      <template v-if="typeof item === 'object'">
                        {{ JSON.stringify(item, null, 2) }}
                      </template>
                      <template v-else>
                        {{ item }}
                      </template>
                    </li>
                  </ul>
                </template>
                <template v-else-if="typeof value === 'object' && value !== null">
                  <pre class="bg-gray-100 p-2 rounded text-sm overflow-x-auto">{{ JSON.stringify(value, null, 2) }}</pre>
                </template>
                <template v-else-if="typeof value === 'boolean'">
                  {{ value ? 'Yes' : 'No' }}
                </template>
                <template v-else>
                  {{ value }}
                </template>
              </div>
            </div>
          </div>
        </div>
        
        <div class="p-6 border-t border-gray-300 bg-gray-50">
          <button
            @click="selectedItem = null"
            class="fantasy-button-secondary"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useContentStore } from '../stores/contentStore'
import { contentApi } from '../services/contentApi'
import type { ContentPackWithStats } from '../types/content'

// Router
const route = useRoute()

// Store
const contentStore = useContentStore()

// State
const pack = ref<ContentPackWithStats | null>(null)
const loading = ref(true)
const error = ref<string | null>(null)
const selectedType = ref('') // Will be set to show all content after loading
const searchQuery = ref('')
const contentItems = ref<any[]>([])
const selectedItem = ref<any>(null)

// Computed
const packId = computed(() => route.params.packId as string)

const contentCounts = computed(() => {
  if (!pack.value) return {}
  const stats = pack.value.statistics || {}
  // Filter out 'total' as it's not a content type
  const { total, ...contentTypes } = stats
  return contentTypes
})

const totalItems = computed(() => {
  if (!pack.value) return 0
  // Use the total from statistics if available, otherwise count loaded items
  return pack.value.statistics?.total || contentItems.value.length
})

const groupedContent = computed(() => {
  const groups: Record<string, any[]> = {}
  
  let items = contentItems.value

  // Filter by type if selected
  if (selectedType.value) {
    items = items.filter(item => item._content_type === selectedType.value)
  }

  // Filter by search query
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    items = items.filter(item => 
      item.name?.toLowerCase().includes(query) ||
      item.index?.toLowerCase().includes(query)
    )
  }

  // Group by type
  items.forEach(item => {
    const type = item._content_type
    if (!groups[type]) {
      groups[type] = []
    }
    groups[type].push(item)
  })

  // Sort each group by name
  Object.keys(groups).forEach(type => {
    groups[type].sort((a, b) => (a.name || '').localeCompare(b.name || ''))
  })

  return groups
})

// Methods
function formatContentType(type: string): string {
  return type
    .split(/[-_]/)
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

function formatFieldName(fieldName: string): string {
  // Convert snake_case or camelCase to Title Case
  return fieldName
    .replace(/_/g, ' ')
    .replace(/([A-Z])/g, ' $1')
    .trim()
    .split(' ')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join(' ')
}

function showItemDetails(item: any) {
  selectedItem.value = item
}

function getItemDisplayFields(item: any): Record<string, any> {
  // Filter out internal fields and empty values
  const excludeFields = ['_content_type', 'index', 'url']
  const fields: Record<string, any> = {}
  
  for (const [key, value] of Object.entries(item)) {
    if (!excludeFields.includes(key) && value !== null && value !== undefined && value !== '') {
      // Skip empty arrays and objects
      if (Array.isArray(value) && value.length === 0) continue
      if (typeof value === 'object' && !Array.isArray(value) && Object.keys(value).length === 0) continue
      
      fields[key] = value
    }
  }
  
  return fields
}

async function loadPackDetails() {
  loading.value = true
  error.value = null

  try {
    // Load pack statistics
    pack.value = await contentStore.getPackStatistics(packId.value)
    
    if (!pack.value) {
      error.value = 'Failed to load content pack details'
      return
    }

    // Load actual content items
    const contentResult = await contentApi.getPackContent(packId.value, undefined, 0, 1000)
    
    if (contentResult.content_type === 'all' && typeof contentResult.items === 'object' && !Array.isArray(contentResult.items)) {
      // We got all content types - flatten them into a single array
      contentItems.value = []
      
      for (const [contentType, items] of Object.entries(contentResult.items)) {
        // Convert backend format (hyphens) to frontend format (underscores)
        const frontendType = contentType.replace(/-/g, '_')
        
        // Add content type metadata to each item
        const typedItems = items.map(item => ({
          ...item,
          _content_type: frontendType
        }))
        
        contentItems.value.push(...typedItems)
      }
    } else if (Array.isArray(contentResult.items)) {
      // Single content type result
      contentItems.value = contentResult.items.map(item => ({
        ...item,
        _content_type: contentResult.content_type.replace(/-/g, '_')
      }))
    }
    
  } catch (err: any) {
    error.value = err.message || 'Failed to load content pack'
    console.error('Error loading pack details:', err)
  } finally {
    loading.value = false
  }
}

// Watch for pack ID changes
watch(() => packId.value, () => {
  if (packId.value) {
    loadPackDetails()
  }
})

// Load on mount
onMounted(() => {
  if (packId.value) {
    loadPackDetails()
  }
})
</script>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>