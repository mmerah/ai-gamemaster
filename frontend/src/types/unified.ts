// Generated TypeScript interfaces from Pydantic models
// DO NOT EDIT - This file is auto-generated
// Generated at: 2025-06-17T14:32:54.441711

// ============================================
// Table of Contents
// ============================================
// 1. Constants and Enums
// 2. D&D 5e Content Base Types
// 3. D&D 5e Content Models
// 4. Runtime Models - Core Types
// 5. Runtime Models - Character & Campaign
// 6. Runtime Models - Combat
// 7. Runtime Models - Game State
// 8. Runtime Models - Events
// 9. Runtime Models - Updates
// ============================================

// ============================================
// 1. Constants and Enums
// ============================================

export const CONTENT_TYPES = {
  ABILITY_SCORES: "ability-scores",
  ALIGNMENTS: "alignments",
  BACKGROUNDS: "backgrounds",
  CLASSES: "classes",
  CONDITIONS: "conditions",
  DAMAGE_TYPES: "damage-types",
  EQUIPMENT: "equipment",
  EQUIPMENT_CATEGORIES: "equipment-categories",
  FEATS: "feats",
  FEATURES: "features",
  LANGUAGES: "languages",
  LEVELS: "levels",
  MAGIC_ITEMS: "magic-items",
  MAGIC_SCHOOLS: "magic-schools",
  MONSTERS: "monsters",
  PROFICIENCIES: "proficiencies",
  RACES: "races",
  RULES: "rules",
  RULE_SECTIONS: "rule-sections",
  SKILLS: "skills",
  SPELLS: "spells",
  SUBCLASSES: "subclasses",
  SUBRACES: "subraces",
  TRAITS: "traits",
  WEAPON_PROPERTIES: "weapon-properties",
} as const;

export type ContentType = typeof CONTENT_TYPES[keyof typeof CONTENT_TYPES];


// ============================================
// 2. D&D 5e Content Base Types
// ============================================

export interface APIReference {
  index: string;
  name: string;
  url: string;
}

export interface OptionSet {
  option_set_type: string;
  options?: any[];
  equipment_category?: APIReference;
  resource_list_url?: string;
}

export interface Choice {
  desc?: string;
  choose: number;
  type: string;
  from_?: OptionSet;
}

export interface DC {
  dc_type: APIReference;
  dc_value?: number;
  success_type?: string;
}

export interface Cost {
  quantity: number;
  unit: string;
}

export interface Damage {
  damage_type?: APIReference;
  damage_dice?: string;
}

export interface DamageAtLevel {
  damage_type?: APIReference;
  damage_at_slot_level?: Record<string, string>;
  damage_at_character_level?: Record<string, string>;
}

export interface Usage {
  type: string;
  dice?: string;
  min_value?: number;
  times?: number;
  rest_types?: string[];
}


// ============================================
// 3. D&D 5e Content Models
// ============================================

export interface D5eSpell {
  index: string;
  name: string;
  desc: string[];
  higher_level?: string[];
  range: string;
  components: string[];
  material?: string;
  ritual: boolean;
  duration: string;
  concentration: boolean;
  casting_time: string;
  level: number;
  attack_type?: string;
  damage?: DamageAtLevel;
  heal_at_slot_level?: Record<string, string>;
  dc?: DC;
  area_of_effect?: Record<string, any>;
  school: APIReference;
  classes: APIReference[];
  subclasses: APIReference[];
  url: string;
}

export interface MonsterSpeed {
  walk?: string;
  swim?: string;
  fly?: string;
  burrow?: string;
  climb?: string;
  hover?: boolean;
}

export interface MonsterArmorClass {
  type: string;
  value: number;
  armor?: APIReference[];
  spell?: APIReference;
  condition?: APIReference;
  desc?: string;
}

export interface MonsterProficiency {
  value: number;
  proficiency: APIReference;
}

export interface SpecialAbility {
  name: string;
  desc: string;
  attack_bonus?: number;
  damage?: Damage[];
  dc?: DC;
  spellcasting?: Record<string, any>;
  usage?: Usage;
}

export interface MonsterAction {
  name: string;
  multiattack_type?: string;
  desc: string;
  attack_bonus?: number;
  damage?: Damage[];
  dc?: DC;
  usage?: Usage;
  options?: Record<string, any>;
  actions?: Record<string, any>[];
}

