<template>
  <div class="space-y-6">
    <h3 class="text-lg font-semibold text-foreground">Review Character</h3>

    <!-- Validation Summary -->
    <div v-if="validationIssues.length > 0" class="space-y-2">
      <BaseAlert
        v-for="(issue, index) in validationIssues"
        :key="index"
        type="warning"
      >
        {{ issue }}
      </BaseAlert>
    </div>
    <BaseAlert v-else type="success">
      All character details are valid and ready to save!
    </BaseAlert>

    <!-- Character Summary -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <!-- Basic Info -->
      <AppCard>
        <h4 class="font-semibold text-foreground mb-3">Basic Information</h4>
        <dl class="space-y-2 text-sm">
          <div>
            <dt class="text-foreground/60 inline">Name:</dt>
            <dd class="inline ml-2 font-medium">
              {{ character.name || 'Not set' }}
            </dd>
          </div>
          <div>
            <dt class="text-foreground/60 inline">Alignment:</dt>
            <dd class="inline ml-2">
              {{ getAlignmentLabel(character.alignment) }}
            </dd>
          </div>
          <div>
            <dt class="text-foreground/60 inline">Background:</dt>
            <dd class="inline ml-2">
              {{ getBackgroundLabel(character.background) }}
              <BaseBadge
                v-if="getBackgroundSource(character.background)"
                size="sm"
                variant="default"
                class="ml-1"
              >
                {{ getBackgroundSource(character.background) }}
              </BaseBadge>
            </dd>
          </div>
        </dl>
      </AppCard>

      <!-- Race & Class -->
      <AppCard>
        <h4 class="font-semibold text-foreground mb-3">Race & Class</h4>
        <dl class="space-y-2 text-sm">
          <div>
            <dt class="text-foreground/60 inline">Race:</dt>
            <dd class="inline ml-2">
              {{ getRaceLabel(character.race) }}
              <BaseBadge
                v-if="getRaceSource(character.race)"
                size="sm"
                variant="default"
                class="ml-1"
              >
                {{ getRaceSource(character.race) }}
              </BaseBadge>
            </dd>
          </div>
          <div>
            <dt class="text-foreground/60 inline">Class:</dt>
            <dd class="inline ml-2">
              Level {{ character.level }}
              {{ getClassLabel(character.char_class) }}
              <BaseBadge
                v-if="getClassSource(character.char_class)"
                size="sm"
                variant="default"
                class="ml-1"
              >
                {{ getClassSource(character.char_class) }}
              </BaseBadge>
            </dd>
          </div>
        </dl>
      </AppCard>

      <!-- Ability Scores -->
      <AppCard>
        <h4 class="font-semibold text-foreground mb-3">Ability Scores</h4>
        <p class="text-xs text-foreground/60 mb-2">
          Method: {{ character.ability_score_method }}
        </p>
        <div class="grid grid-cols-3 gap-2 text-sm">
          <div v-for="ability in abilities" :key="ability.key">
            <span class="text-foreground/60">{{ ability.abbr }}:</span>
            <span class="font-medium ml-1">
              {{ character[ability.key] }}
              <span class="text-xs text-foreground/40">
                ({{ getModifier(character[ability.key]) >= 0 ? '+' : ''
                }}{{ getModifier(character[ability.key]) }})
              </span>
            </span>
          </div>
        </div>
      </AppCard>

      <!-- Skills & Proficiencies -->
      <AppCard>
        <h4 class="font-semibold text-foreground mb-3">
          Skills & Proficiencies
        </h4>
        <div class="space-y-2 text-sm">
          <div v-if="character.class_skills.length > 0">
            <span class="text-foreground/60">Class Skills:</span>
            <span class="ml-2"
              >{{ character.class_skills.length }} selected</span
            >
          </div>
          <div v-if="character.expertise.length > 0">
            <span class="text-foreground/60">Expertise:</span>
            <span class="ml-2">{{ character.expertise.length }} selected</span>
          </div>
          <div v-if="grantedLanguages.length > 0">
            <span class="text-foreground/60">Languages:</span>
            <span class="ml-2">{{ grantedLanguages.join(', ') }}</span>
          </div>
        </div>
      </AppCard>

      <!-- Equipment & Spells -->
      <AppCard v-if="isSpellcaster || character.equipment_method">
        <h4 class="font-semibold text-foreground mb-3">Equipment & Spells</h4>
        <div class="space-y-2 text-sm">
          <div>
            <span class="text-foreground/60">Equipment:</span>
            <span class="ml-2">{{ character.equipment_method }}</span>
          </div>
          <div v-if="character.cantrips.length > 0">
            <span class="text-foreground/60">Cantrips:</span>
            <span class="ml-2">{{ character.cantrips.length }} selected</span>
          </div>
          <div v-if="character.spells.length > 0">
            <span class="text-foreground/60">1st Level Spells:</span>
            <span class="ml-2">{{ character.spells.length }} selected</span>
          </div>
        </div>
      </AppCard>

      <!-- Content Packs -->
      <AppCard>
        <h4 class="font-semibold text-foreground mb-3">Content Packs</h4>
        <div class="flex flex-wrap gap-2">
          <BaseBadge
            v-for="packId in character.content_pack_ids"
            :key="packId"
            variant="secondary"
          >
            {{ getContentPackName(packId) }}
          </BaseBadge>
        </div>
      </AppCard>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { D5eContentPack } from '@/types/unified'
