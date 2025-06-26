<template>
  <div
    class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
    @click.self="$emit('close')"
  >
    <div class="bg-parchment rounded-lg shadow-xl max-w-md w-full mx-4">
      <div class="p-6">
        <!-- Header -->
        <div class="flex items-center justify-between mb-6">
          <h2 class="text-2xl font-cinzel font-bold text-text-primary">
            Create Content Pack
          </h2>
          <button
            class="text-text-secondary hover:text-text-primary transition-colors"
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

        <!-- Form -->
        <form @submit.prevent="handleSubmit">
          <!-- Name -->
          <div class="mb-4">
            <label
              for="name"
              class="block text-sm font-medium text-text-primary mb-2"
            >
              Pack Name <span class="text-red-500">*</span>
            </label>
            <input
              id="name"
              v-model="formData.name"
              type="text"
              required
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold"
              placeholder="My Custom Content"
            />
          </div>

          <!-- Description -->
          <div class="mb-4">
            <label
              for="description"
              class="block text-sm font-medium text-text-primary mb-2"
            >
              Description
            </label>
            <textarea
              id="description"
              v-model="formData.description"
              rows="3"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold"
              placeholder="A collection of custom spells and monsters..."
            />
          </div>

          <!-- Author -->
          <div class="mb-4">
            <label
              for="author"
              class="block text-sm font-medium text-text-primary mb-2"
            >
              Author
            </label>
            <input
              id="author"
              v-model="formData.author"
              type="text"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold"
              placeholder="Your name"
            />
          </div>

          <!-- Version -->
          <div class="mb-4">
            <label
              for="version"
              class="block text-sm font-medium text-text-primary mb-2"
            >
              Version
            </label>
            <input
              id="version"
              v-model="formData.version"
              type="text"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold"
              placeholder="1.0.0"
            />
          </div>

          <!-- Activate immediately -->
          <div class="mb-6">
            <label class="flex items-center">
              <input
                v-model="formData.is_active"
                type="checkbox"
                class="mr-2 text-gold focus:ring-gold"
              />
              <span class="text-sm text-text-primary"
                >Activate immediately</span
              >
            </label>
          </div>

          <!-- Error message -->
          <div
            v-if="error"
            class="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded"
          >
            {{ error }}
          </div>

          <!-- Actions -->
          <div class="flex justify-end gap-3">
            <button
              type="button"
              class="px-4 py-2 text-gray-700 bg-gray-200 hover:bg-gray-300 rounded-md transition-colors"
              @click="$emit('close')"
            >
              Cancel
            </button>
            <button
              type="submit"
              :disabled="loading"
              class="fantasy-button px-4 py-2"
            >
              <span
                v-if="loading"
                class="inline-block animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"
              />
              {{ loading ? 'Creating...' : 'Create Pack' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useContentStore } from '../../stores/contentStore'
import type { ContentPackCreate, ContentPack } from '../../types/content'
import { getErrorMessage } from '@/utils/errorHelpers'

// Store
const contentStore = useContentStore()

// Emits
const emit = defineEmits<{
  close: []
  created: [pack: ContentPack]
}>()

// State
const loading = ref(false)
const error = ref<string | null>(null)

const formData = reactive<ContentPackCreate>({
  name: '',
  description: '',
  author: '',
  version: '1.0.0',
  is_active: true,
})

// Methods
async function handleSubmit() {
  error.value = null
  loading.value = true

  try {
    const newPack = await contentStore.createPack(formData)

    if (newPack) {
      emit('created', newPack)
      emit('close')
    } else {
      error.value = contentStore.error || 'Failed to create content pack'
    }
  } catch (err) {
    error.value = getErrorMessage(err)
    console.error('Error creating pack:', err)
  } finally {
    loading.value = false
  }
}
</script>