export interface D5eMonster {
  index: string;
  name: string;
  size: string;
  type: string;
  subtype?: string;
  alignment: string;
  armor_class: MonsterArmorClass[];
  hit_points: number;
  hit_dice: string;
  hit_points_roll: string;
  speed: MonsterSpeed;
  strength: number;
  dexterity: number;
  constitution: number;
  intelligence: number;
  wisdom: number;
  charisma: number;
  proficiencies: MonsterProficiency[];
  damage_vulnerabilities: string[];
  damage_resistances: string[];
  damage_immunities: string[];
  condition_immunities: APIReference[];
  senses: Record<string, any>;
  languages: string;
  telepathy?: string;
  challenge_rating: number;
  proficiency_bonus: number;
  xp: number;
  special_abilities?: SpecialAbility[];
  actions?: MonsterAction[];
  legendary_actions?: MonsterAction[];
  reactions?: MonsterAction[];
  desc?: string | string[];
  image?: string;
  url: string;
}

export interface EquipmentRange {
  normal: number;
  long?: number;
}

export interface ArmorClass {
  base: number;
  dex_bonus: boolean;
  max_bonus?: number;
}

export interface D5eEquipment {
  index: string;
  name: string;
  equipment_category: APIReference;
  cost: Cost;
  weight?: number;
  desc?: string[];
  weapon_category?: string;
  weapon_range?: string;
  category_range?: string;
  damage?: Damage;
  two_handed_damage?: Damage;
  range?: EquipmentRange;
  throw_range?: EquipmentRange;
  properties?: APIReference[];
  armor_category?: string;
  armor_class?: ArmorClass;
  str_minimum?: number;
  stealth_disadvantage?: boolean;
  gear_category?: APIReference;
  quantity?: number;
  contents?: Record<string, any>[];
  tool_category?: string;
  vehicle_category?: string;
  speed?: Record<string, any>;
  capacity?: string;
  url: string;
}

export interface AbilityBonus {
  ability_score: APIReference;
  bonus: number;
}

export interface StartingEquipment {
  equipment: APIReference;
  quantity: number;
}

export interface StartingEquipmentOption {
  desc?: string;
  choose: number;
  type: string;
  from_: Record<string, any>;
}

export interface SpellcastingInfo {
  name: string;
  desc: string[];
  count?: number;
  level?: number;
}

export interface Spellcasting {
  level: number;
  spellcasting_ability: APIReference;
  info: SpellcastingInfo[];
}

export interface MultiClassing {
  prerequisites?: MultiClassingPrereq[];
  prerequisite_options?: Choice;
  proficiencies?: APIReference[];
  proficiency_choices?: Choice[];
}

export interface MultiClassingPrereq {
  ability_score: APIReference;
  minimum_score: number;
}

export interface Feature {
  name: string;
  desc: string[];
}

export interface D5eClass {
  index: string;
  name: string;
  hit_die: number;
  proficiency_choices: Choice[];
  proficiencies: APIReference[];
  saving_throws: APIReference[];
  starting_equipment: StartingEquipment[];
  starting_equipment_options: StartingEquipmentOption[];
  class_levels: string;
  multi_classing?: MultiClassing;
  subclasses: APIReference[];
  spellcasting?: Spellcasting;
  spells?: string;
  url: string;
}

export interface D5eSubclass {
  index: string;
  class_?: APIReference;
  name: string;
  subclass_flavor: string;
  desc: string[];
  subclass_levels: string;
  spells?: string | Record<string, any>[];
  url: string;
}

export interface D5eRace {
  index: string;
  name: string;
  speed: number;
  ability_bonuses: AbilityBonus[];
  ability_bonus_options?: Choice;
  alignment: string;
  age: string;
  size: string;
  size_description: string;
  starting_proficiencies: APIReference[];
  starting_proficiency_options?: Choice;
  languages: APIReference[];
  language_options?: Choice;
  language_desc: string;
  traits: APIReference[];
  subraces: APIReference[];
  url: string;
}

export interface D5eSubrace {
  index: string;
  name: string;
  race: APIReference;
  desc: string;
  ability_bonuses: AbilityBonus[];
  ability_bonus_options?: Choice;
  starting_proficiencies: APIReference[];
  starting_proficiency_options?: Choice;
  languages: APIReference[];
  language_options?: Choice;
  racial_traits: APIReference[];
  racial_trait_options?: Choice;
  url: string;
}

export interface D5eBackground {
  index: string;
  name: string;
  starting_proficiencies: APIReference[];
  language_options?: Choice;
  starting_equipment: StartingEquipment[];
  starting_equipment_options: StartingEquipmentOption[];
  feature: Feature;
  personality_traits: Choice;
  ideals: Choice;
  bonds: Choice;
  flaws: Choice;
  url: string;
}

