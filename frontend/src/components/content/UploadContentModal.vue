<template>
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" @click.self="$emit('close')">
    <div class="bg-parchment rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[80vh] overflow-hidden flex flex-col">
      <div class="p-6 border-b border-gray-300">
        <!-- Header -->
        <div class="flex items-center justify-between">
          <h2 class="text-2xl font-cinzel font-bold text-text-primary">
            Upload Content to {{ pack.name }}
          </h2>
          <button
            @click="$emit('close')"
            class="text-text-secondary hover:text-text-primary transition-colors"
          >
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
            </svg>
          </button>
        </div>
      </div>

      <div class="flex-1 overflow-y-auto p-6">
        <!-- Instructions -->
        <div class="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <h3 class="font-semibold text-blue-900 mb-2">Upload Instructions</h3>
          <ul class="text-sm text-blue-800 space-y-1">
            <li>• Select the type of content you want to upload</li>
            <li>• Upload a JSON file or paste JSON content directly</li>
            <li>• Content must follow the D&D 5e SRD format</li>
            <li>• You can upload multiple items at once</li>
          </ul>
        </div>

        <!-- Content Type Selection -->
        <div class="mb-4">
          <label for="content-type" class="block text-sm font-medium text-text-primary mb-2">
            Content Type <span class="text-red-500">*</span>
          </label>
          <select
            id="content-type"
            v-model="selectedType"
            required
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold"
          >
            <option value="">Select content type...</option>
            <option v-for="type in contentTypes" :key="type" :value="type">
              {{ formatContentType(type) }}
            </option>
          </select>
        </div>

        <!-- File Upload -->
        <div class="mb-4">
          <label class="block text-sm font-medium text-text-primary mb-2">
            Upload JSON File
          </label>
          <div class="relative">
            <input
              type="file"
              accept=".json,application/json"
              @change="handleFileSelect"
              class="hidden"
              ref="fileInput"
            />
            <button
              type="button"
              @click="$refs.fileInput.click()"
              class="w-full px-4 py-3 border-2 border-dashed border-gray-300 rounded-lg hover:border-gold transition-colors flex items-center justify-center"
            >
              <svg class="w-6 h-6 mr-2 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"></path>
              </svg>
              <span class="text-gray-600">
                {{ selectedFile ? selectedFile.name : 'Click to upload or drag and drop' }}
              </span>
            </button>
          </div>
        </div>

        <!-- OR Divider -->
        <div class="relative my-6">
          <div class="absolute inset-0 flex items-center">
            <div class="w-full border-t border-gray-300"></div>
          </div>
          <div class="relative flex justify-center text-sm">
            <span class="px-2 bg-parchment text-gray-500">OR</span>
          </div>
        </div>

        <!-- Input Method Toggle -->
        <div class="mb-4">
          <div class="flex items-center justify-center space-x-4">
            <button
              @click="inputMethod = 'json'"
              :class="[
                'px-4 py-2 rounded-md transition-colors',
                inputMethod === 'json' 
                  ? 'bg-gold text-white' 
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              ]"
            >
              JSON Input
            </button>
            <button
              @click="inputMethod = 'form'"
              :class="[
                'px-4 py-2 rounded-md transition-colors',
                inputMethod === 'form' 
                  ? 'bg-gold text-white' 
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              ]"
            >
              Form Input
            </button>
          </div>
        </div>

        <!-- JSON Text Input -->
        <div v-if="inputMethod === 'json'" class="mb-4">
          <div class="flex justify-between items-center mb-2">
            <label for="json-content" class="block text-sm font-medium text-text-primary">
              Paste JSON Content
            </label>
            <button
              v-if="selectedType && jsonExamples[selectedType]"
              @click="copyJsonExample"
              type="button"
              class="text-sm px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
            >
              Copy Example
            </button>
          </div>
          <textarea
            id="json-content"
            v-model="jsonContent"
            rows="8"
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold font-mono text-sm"
            :placeholder="jsonPlaceholder"
          ></textarea>
        </div>

        <!-- Form Input -->
        <div v-else-if="inputMethod === 'form' && selectedType" class="mb-4">
          <ContentCreationForm 
            :content-type="selectedType"
            @json-generated="handleFormJSON"
          />
        </div>

        <!-- Upload Result -->
        <div v-if="uploadResult" class="mt-6">
          <div
            :class="[
              'p-4 rounded-lg',
              uploadResult.failed_items === 0
                ? 'bg-green-50 border border-green-200'
                : 'bg-yellow-50 border border-yellow-200'
            ]"
          >
            <h4 class="font-semibold mb-2" :class="uploadResult.failed_items === 0 ? 'text-green-900' : 'text-yellow-900'">
              Upload {{ uploadResult.failed_items === 0 ? 'Successful' : 'Completed with Errors' }}
            </h4>
            <div class="text-sm" :class="uploadResult.failed_items === 0 ? 'text-green-800' : 'text-yellow-800'">
              <p>• Total items: {{ uploadResult.total_items }}</p>
              <p>• Successful: {{ uploadResult.successful_items }}</p>
              <p v-if="uploadResult.failed_items > 0">• Failed: {{ uploadResult.failed_items }}</p>
            </div>
            
            <!-- Validation Errors -->
            <div v-if="Object.keys(uploadResult.validation_errors).length > 0" class="mt-3">
              <h5 class="font-medium text-red-900 mb-1">Validation Errors:</h5>
              <ul class="text-sm text-red-800 space-y-1">
                <li v-for="(error, key) in uploadResult.validation_errors" :key="key">
                  • {{ key }}: {{ error }}
                </li>
              </ul>
            </div>
            
            <!-- Warnings -->
            <div v-if="uploadResult.warnings.length > 0" class="mt-3">
              <h5 class="font-medium text-yellow-900 mb-1">Warnings:</h5>
              <ul class="text-sm text-yellow-800 space-y-1">
                <li v-for="warning in uploadResult.warnings" :key="warning">
                  • {{ warning }}
                </li>
              </ul>
            </div>
          </div>
        </div>

        <!-- Error message -->
        <div v-if="error" class="mt-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
          {{ error }}
        </div>
      </div>

      <!-- Footer Actions -->
      <div class="p-6 border-t border-gray-300 bg-gray-50">
        <div class="flex justify-end gap-3">
          <button
            type="button"
            @click="$emit('close')"
            class="px-4 py-2 text-gray-700 bg-gray-200 hover:bg-gray-300 rounded-md transition-colors"
          >
            {{ uploadResult ? 'Close' : 'Cancel' }}
          </button>
          <button
            v-if="!uploadResult"
            @click="handleUpload"
            :disabled="loading || !selectedType || (!selectedFile && !jsonContent && inputMethod === 'json')"
            class="fantasy-button px-4 py-2"
          >
            <span v-if="loading" class="inline-block animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></span>
            {{ loading ? 'Uploading...' : 'Upload Content' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useContentStore } from '../../stores/contentStore'
import type { ContentPack, ContentType, ContentUploadResult } from '../../types/content'
import ContentCreationForm from './ContentCreationForm.vue'

// Store
const contentStore = useContentStore()

// Props
const props = defineProps<{
  pack: ContentPack
}>()

// Emits
const emit = defineEmits<{
  close: []
  uploaded: []
}>()

// Content types - will be loaded from API
const contentTypes = ref<ContentType[]>([])

// State
const loading = ref(false)
const error = ref<string | null>(null)
const selectedType = ref<ContentType | ''>('')
const selectedFile = ref<File | null>(null)
const jsonContent = ref('')
const uploadResult = ref<ContentUploadResult | null>(null)
const fileInput = ref<HTMLInputElement>()
const inputMethod = ref<'json' | 'form'>('form')

// JSON Examples for each content type
const jsonExamples: Record<string, string> = {
  'spells': `[
  {
    "index": "custom-fireball",
    "name": "Custom Fireball",
    "desc": ["A bright streak flashes from your pointing finger to a point you choose within range and then blossoms with a low roar into an explosion of flame."],
    "higher_level": ["When you cast this spell using a spell slot of 4th level or higher, the damage increases by 1d6 for each slot level above 3rd."],
    "range": "150 feet",
    "components": ["V", "S", "M"],
    "material": "A tiny ball of bat guano and sulfur",
    "ritual": false,
    "duration": "Instantaneous",
    "concentration": false,
    "casting_time": "1 action",
    "level": 3,
    "school": "Evocation",
    "damage": {
      "damage_type": "Fire",
      "damage_at_slot_level": {
        "3": "8d6"
      }
    },
    "dc": {
      "dc_type": "DEX",
      "dc_success": "half"
    },
    "area_of_effect": {
      "type": "sphere",
      "size": 20
    },
    "classes": ["Sorcerer", "Wizard"]
  }
]`,
  'monsters': `[
  {
    "index": "custom-dragon",
    "name": "Custom Dragon",
    "size": "Large",
    "type": "dragon",
    "alignment": "chaotic evil",
    "armor_class": 18,
    "hit_points": 152,
    "hit_dice": "16d10+64",
    "speed": {
      "walk": "40 ft.",
      "fly": "80 ft."
    },
    "strength": 23,
    "dexterity": 10,
    "constitution": 19,
    "intelligence": 14,
    "wisdom": 11,
    "charisma": 17,
    "proficiencies": [
      {
        "value": 6,
        "proficiency": "Saving Throw: DEX"
      }
    ],
    "damage_resistances": [],
    "damage_immunities": ["fire"],
    "senses": {
      "blindsight": "30 ft.",
      "darkvision": "120 ft.",
      "passive_perception": 19
    },
    "languages": "Common, Draconic",
    "challenge_rating": 10,
    "xp": 5900,
    "actions": [
      {
        "name": "Bite",
        "desc": "Melee Weapon Attack: +10 to hit, reach 10 ft., one target. Hit: 17 (2d10 + 6) piercing damage plus 3 (1d6) fire damage."
      }
    ]
  }
]`,
  'equipment': `[
  {
    "index": "custom-sword",
    "name": "Custom Sword",
    "equipment_category": "Weapon",
    "weapon_category": "Martial",
    "weapon_range": "Melee",
    "category_range": "Martial Melee",
    "cost": {
      "quantity": 50,
      "unit": "gp"
    },
    "damage": {
      "damage_dice": "1d8",
      "damage_type": "Slashing"
    },
    "range": {
      "normal": 5
    },
    "weight": 3,
    "properties": [
      "Versatile"
    ],
    "two_handed_damage": {
      "damage_dice": "1d10",
      "damage_type": "Slashing"
    }
  }
]`,
  'classes': `[
  {
    "index": "custom-warrior",
    "name": "Custom Warrior",
    "hit_die": 10,
    "proficiency_choices": [
      {
        "desc": "Choose two skills from Acrobatics, Animal Handling, Athletics, History, Insight, Intimidation, Perception, and Survival",
        "choose": 2,
        "type": "proficiencies",
        "from": {
          "options": [
            {"name": "Skill: Acrobatics"},
            {"name": "Skill: Athletics"}
          ]
        }
      }
    ],
    "proficiencies": [
      "All armor",
      "Shields",
      "Simple weapons",
      "Martial weapons"
    ],
    "saving_throws": [
      "STR",
      "CON"
    ],
    "starting_equipment": [
      {
        "quantity": 1,
        "equipment": "Chain mail"
      }
    ],
    "class_levels": "/api/classes/custom-warrior/levels",
    "subclasses": []
  }
]`,
  'races': `[
  {
    "index": "custom-halfling",
    "name": "Custom Halfling",
    "speed": 25,
    "ability_bonuses": [
      { "ability_score": "DEX", "bonus": 2 }
    ],
    "alignment": "Lawful Good",
    "age": "A halfling reaches adulthood at 20 and lives into the middle of their second century.",
    "size": "Small",
    "size_description": "Halflings average about 3 feet tall and weigh about 40 pounds.",
    "starting_proficiencies": [],
    "languages": ["Common", "Halfling"],
    "language_desc": "You can speak, read, and write Common and Halfling.",
    "traits": [],
    "subraces": []
  }
]`,
  'backgrounds': `[
  {
    "index": "custom-soldier",
    "name": "Custom Soldier",
    "starting_proficiencies": ["Skill: Athletics", "Skill: Intimidation"],
    "language_options": {
      "choose": 1,
      "type": "languages",
      "from": { "options": [{"name": "Dwarvish"}, {"name": "Elvish"}] }
    },
    "starting_equipment": [
      { "equipment": "Clothes, common", "quantity": 1 }
    ],
    "feature": {
      "name": "Military Rank",
      "desc": ["You have a military rank from your career as a soldier."]
    },
    "personality_traits": {
      "choose": 2,
      "type": "personality_traits",
      "from": { "options": [] }
    }
  }
]`,
  'feats': `[
  {
    "index": "custom-alert",
    "name": "Custom Alert",
    "prerequisites": [],
    "desc": ["Always on the lookout for danger, you gain the following benefits:",
            "• You gain a +5 bonus to initiative.",
            "• You can't be surprised while you are conscious.",
            "• Other creatures don't gain advantage on attack rolls against you."]
  }
]`,
  'traits': `[
  {
    "index": "custom-darkvision",
    "name": "Custom Darkvision",
    "races": ["Dwarf", "Elf"],
    "subraces": [],
    "desc": ["You can see in dim light within 60 feet as if it were bright light."],
    "proficiencies": []
  }
]`,
  'skills': `[
  {
    "index": "custom-athletics",
    "name": "Custom Athletics",
    "desc": ["Your Athletics check covers difficult situations while climbing, jumping, or swimming."],
    "ability_score": "STR"
  }
]`,
  'conditions': `[
  {
    "index": "custom-stunned",
    "name": "Custom Stunned",
    "desc": ["• A stunned creature is incapacitated and can't move.",
            "• The creature automatically fails Strength and Dexterity saving throws.",
            "• Attack rolls against the creature have advantage."]
  }
]`,
  'magic-items': `[
  {
    "index": "custom-sword-of-fire",
    "name": "Custom Sword of Fire",
    "equipment_category": "Weapon",
    "desc": ["This magic sword deals an extra 1d6 fire damage on hit.",
            "While holding this sword, you have resistance to fire damage."],
    "rarity": { "name": "Rare" },
    "variant": false
  }
]`,
  'subclasses': `[
  {
    "index": "custom-champion",
    "name": "Custom Champion",
    "class": "Fighter",
    "subclass_flavor": "Martial Archetype",
    "desc": ["The archetypal Champion focuses on the development of raw physical power."],
    "subclass_levels": "/api/subclasses/champion/levels"
  }
]`,
  'alignments': `[
  {
    "index": "custom-neutral",
    "name": "Custom Neutral",
    "abbreviation": "CN",
    "desc": "Those who are neutral with respect to law and chaos have a normal respect for authority."
  }
]`,
  'ability-scores': `[
  {
    "index": "custom-str",
    "name": "Custom Strength",
    "full_name": "Strength",
    "desc": ["Strength measures bodily power, athletic training, and raw physical force."],
    "skills": ["Athletics"]
  }
]`,
  'damage-types': `[
  {
    "index": "custom-psychic",
    "name": "Custom Psychic",
    "desc": ["Mental abilities assault the mind, dealing psychic damage."]
  }
]`,
  'features': `[
  {
    "index": "custom-action-surge",
    "name": "Custom Action Surge",
    "level": 2,
    "class": "Fighter",
    "subclass": null,
    "desc": ["You can push yourself beyond your normal limits for a moment."]
  }
]`,
  'languages': `[
  {
    "index": "custom-draconic",
    "name": "Custom Draconic",
    "type": "Exotic",
    "typical_speakers": ["Dragons", "Dragonborn"],
    "script": "Draconic"
  }
]`,
  'levels': `[
  {
    "level": 1,
    "ability_score_bonuses": 0,
    "prof_bonus": 2,
    "features": [],
    "class": "Fighter",
    "subclass": null,
    "class_specific": {}
  }
]`,
  'proficiencies': `[
  {
    "index": "custom-shields",
    "name": "Custom Shields",
    "type": "Armor",
    "classes": ["Fighter", "Paladin"],
    "races": []
  }
]`,
  'rules': `[
  {
    "index": "custom-advantage",
    "name": "Custom Advantage",
    "desc": "When you have advantage on an attack roll or ability check, you roll two d20s and use the higher roll.",
    "subsections": []
  }
]`,
  'rule-sections': `[
  {
    "index": "custom-combat",
    "name": "Custom Combat",
    "desc": "This section provides the rules you need for your characters and monsters to engage in combat."
  }
]`,
  'subraces': `[
  {
    "index": "custom-hill-dwarf",
    "name": "Custom Hill Dwarf",
    "race": "Dwarf",
    "desc": "As a hill dwarf, you have keen senses, deep intuition, and remarkable resilience.",
    "ability_bonuses": [
      { "ability_score": "WIS", "bonus": 1 }
    ],
    "starting_proficiencies": [],
    "languages": [],
    "racial_traits": []
  }
]`,
  'weapon-properties': `[
  {
    "index": "custom-finesse",
    "name": "Custom Finesse",
    "desc": ["When making an attack with a finesse weapon, you use your choice of your Strength or Dexterity modifier."]
  }
]`,
  'equipment-categories': `[
  {
    "index": "custom-adventuring-gear",
    "name": "Custom Adventuring Gear",
    "equipment": [
      "Backpack",
      "Bedroll",
      "Rope"
    ]
  }
]`,
  '_default': `[
  {
    "index": "unique-identifier",
    "name": "Item Name",
    "desc": ["Description of the item"]
  }
]`
}

// Computed
const jsonPlaceholder = computed(() => {
  // selectedType is already in frontend format (underscores), which matches our jsonExamples keys
  if (selectedType.value && jsonExamples[selectedType.value]) {
    return jsonExamples[selectedType.value]
  }
  return jsonExamples['_default']
})

// Methods
function formatContentType(type: string): string {
  return type
    .split('-')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

function handleFileSelect(event: Event) {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  
  if (file) {
    // Validate file type
    if (!file.type.includes('json') && !file.name.endsWith('.json')) {
      error.value = 'Please select a JSON file'
      selectedFile.value = null
      return
    }
    
    // Validate file size (10MB limit)
    const MAX_FILE_SIZE = 10 * 1024 * 1024
    if (file.size > MAX_FILE_SIZE) {
      error.value = 'File too large (max 10MB)'
      selectedFile.value = null
      return
    }
    
    selectedFile.value = file
    // Clear text input when file is selected
    jsonContent.value = ''
    error.value = ''
  }
}

async function readFileContent(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = (e) => resolve(e.target?.result as string)
    reader.onerror = reject
    reader.readAsText(file)
  })
}

