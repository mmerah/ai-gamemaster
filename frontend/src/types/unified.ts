// Generated TypeScript interfaces from Pydantic models
// DO NOT EDIT - This file is auto-generated
// Generated at: 2025-06-08T15:25:21.430163

export interface ItemModel {
  id: string;
  name: string;
  description: string;
  quantity: number;
}

export interface NPCModel {
  id: string;
  name: string;
  description: string;
  last_location: string;
}

export interface QuestModel {
  id: string;
  title: string;
  description: string;
  status: string;
}

export interface LocationModel {
  name: string;
  description: string;
}

export interface HouseRulesModel {
  critical_hit_tables: boolean;
  flanking_rules: boolean;
  milestone_leveling: boolean;
  death_saves_public: boolean;
}

export interface GoldRangeModel {
  min: number;
  max: number;
}

export interface BaseStatsModel {
  STR: number;
  DEX: number;
  CON: number;
  INT: number;
  WIS: number;
  CHA: number;
}

export interface ProficienciesModel {
  armor: string[];
  weapons: string[];
  tools: string[];
  saving_throws: string[];
  skills: string[];
}

export interface TraitModel {
  name: string;
  description: string;
}

export interface ClassFeatureModel {
  name: string;
  description: string;
  level_acquired: number;
}

export interface ChatMessageModel {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: string;
  is_dice_result: boolean;
  gm_thought?: string;
  ai_response_json?: string;
  detailed_content?: string;
  audio_path?: string;
}

export interface DiceRequestModel {
  request_id: string;
  character_ids: string[];
  type: string;
  dice_formula: string;
  reason: string;
  skill?: string;
  ability?: string;
  dc?: number;
}

export interface DiceRollResultModel {
  character_id: string;
  roll_type: string;
  total: number;
  result_summary: string;
  result_message?: string;
  skill?: string;
  ability?: string;
  dc?: number;
  reason?: string;
  original_request_id?: string;
}

export interface InitialCombatantData {
  id: string;
  name: string;
  hp: number;
  ac: number;
  stats?: Record<string, number>;
  abilities?: string[];
  attacks?: Record<string, any>[];
  icon_path?: string;
}

export interface LocationUpdateModel {
  name: string;
  description: string;
}

export interface HPChangeUpdateModel {
  character_id: string;
  value: number;
  attacker?: string;
  weapon?: string;
  damage_type?: string;
  critical?: boolean;
  source?: string;
  reason?: string;
  description?: string;
}

export interface ConditionAddUpdateModel {
  character_id: string;
  value: string;
  duration?: string;
  save_dc?: number;
  save_type?: string;
  source?: string;
  reason?: string;
  description?: string;
}

export interface ConditionRemoveUpdateModel {
  character_id: string;
  value: string;
}

export interface InventoryAddUpdateModel {
  character_id: string;
  value: string | ItemModel;
  quantity?: number;
  item_value?: number;
  rarity?: string;
  source?: string;
  reason?: string;
  description?: string;
}

export interface InventoryRemoveUpdateModel {
  character_id: string;
  value: string;
}

export interface GoldUpdateModel {
  character_id: string;
  value: number;
  source?: string;
  reason?: string;
  description?: string;
}

export interface QuestUpdateModel {
  quest_id: string;
  status?: "active" | "completed" | "failed";
  objectives_completed?: number;
  objectives_total?: number;
  rewards_experience?: number;
  rewards_gold?: number;
  rewards_items?: string[];
  rewards_reputation?: string;
  source?: string;
  reason?: string;
  description?: string;
}

export interface CombatStartUpdateModel {
  combatants: InitialCombatantData[];
  source?: string;
  reason?: string;
  description?: string;
}

export interface CombatEndUpdateModel {
  source?: string;
  reason?: string;
  description?: string;
}

export interface CombatantRemoveUpdateModel {
  character_id: string;
  source?: string;
  reason?: string;
  description?: string;
}

