<template>
  <div class="content-manager min-h-screen bg-parchment">
    <!-- Header -->
    <div class="bg-primary-dark shadow-lg">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <div class="flex items-center justify-between">
          <div class="flex items-center">
            <router-link
              to="/"
              class="text-gold hover:text-gold-light transition-colors mr-4"
            >
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"></path>
              </svg>
            </router-link>
            <h1 class="text-2xl font-cinzel font-bold text-gold">
              Content Manager
            </h1>
          </div>
          <button
            @click="showCreateModal = true"
            class="fantasy-button px-4 py-2"
          >
            <svg class="w-5 h-5 inline mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path>
            </svg>
            New Content Pack
          </button>
        </div>
      </div>
    </div>

    <!-- Main Content -->
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <!-- Loading State -->
      <div v-if="loading" class="text-center py-12">
        <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-gold"></div>
        <p class="mt-4 text-text-secondary">Loading content packs...</p>
      </div>

      <!-- Error State -->
      <div v-else-if="error" class="fantasy-card p-8 text-center">
        <p class="text-red-600">{{ error }}</p>
        <button @click="loadContentPacks" class="fantasy-button mt-4">
          Try Again
        </button>
      </div>

      <!-- Content Packs Grid -->
      <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <ContentPackCard
          v-for="pack in contentPacks"
          :key="pack.id"
          :pack="pack"
          @activate="handleActivate"
          @deactivate="handleDeactivate"
          @delete="handleDelete"
          @upload="handleUpload"
        />
      </div>

      <!-- Empty State -->
      <div v-if="!loading && !error && contentPacks.length === 0" class="text-center py-12">
        <svg class="w-16 h-16 mx-auto text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path>
        </svg>
        <p class="mt-4 text-xl text-text-secondary">No content packs found</p>
        <button @click="showCreateModal = true" class="fantasy-button mt-4">
          Create Your First Pack
        </button>
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
import { useContentStore } from '../stores/contentStore'
import type { ContentPack } from '../types/content'

// Store
const contentStore = useContentStore()
const { contentPacks, loading, error } = storeToRefs(contentStore)

// Local state
const showCreateModal = ref(false)
const uploadTarget = ref<ContentPack | null>(null)

// Load content packs
async function loadContentPacks() {
  await contentStore.loadContentPacks()
}

// Event handlers
async function handleActivate(packId: string) {
  const success = await contentStore.activatePack(packId)
  if (!success) {
    alert('Failed to activate content pack')
  }
}

async function handleDeactivate(packId: string) {
  const success = await contentStore.deactivatePack(packId)
  if (!success) {
    alert('Failed to deactivate content pack')
  }
}

async function handleDelete(packId: string) {
  if (!confirm('Are you sure you want to delete this content pack? This action cannot be undone.')) {
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
</style>