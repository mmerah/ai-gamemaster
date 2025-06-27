<template>
  <div class="min-h-screen bg-background p-4">
    <div class="max-w-7xl mx-auto">
      <!-- Header -->
      <AppCard class="mb-6">
        <div class="flex items-center justify-between mb-4">
          <div>
            <h1 class="text-3xl font-cinzel font-bold text-foreground mb-2">
              {{ pack?.name || 'Loading...' }}
            </h1>
            <p v-if="pack" class="text-foreground/60">
              {{ pack.description || 'No description available' }}
            </p>
          </div>
          <AppButton variant="secondary" @click="$router.push('/content')">
            <svg
              class="w-5 h-5 mr-2 inline"
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
            Back to Content Manager
          </AppButton>
        </div>

        <!-- Pack Info -->
        <div v-if="pack" class="grid grid-cols-1 md:grid-cols-4 gap-4 text-sm">
          <div>
            <span class="font-semibold text-foreground/60">Version:</span>
            <span class="ml-2">{{ pack.version }}</span>
          </div>
          <div>
            <span class="font-semibold text-foreground/60">Author:</span>
            <span class="ml-2">{{ pack.author || 'Unknown' }}</span>
          </div>
          <div>
            <span class="font-semibold text-foreground/60">Status:</span>
            <span class="ml-2">
              <BaseBadge :variant="pack.is_active ? 'success' : 'secondary'">
                {{ pack.is_active ? 'Available' : 'Hidden' }}
              </BaseBadge>
            </span>
          </div>
          <div>
            <span class="font-semibold text-foreground/60">Total Items:</span>
            <span class="ml-2">{{ totalItems }}</span>
          </div>
        </div>
      </AppCard>

      <!-- Content Filters -->
      <AppCard class="mb-6">
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <!-- Content Type Filter -->
          <div>
            <label
              for="content-type-filter"
              class="block text-sm font-medium text-foreground mb-2"
            >
              Content Type
            </label>
            <AppSelect id="content-type-filter" v-model="selectedType">
              <option value="">All Content Types</option>
              <option
                v-for="(count, type) in contentCounts"
                :key="type"
                :value="type"
              >
                {{ formatContentType(type) }} ({{ count }})
              </option>
            </AppSelect>
          </div>

          <!-- Search Filter -->
          <div class="md:col-span-2">
            <label
              for="search-filter"
              class="block text-sm font-medium text-foreground mb-2"
            >
              Search
            </label>
            <AppInput
              id="search-filter"
              v-model="searchQuery"
              type="text"
              placeholder="Search by name..."
            />
          </div>
        </div>
      </AppCard>

      <!-- Content Display -->
      <AppCard v-if="loading" class="p-6">
        <div class="flex justify-center items-center py-12">
          <BaseLoader size="lg" />
        </div>
      </AppCard>

      <AppCard v-else-if="error" class="p-6">
        <div class="text-center py-12">
          <p class="text-red-600 mb-4">
            {{ error }}
          </p>
          <AppButton variant="primary" @click="loadPackDetails">
            Try Again
          </AppButton>
        </div>
      </AppCard>

      <AppCard v-else-if="!pack" class="p-6">
        <div class="text-center py-12">
          <p class="text-foreground/60">Content pack not found</p>
        </div>
      </AppCard>

      <AppCard v-else class="p-6">
        <!-- No Content Message -->
        <div v-if="contentItems.length === 0" class="text-center py-12">
          <svg
            class="mx-auto h-12 w-12 text-foreground/40 mb-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
          <p class="text-foreground/60 mb-4">This content pack is empty</p>
          <p class="text-sm text-foreground/40">
            Upload content to get started
          </p>
        </div>

        <!-- Content Sections -->
        <div v-else class="space-y-6">
          <div
            v-for="(items, type) in groupedContent"
            :key="type"
            class="border-t pt-6 first:border-t-0 first:pt-0"
          >
            <h3 class="text-xl font-cinzel font-semibold text-foreground mb-4">
              {{ formatContentType(type) }}
              <span class="text-sm font-normal text-foreground/60 ml-2"
                >({{ items.length }})</span
              >
            </h3>

            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <BasePanel
                v-for="item in items"
                :key="item.index"
                class="p-4 hover:shadow-md transition-shadow cursor-pointer hover:border-accent"
                @click="showItemDetails(item)"
              >
                <h4 class="font-semibold text-foreground mb-2">
                  {{ item.name }}
                </h4>

                <!-- Type-specific info -->
                <div class="text-sm text-foreground/60 space-y-1">
                  <!-- Spell-specific -->
                  <template
                    v-if="type === 'spells' && item.level !== undefined"
                  >
                    <p>
                      Level: {{ item.level === 0 ? 'Cantrip' : item.level }}
                    </p>
                    <p v-if="item.school">
                      School: {{ item.school.name || item.school }}
                    </p>
                  </template>

                  <!-- Monster-specific -->
                  <template v-else-if="type === 'monsters'">
                    <p v-if="item.challenge_rating">
                      CR: {{ item.challenge_rating }}
                    </p>
                    <p v-if="item.type">Type: {{ item.type }}</p>
                  </template>

                  <!-- Equipment-specific -->
                  <template v-else-if="type === 'equipment'">
                    <p v-if="item.equipment_category">
                      Category:
                      {{
                        item.equipment_category.name || item.equipment_category
                      }}
                    </p>
                    <p v-if="item.cost">
                      Cost: {{ item.cost.quantity }} {{ item.cost.unit }}
                    </p>
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
              </BasePanel>
            </div>
          </div>
        </div>
      </AppCard>
    </div>
    <!-- Item Detail Modal -->
    <AppModal
      v-if="selectedItem"
      :visible="!!selectedItem"
      size="lg"
      @close="selectedItem = null"
    >
      <template #header>
        <h2 class="text-xl font-cinzel font-bold text-foreground">
          {{ selectedItem.name }}
        </h2>
      </template>

      <template #body>
        <div class="space-y-4">
          <!-- Dynamic Field Display -->
          <div
            v-for="(value, key) in getItemDisplayFields(selectedItem)"
            :key="key"
            class="border-b border-border pb-3 last:border-b-0"
          >
            <h4 class="font-semibold text-foreground capitalize mb-1">
              {{ formatFieldName(key) }}
            </h4>
            <div class="text-foreground/60">
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
                <pre
                  class="bg-card p-2 rounded text-sm overflow-x-auto border border-border"
                  >{{ JSON.stringify(value, null, 2) }}</pre
                >
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
      </template>

      <template #footer>
        <AppButton variant="secondary" @click="selectedItem = null">
          Close
        </AppButton>
      </template>
    </AppModal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useContentStore } from '../stores/contentStore'
