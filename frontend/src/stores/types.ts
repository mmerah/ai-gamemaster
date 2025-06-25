/**
 * Typed store references to fix TypeScript inference issues
 * 
 * This file exports properly typed store instances to avoid
 * the need for type casting when accessing store methods
 */

import type { useGameStore } from './gameStore'
import type { useCombatStore } from './combatStore'
import type { useDiceStore } from './diceStore'
import type { useUiStore } from './uiStore'
import type { usePartyStore } from './partyStore'
import type { useChatStore } from './chatStore'
import type { useCampaignStore } from './campaignStore'
import type { useCampaignTemplateStore } from './campaignTemplateStore'
import type { useConfigStore } from './configStore'
import type { useContentStore } from './contentStore'

// Export typed store instances
export type GameStoreType = ReturnType<typeof useGameStore>
export type CombatStoreType = ReturnType<typeof useCombatStore>
export type DiceStoreType = ReturnType<typeof useDiceStore>
export type UiStoreType = ReturnType<typeof useUiStore>
export type PartyStoreType = ReturnType<typeof usePartyStore>
export type ChatStoreType = ReturnType<typeof useChatStore>
export type CampaignStoreType = ReturnType<typeof useCampaignStore>
export type CampaignTemplateStoreType = ReturnType<typeof useCampaignTemplateStore>
export type ConfigStoreType = ReturnType<typeof useConfigStore>
export type ContentStoreType = ReturnType<typeof useContentStore>

// Store collection interface with proper typing
export interface Stores {
  game: GameStoreType
  combat: CombatStoreType
  dice: DiceStoreType
  ui: UiStoreType
  party: PartyStoreType
  chat: ChatStoreType
  campaign?: CampaignStoreType
  campaignTemplate?: CampaignTemplateStoreType
  config?: ConfigStoreType
  content?: ContentStoreType
}