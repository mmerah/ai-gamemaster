import { computed } from 'vue'
import { useCampaignStore } from '../stores/campaignStore'

export function useD5eData() {
  const campaignStore = useCampaignStore()

  // Computed properties for easy access
  const races = computed(() => campaignStore.d5eRaces?.races || {})
  const classes = computed(() => campaignStore.d5eClasses?.classes || {})
  const isLoading = computed(() => campaignStore.d5eDataLoading)

  // Helper functions
  const getRaceOptions = () => {
    return Object.entries(races.value).map(([key, race]) => ({
      value: key,
      label: race.name,
      data: race
    }))
  }

  const getClassOptions = () => {
    return Object.entries(classes.value).map(([key, clazz]) => ({
      value: key,
      label: clazz.name,
      data: clazz
    }))
  }

  const getSubraceOptions = (raceKey) => {
    const race = races.value[raceKey]
    if (!race?.subraces) return []
    
    return Object.entries(race.subraces).map(([key, subrace]) => ({
      value: key,
      label: subrace.name,
      data: subrace
    }))
  }

  const getSubclassOptions = (classKey) => {
    const clazz = classes.value[classKey]
    if (!clazz?.subclasses) return []
    
    return Object.entries(clazz.subclasses).map(([key, subclass]) => ({
      value: key,
      label: subclass.name,
      data: subclass
    }))
  }

  const getBackgroundOptions = () => {
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

  const getAlignmentOptions = () => {
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
  const getAbilityModifier = (score) => {
    return Math.floor((score - 10) / 2)
  }

  const getProficiencyBonus = (level) => {
    return Math.ceil(level / 4) + 1
  }

  // Calculate total ability scores with racial bonuses
  const calculateTotalAbilityScores = (baseScores, raceKey, subraceKey) => {
    const race = races.value[raceKey]
    if (!race) return baseScores

    const totals = { ...baseScores }
    
    // Apply racial bonuses
    if (race.ability_score_increase) {
      Object.entries(race.ability_score_increase).forEach(([ability, bonus]) => {
        totals[ability] = (totals[ability] || 0) + bonus
      })
    }

    // Apply subrace bonuses
    if (subraceKey && race.subraces?.[subraceKey]?.ability_score_increase) {
      Object.entries(race.subraces[subraceKey].ability_score_increase).forEach(([ability, bonus]) => {
        totals[ability] = (totals[ability] || 0) + bonus
      })
    }

    return totals
  }

  // Calculate hit points
  const calculateHitPoints = (classKey, level, constitutionModifier) => {
    const clazz = classes.value[classKey]
    if (!clazz) return 0

    const hitDie = clazz.hit_die
    const baseHP = hitDie + constitutionModifier // First level
    const additionalHP = (level - 1) * (Math.floor(hitDie / 2) + 1 + constitutionModifier) // Average for additional levels
    
    return Math.max(1, baseHP + additionalHP) // Minimum 1 HP
  }

  // Get class proficiencies
  const getClassProficiencies = (classKey) => {
    const clazz = classes.value[classKey]
    if (!clazz) return {}

    return {
      armor: clazz.armor_proficiencies || [],
      weapons: clazz.weapon_proficiencies || [],
      tools: clazz.tool_proficiencies || [],
      savingThrows: clazz.saving_throw_proficiencies || [],
      skillChoices: clazz.skill_choices || { count: 0, options: [] }
    }
  }

  // Get racial traits and proficiencies
  const getRacialTraits = (raceKey, subraceKey) => {
    const race = races.value[raceKey]
    if (!race) return { traits: [], proficiencies: {}, languages: [] }

    let traits = [...(race.traits || [])]
    let proficiencies = { ...(race.proficiencies || {}) }
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
    getRacialTraits
  }
}