import { contentApi } from '../services/contentApi'
import type { ContentPackWithStatisticsResponse } from '@/types/unified'
import { getErrorMessage } from '@/utils/errorHelpers'
import AppButton from '../components/base/AppButton.vue'
import AppCard from '../components/base/AppCard.vue'
import AppInput from '../components/base/AppInput.vue'
import AppSelect from '../components/base/AppSelect.vue'
import AppModal from '../components/base/AppModal.vue'
import BaseAlert from '../components/base/BaseAlert.vue'
import BaseBadge from '../components/base/BaseBadge.vue'
import BaseLoader from '../components/base/BaseLoader.vue'
import BasePanel from '../components/base/BasePanel.vue'

// Generic content item interface
interface ContentItem {
  name: string
  index?: string
  url?: string
  _content_type?: string
  [key: string]: unknown
}

// Router
const route = useRoute()

// Store
const contentStore = useContentStore()

// State
const pack = ref<ContentPackWithStatisticsResponse | null>(null)
const loading = ref(true)
const error = ref<string | null>(null)
const selectedType = ref('') // Will be set to show all content after loading
const searchQuery = ref('')
const contentItems = ref<ContentItem[]>([])
const selectedItem = ref<ContentItem | null>(null)

// Computed
const packId = computed(() => route.params.packId as string)

const contentCounts = computed<Record<string, number>>(() => {
  if (!pack.value) return {}
  const stats = pack.value.statistics?.items_by_type || {}
  return stats
})

const totalItems = computed(() => {
  if (!pack.value) return 0
  // Use the total from statistics if available, otherwise count loaded items
  return pack.value.statistics?.total_items || contentItems.value.length
})

const groupedContent = computed(() => {
  const groups: Record<string, ContentItem[]> = {}

  let items = contentItems.value

  // Filter by type if selected
  if (selectedType.value) {
    items = items.filter(item => item._content_type === selectedType.value)
  }

  // Filter by search query
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    items = items.filter(
      item =>
        item.name?.toLowerCase().includes(query) ||
        item.index?.toLowerCase().includes(query)
    )
  }

  // Group by type
  items.forEach(item => {
    const type = item._content_type
    if (type && !groups[type]) {
      groups[type] = []
    }
    if (type && groups[type]) {
      groups[type].push(item)
    }
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

function showItemDetails(item: ContentItem) {
  selectedItem.value = item
}

function getItemDisplayFields(item: ContentItem): Record<string, unknown> {
  // Filter out internal fields and empty values
  const excludeFields = ['_content_type', 'index', 'url']
  const fields: Record<string, unknown> = {}

  for (const [key, value] of Object.entries(item)) {
    if (
      !excludeFields.includes(key) &&
      value !== null &&
      value !== undefined &&
      value !== ''
    ) {
      // Skip empty arrays and objects
      if (Array.isArray(value) && value.length === 0) continue
      if (
        typeof value === 'object' &&
        !Array.isArray(value) &&
        Object.keys(value).length === 0
      )
        continue

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
    const contentResult = await contentApi.getPackContent(
      packId.value,
      undefined,
      0,
      1000
    )

    if (
      contentResult.data.content_type === 'all' &&
      typeof contentResult.data.items === 'object' &&
      !Array.isArray(contentResult.data.items)
    ) {
      // We got all content types - flatten them into a single array
      contentItems.value = []

      for (const [contentType, items] of Object.entries(
        contentResult.data.items
      )) {
        if (Array.isArray(items)) {
          // Add content type metadata to each item
          const typedItems = items.map((item: unknown) => ({
            ...(item as ContentItem),
            _content_type: contentType,
          }))

          contentItems.value.push(...typedItems)
        }
      }
    } else if (Array.isArray(contentResult.data.items)) {
      // Single content type result
      contentItems.value = contentResult.data.items.map((item: unknown) => ({
        ...(item as ContentItem),
        _content_type: contentResult.data.content_type,
      }))
    }
  } catch (err) {
    error.value = getErrorMessage(err)
    console.error('Error loading pack details:', err)
  } finally {
    loading.value = false
  }
}

// Watch for pack ID changes
watch(
  () => packId.value,
  () => {
    if (packId.value) {
      loadPackDetails()
    }
  }
)

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
