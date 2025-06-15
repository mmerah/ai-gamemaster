<template>
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" @click.self="$emit('close')">
    <div class="bg-parchment rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[80vh] overflow-hidden flex flex-col">
      <div class="p-6 border-b border-gray-300">
        <!-- Header -->
        <div class="flex items-center justify-between">
          <h2 class="text-2xl font-cinzel font-bold text-text-primary">
            Upload Content to {{ pack.name }}
          </h2>
          <button
            @click="$emit('close')"
            class="text-text-secondary hover:text-text-primary transition-colors"
          >
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
            </svg>
          </button>
        </div>
      </div>

      <div class="flex-1 overflow-y-auto p-6">
        <!-- Instructions -->
        <div class="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <h3 class="font-semibold text-blue-900 mb-2">Upload Instructions</h3>
          <ul class="text-sm text-blue-800 space-y-1">
            <li>• Select the type of content you want to upload</li>
            <li>• Upload a JSON file or paste JSON content directly</li>
            <li>• Content must follow the D&D 5e SRD format</li>
            <li>• You can upload multiple items at once</li>
          </ul>
        </div>

        <!-- Content Type Selection -->
        <div class="mb-4">
          <label for="content-type" class="block text-sm font-medium text-text-primary mb-2">
            Content Type <span class="text-red-500">*</span>
          </label>
          <select
            id="content-type"
            v-model="selectedType"
            required
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold"
          >
            <option value="">Select content type...</option>
            <option v-for="type in contentTypes" :key="type" :value="type">
              {{ formatContentType(type) }}
            </option>
          </select>
        </div>

        <!-- File Upload -->
        <div class="mb-4">
          <label class="block text-sm font-medium text-text-primary mb-2">
            Upload JSON File
          </label>
          <div class="relative">
            <input
              type="file"
              accept=".json,application/json"
              @change="handleFileSelect"
              class="hidden"
              ref="fileInput"
            />
            <button
              type="button"
              @click="$refs.fileInput.click()"
              class="w-full px-4 py-3 border-2 border-dashed border-gray-300 rounded-lg hover:border-gold transition-colors flex items-center justify-center"
            >
              <svg class="w-6 h-6 mr-2 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"></path>
              </svg>
              <span class="text-gray-600">
                {{ selectedFile ? selectedFile.name : 'Click to upload or drag and drop' }}
              </span>
            </button>
          </div>
        </div>

        <!-- OR Divider -->
        <div class="relative my-6">
          <div class="absolute inset-0 flex items-center">
            <div class="w-full border-t border-gray-300"></div>
          </div>
          <div class="relative flex justify-center text-sm">
            <span class="px-2 bg-parchment text-gray-500">OR</span>
          </div>
        </div>

        <!-- JSON Text Input -->
        <div class="mb-4">
          <label for="json-content" class="block text-sm font-medium text-text-primary mb-2">
            Paste JSON Content
          </label>
          <textarea
            id="json-content"
            v-model="jsonContent"
            rows="8"
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold font-mono text-sm"
            placeholder='[
  {
    "name": "Fireball",
    "level": 3,
    "school": "evocation",
    ...
  }
]'
          ></textarea>
        </div>

        <!-- Upload Result -->
        <div v-if="uploadResult" class="mt-6">
          <div
            :class="[
              'p-4 rounded-lg',
              uploadResult.failed_items === 0
                ? 'bg-green-50 border border-green-200'
                : 'bg-yellow-50 border border-yellow-200'
            ]"
          >
            <h4 class="font-semibold mb-2" :class="uploadResult.failed_items === 0 ? 'text-green-900' : 'text-yellow-900'">
              Upload {{ uploadResult.failed_items === 0 ? 'Successful' : 'Completed with Errors' }}
            </h4>
            <div class="text-sm" :class="uploadResult.failed_items === 0 ? 'text-green-800' : 'text-yellow-800'">
              <p>• Total items: {{ uploadResult.total_items }}</p>
              <p>• Successful: {{ uploadResult.successful_items }}</p>
              <p v-if="uploadResult.failed_items > 0">• Failed: {{ uploadResult.failed_items }}</p>
            </div>
            
            <!-- Validation Errors -->
            <div v-if="Object.keys(uploadResult.validation_errors).length > 0" class="mt-3">
              <h5 class="font-medium text-red-900 mb-1">Validation Errors:</h5>
              <ul class="text-sm text-red-800 space-y-1">
                <li v-for="(error, key) in uploadResult.validation_errors" :key="key">
                  • {{ key }}: {{ error }}
                </li>
              </ul>
            </div>
            
            <!-- Warnings -->
            <div v-if="uploadResult.warnings.length > 0" class="mt-3">
              <h5 class="font-medium text-yellow-900 mb-1">Warnings:</h5>
              <ul class="text-sm text-yellow-800 space-y-1">
                <li v-for="warning in uploadResult.warnings" :key="warning">
                  • {{ warning }}
                </li>
              </ul>
            </div>
          </div>
        </div>

        <!-- Error message -->
        <div v-if="error" class="mt-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
          {{ error }}
        </div>
      </div>

      <!-- Footer Actions -->
      <div class="p-6 border-t border-gray-300 bg-gray-50">
        <div class="flex justify-end gap-3">
          <button
            type="button"
            @click="$emit('close')"
            class="px-4 py-2 text-gray-700 bg-gray-200 hover:bg-gray-300 rounded-md transition-colors"
          >
            {{ uploadResult ? 'Close' : 'Cancel' }}
          </button>
          <button
            v-if="!uploadResult"
            @click="handleUpload"
            :disabled="loading || !selectedType || (!selectedFile && !jsonContent)"
            class="fantasy-button px-4 py-2"
          >
            <span v-if="loading" class="inline-block animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></span>
            {{ loading ? 'Uploading...' : 'Upload Content' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useContentStore } from '../../stores/contentStore'
import type { ContentPack, ContentType, ContentUploadResult } from '../../types/content'

// Store
const contentStore = useContentStore()

// Props
const props = defineProps<{
  pack: ContentPack
}>()

// Emits
const emit = defineEmits<{
  close: []
  uploaded: []
}>()

// Content types - will be loaded from API
const contentTypes = ref<ContentType[]>([])

// State
const loading = ref(false)
const error = ref<string | null>(null)
const selectedType = ref<ContentType | ''>('')
const selectedFile = ref<File | null>(null)
const jsonContent = ref('')
const uploadResult = ref<ContentUploadResult | null>(null)
const fileInput = ref<HTMLInputElement>()

// Methods
function formatContentType(type: string): string {
  return type
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

function handleFileSelect(event: Event) {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  
  if (file) {
    selectedFile.value = file
    // Clear text input when file is selected
    jsonContent.value = ''
  }
}

async function readFileContent(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = (e) => resolve(e.target?.result as string)
    reader.onerror = reject
    reader.readAsText(file)
  })
}

