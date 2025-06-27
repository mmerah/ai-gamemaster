<template>
  <AppModal :visible="true" size="sm" @close="$emit('close')">
    <template #header>
      <h2 class="text-2xl font-cinzel font-bold text-foreground">
        Create Content Pack
      </h2>
    </template>

    <!-- Form -->
    <form @submit.prevent="handleSubmit">
      <!-- Name -->
      <div class="mb-4">
        <AppInput
          v-model="formData.name"
          label="Pack Name"
          placeholder="My Custom Content"
          required
        />
      </div>

      <!-- Description -->
      <div class="mb-4">
        <AppTextarea
          v-model="formData.description"
          label="Description"
          placeholder="A collection of custom spells and monsters..."
          rows="3"
        />
      </div>

      <!-- Author -->
      <div class="mb-4">
        <AppInput
          v-model="formData.author"
          label="Author"
          placeholder="Your name"
        />
      </div>

      <!-- Version -->
      <div class="mb-4">
        <AppInput
          v-model="formData.version"
          label="Version"
          placeholder="1.0.0"
        />
      </div>

      <!-- Activate immediately -->
      <div class="mb-6">
        <label class="flex items-center">
          <input
            v-model="formData.is_active"
            type="checkbox"
            class="mr-2 text-accent focus:ring-accent"
          />
          <span class="text-sm text-foreground">Activate immediately</span>
        </label>
      </div>

      <!-- Error message -->
      <BaseAlert v-if="error" variant="error" class="mb-4">
        {{ error }}
      </BaseAlert>
    </form>

    <template #footer>
      <div class="flex justify-end gap-3">
        <AppButton variant="secondary" @click="$emit('close')">
          Cancel
        </AppButton>
        <AppButton
          variant="primary"
          :is-loading="loading"
          :disabled="loading"
          @click="handleSubmit"
        >
          {{ loading ? 'Creating...' : 'Create Pack' }}
        </AppButton>
      </div>
    </template>
  </AppModal>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useContentStore } from '../../stores/contentStore'
import type { ContentPackCreate, ContentPack } from '../../types/content'
import { getErrorMessage } from '@/utils/errorHelpers'
import AppModal from '../base/AppModal.vue'
import AppInput from '../base/AppInput.vue'
import AppTextarea from '../base/AppTextarea.vue'
import AppButton from '../base/AppButton.vue'
import BaseAlert from '../base/BaseAlert.vue'

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
