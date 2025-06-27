/**
 * Character creation constants
 */

// Default ability scores for new characters
export const DEFAULT_ABILITY_SCORES = {
  strength: 10,
  dexterity: 10,
  constitution: 10,
  intelligence: 10,
  wisdom: 10,
  charisma: 10,
} as const

// Ability score constraints
export const ABILITY_SCORE_MIN = 3
export const ABILITY_SCORE_MAX = 20
export const POINT_BUY_MIN = 8
export const POINT_BUY_MAX = 15
export const POINT_BUY_TOTAL = 27

// Point buy costs for each score
export const POINT_BUY_COSTS: Record<number, number> = {
  8: 0,
  9: 1,
  10: 2,
  11: 3,
  12: 4,
  13: 5,
  14: 7,
  15: 9,
}

// Standard array values
export const STANDARD_ARRAY = [15, 14, 13, 12, 10, 8] as const

// Ability definitions
export const ABILITIES = [
  { key: 'strength', name: 'Strength', abbr: 'STR' },
  { key: 'dexterity', name: 'Dexterity', abbr: 'DEX' },
  { key: 'constitution', name: 'Constitution', abbr: 'CON' },
  { key: 'intelligence', name: 'Intelligence', abbr: 'INT' },
  { key: 'wisdom', name: 'Wisdom', abbr: 'WIS' },
  { key: 'charisma', name: 'Charisma', abbr: 'CHA' },
] as const

// Alignment options
export const ALIGNMENTS = [
  { value: 'lawful_good', label: 'Lawful Good' },
  { value: 'neutral_good', label: 'Neutral Good' },
  { value: 'chaotic_good', label: 'Chaotic Good' },
  { value: 'lawful_neutral', label: 'Lawful Neutral' },
  { value: 'true_neutral', label: 'True Neutral' },
  { value: 'chaotic_neutral', label: 'Chaotic Neutral' },
  { value: 'lawful_evil', label: 'Lawful Evil' },
  { value: 'neutral_evil', label: 'Neutral Evil' },
  { value: 'chaotic_evil', label: 'Chaotic Evil' },
] as const

// Character level constraints
export const MIN_LEVEL = 1
export const MAX_LEVEL = 20

// Expertise constants for classes that get it
export const EXPERTISE_CLASSES = ['rogue', 'bard'] as const
export const EXPERTISE_CHOICES_AT_LEVEL_1 = 2
