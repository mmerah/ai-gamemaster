import type { D5eRace, D5eClass } from '@/types/unified'

// Type-safe helper functions for D&D 5e data access

export type D5eRaceMap = Record<string, D5eRace>
export type D5eClassMap = Record<string, D5eClass>

/**
 * Safely get a race by its index
 */
export function getRaceByIndex(races: D5eRaceMap, index: string): D5eRace | undefined {
  return races[index]
}

/**
 * Safely get a class by its index
 */
export function getClassByIndex(classes: D5eClassMap, index: string): D5eClass | undefined {
  return classes[index]
}

/**
 * Convert an array of races to a map indexed by their 'index' property
 */
export function racesToMap(races: D5eRace[]): D5eRaceMap {
  const map: D5eRaceMap = {}
  races.forEach(race => {
    const key = race.index || race.name.toLowerCase().replace(/\s+/g, '-')
    map[key] = race
  })
  return map
}

/**
 * Convert an array of classes to a map indexed by their 'index' property
 */
export function classesToMap(classes: D5eClass[]): D5eClassMap {
  const map: D5eClassMap = {}
  classes.forEach(cls => {
    const key = cls.index || cls.name.toLowerCase().replace(/\s+/g, '-')
    map[key] = cls
  })
  return map
}

/**
 * Get all race indices from a race map
 */
export function getRaceIndices(races: D5eRaceMap): string[] {
  return Object.keys(races)
}

/**
 * Get all class indices from a class map
 */
export function getClassIndices(classes: D5eClassMap): string[] {
  return Object.keys(classes)
}