import { apiClient } from './apiClient'
import type {
  D5eRace,
  D5eClass,
  D5eBackground,
  D5eSpell,
  D5eMonster,
  D5eFeature,
  D5eSubrace,
  D5eSubclass,
} from '@/types/unified'

// Union type for all D5E entities
export type D5eEntity =
  | D5eRace
  | D5eClass
  | D5eBackground
  | D5eSpell
  | D5eMonster
  | D5eFeature
  | D5eSubrace
  | D5eSubclass

/**
 * API service for D&D 5e content operations.
 * Provides methods for fetching D5E data with content pack support.
 */

// Generic function to get any D5E item by type and ID
export async function getD5eItem(
  contentType: string,
  itemId: string,
  contentPackIds?: string[]
): Promise<D5eEntity> {
  const params = new URLSearchParams()
  if (contentPackIds && contentPackIds.length > 0) {
    params.append('content_pack_ids', contentPackIds.join(','))
  }

  const queryString = params.toString()
  const url = `/api/d5e/content/${contentType}/${itemId}${
    queryString ? `?${queryString}` : ''
  }`

  const response = await apiClient.get<D5eEntity>(url)
  return response.data
}

// Type-specific convenience methods
export async function getRaceById(
  raceId: string,
  contentPackIds?: string[]
): Promise<D5eRace> {
  return (await getD5eItem('races', raceId, contentPackIds)) as D5eRace
}

export async function getClassById(
  classId: string,
  contentPackIds?: string[]
): Promise<D5eClass> {
  return (await getD5eItem('classes', classId, contentPackIds)) as D5eClass
}

export async function getBackgroundById(
  backgroundId: string,
  contentPackIds?: string[]
): Promise<D5eBackground> {
  return (await getD5eItem(
    'backgrounds',
    backgroundId,
    contentPackIds
  )) as D5eBackground
}

export async function getSpellById(
  spellId: string,
  contentPackIds?: string[]
): Promise<D5eSpell> {
  return (await getD5eItem('spells', spellId, contentPackIds)) as D5eSpell
}

export async function getMonsterById(
  monsterId: string,
  contentPackIds?: string[]
): Promise<D5eMonster> {
  return (await getD5eItem('monsters', monsterId, contentPackIds)) as D5eMonster
}

export async function getFeatureById(
  featureId: string,
  contentPackIds?: string[]
): Promise<D5eFeature> {
  return (await getD5eItem('features', featureId, contentPackIds)) as D5eFeature
}

export async function getSubraceById(
  subraceId: string,
  contentPackIds?: string[]
): Promise<D5eSubrace> {
  return (await getD5eItem('subraces', subraceId, contentPackIds)) as D5eSubrace
}

export async function getSubclassById(
  subclassId: string,
  contentPackIds?: string[]
): Promise<D5eSubclass> {
  return (await getD5eItem(
    'subclasses',
    subclassId,
    contentPackIds
  )) as D5eSubclass
}

// Batch fetch methods for multiple items
export async function getRacesByIds(
  raceIds: string[],
  contentPackIds?: string[]
): Promise<D5eRace[]> {
  return Promise.all(raceIds.map(id => getRaceById(id, contentPackIds)))
}

export async function getClassesByIds(
  classIds: string[],
  contentPackIds?: string[]
): Promise<D5eClass[]> {
  return Promise.all(classIds.map(id => getClassById(id, contentPackIds)))
}

export async function getBackgroundsByIds(
  backgroundIds: string[],
  contentPackIds?: string[]
): Promise<D5eBackground[]> {
  return Promise.all(
    backgroundIds.map(id => getBackgroundById(id, contentPackIds))
  )
}

export async function getSubracesByIds(
  subraceIds: string[],
  contentPackIds?: string[]
): Promise<D5eSubrace[]> {
  return Promise.all(subraceIds.map(id => getSubraceById(id, contentPackIds)))
}

export async function getSubclassesByIds(
  subclassIds: string[],
  contentPackIds?: string[]
): Promise<D5eSubclass[]> {
  return Promise.all(subclassIds.map(id => getSubclassById(id, contentPackIds)))
}

// Get filtered content (existing endpoint)
export async function getD5eContent<T extends D5eEntity>(
  contentType: string,
  filters?: Record<string, string | number>,
  contentPackIds?: string[]
): Promise<T[]> {
  const params = new URLSearchParams()
  params.append('type', contentType)

  if (contentPackIds && contentPackIds.length > 0) {
    params.append('content_pack_ids', contentPackIds.join(','))
  }

  if (filters) {
    Object.entries(filters).forEach(([key, value]) => {
      params.append(key, String(value))
    })
  }

  const response = await apiClient.get<T[]>(`/api/d5e/content?${params}`)
  return response.data
}

// Specialized content fetching methods
export async function getSpellsForClass(
  className: string,
  spellLevel?: number,
  contentPackIds?: string[]
): Promise<D5eSpell[]> {
  const filters: Record<string, string | number> = {
    class_name: className,
  }
  if (spellLevel !== undefined) {
    filters.level = spellLevel
  }

  return getD5eContent<D5eSpell>('spells', filters, contentPackIds)
}

export async function getCantripsForClass(
  className: string,
  contentPackIds?: string[]
): Promise<D5eSpell[]> {
  return getSpellsForClass(className, 0, contentPackIds)
}

export async function getFirstLevelSpellsForClass(
  className: string,
  contentPackIds?: string[]
): Promise<D5eSpell[]> {
  return getSpellsForClass(className, 1, contentPackIds)
}

// Get subraces for a specific race
export async function getSubracesForRace(
  race: D5eRace,
  contentPackIds?: string[]
): Promise<D5eSubrace[]> {
  if (!race.subraces || race.subraces.length === 0) {
    return []
  }

  const subraceIds = race.subraces.map(ref => ref.index)
  return getSubracesByIds(subraceIds, contentPackIds)
}

// Get subclasses for a specific class
export async function getSubclassesForClass(
  clazz: D5eClass,
  contentPackIds?: string[]
): Promise<D5eSubclass[]> {
  if (!clazz.subclasses || clazz.subclasses.length === 0) {
    return []
  }

  const subclassIds = clazz.subclasses.map(ref => ref.index)
  return getSubclassesByIds(subclassIds, contentPackIds)
}
