<template>
  <div class="space-y-4">
    <div v-if="label" class="flex items-center justify-between">
      <label class="text-sm font-medium text-foreground">{{ label }}</label>
      <span v-if="maxItems" class="text-sm text-foreground/60">
        {{ items.length }} / {{ maxItems }}
      </span>
    </div>

    <div
      v-if="items.length === 0"
      class="text-center py-8 border-2 border-dashed border-border rounded-md"
    >
      <p class="text-foreground/60">{{ emptyMessage }}</p>
    </div>

    <div v-else class="space-y-2">
      <div
        v-for="(item, index) in items"
        :key="getItemKey(item, index)"
        class="flex items-start gap-2"
      >
        <div class="flex-1">
          <slot
            name="item"
            :item="item"
            :index="index"
            :update="(value: any) => updateItem(index, value)"
          >
            <div class="p-3 bg-card rounded-md border border-border">
              {{ item }}
            </div>
          </slot>
        </div>
        <button
          type="button"
          class="p-2 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded transition-colors"
          :disabled="disabled"
          @click="removeItem(index)"
        >
          <svg
            class="w-5 h-5"
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
        </button>
      </div>
    </div>

    <div class="flex gap-2">
      <AppButton
        type="button"
        variant="secondary"
        size="sm"
        :disabled="
          disabled || (maxItems !== undefined && items.length >= maxItems)
        "
        @click="addItem"
      >
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
            d="M12 4v16m8-8H4"
          />
        </svg>
        {{ addLabel }}
      </AppButton>

      <slot name="actions" />
    </div>

    <p v-if="hint" class="text-sm text-foreground/60">{{ hint }}</p>
    <p v-if="error" class="text-sm text-red-500">{{ error }}</p>
  </div>
</template>

<script lang="ts" setup>
import AppButton from './AppButton.vue'

export interface AppDynamicListProps<T = unknown> {
  items: T[]
  label?: string
  addLabel?: string
  emptyMessage?: string
  maxItems?: number
  disabled?: boolean
  hint?: string
  error?: string
  itemKeyField?: string
  defaultItem?: () => T
}

const props = withDefaults(defineProps<AppDynamicListProps>(), {
  addLabel: 'Add Item',
  emptyMessage: 'No items yet. Click the button below to add one.',
  defaultItem: () => () => '',
  label: undefined,
  maxItems: undefined,
  disabled: false,
  hint: undefined,
  error: undefined,
  itemKeyField: undefined,
})

const emit = defineEmits<{
  'update:items': [items: unknown[]]
  add: []
  remove: [index: number]
}>()

const getItemKey = (item: unknown, index: number): string => {
  if (
    props.itemKeyField &&
    typeof item === 'object' &&
    item[props.itemKeyField]
  ) {
    return String(item[props.itemKeyField])
  }
  return `item-${index}`
}

const addItem = () => {
  const newItems = [...props.items, props.defaultItem()]
  emit('update:items', newItems)
  emit('add')
}

const removeItem = (index: number) => {
  const newItems = [...props.items]
  newItems.splice(index, 1)
  emit('update:items', newItems)
  emit('remove', index)
}

const updateItem = (index: number, value: unknown) => {
  const newItems = [...props.items]
  newItems[index] = value
  emit('update:items', newItems)
}
</script>