export interface CharacterTemplateModel {
  version: number;
  id: string;
  name: string;
  race: string;
  subrace?: string;
  char_class: string;
  subclass?: string;
  level: number;
  background: string;
  alignment: string;
  base_stats: BaseStatsModel;
  proficiencies: ProficienciesModel;
  languages: string[];
  racial_traits: TraitModel[];
  class_features: ClassFeatureModel[];
  feats: TraitModel[];
  spells_known: string[];
  cantrips_known: string[];
  starting_equipment: ItemModel[];
  starting_gold: number;
  portrait_path?: string;
  personality_traits: string[];
  ideals: string[];
  bonds: string[];
  flaws: string[];
  appearance?: string;
  backstory?: string;
  created_date?: string;
  last_modified?: string;
}

export interface CampaignTemplateModel {
  version: number;
  id: string;
  name: string;
  description: string;
  campaign_goal: string;
  starting_location: LocationModel;
  opening_narrative: string;
  starting_level: number;
  difficulty: string;
  ruleset_id: string;
  lore_id: string;
  initial_npcs: Record<string, NPCModel>;
  initial_quests: Record<string, QuestModel>;
  world_lore: string[];
  house_rules: HouseRulesModel;
  allowed_races?: string[];
  allowed_classes?: string[];
  starting_gold_range?: GoldRangeModel;
  theme_mood?: string;
  world_map_path?: string;
  session_zero_notes?: string;
  xp_system: string;
  narration_enabled: boolean;
  tts_voice: string;
  created_date: string;
  last_modified: string;
  tags: string[];
}

export interface CharacterInstanceModel {
  version: number;
  template_id: string;
  campaign_id: string;
  current_hp: number;
  max_hp: number;
  temp_hp: number;
  experience_points: number;
  level: number;
  spell_slots_used: { [key: number]: number };
  hit_dice_used: number;
  death_saves: Record<string, number>;
  inventory: ItemModel[];
  gold: number;
  conditions: string[];
  exhaustion_level: number;
  notes: string;
  achievements: string[];
  relationships: Record<string, string>;
  last_played: string;
}

export interface CampaignInstanceModel {
  version: number;
  id: string;
  name: string;
  template_id?: string;
  character_ids: string[];
  current_location: string;
  session_count: number;
  in_combat: boolean;
  event_summary: string[];
  event_log_path: string;
  last_event_id?: string;
  narration_enabled?: boolean;
  tts_voice?: string;
  created_date: string;
  last_played: string;
}

export interface CombinedCharacterModel {
  id: string;
  template_id: string;
  campaign_id: string;
  name: string;
  race: string;
  subrace?: string;
  char_class: string;
  subclass?: string;
  background: string;
  alignment: string;
  current_hp: number;
  max_hp: number;
  temp_hp: number;
  level: number;
  experience_points: number;
  base_stats: BaseStatsModel;
  armor_class: number;
  conditions: string[];
  spell_slots_used: { [key: number]: number };
  hit_dice_used: number;
  death_saves: Record<string, number>;
  exhaustion_level: number;
  inventory: ItemModel[];
  gold: number;
  proficiencies: ProficienciesModel;
  languages: string[];
  racial_traits: TraitModel[];
  class_features: ClassFeatureModel[];
  feats: TraitModel[];
  spells_known: string[];
  cantrips_known: string[];
  portrait_path?: string;
  hp: number;
  maximum_hp: number;
}

export interface CampaignSummaryModel {
  id: string;
  name: string;
  description: string;
  starting_level: number;
  difficulty: string;
  created_date: string;
  last_modified?: string;
}

export interface SharedHandlerStateModel {
  ai_processing: boolean;
  needs_backend_trigger: boolean;
}

export interface CombatantModel {
  id: string;
  name: string;
  initiative: number;
  initiative_modifier: number;
  current_hp: number;
  max_hp: number;
  armor_class: number;
  conditions: string[];
  is_player: boolean;
  icon_path?: string;
  stats?: Record<string, number>;
  abilities?: string[];
  attacks?: Record<string, any>[];
  conditions_immune?: string[];
  resistances?: string[];
  vulnerabilities?: string[];
}

export interface CombatStateModel {
  is_active: boolean;
  combatants: CombatantModel[];
  current_turn_index: number;
  round_number: number;
  current_turn_instruction_given: boolean;
}

