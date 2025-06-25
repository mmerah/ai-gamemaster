import { computed } from 'vue'
import { useCampaignStore } from '../stores/campaignStore'

// Types
interface SelectOption<T = unknown> {
  value: string
  label: string
  data?: T
  source?: {
    content_pack_id: string
    content_pack_name: string
  }
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

export function useD5eData(contentPackOptions?: {
  contentPackIds?: string[]
  campaignId?: string
}) {
  const campaignStore = useCampaignStore()

  // Computed properties for easy access
  const races = computed(() => campaignStore.d5eRaces?.races || {})
  const classes = computed(() => campaignStore.d5eClasses?.classes || {})
  const isLoading = computed(() => campaignStore.d5eDataLoading)
  
  // Direct access to character creation options when using content pack filtering
  const characterCreationOptions = computed(() => campaignStore.characterCreationOptions)
  
  // Load character creation options with content pack filtering if requested
  if (contentPackOptions) {
    campaignStore.loadCharacterCreationOptions(contentPackOptions)
  }

  // Helper functions
  const getRaceOptions = (): SelectOption[] => {
    // Use content pack filtered options if available
    if (characterCreationOptions.value?.races) {
      return characterCreationOptions.value.races.map((race) => ({
        value: race.index || race.name.toLowerCase().replace(/\s+/g, '-'),
        label: race.name,
        data: race,
        source: undefined // TODO: Add _source to D5eRace type when available
      }))
    }
    
    // Fallback to legacy format
    return Object.entries(races.value).map(([key, race]) => ({
      value: key,
      label: race.name,
      data: race
    }))
  }

  const getClassOptions = (): SelectOption[] => {
    // Use content pack filtered options if available
    if (characterCreationOptions.value?.classes) {
      return characterCreationOptions.value.classes.map((clazz) => ({
        value: clazz.index || clazz.name.toLowerCase().replace(/\s+/g, '-'),
        label: clazz.name,
        data: clazz,
        source: undefined // TODO: Add _source to D5eClass type when available
      }))
    }
    
    // Fallback to legacy format
    return Object.entries(classes.value).map(([key, clazz]) => ({
      value: key,
      label: clazz.name,
      data: clazz
    }))
  }

  const getSubraceOptions = (raceKey: string): SelectOption[] => {
    const race = races.value[raceKey]
    if (!race?.subraces) return []

    // TODO: The current D5eRace type has subraces as APIReference[], not an object
    // This function needs to be refactored when subrace data is properly loaded
    // For now, return empty array
    return []
  }

  const getSubclassOptions = (classKey: string): SelectOption[] => {
    const clazz = classes.value[classKey]
    if (!clazz?.subclasses) return []

    // TODO: The current D5eClass type has subclasses as APIReference[], not an object
    // This function needs to be refactored when subclass data is properly loaded
    // For now, return empty array
    return []
  }

  const getBackgroundOptions = (): SelectOption[] => {
    // Use content pack filtered options if available
    if (characterCreationOptions.value?.backgrounds) {
      return characterCreationOptions.value.backgrounds.map((background) => ({
        value: background.index || background.name.toLowerCase().replace(/\s+/g, '_'),
        label: background.name,
        data: background,
        source: undefined // TODO: Add _source to D5eBackground type when available
      }))
    }
    
    // Fallback to hardcoded backgrounds
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
    // Use content pack filtered options if available
    if (characterCreationOptions.value?.alignments) {
      return characterCreationOptions.value.alignments.map((alignment) => ({
        value: alignment.index || alignment.name.toLowerCase().replace(/\s+/g, '_'),
        label: alignment.name,
        data: alignment,
        source: undefined // TODO: Add _source to D5eAlignment type when available
      }))
    }
    
    // Fallback to hardcoded alignments
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
    _subraceKey?: string  // TODO: Use when subrace data is available
  ): AbilityScores => {
    const race = races.value[raceKey]
    if (!race) return baseScores

    const totals = { ...baseScores }

    // Apply racial bonuses
    if (race.ability_bonuses) {
      race.ability_bonuses.forEach((abilityBonus) => {
        const ability = abilityBonus.ability_score.index
        totals[ability] = (totals[ability] || 0) + abilityBonus.bonus
      })
    }

    // Apply subrace bonuses
    // TODO: The current D5eRace type has subraces as APIReference[], not an object
    // This needs to be refactored when subrace data structure is updated
    // For now, we'll skip subrace bonuses
    /*
    if (subraceKey && race.subraces?.[subraceKey]?.ability_score_increase) {
      Object.entries(race.subraces[subraceKey].ability_score_increase).forEach(([ability, bonus]: [string, any]) => {
        totals[ability] = (totals[ability] || 0) + bonus
      })
    }
    */

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
      armor: [], // TODO: Extract armor proficiencies from clazz.proficiencies
      weapons: [], // TODO: Extract weapon proficiencies from clazz.proficiencies
      tools: [], // TODO: Extract tool proficiencies from clazz.proficiencies
      savingThrows: clazz.saving_throws.map(st => st.name),
      skillChoices: { 
        count: clazz.proficiency_choices?.[0]?.choose || 0,
        options: [] // TODO: Extract options from clazz.proficiency_choices when the structure is clarified
      }
    }
  }

  // Get racial traits and proficiencies
  const getRacialTraits = (raceKey: string, _subraceKey?: string): RacialTraits => {  // TODO: Use when subrace data is available
    const race = races.value[raceKey]
    if (!race) return { traits: [], proficiencies: {}, languages: [] }

    const traits = race.traits.map(t => t.name)
    const proficiencies: Record<string, string[]> = {
      skills: race.starting_proficiencies.map(p => p.name)
    }
    const languages = race.languages.map(l => l.name)

    // TODO: Add subrace traits when subrace data structure is updated
    // Currently subraces are APIReference[], not detailed objects

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
    characterCreationOptions,

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