export interface D5eFeat {
  index: string;
  name: string;
  prerequisites: Record<string, any>[];
  desc: string[];
  url: string;
}

export interface D5eTrait {
  index: string;
  races: APIReference[];
  subraces: APIReference[];
  name: string;
  desc: string[];
  proficiencies: APIReference[];
  proficiency_choices?: Choice;
  language_options?: Choice;
  trait_specific?: Record<string, any>;
  url: string;
}

export interface D5eMagicItem {
  index: string;
  name: string;
  equipment_category: APIReference;
  desc: string[];
  rarity: Record<string, string>;
  variant: boolean;
  variants?: APIReference[];
  url: string;
}

export interface D5eMagicSchool {
  index: string;
  name: string;
  desc: string;
  url: string;
}

export interface D5eWeaponProperty {
  index: string;
  name: string;
  desc: string[];
  url: string;
}

export interface D5eEquipmentCategory {
  index: string;
  name: string;
  equipment: APIReference[];
  url: string;
}

export interface SpellSlotInfo {
  spell_slots_level_1?: number;
  spell_slots_level_2?: number;
  spell_slots_level_3?: number;
  spell_slots_level_4?: number;
  spell_slots_level_5?: number;
  spell_slots_level_6?: number;
  spell_slots_level_7?: number;
  spell_slots_level_8?: number;
  spell_slots_level_9?: number;
}

export interface Prerequisite {
  type: string;
  level?: number;
  feature?: string;
}

export interface D5eFeature {
  index: string;
  name: string;
  level: number;
  class_: APIReference;
  subclass?: APIReference;
  desc: string[];
  prerequisites: Prerequisite[];
  parent?: APIReference;
  reference?: string;
  feature_specific?: Record<string, any>;
  url: string;
}

export interface D5eLevel {
  level: number;
  ability_score_bonuses?: number;
  prof_bonus?: number;
  features: APIReference[];
  spellcasting?: SpellSlotInfo;
  class_specific?: Record<string, any>;
  index: string;
  class_?: APIReference;
  subclass?: APIReference;
  url: string;
}

export interface D5eCondition {
  index: string;
  name: string;
  desc: string[];
  url: string;
}

export interface D5eDamageType {
  index: string;
  name: string;
  desc: string[];
  url: string;
}

export interface D5eLanguage {
  index: string;
  name: string;
  type: string;
  typical_speakers: string[];
  script?: string;
  url: string;
}

export interface D5eProficiency {
  index: string;
  type: string;
  name: string;
  classes: APIReference[];
  races: APIReference[];
  url: string;
  reference?: APIReference;
}

export interface D5eSkill {
  index: string;
  name: string;
  desc: string[];
  ability_score: APIReference;
  url: string;
}

export interface D5eAbilityScore {
  index: string;
  name: string;
  full_name: string;
  desc: string[];
  skills: APIReference[];
  url: string;
}

export interface D5eAlignment {
  index: string;
  name: string;
  abbreviation: string;
  desc: string;
  url: string;
}

export interface D5eRule {
  index: string;
  name: string;
  desc: string;
  subsections: APIReference[];
  url: string;
}

export interface D5eRuleSection {
  index: string;
  name: string;
  desc: string;
  url: string;
}


// ============================================
// 4. Runtime Models - Core Types
// ============================================

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

export interface SharedHandlerStateModel {
  ai_processing: boolean;
  needs_backend_trigger: boolean;
}


// ============================================
// 5. Runtime Models - Character & Campaign
// ============================================

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
  content_pack_ids: string[];
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
  content_pack_ids: string[];
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
  id: string;
  name: string;
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
  content_pack_priority: string[];
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


// ============================================
// 6. Runtime Models - Combat
// ============================================

export interface AttackModel {
  name: string;
  description: string;
  attack_type?: "melee" | "ranged";
  to_hit_bonus?: number;
  reach?: string;
  range?: string;
  damage_formula?: string;
  damage_type?: string;
}

export interface InitialCombatantData {
  id: string;
  name: string;
  hp: number;
  ac: number;
  stats?: Record<string, number>;
  abilities?: string[];
  attacks?: AttackModel[];
  icon_path?: string;
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
  attacks?: AttackModel[];
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


// ============================================
// 7. Runtime Models - Game State
// ============================================

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
  content_pack_priority: string[];
}


// ============================================
// 8. Runtime Models - Events
// ============================================

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


// ============================================
// 9. Runtime Models - Updates
// ============================================

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
