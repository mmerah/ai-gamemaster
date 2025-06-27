<template>
  <div class="campaign-template-grid">
    <!-- Loading State -->
    <div
      v-if="loading"
      class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
    >
      <AppCard v-for="i in 3" :key="`skeleton-${i}`" class="animate-pulse">
        <div class="h-6 bg-foreground/20 rounded mb-2" />
        <div class="h-20 bg-foreground/10 rounded mb-4" />
        <div class="h-10 bg-foreground/20 rounded" />
      </AppCard>
    </div>

    <!-- Empty State -->
    <AppCard
      v-else-if="!loading && templates.length === 0"
      padding="lg"
      class="text-center"
    >
      <svg
        class="w-16 h-16 mx-auto text-accent/30 mb-4"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"
        />
      </svg>
      <p class="text-foreground/60 font-crimson text-lg">
        No campaign templates yet
      </p>
      <p class="text-foreground/40 text-sm mt-2">
        Create your first template to reuse campaign scenarios
      </p>
    </AppCard>

    <!-- Templates Grid -->
    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <AppCard
        v-for="template in templates"
        :key="template.id"
        class="hover:shadow-lg transition-shadow duration-200"
      >
        <!-- Template Header -->
        <div class="mb-4">
          <h3 class="text-lg font-cinzel font-semibold text-foreground mb-1">
            {{ template.name }}
          </h3>
          <div class="flex items-center text-sm text-foreground/60 space-x-4">
            <span class="flex items-center">
              <svg
                class="w-4 h-4 mr-1"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
                />
              </svg>
              Level {{ template.starting_level }}
            </span>
            <span class="capitalize">{{ template.difficulty }}</span>
          </div>
        </div>

        <!-- Description -->
        <p class="text-sm text-foreground/60 font-crimson mb-4 line-clamp-3">
          {{ template.description }}
        </p>

        <!-- Tags -->
        <div
          v-if="template.tags && template.tags.length > 0"
          class="flex flex-wrap gap-2 mb-4"
        >
          <BaseBadge
            v-for="tag in template.tags"
            :key="tag"
            variant="warning"
            size="sm"
          >
            {{ tag }}
          </BaseBadge>
        </div>

        <!-- Actions -->
        <div class="flex space-x-2">
          <AppButton
            class="flex-1"
            variant="secondary"
            size="sm"
            @click="$emit('use', template)"
          >
            <svg
              class="w-4 h-4 inline mr-1"
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
            Start Campaign
          </AppButton>
          <AppButton
            variant="secondary"
            size="sm"
            :title="'Edit ' + template.name"
            @click="$emit('edit', template)"
          >
            <svg
              class="w-4 h-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"
              />
            </svg>
          </AppButton>
          <AppButton
            variant="danger"
            size="sm"
            :title="'Delete ' + template.name"
            @click="$emit('delete', template.id)"
          >
            <svg
              class="w-4 h-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
              />
            </svg>
          </AppButton>
        </div>
      </AppCard>
    </div>
  </div>
</template>

<script setup>
import AppCard from '../base/AppCard.vue'
import AppButton from '../base/AppButton.vue'
import BaseBadge from '../base/BaseBadge.vue'

defineProps({
  templates: {
    type: Array,
    required: true,
  },
  loading: {
    type: Boolean,
    default: false,
  },
})

defineEmits(['use', 'edit', 'delete'])
</script>

<style scoped>
.line-clamp-3 {
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
