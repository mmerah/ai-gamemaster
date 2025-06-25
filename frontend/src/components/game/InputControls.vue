<template>
  <div class="fantasy-panel">
    <div class="space-y-4">
      <!-- Message Input -->
      <div>
        <label class="block text-sm font-medium text-text-primary mb-2">
          Send Message
        </label>
        <div class="flex space-x-2">
          <textarea
            v-model="message"
            placeholder="Describe your action or ask the GM a question..."
            class="fantasy-input flex-1 resize-none"
            rows="3"
            :disabled="disabled"
            @keydown.enter.exact.prevent="handleSendMessage"
            @keydown.enter.shift.exact="handleNewLine"
          />
          <button
            :disabled="disabled || !message.trim()"
            class="fantasy-button px-6 py-2 self-end"
            @click="handleSendMessage"
          >
            Send
          </button>
        </div>
        <p class="text-xs text-text-secondary mt-1">
          Press Enter to send, Shift+Enter for new line
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, Ref } from 'vue'

// Props interface
interface Props {
  disabled?: boolean
}

// Emits interface
interface Emits {
  (e: 'send-message', message: string): void
}

const props = withDefaults(defineProps<Props>(), {
  disabled: false
})

const emit = defineEmits<Emits>()

const message: Ref<string> = ref('')

function handleSendMessage(): void {
  if (message.value.trim() && !props.disabled) {
    emit('send-message', message.value.trim())
    message.value = ''
  }
}

function handleNewLine(): void {
  message.value += '\n'
}
</script>

<style scoped>
/* Component-specific styles if needed */
</style>
