/**
 * Content-related types for the frontend
 */

// Content pack types
export interface ContentPack {
  id: string
  name: string
  description: string | null
  version: string
  author: string | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface ContentPackCreate {
  id: string
  name: string
  description?: string
  version: string
  author?: string
}

export interface ContentPackUpdate {
  name?: string
  description?: string
  version?: string
  author?: string
  is_active?: boolean
}

export interface ContentPackWithStats extends ContentPack {
  statistics: Record<string, number>
  total_items: number
}

// Content upload types
export interface ContentUploadResult {
  pack_id: string
  content_type: string
  total_items: number
  successful_items: number
  failed_items: number
  validation_errors: Record<string, string>
  warnings: string[]
}

// Content types enum (using hyphenated names to match backend)
export type ContentType = 
  | 'ability-scores'
  | 'alignments'
  | 'backgrounds'
  | 'classes'
  | 'conditions'
  | 'damage-types'
  | 'equipment'
  | 'equipment-categories'
  | 'feats'
  | 'features'
  | 'languages'
  | 'levels'
  | 'magic-items'
  | 'magic-schools'
  | 'monsters'
  | 'proficiencies'
  | 'races'
  | 'rules'
  | 'rule-sections'
  | 'skills'
  | 'spells'
  | 'subclasses'
  | 'subraces'
  | 'traits'
  | 'weapon-properties'

// Export all content types
export const CONTENT_TYPES: ContentType[] = [
  'ability-scores',
  'alignments',
  'backgrounds',
  'classes',
  'conditions',
  'damage-types',
  'equipment',
  'equipment-categories',
  'feats',
  'features',
  'languages',
  'levels',
  'magic-items',
  'magic-schools',
  'monsters',
  'proficiencies',
  'races',
  'rules',
  'rule-sections',
  'skills',
  'spells',
  'subclasses',
  'subraces',
  'traits',
  'weapon-properties'
]