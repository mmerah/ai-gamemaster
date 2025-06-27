<template>
  <AppModal
    :visible="visible"
    size="xl"
    :title="`${character?.name || 'Character'} Details`"
    @close="$emit('close')"
  >
    <template v-if="character">
      <!-- Tabs for navigation -->
      <AppTabs
        :tabs="tabs"
        :active-tab="activeTab"
        class="mb-6"
        @update:active-tab="activeTab = $event"
      />

      <!-- Tab Content -->
      <div class="min-h-[400px]">
        <!-- Overview Tab -->
        <div v-show="activeTab === 'overview'" class="space-y-4">
          <!-- Basic Info -->
          <AppCard>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <h3 class="text-sm font-medium text-foreground/60 mb-1">
                  Race
                </h3>
                <p class="text-foreground">
                  {{ character.race }}
                  <span v-if="character.subrace" class="text-foreground/80">
                    ({{ character.subrace }})
                  </span>
                </p>
              </div>
              <div>
                <h3 class="text-sm font-medium text-foreground/60 mb-1">
                  Class
                </h3>
                <p class="text-foreground">
                  {{ character.char_class }}
                  <span v-if="character.subclass" class="text-foreground/80">
                    ({{ character.subclass }})
                  </span>
                </p>
              </div>
              <div>
                <h3 class="text-sm font-medium text-foreground/60 mb-1">
                  Background
                </h3>
                <p class="text-foreground">{{ character.background }}</p>
              </div>
              <div>
                <h3 class="text-sm font-medium text-foreground/60 mb-1">
                  Alignment
                </h3>
                <p class="text-foreground">{{ character.alignment }}</p>
              </div>
              <div>
                <h3 class="text-sm font-medium text-foreground/60 mb-1">
                  Level
                </h3>
                <p class="text-foreground">{{ character.level }}</p>
              </div>
              <div>
                <h3 class="text-sm font-medium text-foreground/60 mb-1">
                  Experience
                </h3>
                <p class="text-foreground">
                  {{ character.experience_points }} XP
                </p>
              </div>
            </div>
          </AppCard>

          <!-- Health & Status -->
          <AppCard>
            <h3 class="text-lg font-semibold text-foreground mb-3">
              Health & Status
            </h3>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <div class="flex items-center justify-between mb-1">
                  <span class="text-sm font-medium text-foreground/60"
                    >Hit Points</span
                  >
                  <span class="text-foreground font-medium">
                    {{ character.current_hp }}/{{ character.max_hp }}
                  </span>
                </div>
                <div
                  class="w-full bg-card border border-border rounded-full h-3"
                >
                  <div
                    class="bg-green-600 dark:bg-green-500 h-full rounded-full transition-all"
                    :style="{ width: `${getHealthPercent(character)}%` }"
                  />
                </div>
              </div>
              <div>
                <h4 class="text-sm font-medium text-foreground/60 mb-1">
                  Armor Class
                </h4>
                <p class="text-2xl font-bold text-primary">
                  {{ character.armor_class }}
                </p>
              </div>
              <div>
                <h4 class="text-sm font-medium text-foreground/60 mb-1">
                  Initiative
                </h4>
                <p class="text-2xl font-bold text-primary">
                  {{ getInitiativeBonus(character) >= 0 ? '+' : ''
                  }}{{ getInitiativeBonus(character) }}
                </p>
              </div>
            </div>

            <!-- Conditions -->
            <div v-if="character.conditions?.length" class="mt-4">
              <h4 class="text-sm font-medium text-foreground/60 mb-2">
                Active Conditions
              </h4>
              <div class="flex flex-wrap gap-2">
                <BaseBadge
                  v-for="condition in character.conditions"
                  :key="condition"
                  variant="warning"
                >
                  {{ condition }}
                </BaseBadge>
              </div>
            </div>
          </AppCard>
        </div>

        <!-- Abilities Tab -->
        <div v-show="activeTab === 'abilities'" class="space-y-4">
          <AppCard>
            <h3 class="text-lg font-semibold text-foreground mb-3">
              Ability Scores
            </h3>
            <div class="grid grid-cols-2 md:grid-cols-3 gap-4">
              <div
                v-for="(value, ability) in character.base_stats"
                :key="ability"
                class="text-center p-3 bg-accent/10 rounded-lg border border-accent/30"
              >
                <h4 class="text-sm font-medium text-foreground/60 mb-1">
                  {{ getAbilityName(ability) }}
                </h4>
                <p class="text-2xl font-bold text-primary">{{ value }}</p>
                <p class="text-sm text-foreground/60">
                  {{ getModifierString(value) }}
                </p>
              </div>
            </div>
          </AppCard>

          <AppCard>
            <h3 class="text-lg font-semibold text-foreground mb-3">
              Saving Throws
            </h3>
            <div class="grid grid-cols-2 md:grid-cols-3 gap-3">
              <div
                v-for="(value, ability) in character.base_stats"
                :key="`save-${ability}`"
                class="flex items-center justify-between p-2 rounded bg-card"
              >
                <span class="text-sm font-medium text-foreground/60">
                  {{ getAbilityName(ability) }}
                </span>
                <span class="font-medium" :class="getProficiencyClass(ability)">
                  {{ getSavingThrowBonus(character, ability) >= 0 ? '+' : ''
                  }}{{ getSavingThrowBonus(character, ability) }}
                </span>
              </div>
            </div>
          </AppCard>
        </div>

        <!-- Skills Tab -->
        <div v-show="activeTab === 'skills'" class="space-y-4">
          <AppCard>
            <h3 class="text-lg font-semibold text-foreground mb-3">
              Skill Proficiencies
            </h3>
            <div
              v-if="character.proficiencies?.skills?.length"
              class="space-y-2"
            >
              <div
                v-for="skill in character.proficiencies.skills"
                :key="skill"
                class="flex items-center justify-between p-2 rounded bg-accent/10"
              >
                <span class="font-medium text-foreground">{{ skill }}</span>
                <BaseBadge variant="primary">Proficient</BaseBadge>
              </div>
            </div>
            <p v-else class="text-foreground/60">No skill proficiencies</p>
          </AppCard>

          <AppCard>
            <h3 class="text-lg font-semibold text-foreground mb-3">
              Other Proficiencies
            </h3>
            <div class="space-y-3">
              <div v-if="character.proficiencies?.armor?.length">
                <h4 class="text-sm font-medium text-foreground/60 mb-1">
                  Armor
                </h4>
                <div class="flex flex-wrap gap-2">
                  <BaseBadge
                    v-for="prof in character.proficiencies.armor"
                    :key="prof"
                  >
                    {{ prof }}
                  </BaseBadge>
                </div>
              </div>
              <div v-if="character.proficiencies?.weapons?.length">
                <h4 class="text-sm font-medium text-foreground/60 mb-1">
                  Weapons
                </h4>
                <div class="flex flex-wrap gap-2">
                  <BaseBadge
                    v-for="prof in character.proficiencies.weapons"
                    :key="prof"
                  >
                    {{ prof }}
                  </BaseBadge>
                </div>
              </div>
              <div v-if="character.proficiencies?.tools?.length">
                <h4 class="text-sm font-medium text-foreground/60 mb-1">
                  Tools
                </h4>
                <div class="flex flex-wrap gap-2">
                  <BaseBadge
                    v-for="prof in character.proficiencies.tools"
                    :key="prof"
                  >
                    {{ prof }}
                  </BaseBadge>
                </div>
              </div>
              <div v-if="character.languages?.length">
                <h4 class="text-sm font-medium text-foreground/60 mb-1">
                  Languages
                </h4>
                <div class="flex flex-wrap gap-2">
                  <BaseBadge v-for="lang in character.languages" :key="lang">
                    {{ lang }}
                  </BaseBadge>
                </div>
              </div>
            </div>
          </AppCard>
        </div>

        <!-- Inventory Tab -->
        <div v-show="activeTab === 'inventory'" class="space-y-4">
          <AppCard>
            <div class="flex items-center justify-between mb-3">
              <h3 class="text-lg font-semibold text-foreground">Inventory</h3>
              <div class="flex items-center gap-2">
                <span class="text-sm font-medium text-foreground/60"
                  >Gold:</span
                >
                <span class="text-lg font-bold text-accent">
                  {{ character.gold }} gp
                </span>
              </div>
            </div>
            <div v-if="character.inventory?.length" class="space-y-2">
              <div
                v-for="item in character.inventory"
                :key="item.id"
                class="flex items-center justify-between p-3 bg-accent/10 rounded-lg border border-accent/30"
              >
                <div>
                  <h4 class="font-medium text-foreground">{{ item.name }}</h4>
                  <p
                    v-if="item.description"
                    class="text-sm text-foreground/60 mt-1"
                  >
                    {{ item.description }}
                  </p>
                </div>
                <BaseBadge v-if="item.quantity > 1" variant="secondary">
                  x{{ item.quantity }}
                </BaseBadge>
              </div>
            </div>
            <p v-else class="text-foreground/60">No items in inventory</p>
          </AppCard>
        </div>

        <!-- Features Tab -->
        <div v-show="activeTab === 'features'" class="space-y-4">
          <AppCard v-if="character.racial_traits?.length">
            <h3 class="text-lg font-semibold text-foreground mb-3">
              Racial Traits
            </h3>
            <div class="space-y-3">
              <div
                v-for="trait in character.racial_traits"
                :key="trait.name"
                class="border-l-4 border-primary pl-3"
              >
                <h4 class="font-medium text-foreground">{{ trait.name }}</h4>
                <p class="text-sm text-foreground/80 mt-1">
                  {{ trait.description }}
                </p>
              </div>
            </div>
          </AppCard>

          <AppCard v-if="character.class_features?.length">
            <h3 class="text-lg font-semibold text-foreground mb-3">
              Class Features
            </h3>
            <div class="space-y-3">
              <div
                v-for="feature in character.class_features"
                :key="feature.name"
                class="border-l-4 border-accent pl-3"
              >
                <div class="flex items-center justify-between">
                  <h4 class="font-medium text-foreground">
                    {{ feature.name }}
                  </h4>
                  <BaseBadge variant="secondary" size="sm">
                    Level {{ feature.level_acquired }}
                  </BaseBadge>
                </div>
                <p class="text-sm text-foreground/80 mt-1">
                  {{ feature.description }}
                </p>
              </div>
            </div>
          </AppCard>

          <AppCard v-if="character.feats?.length">
            <h3 class="text-lg font-semibold text-foreground mb-3">Feats</h3>
            <div class="space-y-3">
              <div
                v-for="feat in character.feats"
                :key="feat.name"
                class="border-l-4 border-secondary pl-3"
              >
                <h4 class="font-medium text-foreground">{{ feat.name }}</h4>
                <p class="text-sm text-foreground/80 mt-1">
                  {{ feat.description }}
                </p>
              </div>
            </div>
          </AppCard>
        </div>

        <!-- Spells Tab (if spellcaster) -->
        <div
          v-if="isSpellcaster"
          v-show="activeTab === 'spells'"
          class="space-y-4"
        >
          <AppCard>
            <h3 class="text-lg font-semibold text-foreground mb-3">
              Spell Slots
            </h3>
            <div class="grid grid-cols-3 md:grid-cols-5 gap-3">
              <div
                v-for="level in 9"
                :key="level"
                class="text-center p-2 bg-accent/10 rounded-lg"
              >
                <h4 class="text-xs font-medium text-foreground/60 mb-1">
                  Level {{ level }}
                </h4>
                <p class="text-lg font-bold text-primary">
                  {{ getSpellSlotsRemaining(character, level) }}/{{
                    getMaxSpellSlots(character, level)
                  }}
                </p>
              </div>
            </div>
          </AppCard>

          <AppCard v-if="character.cantrips_known?.length">
            <h3 class="text-lg font-semibold text-foreground mb-3">Cantrips</h3>
            <div class="flex flex-wrap gap-2">
              <BaseBadge
                v-for="cantrip in character.cantrips_known"
                :key="cantrip"
                variant="primary"
              >
                {{ cantrip }}
              </BaseBadge>
            </div>
          </AppCard>

          <AppCard v-if="character.spells_known?.length">
            <h3 class="text-lg font-semibold text-foreground mb-3">
              Known Spells
            </h3>
            <div class="flex flex-wrap gap-2">
              <BaseBadge
                v-for="spell in character.spells_known"
                :key="spell"
                variant="secondary"
              >
                {{ spell }}
              </BaseBadge>
            </div>
          </AppCard>
        </div>
      </div>
    </template>

    <!-- Loading State -->
    <div v-else class="flex items-center justify-center min-h-[400px]">
      <BaseLoader size="lg" />
    </div>
  </AppModal>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import AppModal from '@/components/base/AppModal.vue'
