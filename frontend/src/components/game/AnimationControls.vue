<template>
  <Transition name="slide-up">
    <div v-if="isAnimating" class="animation-controls">
      <div class="animation-header">
        <div class="animation-progress">
          <span class="progress-text">NPC Actions</span>
          <span class="progress-counter">{{ currentStepIndex + 1 }} / {{ totalSteps }}</span>
        </div>
        <div class="animation-buttons">
          <button 
            @click="toggleSpeed" 
            class="control-button speed-button"
            :title="`Current speed: ${animationSpeed}ms per action`"
          >
            <svg class="icon" viewBox="0 0 24 24" width="16" height="16">
              <path fill="currentColor" d="M13,2.05C18.05,2.55 22,6.82 22,12C22,17.52 17.52,22 12,22C6.48,22 2,17.52 2,12C2,6.82 5.95,2.55 11,2.05V4.07C7.05,4.56 4,7.92 4,12C4,16.41 7.59,20 12,20C16.41,20 20,16.41 20,12C20,7.92 16.95,4.56 13,4.07V2.05M12,6L16,10H13V16H11V10H8L12,6Z" />
            </svg>
            {{ speedLabel }}
          </button>
          <button 
            @click="skipAnimation" 
            class="control-button skip-button"
            title="Skip to final result"
          >
            <svg class="icon" viewBox="0 0 24 24" width="16" height="16">
              <path fill="currentColor" d="M16,18H18V6H16M6,18L14.5,12L6,6V18Z" />
            </svg>
            Skip
          </button>
        </div>
      </div>
      <div class="animation-bar">
        <div 
          class="animation-progress-bar" 
          :style="{ width: progressPercentage + '%' }"
        ></div>
      </div>
    </div>
  </Transition>
</template>

<script setup>
import { computed } from 'vue'
import { storeToRefs } from 'pinia'
import { useGameStore } from '../../stores/gameStore'

const gameStore = useGameStore()
const { 
  isAnimating, 
  currentStepIndex, 
  totalSteps, 
  animationSpeed 
} = storeToRefs(gameStore)

const progressPercentage = computed(() => {
  if (totalSteps.value === 0) return 0
  return ((currentStepIndex.value + 1) / totalSteps.value) * 100
})

const speedLabel = computed(() => {
  const speed = animationSpeed.value
  if (speed <= 500) return 'Fast'
  if (speed <= 1000) return 'Normal'
  if (speed <= 1500) return 'Slow'
  return 'Slower'
})

function toggleSpeed() {
  // Cycle through speeds: 500ms, 1000ms, 1500ms, 2000ms
  const speeds = [500, 1000, 1500, 2000]
  const currentIndex = speeds.indexOf(animationSpeed.value)
  const nextIndex = (currentIndex + 1) % speeds.length
  animationSpeed.value = speeds[nextIndex]
}

function skipAnimation() {
  gameStore.skipAnimation()
}
</script>

<style scoped>
.animation-controls {
  position: fixed;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(17, 24, 39, 0.95);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 16px 20px;
  min-width: 320px;
  box-shadow: 
    0 4px 6px -1px rgba(0, 0, 0, 0.1),
    0 2px 4px -1px rgba(0, 0, 0, 0.06),
    0 0 0 1px rgba(255, 255, 255, 0.05) inset;
  z-index: 1000;
}

.animation-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.animation-progress {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.progress-text {
  font-size: 14px;
  font-weight: 600;
  color: #f3f4f6;
  letter-spacing: 0.025em;
}

.progress-counter {
  font-size: 12px;
  color: #9ca3af;
}

.animation-buttons {
  display: flex;
  gap: 8px;
}

.control-button {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: rgba(55, 65, 81, 0.5);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 6px;
  color: #e5e7eb;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.control-button:hover {
  background: rgba(75, 85, 99, 0.6);
  border-color: rgba(255, 255, 255, 0.2);
  transform: translateY(-1px);
}

.control-button:active {
  transform: translateY(0);
}

.icon {
  opacity: 0.8;
}

.speed-button {
  min-width: 90px;
}

.skip-button:hover {
  background: rgba(239, 68, 68, 0.2);
  border-color: rgba(239, 68, 68, 0.3);
}

.animation-bar {
  position: relative;
  height: 4px;
  background: rgba(55, 65, 81, 0.5);
  border-radius: 2px;
  overflow: hidden;
}

.animation-progress-bar {
  position: absolute;
  top: 0;
  left: 0;
  height: 100%;
  background: linear-gradient(90deg, #3b82f6 0%, #60a5fa 100%);
  border-radius: 2px;
  transition: width 0.3s ease;
  box-shadow: 0 0 8px rgba(59, 130, 246, 0.5);
}

/* Transition animations */
.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 0.3s ease;
}

.slide-up-enter-from {
  transform: translate(-50%, 100%);
  opacity: 0;
}

.slide-up-leave-to {
  transform: translate(-50%, 100%);
  opacity: 0;
}

/* Mobile responsiveness */
@media (max-width: 640px) {
  .animation-controls {
    left: 10px;
    right: 10px;
    transform: none;
    min-width: auto;
    padding: 12px 16px;
  }
  
  .control-button {
    padding: 6px 10px;
    font-size: 12px;
  }
  
  .speed-button {
    min-width: 80px;
  }
}
</style>