import { computed, reactive } from 'vue'
import type { CharacterTemplateModel } from '@/types/unified'

// Types
interface AbilityScores {
  STR: number
  DEX: number
  CON: number
  INT: number
  WIS: number
  CHA: number
}

interface AbilityInfo {
  name: string
  description: string
}

type AbilityKey = keyof AbilityScores

export function usePointBuy() {
  // Standard D&D 5e Point Buy system (27 points total)
  const POINT_BUY_COSTS: Record<number, number> = {
    8: 0, 9: 1, 10: 2, 11: 3, 12: 4, 13: 5, 14: 7, 15: 9
  }

  const MAX_POINTS = 27
  const MIN_SCORE = 8
  const MAX_SCORE = 15

  // Base ability scores (before racial bonuses)
  const baseScores = reactive<AbilityScores>({
    STR: 8,
    DEX: 8,
    CON: 8,
    INT: 8,
    WIS: 8,
    CHA: 8
  })

  // Calculate points spent
  const pointsSpent = computed(() => {
    return Object.values(baseScores).reduce((total, score) => {
      return total + (POINT_BUY_COSTS[score] || 0)
    }, 0)
  })

  // Calculate remaining points
  const pointsRemaining = computed(() => {
    return MAX_POINTS - pointsSpent.value
  })

  // Check if point buy is valid
  const isValid = computed(() => {
    return pointsRemaining.value >= 0 && pointsRemaining.value <= MAX_POINTS
  })

  // Get cost for increasing a specific ability score
  const getIncreaseCost = (ability: AbilityKey): number | null => {
    const currentScore = baseScores[ability]
    const nextScore = currentScore + 1

    if (nextScore > MAX_SCORE) return null

    const currentCost = POINT_BUY_COSTS[currentScore] || 0
    const nextCost = POINT_BUY_COSTS[nextScore] || 0

    return nextCost - currentCost
  }

  // Get points refunded for decreasing a specific ability score
  const getDecreaseCost = (ability: AbilityKey): number | null => {
    const currentScore = baseScores[ability]
    const prevScore = currentScore - 1

    if (prevScore < MIN_SCORE) return null

    const currentCost = POINT_BUY_COSTS[currentScore] || 0
    const prevCost = POINT_BUY_COSTS[prevScore] || 0

    return currentCost - prevCost
  }

  // Check if an ability can be increased
  const canIncrease = (ability: AbilityKey): boolean => {
    const cost = getIncreaseCost(ability)
    return cost !== null && cost <= pointsRemaining.value
  }

  // Check if an ability can be decreased
  const canDecrease = (ability: AbilityKey): boolean => {
    return baseScores[ability] > MIN_SCORE
  }

  // Increase an ability score
  const increaseAbility = (ability: AbilityKey): boolean => {
    if (canIncrease(ability)) {
      baseScores[ability]++
      return true
    }
    return false
  }

  // Decrease an ability score
  const decreaseAbility = (ability: AbilityKey): boolean => {
    if (canDecrease(ability)) {
      baseScores[ability]--
      return true
    }
    return false
  }

  // Set an ability score directly (with validation)
  const setAbilityScore = (ability: AbilityKey, score: number): boolean => {
    const clampedScore = Math.max(MIN_SCORE, Math.min(MAX_SCORE, score))
    const tempScores = { ...baseScores }
    tempScores[ability] = clampedScore

    // Calculate if this would be valid
    const tempPointsSpent = Object.values(tempScores).reduce((total, s) => {
      return total + (POINT_BUY_COSTS[s] || 0)
    }, 0)

    if (tempPointsSpent <= MAX_POINTS) {
      baseScores[ability] = clampedScore
      return true
    }
    return false
  }

  // Reset all scores to minimum
  const resetScores = (): void => {
    Object.keys(baseScores).forEach(ability => {
      baseScores[ability as AbilityKey] = MIN_SCORE
    })
  }

  // Apply standard array (15, 14, 13, 12, 10, 8)
  const applyStandardArray = (): void => {
    const standardArray = [15, 14, 13, 12, 10, 8]
    const abilities = Object.keys(baseScores) as AbilityKey[]

    standardArray.forEach((score, index) => {
      if (abilities[index]) {
        baseScores[abilities[index]] = score
      }
    })
  }

  // Get ability score names and descriptions
  const getAbilityInfo = (ability: AbilityKey): AbilityInfo => {
    const info: Record<AbilityKey, AbilityInfo> = {
      STR: { name: 'Strength', description: 'Physical power, athletics, melee attacks' },
      DEX: { name: 'Dexterity', description: 'Agility, reflexes, ranged attacks, AC' },
      CON: { name: 'Constitution', description: 'Health, stamina, hit points' },
      INT: { name: 'Intelligence', description: 'Reasoning, memory, knowledge' },
      WIS: { name: 'Wisdom', description: 'Awareness, insight, perception' },
      CHA: { name: 'Charisma', description: 'Force of personality, social skills' }
    }
    return info[ability] || { name: ability, description: '' }
  }

  // Load scores from existing character template
  const loadFromTemplate = (template: Partial<CharacterTemplateModel>): void => {
    if (template?.base_stats) {
      Object.entries(template.base_stats).forEach(([ability, score]) => {
        if (ability in baseScores && typeof score === 'number') {
          baseScores[ability as AbilityKey] = Math.max(MIN_SCORE, Math.min(MAX_SCORE, score))
        }
      })
    }
  }

  // Export scores in template format
  const exportScores = (): AbilityScores => {
    return { ...baseScores }
  }

  return {
    // State
    baseScores,

    // Computed
    pointsSpent,
    pointsRemaining,
    isValid,

    // Methods
    getIncreaseCost,
    getDecreaseCost,
    canIncrease,
    canDecrease,
    increaseAbility,
    decreaseAbility,
    setAbilityScore,
    resetScores,
    applyStandardArray,
    getAbilityInfo,
    loadFromTemplate,
    exportScores,

    // Constants
    MAX_POINTS,
    MIN_SCORE,
    MAX_SCORE
  }
}
