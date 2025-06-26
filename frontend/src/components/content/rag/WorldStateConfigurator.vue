<template>
  <div class="world-configurator">
    <h5 class="world-configurator__title">
      World State
    </h5>
    
    <div class="world-configurator__sections">
      <!-- Campaign Context -->
      <div class="world-configurator__section">
        <h6>Campaign Context</h6>
        <div class="world-configurator__field">
          <label>Campaign Goal:</label>
          <textarea
            v-model="localState.campaign_goal"
            rows="2"
            placeholder="e.g., Defeat the evil necromancer threatening the kingdom"
            class="world-configurator__textarea"
            @input="emitUpdate"
          />
        </div>
        <div class="world-configurator__field-group">
          <div class="world-configurator__field world-configurator__field--small">
            <label>Session Count:</label>
            <input
              v-model.number="localState.session_count"
              type="number"
              min="0"
              class="world-configurator__input"
              @input="emitUpdate"
            >
          </div>
          <div class="world-configurator__field">
            <label>Active Ruleset:</label>
            <input
              v-model="localState.active_ruleset_id"
              type="text"
              placeholder="e.g., dnd_5e_srd"
              class="world-configurator__input"
              @input="emitUpdate"
            >
          </div>
        </div>
      </div>
      
      <!-- NPCs -->
      <div class="world-configurator__section">
        <h6>Known NPCs</h6>
        <div class="world-configurator__npcs">
          <div
            v-for="(npc, index) in npcs"
            :key="npc.id"
            class="world-configurator__npc"
          >
            <div class="world-configurator__npc-header">
              <input
                v-model="npc.name"
                type="text"
                placeholder="NPC name"
                class="world-configurator__input world-configurator__input--name"
                @input="updateNPC(index)"
              >
              <button
                @click="removeNPC(index)"
                class="world-configurator__button world-configurator__button--remove"
                title="Remove NPC"
              >
                ✕
              </button>
            </div>
            <div class="world-configurator__field-group">
              <div class="world-configurator__field">
                <label>Description:</label>
                <input
                  v-model="npc.description"
                  type="text"
                  placeholder="e.g., Friendly tavern keeper"
                  class="world-configurator__input"
                  @input="updateNPC(index)"
                >
              </div>
              <div class="world-configurator__field">
                <label>Location:</label>
                <input
                  v-model="npc.last_location"
                  type="text"
                  placeholder="e.g., The Prancing Pony"
                  class="world-configurator__input"
                  @input="updateNPC(index)"
                >
              </div>
            </div>
          </div>
          <button
            @click="addNPC"
            class="world-configurator__button world-configurator__button--add"
          >
            + Add NPC
          </button>
        </div>
      </div>
      
      <!-- Quests -->
      <div class="world-configurator__section">
        <h6>Active Quests</h6>
        <div class="world-configurator__quests">
          <div
            v-for="(quest, index) in quests"
            :key="quest.id"
            class="world-configurator__quest"
          >
            <div class="world-configurator__quest-header">
              <input
                v-model="quest.title"
                type="text"
                placeholder="Quest title"
                class="world-configurator__input world-configurator__input--name"
                @input="updateQuest(index)"
              >
              <button
                @click="removeQuest(index)"
                class="world-configurator__button world-configurator__button--remove"
                title="Remove quest"
              >
                ✕
              </button>
            </div>
            <div class="world-configurator__field">
              <label>Description:</label>
              <textarea
                v-model="quest.description"
                rows="2"
                placeholder="Quest description"
                class="world-configurator__textarea"
                @input="updateQuest(index)"
              />
            </div>
            <div class="world-configurator__field">
              <label>Status:</label>
              <select
                v-model="quest.status"
                class="world-configurator__select"
                @change="updateQuest(index)"
              >
                <option value="active">Active</option>
                <option value="completed">Completed</option>
                <option value="failed">Failed</option>
                <option value="inactive">Inactive</option>
              </select>
            </div>
          </div>
          <button
            @click="addQuest"
            class="world-configurator__button world-configurator__button--add"
          >
            + Add Quest
          </button>
        </div>
      </div>
      
      <!-- World Lore -->
      <div class="world-configurator__section">
        <h6>World Lore</h6>
        <div class="world-configurator__field">
          <label>Lore Entries (one per line):</label>
          <textarea
            v-model="worldLoreText"
            rows="4"
            placeholder="e.g.&#10;The kingdom was founded 500 years ago&#10;Dragons are extinct in this realm&#10;Magic is rare and feared"
            class="world-configurator__textarea"
            @input="updateWorldLore"
          />
        </div>
      </div>
      
      <!-- Event Summary -->
      <div class="world-configurator__section">
        <h6>Event History</h6>
        <div class="world-configurator__field">
          <label>Recent Events (one per line):</label>
          <textarea
            v-model="eventSummaryText"
            rows="4"
            placeholder="e.g.&#10;Party defeated the goblin raiders&#10;Found mysterious artifact in the cave&#10;Met the wizard Gandalf"
            class="world-configurator__textarea"
            @input="updateEventSummary"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import type { NPCModel, QuestModel } from '@/types/unified'

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
  active_ruleset_id: undefined
})

