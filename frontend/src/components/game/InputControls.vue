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
            @keydown.enter.exact.prevent="handleSendMessage"
            @keydown.enter.shift.exact="handleNewLine"
            placeholder="Describe your action or ask the GM a question..."
            class="fantasy-input flex-1 resize-none"
            rows="3"
            :disabled="disabled"
          />
          <button
            @click="handleSendMessage"
            :disabled="disabled || !message.trim()"
            class="fantasy-button px-6 py-2 self-end"
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

<script setup>
import { ref } from 'vue'

const props = defineProps({
  disabled: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['send-message'])

const message = ref('')

function handleSendMessage() {
  if (message.value.trim() && !props.disabled) {
    emit('send-message', message.value.trim())
    message.value = ''
  }
}

function handleNewLine() {
  message.value += '\n'
}
</script>

<style scoped>
/* Component-specific styles if needed */
</style>
