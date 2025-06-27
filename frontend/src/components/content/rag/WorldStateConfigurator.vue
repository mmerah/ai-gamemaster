<template>
  <BasePanel class="world-configurator">
    <h5 class="text-lg font-semibold mb-4 text-foreground">World State</h5>

    <div class="space-y-4">
      <!-- Campaign Context -->
      <AppCard variant="subtle" padding="sm">
        <h6 class="font-medium mb-3 text-foreground">Campaign Context</h6>
        <div class="space-y-3">
          <AppTextarea
            v-model="localState.campaign_goal"
            label="Campaign Goal:"
            :rows="2"
            placeholder="e.g., Defeat the evil necromancer threatening the kingdom"
            @input="emitUpdate"
          />
          <div class="grid grid-cols-2 gap-3">
            <AppInput
              v-model.number="localState.session_count"
              label="Session Count:"
              type="number"
              :min="0"
              @input="emitUpdate"
            />
            <AppInput
              v-model="localState.active_ruleset_id"
              label="Active Ruleset:"
              placeholder="e.g., dnd_5e_srd"
              @input="emitUpdate"
            />
          </div>
        </div>
      </AppCard>

      <!-- NPCs -->
      <AppCard variant="subtle" padding="sm">
        <h6 class="font-medium mb-3 text-foreground">Known NPCs</h6>
        <div class="space-y-3">
          <AppCard
            v-for="(npc, index) in npcs"
            :key="npc.id"
            variant="subtle"
            padding="sm"
          >
            <div class="flex gap-2 mb-3">
              <AppInput
                v-model="npc.name"
                placeholder="NPC name"
                class="flex-1 font-medium"
                @input="updateNPC(index)"
              />
              <AppButton
                variant="danger"
                size="sm"
                title="Remove NPC"
                @click="removeNPC(index)"
              >
                ✕
              </AppButton>
            </div>
            <div class="grid grid-cols-2 gap-3">
              <AppInput
                v-model="npc.description"
                label="Description:"
                placeholder="e.g., Friendly tavern keeper"
                @input="updateNPC(index)"
              />
              <AppInput
                v-model="npc.last_location"
                label="Location:"
                placeholder="e.g., The Prancing Pony"
                @input="updateNPC(index)"
              />
            </div>
          </AppCard>
          <AppButton variant="secondary" @click="addNPC"> + Add NPC </AppButton>
        </div>
      </AppCard>

      <!-- Quests -->
      <AppCard variant="subtle" padding="sm">
        <h6 class="font-medium mb-3 text-foreground">Active Quests</h6>
        <div class="space-y-3">
          <AppCard
            v-for="(quest, index) in quests"
            :key="quest.id"
            variant="subtle"
            padding="sm"
          >
            <div class="flex gap-2 mb-3">
              <AppInput
                v-model="quest.title"
                placeholder="Quest title"
                class="flex-1 font-medium"
                @input="updateQuest(index)"
              />
              <AppButton
                variant="danger"
                size="sm"
                title="Remove quest"
                @click="removeQuest(index)"
              >
                ✕
              </AppButton>
            </div>
            <AppTextarea
              v-model="quest.description"
              label="Description:"
              :rows="2"
              placeholder="Quest description"
              @input="updateQuest(index)"
            />
            <AppSelect
              v-model="quest.status"
              label="Status:"
              @change="updateQuest(index)"
            >
              <option value="active">Active</option>
              <option value="completed">Completed</option>
              <option value="failed">Failed</option>
              <option value="inactive">Inactive</option>
            </AppSelect>
          </AppCard>
          <AppButton variant="secondary" @click="addQuest">
            + Add Quest
          </AppButton>
        </div>
      </AppCard>

      <!-- World Lore -->
      <AppCard variant="subtle" padding="sm">
        <h6 class="font-medium mb-3 text-foreground">World Lore</h6>
        <AppTextarea
          v-model="worldLoreText"
          label="Lore Entries (one per line):"
          :rows="4"
          placeholder="e.g.&#10;The kingdom was founded 500 years ago&#10;Dragons are extinct in this realm&#10;Magic is rare and feared"
          @input="updateWorldLore"
        />
      </AppCard>

      <!-- Event Summary -->
      <AppCard variant="subtle" padding="sm">
        <h6 class="font-medium mb-3 text-foreground">Event History</h6>
        <AppTextarea
          v-model="eventSummaryText"
          label="Recent Events (one per line):"
          :rows="4"
          placeholder="e.g.&#10;Party defeated the goblin raiders&#10;Found mysterious artifact in the cave&#10;Met the wizard Gandalf"
          @input="updateEventSummary"
        />
      </AppCard>
    </div>
  </BasePanel>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import type { NPCModel, QuestModel } from '@/types/unified'
