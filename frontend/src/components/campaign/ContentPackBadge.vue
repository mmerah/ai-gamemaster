<template>
  <span
    v-if="source"
    class="inline-flex items-center ml-2 px-2 py-0.5 rounded-full text-xs font-medium bg-accent/10 text-accent border border-accent/20"
    :title="`From content pack: ${source.content_pack_name}`"
  >
    <svg
      class="w-3 h-3 mr-1"
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
    {{ source.content_pack_name }}
  </span>
</template>

<script setup lang="ts">
interface ContentPackSource {
  content_pack_id: string
  content_pack_name: string
}

defineProps<{
  source?: ContentPackSource
}>()
</script>