function handleFormJSON(json: string) {
  jsonContent.value = json
  // Optionally switch back to JSON view to show the generated content
  inputMethod.value = 'json'
}

function copyJsonExample() {
  if (selectedType.value && jsonExamples[selectedType.value]) {
    navigator.clipboard.writeText(jsonExamples[selectedType.value])
      .then(() => {
        // Optional: Add a toast notification or visual feedback
      })
      .catch(err => {
        console.error('Failed to copy:', err)
      })
  }
}

async function handleUpload() {
  if (!selectedType.value) {
    error.value = 'Please select a content type'
    return
  }

  error.value = null
  loading.value = true
  uploadResult.value = null

  try {
    let content: any

    // Get content from file or text input
    if (selectedFile.value) {
      const fileContent = await readFileContent(selectedFile.value)
      try {
        content = JSON.parse(fileContent)
      } catch (e) {
        throw new Error('Invalid JSON in file')
      }
    } else if (jsonContent.value) {
      try {
        content = JSON.parse(jsonContent.value)
      } catch (e) {
        throw new Error('Invalid JSON content')
      }
    } else {
      throw new Error('No content provided')
    }

    const result = await contentStore.uploadContent(props.pack.id, selectedType.value, content)
    
    if (result) {
      uploadResult.value = result
      emit('uploaded')
    } else {
      throw new Error(contentStore.error || 'Upload failed')
    }
  } catch (err: any) {
    error.value = err.message || 'Failed to upload content'
    console.error('Error uploading content:', err)
  } finally {
    loading.value = false
  }
}

// Load supported content types on mount
onMounted(async () => {
  await contentStore.loadSupportedTypes()
  
  contentTypes.value = contentStore.supportedTypes as ContentType[]
})
</script>