import AppTabs from '@/components/base/AppTabs.vue'
import AppCard from '@/components/base/AppCard.vue'
import BaseBadge from '@/components/base/BaseBadge.vue'
import BaseLoader from '@/components/base/BaseLoader.vue'
import type { UIPartyMember } from '@/types/ui'

interface Props {
  visible: boolean
  character: UIPartyMember | null
}

const props = defineProps<Props>()
const emit = defineEmits<{
  close: []
}>()

const activeTab = ref('overview')

const tabs = computed(() => {
  const baseTabs = [
    { id: 'overview', label: 'Overview' },
    { id: 'abilities', label: 'Abilities' },
    { id: 'skills', label: 'Skills' },
    { id: 'inventory', label: 'Inventory' },
    { id: 'features', label: 'Features' },
  ]

  if (isSpellcaster.value) {
    baseTabs.push({ id: 'spells', label: 'Spells' })
  }

  return baseTabs
})

const isSpellcaster = computed(() => {
  if (!props.character) return false
  return (
    props.character.spells_known?.length > 0 ||
    props.character.cantrips_known?.length > 0 ||
    Object.keys(props.character.spell_slots_used || {}).length > 0
  )
})

function getHealthPercent(character: UIPartyMember): number {
  if (!character.max_hp || character.max_hp === 0) return 0
  return Math.max(
    0,
    Math.min(100, (character.current_hp / character.max_hp) * 100)
  )
}

