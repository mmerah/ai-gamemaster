<template>
  <div class="content-manager min-h-screen bg-background">
    <!-- Header -->
    <div class="bg-primary shadow-lg">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <div class="flex items-center justify-between">
          <div class="flex items-center">
            <router-link
              to="/"
              class="text-accent hover:text-accent/80 transition-colors mr-4"
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
                  d="M15 19l-7-7 7-7"
                />
              </svg>
            </router-link>
            <h1 class="text-2xl font-cinzel font-bold text-accent">
              Content Manager
            </h1>
          </div>
          <div class="flex gap-2">
            <AppButton
              variant="secondary"
              @click="showRAGTester = !showRAGTester"
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
                  d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
                />
              </svg>
              {{ showRAGTester ? 'Hide' : 'Show' }} RAG Tester
            </AppButton>
            <AppButton @click="showCreateModal = true">
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
                  d="M12 4v16m8-8H4"
                />
              </svg>
              New Content Pack
            </AppButton>
          </div>
        </div>
      </div>
    </div>

    <!-- Main Content -->
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <!-- Info Panel -->
      <div v-if="!showRAGTester" class="mb-6">
        <BaseAlert variant="info">
          <div class="flex items-start">
            <svg
              class="w-5 h-5 mr-3 mt-0.5 text-blue-500"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <div>
              <h4 class="font-medium text-foreground mb-1">
                Content Pack Availability
              </h4>
              <p class="text-sm text-foreground/70">
                Content packs marked as "Available" can be selected during
                character creation. Hidden packs won't appear in character
                creation options but existing characters using them remain
                unaffected.
              </p>
            </div>
          </div>
        </BaseAlert>
      </div>
      <!-- Loading State -->
      <div v-if="loading" class="text-center py-12">
        <BaseLoader />
        <p class="mt-4 text-foreground/60">Loading content packs...</p>
      </div>

      <!-- Error State -->
      <div v-else-if="error" class="text-center py-8">
        <BaseAlert variant="danger">
          {{ error }}
        </BaseAlert>
        <AppButton class="mt-4" @click="loadContentPacks">
          Try Again
        </AppButton>
      </div>

      <!-- RAG Tester Section -->
      <div v-else-if="showRAGTester" class="mb-8">
        <transition name="fade">
          <RAGTester />
        </transition>
      </div>

      <!-- Content Packs Grid -->
      <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <ContentPackCard
          v-for="pack in contentPacks"
          :key="pack.id"
          :pack="pack"
          :usage-count="getUsageCount(pack.id)"
          @activate="handleActivate"
          @deactivate="handleDeactivate"
          @delete="handleDelete"
          @upload="handleUpload"
        />
      </div>

      <!-- Empty State -->
      <div
        v-if="!loading && !error && contentPacks.length === 0"
        class="text-center py-12"
      >
        <svg
          class="w-16 h-16 mx-auto text-gray-400"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"
          />
        </svg>
        <p class="mt-4 text-xl text-foreground/60">No content packs found</p>
        <AppButton class="mt-4" @click="showCreateModal = true">
          Create Your First Pack
        </AppButton>
      </div>
    </div>

    <!-- Create Pack Modal -->
    <CreatePackModal
      v-if="showCreateModal"
      @close="showCreateModal = false"
      @created="handlePackCreated"
    />

    <!-- Upload Content Modal -->
    <UploadContentModal
      v-if="uploadTarget"
      :pack="uploadTarget"
      @close="uploadTarget = null"
      @uploaded="handleContentUploaded"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { storeToRefs } from 'pinia'
import ContentPackCard from '../components/content/ContentPackCard.vue'
import CreatePackModal from '../components/content/CreatePackModal.vue'
import UploadContentModal from '../components/content/UploadContentModal.vue'
import RAGTester from '../components/content/RAGTester.vue'
import AppButton from '../components/base/AppButton.vue'
import BaseLoader from '../components/base/BaseLoader.vue'
import BaseAlert from '../components/base/BaseAlert.vue'
import { useContentStore } from '../stores/contentStore'
import type { ContentPack } from '../types/content'

// Store
const contentStore = useContentStore()
const { contentPacks, loading, error, usageStatistics } =
  storeToRefs(contentStore)

// Local state
const showCreateModal = ref(false)
const uploadTarget = ref<ContentPack | null>(null)
const showRAGTester = ref(false)

// Load content packs
async function loadContentPacks() {
  await contentStore.loadContentPacks()
  // Also load usage statistics
  await contentStore.loadUsageStatistics()
}

// Get usage count for a specific pack
function getUsageCount(packId: string): number | undefined {
  const stat = usageStatistics.value.find(s => s.pack_id === packId)
  return stat?.character_count
}

// Event handlers
async function handleActivate(packId: string) {
  const success = await contentStore.activatePack(packId)
  if (!success) {
    alert('Failed to make content pack available for selection')
  }
}

async function handleDeactivate(packId: string) {
  const success = await contentStore.deactivatePack(packId)
  if (!success) {
    alert('Failed to hide content pack from selection')
  }
}

async function handleDelete(packId: string) {
  if (
    !confirm(
      'Are you sure you want to delete this content pack? This action cannot be undone.'
    )
  ) {
    return
  }

  const success = await contentStore.deletePack(packId)
  if (!success) {
    alert('Failed to delete content pack')
  }
}

function handleUpload(pack: ContentPack) {
  uploadTarget.value = pack
}

function handlePackCreated(newPack: ContentPack) {
  // Don't push - the store already did this
  showCreateModal.value = false
}

function handleContentUploaded() {
  uploadTarget.value = null
  // Optionally reload packs to get updated statistics
  loadContentPacks()
}

// Load data on mount
onMounted(() => {
  loadContentPacks()
})
</script>

<style scoped>
.content-manager {
  min-height: 100vh;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
