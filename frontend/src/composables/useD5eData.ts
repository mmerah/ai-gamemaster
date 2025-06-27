import { computed } from 'vue'
import { useCampaignStore } from '../stores/campaignStore'
import { useContentStore } from '../stores/contentStore'
import type { APIReference } from '../types/unified'

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
  const contentStore = useContentStore()

  // Computed properties for easy access
  const races = computed(() => campaignStore.d5eRaces?.races || {})
  const classes = computed(() => campaignStore.d5eClasses?.classes || {})
  const isLoading = computed(() => campaignStore.d5eDataLoading)

  // Direct access to character creation options when using content pack filtering
  const characterCreationOptions = computed(
    () => campaignStore.characterCreationOptions
  )

  // Load character creation options with content pack filtering if requested
  if (contentPackOptions) {
    campaignStore.loadCharacterCreationOptions(contentPackOptions)
  }

  // Helper functions
  const getRaceOptions = (): SelectOption[] => {
    // Use content pack filtered options if available
    if (characterCreationOptions.value?.races) {
      return characterCreationOptions.value.races.map(race => ({
        value: race.index || race.name.toLowerCase().replace(/\s+/g, '-'),
        label: race.name,
        data: race,
        source: race._source
          ? {
              content_pack_id: race._source,
              content_pack_name: contentPackOptions?.contentPackIds?.includes(
                race._source
              )
                ? contentStore.contentPacks.find(p => p.id === race._source)
                    ?.name || race._source
                : race._source,
            }
          : undefined,
      }))
    }

    // Fallback to legacy format
    return Object.entries(races.value).map(([key, race]) => ({
      value: key,
      label: race.name,
      data: race,
    }))
  }

  const getClassOptions = (): SelectOption[] => {
    // Use content pack filtered options if available
    if (characterCreationOptions.value?.classes) {
      return characterCreationOptions.value.classes.map(clazz => ({
        value: clazz.index || clazz.name.toLowerCase().replace(/\s+/g, '-'),
        label: clazz.name,
        data: clazz,
        source: clazz._source
          ? {
              content_pack_id: clazz._source,
              content_pack_name:
                contentStore.contentPacks.find(p => p.id === clazz._source)
                  ?.name || clazz._source,
            }
          : undefined,
      }))
    }

    // Fallback to legacy format
    return Object.entries(classes.value).map(([key, clazz]) => ({
      value: key,
      label: clazz.name,
      data: clazz,
    }))
  }

  const getSubraceOptions = (raceKey: string): SelectOption[] => {
    // Use content pack filtered options if available
    if (characterCreationOptions.value?.races) {
      const race = characterCreationOptions.value.races.find(
        r => r.index === raceKey
      )
      if (race?.subraces && race.subraces.length > 0) {
        // Subraces are APIReference[], convert to SelectOption[]
        return race.subraces.map(subrace => ({
          value: subrace.index,
          label: subrace.name,
        }))
      }
    }

    // Fallback to legacy races data
    const race = races.value[raceKey]
    if (!race?.subraces || !Array.isArray(race.subraces)) return []

    // Convert APIReference[] to SelectOption[]
    return race.subraces.map(subrace => ({
      value: subrace.index,
      label: subrace.name,
    }))
  }

  const getSubclassOptions = (classKey: string): SelectOption[] => {
    // Use content pack filtered options if available
    if (characterCreationOptions.value?.classes) {
      const clazz = characterCreationOptions.value.classes.find(
        c => c.index === classKey
      )
      if (clazz?.subclasses && clazz.subclasses.length > 0) {
        // Subclasses are APIReference[], convert to SelectOption[]
        return clazz.subclasses.map(subclass => ({
          value: subclass.index,
          label: subclass.name,
        }))
      }
    }

    // Fallback to legacy classes data
    const clazz = classes.value[classKey]
    if (!clazz?.subclasses || !Array.isArray(clazz.subclasses)) return []

    // Convert APIReference[] to SelectOption[]
    return clazz.subclasses.map(subclass => ({
      value: subclass.index,
      label: subclass.name,
    }))
  }

  const getBackgroundOptions = (): SelectOption[] => {
    // Use content pack filtered options if available
    if (characterCreationOptions.value?.backgrounds) {
      return characterCreationOptions.value.backgrounds.map(background => ({
        value:
          background.index ||
          background.name.toLowerCase().replace(/\s+/g, '_'),
        label: background.name,
        data: background,
        source: background._source
          ? {
              content_pack_id: background._source,
              content_pack_name:
                contentStore.contentPacks.find(p => p.id === background._source)
                  ?.name || background._source,
            }
          : undefined,
      }))
    }

    // Return empty array if no data available
    return []
  }

  const getAlignmentOptions = (): SelectOption[] => {
    // Use content pack filtered options if available
    if (characterCreationOptions.value?.alignments) {
      return characterCreationOptions.value.alignments.map(alignment => ({
        value:
          alignment.index || alignment.name.toLowerCase().replace(/\s+/g, '_'),
        label: alignment.name,
        data: alignment,
        source: alignment._source
          ? {
              content_pack_id: alignment._source,
              content_pack_name:
                contentStore.contentPacks.find(p => p.id === alignment._source)
                  ?.name || alignment._source,
            }
          : undefined,
      }))
    }

    // Return empty array if no data available
    return []
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
    if (race.ability_bonuses) {
      race.ability_bonuses.forEach(abilityBonus => {
        const ability = abilityBonus.ability_score.index
        totals[ability] = (totals[ability] || 0) + abilityBonus.bonus
      })
    }

    // Note: Subrace bonuses would require fetching detailed subrace data
    // from the API. The current implementation only has subrace references.
    // This would need to be implemented with a separate API call to get
    // subrace details including ability bonuses.
    if (subraceKey) {
      // Future implementation: fetch subrace details from API
      // const subraceDetails = await getSubraceDetails(raceKey, subraceKey)
      // Apply subrace bonuses from subraceDetails
    }

    return totals
  }

  // Calculate hit points
  const calculateHitPoints = (
    classKey: string,
    level: number,
    constitutionModifier: number
  ): number => {
    const clazz = classes.value[classKey]
    if (!clazz) return 0

    const hitDie = clazz.hit_die
    const baseHP = hitDie + constitutionModifier // First level
    const additionalHP =
      (level - 1) * (Math.floor(hitDie / 2) + 1 + constitutionModifier) // Average for additional levels

    return Math.max(1, baseHP + additionalHP) // Minimum 1 HP
  }

  // Get class proficiencies
  const getClassProficiencies = (classKey: string): ClassProficiencies => {
    const clazz = classes.value[classKey]
    if (!clazz)
      return {
        armor: [],
        weapons: [],
        tools: [],
        savingThrows: [],
        skillChoices: { count: 0, options: [] },
      }

    // Extract proficiencies by type
    const armorProfs: string[] = []
    const weaponProfs: string[] = []
    const toolProfs: string[] = []

    if (clazz.proficiencies && Array.isArray(clazz.proficiencies)) {
      clazz.proficiencies.forEach(prof => {
        const name = prof.name
        if (name.includes('Armor') || name.includes('armor')) {
          armorProfs.push(name)
        } else if (
          name.includes('Weapons') ||
          name.includes('weapons') ||
          name.includes('Simple') ||
          name.includes('Martial')
        ) {
          weaponProfs.push(name)
        } else if (
          name.includes('Tools') ||
          name.includes('tools') ||
          name.includes('kit') ||
          name.includes('supplies')
        ) {
          toolProfs.push(name)
        }
      })
    }

    // Extract skill choices
    const skillChoice = clazz.proficiency_choices?.find(
      choice =>
        choice.type === 'skills' ||
        (choice.from_?.options as APIReference[] | undefined)?.some(opt =>
          opt.index?.startsWith('skill-')
        )
    )

    return {
      armor: armorProfs,
      weapons: weaponProfs,
      tools: toolProfs,
      savingThrows: clazz.saving_throws.map(st => st.name),
      skillChoices: {
        count: skillChoice?.choose || 0,
        options:
          (skillChoice?.from_?.options as APIReference[] | undefined)?.map(
            opt => opt.name
          ) || [],
      },
    }
  }

  // Get racial traits and proficiencies
  const getRacialTraits = (
    raceKey: string,
    _subraceKey?: string
  ): RacialTraits => {
    const race = races.value[raceKey]
    if (!race) return { traits: [], proficiencies: {}, languages: [] }

    const traits = race.traits.map(t => t.name)
    const proficiencies: Record<string, string[]> = {
      skills: race.starting_proficiencies.map(p => p.name),
    }
    const languages = race.languages.map(l => l.name)

    // Note: Subrace traits would require fetching detailed subrace data
    // which needs a separate API call. This is tracked in Task 5.5 of the refactor plan.
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
      CHA: { name: 'Charisma', description: 'Force of personality' },
    }

    return (
      abilityData[abilityKey] || {
        name: abilityKey,
        description: 'Unknown ability',
      }
    )
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
    getAbilityInfo,
  }
}