function getAbilityName(ability: string): string {
  const names: Record<string, string> = {
    STR: 'Strength',
    DEX: 'Dexterity',
    CON: 'Constitution',
    INT: 'Intelligence',
    WIS: 'Wisdom',
    CHA: 'Charisma',
  }
  return names[ability] || ability
}

function getModifier(score: number): number {
  return Math.floor((score - 10) / 2)
}

function getModifierString(score: number): string {
  const mod = getModifier(score)
  return mod >= 0 ? `+${mod}` : `${mod}`
}

function getInitiativeBonus(character: UIPartyMember): number {
  return getModifier(character.base_stats.DEX)
}

function getProficiencyBonus(level: number): number {
  return Math.ceil(level / 4) + 1
}

function getSavingThrowBonus(
  character: UIPartyMember,
  ability: string
): number {
  const mod = getModifier(
    character.base_stats[ability as keyof typeof character.base_stats]
  )
  const isProficient = character.proficiencies?.saving_throws?.includes(ability)
  return isProficient ? mod + getProficiencyBonus(character.level) : mod
}

function getProficiencyClass(ability: string): string {
  if (!props.character) return ''
  const isProficient =
    props.character.proficiencies?.saving_throws?.includes(ability)
  return isProficient ? 'text-primary' : 'text-foreground'
}

function getSpellSlotsRemaining(
  character: UIPartyMember,
  level: number
): number {
  const used = character.spell_slots_used?.[level] || 0
  const max = getMaxSpellSlots(character, level)
  return Math.max(0, max - used)
}

function getMaxSpellSlots(character: UIPartyMember, level: number): number {
  // This is a simplified calculation - in reality it depends on class and level
  // You might want to fetch this from the backend or calculate based on class tables
  const spellcasterLevel = character.level
  const spellSlotTable: Record<number, number[]> = {
    1: [2, 0, 0, 0, 0, 0, 0, 0, 0],
    2: [3, 0, 0, 0, 0, 0, 0, 0, 0],
    3: [4, 2, 0, 0, 0, 0, 0, 0, 0],
    4: [4, 3, 0, 0, 0, 0, 0, 0, 0],
    5: [4, 3, 2, 0, 0, 0, 0, 0, 0],
    // ... simplified for brevity
  }
  return spellSlotTable[Math.min(spellcasterLevel, 5)]?.[level - 1] || 0
}
</script>
