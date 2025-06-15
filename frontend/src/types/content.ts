// Content Pack TypeScript interfaces
// These correspond to the backend Pydantic models in app/content/schemas/content_pack.py

export interface ContentPack {
  id: string
  name: string
  description?: string
  version: string
  author?: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface ContentPackCreate {
  name: string
  description?: string
  version?: string
  author?: string
  is_active?: boolean
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
}

export interface ContentUploadResult {
  content_type: string
  total_items: number
  successful_items: number
  failed_items: number
  validation_errors: Record<string, string>
  warnings: string[]
}

// Content types supported by the backend
export const CONTENT_TYPES = [
  'spells',
  'monsters',
  'equipment',
  'classes',
  'races',
  'backgrounds',
  'feats',
  'features',
  'magic_items',
  'conditions',
  'damage_types',
  'languages',
  'proficiencies',
  'properties',
  'schools',
  'skills',
  'subclasses',
  'subraces',
  'traits',
  'weapon_categories',
  'armor_categories',
  'gear_categories',
  'tool_categories',
  'vehicle_categories',
  'equipment_packs'
] as const

export type ContentType = typeof CONTENT_TYPES[number]