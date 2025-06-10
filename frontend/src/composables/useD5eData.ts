import { computed } from 'vue'
import { useCampaignStore } from '../stores/campaignStore'

// Types
interface SelectOption<T = any> {
  value: string
  label: string
  data?: T
}

interface AbilityScores {
  [key: string]: number
}

interface ClassProficiencies {
  armor: string[]
  weapons: string[]
  tools: string[]
  savingThrows: string[]
  skillChoices: {
    count: number
    options: string[]
  }
}

interface RacialTraits {
  traits: string[]
  proficiencies: Record<string, string[]>
  languages: string[]
}

interface AbilityInfo {
  name: string
  description: string
}

export function useD5eData() {
  const campaignStore = useCampaignStore()

  // Computed properties for easy access
  const races = computed(() => campaignStore.d5eRaces?.races || {})
  const classes = computed(() => campaignStore.d5eClasses?.classes || {})
  const isLoading = computed(() => campaignStore.d5eDataLoading)

  // Helper functions
  const getRaceOptions = (): SelectOption[] => {
    return Object.entries(races.value).map(([key, race]: [string, any]) => ({
      value: key,
      label: race.name,
      data: race
    }))
  }

  const getClassOptions = (): SelectOption[] => {
    return Object.entries(classes.value).map(([key, clazz]: [string, any]) => ({
      value: key,
      label: clazz.name,
      data: clazz
    }))
  }

  const getSubraceOptions = (raceKey: string): SelectOption[] => {
    const race = races.value[raceKey]
    if (!race?.subraces) return []

    return Object.entries(race.subraces).map(([key, subrace]: [string, any]) => ({
      value: key,
      label: subrace.name,
      data: subrace
    }))
  }

  const getSubclassOptions = (classKey: string): SelectOption[] => {
    const clazz = classes.value[classKey]
    if (!clazz?.subclasses) return []

    return Object.entries(clazz.subclasses).map(([key, subclass]: [string, any]) => ({
      value: key,
      label: subclass.name,
      data: subclass
    }))
  }

  const getBackgroundOptions = (): SelectOption[] => {
    // Standard D&D 5e backgrounds
    return [
      { value: 'acolyte', label: 'Acolyte' },
      { value: 'criminal', label: 'Criminal' },
      { value: 'folk_hero', label: 'Folk Hero' },
      { value: 'noble', label: 'Noble' },
      { value: 'sage', label: 'Sage' },
      { value: 'soldier', label: 'Soldier' },
      { value: 'charlatan', label: 'Charlatan' },
      { value: 'entertainer', label: 'Entertainer' },
      { value: 'guild_artisan', label: 'Guild Artisan' },
      { value: 'hermit', label: 'Hermit' },
      { value: 'outlander', label: 'Outlander' },
      { value: 'sailor', label: 'Sailor' }
    ]
  }

  const getAlignmentOptions = (): SelectOption[] => {
    return [
      { value: 'lawful_good', label: 'Lawful Good' },
      { value: 'neutral_good', label: 'Neutral Good' },
      { value: 'chaotic_good', label: 'Chaotic Good' },
      { value: 'lawful_neutral', label: 'Lawful Neutral' },
      { value: 'true_neutral', label: 'True Neutral' },
      { value: 'chaotic_neutral', label: 'Chaotic Neutral' },
      { value: 'lawful_evil', label: 'Lawful Evil' },
      { value: 'neutral_evil', label: 'Neutral Evil' },
      { value: 'chaotic_evil', label: 'Chaotic Evil' }
    ]
  }

  // Calculate character modifiers
  const getAbilityModifier = (score: number): number => {
    return Math.floor((score - 10) / 2)
  }

  const getProficiencyBonus = (level: number): number => {
    return Math.ceil(level / 4) + 1
  }

  // Calculate total ability scores with racial bonuses
  const calculateTotalAbilityScores = (
    baseScores: AbilityScores,
    raceKey: string,
    subraceKey?: string
  ): AbilityScores => {
    const race = races.value[raceKey]
    if (!race) return baseScores

    const totals = { ...baseScores }

    // Apply racial bonuses
    if (race.ability_score_increase) {
      Object.entries(race.ability_score_increase).forEach(([ability, bonus]: [string, any]) => {
        totals[ability] = (totals[ability] || 0) + bonus
      })
    }

    // Apply subrace bonuses
    if (subraceKey && race.subraces?.[subraceKey]?.ability_score_increase) {
      Object.entries(race.subraces[subraceKey].ability_score_increase).forEach(([ability, bonus]: [string, any]) => {
        totals[ability] = (totals[ability] || 0) + bonus
      })
    }

    return totals
  }

  // Calculate hit points
  const calculateHitPoints = (classKey: string, level: number, constitutionModifier: number): number => {
    const clazz = classes.value[classKey]
    if (!clazz) return 0

    const hitDie = clazz.hit_die
    const baseHP = hitDie + constitutionModifier // First level
    const additionalHP = (level - 1) * (Math.floor(hitDie / 2) + 1 + constitutionModifier) // Average for additional levels

    return Math.max(1, baseHP + additionalHP) // Minimum 1 HP
  }

  // Get class proficiencies
  const getClassProficiencies = (classKey: string): ClassProficiencies => {
    const clazz = classes.value[classKey]
    if (!clazz) return {
      armor: [],
      weapons: [],
      tools: [],
      savingThrows: [],
      skillChoices: { count: 0, options: [] }
    }

    return {
      armor: clazz.armor_proficiencies || [],
      weapons: clazz.weapon_proficiencies || [],
      tools: clazz.tool_proficiencies || [],
      savingThrows: clazz.saving_throw_proficiencies || [],
      skillChoices: clazz.skill_choices || { count: 0, options: [] }
    }
  }

  // Get racial traits and proficiencies
  const getRacialTraits = (raceKey: string, subraceKey?: string): RacialTraits => {
    const race = races.value[raceKey]
    if (!race) return { traits: [], proficiencies: {}, languages: [] }

    let traits = [...(race.traits || [])]
    let proficiencies: Record<string, string[]> = { ...(race.proficiencies || {}) }
    let languages = [...(race.languages || [])]

    // Add subrace traits
    if (subraceKey && race.subraces?.[subraceKey]) {
      const subrace = race.subraces[subraceKey]
      traits = [...traits, ...(subrace.traits || [])]

      if (subrace.proficiencies) {
        Object.keys(subrace.proficiencies).forEach(key => {
          proficiencies[key] = [...(proficiencies[key] || []), ...(subrace.proficiencies[key] || [])]
        })
      }

      if (subrace.languages) {
        languages = [...languages, ...subrace.languages]
      }
    }

    return { traits, proficiencies, languages }
  }

  // Get ability score information
  const getAbilityInfo = (abilityKey: string): AbilityInfo => {
    const abilityData: Record<string, AbilityInfo> = {
      STR: { name: 'Strength', description: 'Physical power' },
      DEX: { name: 'Dexterity', description: 'Agility and reflexes' },
      CON: { name: 'Constitution', description: 'Health and stamina' },
      INT: { name: 'Intelligence', description: 'Reasoning and memory' },
      WIS: { name: 'Wisdom', description: 'Awareness and insight' },
      CHA: { name: 'Charisma', description: 'Force of personality' }
    }

    return abilityData[abilityKey] || { name: abilityKey, description: 'Unknown ability' }
  }

  return {
    // State
    races,
    classes,
    isLoading,

    // Options
    getRaceOptions,
    getClassOptions,
    getSubraceOptions,
    getSubclassOptions,
    getBackgroundOptions,
    getAlignmentOptions,

    // Calculations
    getAbilityModifier,
    getProficiencyBonus,
    calculateTotalAbilityScores,
    calculateHitPoints,
    getClassProficiencies,
    getRacialTraits,
    getAbilityInfo
  }
}
