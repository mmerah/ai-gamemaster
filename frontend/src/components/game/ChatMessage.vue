<template>
  <div
    :class="[
      'chat-message p-3 rounded-lg transition-all duration-300',
      message.type === 'user'
        ? 'bg-primary/20 ml-8'
        : message.type === 'assistant'
          ? 'bg-accent/20 mr-8'
          : 'bg-card mx-4',
      message.animated ? 'animated-message' : '',
      message.superseded ? 'superseded-message' : '',
    ]"
  >
    <div class="flex items-start space-x-2">
      <div class="flex-shrink-0">
        <div
          :class="[
            'w-8 h-8 rounded-full flex items-center justify-center text-xs font-semibold',
            message.type === 'user'
              ? 'bg-primary text-primary-foreground'
              : message.type === 'assistant'
                ? 'bg-accent text-accent-foreground'
                : 'bg-foreground/20 text-foreground',
          ]"
        >
          {{
            message.type === 'user'
              ? 'U'
              : message.type === 'assistant'
                ? 'GM'
                : 'S'
          }}
        </div>
      </div>

      <div class="flex-1 min-w-0">
        <div class="flex items-center space-x-2 mb-1">
          <span class="text-sm font-medium text-foreground">
            {{
              message.type === 'user'
                ? 'You'
                : message.type === 'assistant'
                  ? 'Game Master'
                  : 'System'
            }}
          </span>
          <span class="text-xs text-foreground/60">
            {{ formatTime(message.timestamp) }}
          </span>

          <!-- TTS Play button for GM messages -->
          <button
            v-if="
              message.type === 'assistant' &&
              ttsEnabled &&
              (message.audio_path || voiceId) &&
              (message.detailed_content || message.content)
            "
            :disabled="audioLoading"
            class="text-xs text-accent hover:text-accent/80 transition-colors flex items-center space-x-1"
            :title="
              audioLoading ? 'Generating audio...' : isPlaying ? 'Stop' : 'Play'
            "
            @click="$emit('toggle-play')"
          >
            <div
              v-if="audioLoading"
              class="w-3 h-3 animate-spin rounded-full border border-accent border-t-transparent"
            />
            <svg
              v-else-if="isPlaying"
              class="w-3 h-3"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fill-rule="evenodd"
                d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zM7 8a1 1 0 012 0v4a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v4a1 1 0 102 0V8a1 1 0 00-1-1z"
                clip-rule="evenodd"
              />
            </svg>
            <svg v-else class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
              <path
                fill-rule="evenodd"
                d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z"
                clip-rule="evenodd"
              />
            </svg>
          </button>

          <!-- Queue indicator for auto-play -->
          <span
            v-if="isQueued && message.type === 'assistant'"
            class="text-xs text-accent/70"
          >
            Queued
          </span>

          <!-- Reasoning toggle button for GM messages -->
          <button
            v-if="message.type === 'assistant' && message.gm_thought"
            class="text-xs text-accent hover:text-accent/80 transition-colors flex items-center space-x-1"
            :title="expandedReasoning ? 'Hide Reasoning' : 'Show Reasoning'"
            @click="$emit('toggle-reasoning')"
          >
            <svg
              class="w-3 h-3"
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
            <span>{{ expandedReasoning ? 'Hide' : 'Show' }} Reasoning</span>
            <svg
              :class="[
                'w-3 h-3 transition-transform',
                expandedReasoning ? 'rotate-180' : '',
              ]"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M19 9l-7 7-7-7"
              />
            </svg>
          </button>
        </div>

        <div class="text-sm text-foreground whitespace-pre-wrap">
          {{ message.content }}
        </div>

        <!-- Audio element for TTS playback -->
        <audio
          v-if="message.type === 'assistant' && audioElement"
          ref="audioRef"
          :src="audioElement"
          class="hidden"
          preload="none"
          @ended="$emit('audio-ended')"
          @error="$emit('audio-error')"
        />

        <!-- Expandable reasoning section for GM messages -->
        <div
          v-if="
            message.type === 'assistant' &&
            message.gm_thought &&
            expandedReasoning
          "
          class="mt-3 p-3 bg-card border border-accent/30 rounded-md"
        >
          <div class="flex items-center space-x-2 mb-2">
            <svg
              class="w-4 h-4 text-accent"
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
            <span class="text-xs font-medium text-accent">AI Reasoning</span>
          </div>
          <div
            class="text-xs text-foreground/60 whitespace-pre-wrap leading-relaxed"
          >
            {{ message.gm_thought }}
          </div>
        </div>

        <!-- Dice roll details -->
        <div
          v-if="message.type === 'dice' && message.details"
          class="mt-2 text-xs text-foreground/60"
        >
          <div class="flex items-center space-x-2">
            <span>🎲 {{ message.details.expression }}</span>
            <span class="font-mono">{{ message.details.breakdown }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { defineProps, defineEmits } from 'vue'
import type { UIChatMessage } from '@/types/ui'

interface Props {
  message: UIChatMessage
  expandedReasoning: boolean
  audioLoading: boolean
  isPlaying: boolean
  isQueued: boolean
  audioElement?: string | null
  ttsEnabled?: boolean
  voiceId?: string | null
}

interface Emits {
  (e: 'toggle-reasoning'): void
  (e: 'toggle-play'): void
  (e: 'audio-ended'): void
  (e: 'audio-error'): void
}

const props = withDefaults(defineProps<Props>(), {
  expandedReasoning: false,
  audioLoading: false,
  isPlaying: false,
  isQueued: false,
  audioElement: null,
  ttsEnabled: false,
  voiceId: null,
})

const emit = defineEmits<Emits>()

function formatTime(timestamp: string | undefined): string {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  return date.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
  })
}
</script>

<style scoped>
/* Animation styles for messages appearing during NPC turn animations */
.animated-message {
  animation: messageSlideIn 0.5s ease-out;
}

@keyframes messageSlideIn {
  0% {
    opacity: 0;
    transform: translateY(10px);
  }
  100% {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Pulse effect for newly animated messages */
.chat-message.animated-message:not(:last-child) {
  animation: messagePulse 0.6s ease-in-out;
}

@keyframes messagePulse {
  0% {
    opacity: 0;
    transform: translateY(10px) scale(0.98);
  }
  50% {
    opacity: 0.8;
    transform: translateY(5px) scale(0.99);
  }
  100% {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

/* Enhanced glow effect for animated GM messages */
.chat-message.animated-message.bg-accent\/20 {
  box-shadow: 0 0 0 1px rgba(var(--color-accent) / 0.2);
  animation: messageGlow 0.6s ease-in-out;
}

@keyframes messageGlow {
  0% {
    box-shadow: 0 0 0 1px rgba(var(--color-accent) / 0);
  }
  50% {
    box-shadow: 0 0 10px 2px rgba(var(--color-accent) / 0.3);
  }
  100% {
    box-shadow: 0 0 0 1px rgba(var(--color-accent) / 0.2);
  }
}

/* Smooth transitions for message updates */
.chat-message {
  transition: all 0.3s ease-out;
}

/* Superseded message styles */
.superseded-message {
  opacity: 0.5;
  position: relative;
}

.superseded-message::after {
  content: '';
  position: absolute;
  top: 50%;
  left: 0;
  right: 0;
  height: 1px;
  background-color: rgba(255, 255, 255, 0.3);
  transform: translateY(-50%);
}
</style>