const npcs = ref<NPCModel[]>([])
const quests = ref<QuestModel[]>([])
const worldLoreText = ref('')
const eventSummaryText = ref('')

// Initialize from props
watch(() => props.modelValue, (newValue) => {
  localState.value = {
    campaign_goal: newValue.campaign_goal,
    world_lore: newValue.world_lore,
    event_summary: newValue.event_summary,
    session_count: newValue.session_count,
    active_ruleset_id: newValue.active_ruleset_id
  }
  
  npcs.value = Object.values(newValue.known_npcs)
  quests.value = Object.values(newValue.active_quests)
  worldLoreText.value = newValue.world_lore.join('\n')
  eventSummaryText.value = newValue.event_summary.join('\n')
}, { immediate: true })

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
    active_quests
  })
}

// NPC methods
const addNPC = () => {
  const newNPC: NPCModel = {
    id: `npc_${Date.now()}`,
    name: `NPC ${npcs.value.length + 1}`,
    description: '',
    last_location: ''
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
    status: 'active'
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
  background: #f8f9fa;
  padding: 1rem;
  border-radius: 6px;
  margin-bottom: 1rem;
}

.world-configurator__title {
  margin: 0 0 1rem 0;
  font-size: 1.1rem;
  font-weight: 600;
  color: #333;
}

.world-configurator__sections {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.world-configurator__section {
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  padding: 1rem;
}

.world-configurator__section h6 {
  margin: 0 0 0.75rem 0;
  font-size: 1rem;
  font-weight: 600;
  color: #555;
}

.world-configurator__field {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  margin-bottom: 0.75rem;
}

.world-configurator__field:last-child {
  margin-bottom: 0;
}

.world-configurator__field-group {
  display: flex;
  gap: 0.75rem;
  margin-bottom: 0.75rem;
}

.world-configurator__field--small {
  flex: 0 0 auto;
  min-width: 120px;
}

.world-configurator__field label {
  font-size: 0.85rem;
  font-weight: 500;
  color: #666;
}

.world-configurator__input,
.world-configurator__textarea,
.world-configurator__select {
  padding: 0.375rem 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 0.9rem;
}

.world-configurator__textarea {
  resize: vertical;
  min-height: 60px;
  font-family: inherit;
}

.world-configurator__input--name {
  flex: 1;
  font-weight: 500;
}

.world-configurator__npcs,
.world-configurator__quests {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.world-configurator__npc,
.world-configurator__quest {
  background: #f8f9fa;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  padding: 0.75rem;
}

.world-configurator__npc-header,
.world-configurator__quest-header {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}

.world-configurator__button {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 4px;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s;
}

.world-configurator__button--add {
  background: #28a745;
  color: white;
  margin-top: 0.5rem;
}

.world-configurator__button--add:hover {
  background: #218838;
}

.world-configurator__button--remove {
  background: #dc3545;
  color: white;
  padding: 0.25rem 0.5rem;
  font-size: 0.8rem;
}

.world-configurator__button--remove:hover {
  background: #c82333;
}
</style>