async function handleUpload() {
  if (!selectedType.value) {
    error.value = 'Please select a content type'
    return
  }

  error.value = null
  loading.value = true
  uploadResult.value = null

  try {
    let content: any

    // Get content from file or text input
    if (selectedFile.value) {
      const fileContent = await readFileContent(selectedFile.value)
      try {
        content = JSON.parse(fileContent)
      } catch (e) {
        throw new Error('Invalid JSON in file')
      }
    } else if (jsonContent.value) {
      try {
        content = JSON.parse(jsonContent.value)
      } catch (e) {
        throw new Error('Invalid JSON content')
      }
    } else {
      throw new Error('No content provided')
    }

    const result = await contentStore.uploadContent(props.pack.id, selectedType.value, content)
    
    if (result) {
      uploadResult.value = result
      emit('uploaded')
    } else {
      throw new Error(contentStore.error || 'Upload failed')
    }
  } catch (err: any) {
    error.value = err.message || 'Failed to upload content'
    console.error('Error uploading content:', err)
  } finally {
    loading.value = false
  }
}

// Load supported content types on mount
onMounted(async () => {
  await contentStore.loadSupportedTypes()
  
  // Convert from backend format (hyphenated) to frontend format (underscored)
  contentTypes.value = contentStore.supportedTypes.map(type => 
    type.replace(/-/g, '_') as ContentType
  )
})
</script>