export interface GameStateModel {
  version: number;
  campaign_id?: string;
  campaign_name?: string;
  active_ruleset_id?: string;
  active_lore_id?: string;
  event_log_path?: string;
  party: Record<string, CharacterInstanceModel>;
  current_location: LocationModel;
  chat_history: ChatMessageModel[];
  pending_player_dice_requests: DiceRequestModel[];
  combat: CombatStateModel;
  campaign_goal: string;
  known_npcs: Record<string, NPCModel>;
  active_quests: Record<string, QuestModel>;
  world_lore: string[];
  event_summary: string[];
  session_count: number;
  in_combat: boolean;
  last_event_id?: string;
  narration_enabled: boolean;
  tts_voice: string;
}

export interface CharacterChangesModel {
  current_hp?: number;
  max_hp?: number;
  temp_hp?: number;
  conditions?: string[];
  gold?: number;
  experience_points?: number;
  level?: number;
  exhaustion_level?: number;
  inventory_added?: string[];
  inventory_removed?: string[];
}

export interface ErrorContextModel {
  event_type?: string;
  character_id?: string;
  location?: string;
  user_action?: string;
  ai_response?: string;
  stack_trace?: string;
}

export interface BaseGameEvent {
  event_id: string;
  timestamp: string;
  sequence_number: number;
  event_type: string;
  correlation_id?: string;
}

export interface NarrativeAddedEvent extends BaseGameEvent {
  event_id: string;
  timestamp: string;
  sequence_number: number;
  event_type: "narrative_added";
  correlation_id?: string;
  role: string;
  content: string;
  gm_thought?: string;
  audio_path?: string;
  message_id?: string;
}

export interface MessageSupersededEvent extends BaseGameEvent {
  event_id: string;
  timestamp: string;
  sequence_number: number;
  event_type: "message_superseded";
  correlation_id?: string;
  message_id: string;
  reason: string;
}

export interface CombatStartedEvent extends BaseGameEvent {
  event_id: string;
  timestamp: string;
  sequence_number: number;
  event_type: "combat_started";
  correlation_id?: string;
  combatants: CombatantModel[];
  round_number: number;
}

export interface CombatEndedEvent extends BaseGameEvent {
  event_id: string;
  timestamp: string;
  sequence_number: number;
  event_type: "combat_ended";
  correlation_id?: string;
  reason: string;
  outcome_description?: string;
}

export interface TurnAdvancedEvent extends BaseGameEvent {
  event_id: string;
  timestamp: string;
  sequence_number: number;
  event_type: "turn_advanced";
  correlation_id?: string;
  new_combatant_id: string;
  new_combatant_name: string;
  round_number: number;
  is_new_round: boolean;
  is_player_controlled: boolean;
}

export interface CombatantHpChangedEvent extends BaseGameEvent {
  event_id: string;
  timestamp: string;
  sequence_number: number;
  event_type: "combatant_hp_changed";
  correlation_id?: string;
  combatant_id: string;
  combatant_name: string;
  old_hp: number;
  new_hp: number;
  max_hp: number;
  change_amount: number;
  is_player_controlled: boolean;
  source?: string;
}

export interface CombatantStatusChangedEvent extends BaseGameEvent {
  event_id: string;
  timestamp: string;
  sequence_number: number;
  event_type: "combatant_status_changed";
  correlation_id?: string;
  combatant_id: string;
  combatant_name: string;
  new_conditions: string[];
  added_conditions: string[];
  removed_conditions: string[];
  is_defeated: boolean;
  condition_details?: Record<string, any>;
}

export interface CombatantAddedEvent extends BaseGameEvent {
  event_id: string;
  timestamp: string;
  sequence_number: number;
  event_type: "combatant_added";
  correlation_id?: string;
  combatant_id: string;
  combatant_name: string;
  hp: number;
  max_hp: number;
  ac: number;
  is_player_controlled: boolean;
  position_in_order?: number;
}

export interface CombatantRemovedEvent extends BaseGameEvent {
  event_id: string;
  timestamp: string;
  sequence_number: number;
  event_type: "combatant_removed";
  correlation_id?: string;
  combatant_id: string;
  combatant_name: string;
  reason: string;
}