import AppCard from '@/components/base/AppCard.vue'
import BaseBadge from '@/components/base/BaseBadge.vue'
import BaseAlert from '@/components/base/BaseAlert.vue'

export interface ReviewStepProps {
  character: {
    name: string
    alignment: string
    background: string
    backstory: string
    race: string
    char_class: string
    level: number
    ability_score_method: string
    strength: number
    dexterity: number
    constitution: number
    intelligence: number
    wisdom: number
    charisma: number
    class_skills: string[]
    expertise: string[]
    equipment_method: string
    cantrips: string[]
    spells: string[]
    content_pack_ids: string[]
  }
  validationIssues: string[]
  isSpellcaster: boolean
  grantedLanguages: string[]
  raceOptions: Array<{ value: string; label: string; _source?: string }>
  classOptions: Array<{ value: string; label: string; _source?: string }>
  backgroundOptions: Array<{ value: string; label: string; _source?: string }>
  alignmentOptions: Array<{ value: string; label: string }>
  contentPacks: D5eContentPack[]
}

const props = defineProps<ReviewStepProps>()

// Constants
const abilities = [
  { key: 'strength', name: 'Strength', abbr: 'STR' },
  { key: 'dexterity', name: 'Dexterity', abbr: 'DEX' },
  { key: 'constitution', name: 'Constitution', abbr: 'CON' },
  { key: 'intelligence', name: 'Intelligence', abbr: 'INT' },
  { key: 'wisdom', name: 'Wisdom', abbr: 'WIS' },
  { key: 'charisma', name: 'Charisma', abbr: 'CHA' },
]

// Helper methods
function getModifier(score: number): number {
  return Math.floor((score - 10) / 2)
}

function getRaceLabel(value: string): string {
  return props.raceOptions.find(opt => opt.value === value)?.label || value
}

function getRaceSource(value: string): string | undefined {
  return props.raceOptions.find(opt => opt.value === value)?._source
}

function getClassLabel(value: string): string {
  return props.classOptions.find(opt => opt.value === value)?.label || value
}

function getClassSource(value: string): string | undefined {
  return props.classOptions.find(opt => opt.value === value)?._source
}

function getBackgroundLabel(value: string): string {
  return (
    props.backgroundOptions.find(opt => opt.value === value)?.label || value
  )
}

function getBackgroundSource(value: string): string | undefined {
  return props.backgroundOptions.find(opt => opt.value === value)?._source
}

function getAlignmentLabel(value: string): string {
  return props.alignmentOptions.find(opt => opt.value === value)?.label || value
}

function getContentPackName(packId: string): string {
  return props.contentPacks.find(pack => pack.id === packId)?.name || packId
}
</script>