import BasePanel from '@/components/base/BasePanel.vue'
import AppCard from '@/components/base/AppCard.vue'
import AppButton from '@/components/base/AppButton.vue'
import AppInput from '@/components/base/AppInput.vue'
import AppTextarea from '@/components/base/AppTextarea.vue'
import AppSelect from '@/components/base/AppSelect.vue'

// Props
interface WorldStateConfig {
  campaign_goal: string
  known_npcs: Record<string, NPCModel>
  active_quests: Record<string, QuestModel>
  world_lore: string[]
  event_summary: string[]
  session_count: number
  active_ruleset_id?: string
}

const props = defineProps<{
  modelValue: WorldStateConfig
}>()

// Emits
const emit = defineEmits<{
  'update:modelValue': [value: WorldStateConfig]
}>()

// Local state
const localState = ref<Omit<WorldStateConfig, 'known_npcs' | 'active_quests'>>({
  campaign_goal: '',
  world_lore: [],
  event_summary: [],
  session_count: 0,
  active_ruleset_id: undefined,
})

const npcs = ref<NPCModel[]>([])
const quests = ref<QuestModel[]>([])
const worldLoreText = ref('')
const eventSummaryText = ref('')

// Initialize from props
watch(
  () => props.modelValue,
  newValue => {
    localState.value = {
      campaign_goal: newValue.campaign_goal,
      world_lore: newValue.world_lore,
      event_summary: newValue.event_summary,
      session_count: newValue.session_count,
      active_ruleset_id: newValue.active_ruleset_id,
    }

    npcs.value = Object.values(newValue.known_npcs)
    quests.value = Object.values(newValue.active_quests)
    worldLoreText.value = newValue.world_lore.join('\n')
    eventSummaryText.value = newValue.event_summary.join('\n')
  },
  { immediate: true }
)

// Methods
const emitUpdate = () => {
  const known_npcs: Record<string, NPCModel> = {}
  npcs.value.forEach(npc => {
    known_npcs[npc.id] = npc
  })

  const active_quests: Record<string, QuestModel> = {}
  quests.value.forEach(quest => {
    active_quests[quest.id] = quest
  })

  emit('update:modelValue', {
    ...localState.value,
    known_npcs,
    active_quests,
  })
}

// NPC methods
const addNPC = () => {
  const newNPC: NPCModel = {
    id: `npc_${Date.now()}`,
    name: `NPC ${npcs.value.length + 1}`,
    description: '',
    last_location: '',
  }
  npcs.value.push(newNPC)
  emitUpdate()
}

const removeNPC = (index: number) => {
  npcs.value.splice(index, 1)
  emitUpdate()
}

const updateNPC = (index: number) => {
  emitUpdate()
}

// Quest methods
const addQuest = () => {
  const newQuest: QuestModel = {
    id: `quest_${Date.now()}`,
    title: `Quest ${quests.value.length + 1}`,
    description: '',
    status: 'active',
  }
  quests.value.push(newQuest)
  emitUpdate()
}

const removeQuest = (index: number) => {
  quests.value.splice(index, 1)
  emitUpdate()
}

const updateQuest = (index: number) => {
  emitUpdate()
}

// Lore and event methods
const updateWorldLore = (event: Event) => {
  const target = event.target as HTMLTextAreaElement
  localState.value.world_lore = target.value
    .split('\n')
    .map(line => line.trim())
    .filter(line => line.length > 0)
  emitUpdate()
}

const updateEventSummary = (event: Event) => {
  const target = event.target as HTMLTextAreaElement
  localState.value.event_summary = target.value
    .split('\n')
    .map(line => line.trim())
    .filter(line => line.length > 0)
  emitUpdate()
}
</script>

<style scoped>
.world-configurator {
  margin-bottom: 1rem;
}
</style>