export interface CombatantInitiativeSetEvent extends BaseGameEvent {
  event_id: string;
  timestamp: string;
  sequence_number: number;
  event_type: "combatant_initiative_set";
  correlation_id?: string;
  combatant_id: string;
  combatant_name: string;
  initiative_value: number;
  roll_details?: string;
}

export interface InitiativeOrderDeterminedEvent extends BaseGameEvent {
  event_id: string;
  timestamp: string;
  sequence_number: number;
  event_type: "initiative_order_determined";
  correlation_id?: string;
  ordered_combatants: CombatantModel[];
}

export interface PlayerDiceRequestAddedEvent extends BaseGameEvent {
  event_id: string;
  timestamp: string;
  sequence_number: number;
  event_type: "player_dice_request_added";
  correlation_id?: string;
  request_id: string;
  character_id: string;
  character_name: string;
  roll_type: string;
  dice_formula: string;
  purpose: string;
  dc?: number;
  skill?: string;
  ability?: string;
}

export interface PlayerDiceRequestsClearedEvent extends BaseGameEvent {
  event_id: string;
  timestamp: string;
  sequence_number: number;
  event_type: "player_dice_requests_cleared";
  correlation_id?: string;
  cleared_request_ids: string[];
}

export interface NpcDiceRollProcessedEvent extends BaseGameEvent {
  event_id: string;
  timestamp: string;
  sequence_number: number;
  event_type: "npc_dice_roll_processed";
  correlation_id?: string;
  character_id: string;
  character_name: string;
  roll_type: string;
  dice_formula: string;
  total: number;
  details: string;
  success?: boolean;
  purpose: string;
}

export interface LocationChangedEvent extends BaseGameEvent {
  event_id: string;
  timestamp: string;
  sequence_number: number;
  event_type: "location_changed";
  correlation_id?: string;
  new_location_name: string;
  new_location_description: string;
  old_location_name?: string;
}

export interface PartyMemberUpdatedEvent extends BaseGameEvent {
  event_id: string;
  timestamp: string;
  sequence_number: number;
  event_type: "party_member_updated";
  correlation_id?: string;
  character_id: string;
  character_name: string;
  changes: CharacterChangesModel;
  gold_source?: string;
}

export interface BackendProcessingEvent extends BaseGameEvent {
  event_id: string;
  timestamp: string;
  sequence_number: number;
  event_type: "backend_processing";
  correlation_id?: string;
  is_processing: boolean;
  needs_backend_trigger: boolean;
  trigger_reason?: string;
}

export interface GameErrorEvent extends BaseGameEvent {
  event_id: string;
  timestamp: string;
  sequence_number: number;
  event_type: "game_error";
  correlation_id?: string;
  error_message: string;
  error_type: string;
  severity: "warning" | "error" | "critical";
  recoverable: boolean;
  context?: ErrorContextModel;
  error_code?: string;
}

export interface GameStateSnapshotEvent extends BaseGameEvent {
  event_id: string;
  timestamp: string;
  sequence_number: number;
  event_type: "game_state_snapshot";
  correlation_id?: string;
  campaign_id?: string;
  session_id?: string;
  location: LocationModel;
  party_members: CharacterInstanceModel | CombinedCharacterModel[];
  active_quests: QuestModel[];
  combat_state?: CombatStateModel;
  pending_dice_requests: DiceRequestModel[];
  chat_history: ChatMessageModel[];
  reason: string;
}

export interface QuestUpdatedEvent extends BaseGameEvent {
  event_id: string;
  timestamp: string;
  sequence_number: number;
  event_type: "quest_updated";
  correlation_id?: string;
  quest_id: string;
  quest_title: string;
  new_status: string;
  old_status?: string;
  description_update?: string;
}

export interface ItemAddedEvent extends BaseGameEvent {
  event_id: string;
  timestamp: string;
  sequence_number: number;
  event_type: "item_added";
  correlation_id?: string;
  character_id: string;
  character_name: string;
  item_name: string;
  quantity: number;
  item_description?: string;
  item_value?: number;
  item_rarity?: string;
}
