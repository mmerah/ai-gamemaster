import { ref, computed } from 'vue'

export function useAnimationSteps() {
  const animationSteps = ref([])
  const currentStepIndex = ref(0)
  const isAnimating = ref(false)
  const animationSpeed = ref(1500) // milliseconds per step
  
  const currentStep = computed(() => {
    if (animationSteps.value.length === 0) return null
    return animationSteps.value[currentStepIndex.value] || null
  })
  
  const hasMoreSteps = computed(() => {
    return currentStepIndex.value < animationSteps.value.length - 1
  })
  
  const totalSteps = computed(() => animationSteps.value.length)
  
  function setAnimationSteps(steps) {
    animationSteps.value = steps || []
    currentStepIndex.value = 0
    isAnimating.value = steps && steps.length > 0
  }
  
  function nextStep() {
    if (hasMoreSteps.value) {
      currentStepIndex.value++
      return true
    }
    return false
  }
  
  function previousStep() {
    if (currentStepIndex.value > 0) {
      currentStepIndex.value--
      return true
    }
    return false
  }
  
  function skipToEnd() {
    if (animationSteps.value.length > 0) {
      currentStepIndex.value = animationSteps.value.length - 1
      isAnimating.value = false
    }
  }
  
  async function playAnimation(onStepCallback) {
    if (!animationSteps.value.length) return
    
    isAnimating.value = true
    currentStepIndex.value = 0
    
    for (let i = 0; i < animationSteps.value.length; i++) {
      if (!isAnimating.value) break // Allow interruption
      
      currentStepIndex.value = i
      
      // Call the callback with current step data
      if (onStepCallback) {
        await onStepCallback(animationSteps.value[i], i)
      }
      
      // Wait before next step (except for last step)
      if (i < animationSteps.value.length - 1 && isAnimating.value) {
        await new Promise(resolve => setTimeout(resolve, animationSpeed.value))
      }
    }
    
    isAnimating.value = false
  }
  
  function stopAnimation() {
    isAnimating.value = false
  }
  
  function reset() {
    animationSteps.value = []
    currentStepIndex.value = 0
    isAnimating.value = false
  }
  
  return {
    // State
    animationSteps,
    currentStep,
    currentStepIndex,
    isAnimating,
    hasMoreSteps,
    totalSteps,
    animationSpeed,
    
    // Methods
    setAnimationSteps,
    nextStep,
    previousStep,
    skipToEnd,
    playAnimation,
    stopAnimation,
    reset
  }
}