<template>
  <div v-if="visible" class="fixed inset-0 z-50 flex items-center justify-center p-4">
    <!-- Backdrop -->
    <div 
      class="absolute inset-0 bg-black bg-opacity-50"
      @click="$emit('close')"
    />
    
    <!-- Modal -->
    <div class="relative bg-parchment rounded-lg shadow-xl max-w-6xl w-full max-h-[95vh] overflow-y-auto">
      <div class="fantasy-panel">
        <!-- Header -->
        <div class="flex items-center justify-between mb-6">
          <h2 class="text-xl font-cinzel font-bold text-text-primary">
            {{ template ? 'Edit Character Template' : 'Create Character Template' }}
          </h2>
          <button
            @click="$emit('close')"
            class="text-text-secondary hover:text-text-primary"
          >
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        <!-- Loading State -->
        <div v-if="d5eData.isLoading.value" class="text-center py-8">
          <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-gold"></div>
          <p class="mt-2 text-text-secondary">Loading D&D 5e data...</p>
        </div>
        
        <!-- Form -->
        <form v-else @submit.prevent="handleSave" class="space-y-8">
          <!-- Tab Navigation -->
          <div class="border-b border-gold/20">
            <nav class="flex space-x-8">
              <button
                v-for="tab in tabs"
                :key="tab.id"
                type="button"
                @click="activeTab = tab.id"
                :class="[
                  'pb-2 font-medium text-sm transition-colors',
                  activeTab === tab.id 
                    ? 'text-gold border-b-2 border-gold' 
                    : 'text-text-secondary hover:text-gold'
                ]"
              >
                {{ tab.label }}
              </button>
            </nav>
          </div>

          <!-- Tab Content -->
          <div class="min-h-[400px]">
            <!-- Basic Information Tab -->
            <div v-if="activeTab === 'basic'" class="grid grid-cols-1 lg:grid-cols-2 gap-8">
              <!-- Left Column -->
              <div class="space-y-6">
                <h3 class="text-lg font-cinzel font-semibold text-text-primary">Character Details</h3>
                
                <!-- Character Name -->
                <div>
                  <label class="block text-sm font-medium text-text-primary mb-2">
                    Character Name *
                  </label>
                  <input
                    v-model="formData.name"
                    type="text"
                    required
                    class="fantasy-input w-full"
                    placeholder="Enter character name..."
                  />
                </div>
                
                <!-- Race Selection -->
                <div>
                  <label class="block text-sm font-medium text-text-primary mb-2">
                    Race *
                  </label>
                  <select
                    v-model="formData.race"
                    required
                    class="fantasy-input w-full"
                    @change="onRaceChange"
                  >
                    <option value="">Select a race...</option>
                    <option
                      v-for="race in d5eData.getRaceOptions()"
                      :key="race.value"
                      :value="race.value"
                    >
                      {{ race.label }}
                    </option>
                  </select>
                </div>

                <!-- Subrace Selection -->
                <div v-if="subraceOptions.length > 0">
                  <label class="block text-sm font-medium text-text-primary mb-2">
                    Subrace
                  </label>
                  <select
                    v-model="formData.subrace"
                    class="fantasy-input w-full"
                    @change="onSubraceChange"
                  >
                    <option value="">Select a subrace...</option>
                    <option
                      v-for="subrace in subraceOptions"
                      :key="subrace.value"
                      :value="subrace.value"
                    >
                      {{ subrace.label }}
                    </option>
                  </select>
                </div>
                
                <!-- Class Selection -->
                <div>
                  <label class="block text-sm font-medium text-text-primary mb-2">
                    Class *
                  </label>
                  <select
                    v-model="formData.class"
                    required
                    class="fantasy-input w-full"
                    @change="onClassChange"
                  >
                    <option value="">Select a class...</option>
                    <option
                      v-for="clazz in d5eData.getClassOptions()"
                      :key="clazz.value"
                      :value="clazz.value"
                    >
                      {{ clazz.label }}
                    </option>
                  </select>
                </div>

                <!-- Subclass Selection -->
                <div v-if="subclassOptions.length > 0">
                  <label class="block text-sm font-medium text-text-primary mb-2">
                    Subclass
                  </label>
                  <select
                    v-model="formData.subclass"
                    class="fantasy-input w-full"
                  >
                    <option value="">Select a subclass...</option>
                    <option
                      v-for="subclass in subclassOptions"
                      :key="subclass.value"
                      :value="subclass.value"
                    >
                      {{ subclass.label }}
                    </option>
                  </select>
                </div>
              </div>

              <!-- Right Column -->
              <div class="space-y-6">
                <h3 class="text-lg font-cinzel font-semibold text-text-primary">Character Basics</h3>
                
                <!-- Level -->
                <div>
                  <label class="block text-sm font-medium text-text-primary mb-2">
                    Level
                  </label>
                  <input
                    v-model.number="formData.level"
                    type="number"
                    min="1"
                    max="20"
                    class="fantasy-input w-full"
                    @input="calculateHitPoints"
                  />
                </div>
                
                <!-- Background -->
                <div>
                  <label class="block text-sm font-medium text-text-primary mb-2">
                    Background
                  </label>
                  <select
                    v-model="formData.background"
                    class="fantasy-input w-full"
                  >
                    <option value="">Select a background...</option>
                    <option
                      v-for="bg in d5eData.getBackgroundOptions()"
                      :key="bg.value"
                      :value="bg.value"
                    >
                      {{ bg.label }}
                    </option>
                  </select>
                </div>

                <!-- Alignment -->
                <div>
                  <label class="block text-sm font-medium text-text-primary mb-2">
                    Alignment
                  </label>
                  <select
                    v-model="formData.alignment"
                    class="fantasy-input w-full"
                  >
                    <option value="">Select alignment...</option>
                    <option
                      v-for="alignment in d5eData.getAlignmentOptions()"
                      :key="alignment.value"
                      :value="alignment.value"
                    >
                      {{ alignment.label }}
                    </option>
                  </select>
                </div>

                <!-- Description -->
                <div>
                  <label class="block text-sm font-medium text-text-primary mb-2">
                    Description
                  </label>
                  <textarea
                    v-model="formData.description"
                    rows="4"
                    class="fantasy-input w-full resize-none"
                    placeholder="Describe this character template..."
                  ></textarea>
                </div>
              </div>
            </div>

            <!-- Ability Scores Tab -->
            <div v-if="activeTab === 'abilities'" class="space-y-6">
              <div class="flex justify-between items-center">
                <h3 class="text-lg font-cinzel font-semibold text-text-primary">Ability Scores</h3>
                <div class="flex space-x-2">
                  <button
                    type="button"
                    @click="pointBuy.resetScores()"
                    class="fantasy-button-secondary text-sm"
                  >
                    Reset
                  </button>
                  <button
                    type="button"
                    @click="pointBuy.applyStandardArray()"
                    class="fantasy-button-secondary text-sm"
                  >
                    Standard Array
                  </button>
                </div>
              </div>

              <!-- Point Buy Info -->
              <div class="bg-secondary/20 rounded-lg p-4">
                <div class="flex justify-between items-center text-sm">
                  <span class="text-text-secondary">Points Spent:</span>
                  <span :class="pointBuy.isValid.value ? 'text-green-600' : 'text-red-600'">
                    {{ pointBuy.pointsSpent.value }} / {{ pointBuy.MAX_POINTS }}
                  </span>
                </div>
                <div class="flex justify-between items-center text-sm mt-1">
                  <span class="text-text-secondary">Points Remaining:</span>
                  <span :class="pointBuy.pointsRemaining.value >= 0 ? 'text-green-600' : 'text-red-600'">
                    {{ pointBuy.pointsRemaining.value }}
                  </span>
                </div>
              </div>

              <!-- Ability Score Grid -->
              <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                <div
                  v-for="(ability, key) in pointBuy.baseScores"
                  :key="key"
                  class="bg-secondary/10 rounded-lg p-4"
                >
                  <div class="text-center">
                    <h4 class="font-cinzel font-semibold text-text-primary">
                      {{ d5eData.getAbilityInfo(key).name }}
                    </h4>
                    <p class="text-xs text-text-secondary mb-3">
                      {{ d5eData.getAbilityInfo(key).description }}
                    </p>
                    
                    <!-- Score Controls -->
                    <div class="flex items-center justify-center space-x-2 mb-2">
                      <button
                        type="button"
                        @click="pointBuy.decreaseAbility(key)"
                        :disabled="!pointBuy.canDecrease(key)"
                        class="w-8 h-8 rounded-full bg-red-600 text-white disabled:bg-gray-400 disabled:cursor-not-allowed hover:bg-red-700 transition-colors"
                      >
                        -
                      </button>
                      <div class="w-16 text-center">
                        <input
                          :value="ability"
                          @input="(e) => pointBuy.setAbilityScore(key, parseInt(e.target.value) || 8)"
                          type="number"
                          :min="pointBuy.MIN_SCORE"
                          :max="pointBuy.MAX_SCORE"
                          class="w-full text-center fantasy-input"
                        />
                      </div>
                      <button
                        type="button"
                        @click="pointBuy.increaseAbility(key)"
                        :disabled="!pointBuy.canIncrease(key)"
                        class="w-8 h-8 rounded-full bg-green-600 text-white disabled:bg-gray-400 disabled:cursor-not-allowed hover:bg-green-700 transition-colors"
                      >
                        +
                      </button>
                    </div>

                    <!-- Racial Bonus -->
                    <div v-if="racialBonuses[key]" class="text-xs text-gold mb-1">
                      Racial: +{{ racialBonuses[key] }}
                    </div>

                    <!-- Final Score -->
                    <div class="text-lg font-bold text-text-primary">
                      {{ totalAbilityScores[key] }}
                      <span class="text-sm text-text-secondary">
                        ({{ d5eData.getAbilityModifier(totalAbilityScores[key]) >= 0 ? '+' : '' }}{{ d5eData.getAbilityModifier(totalAbilityScores[key]) }})
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Calculated Stats -->
              <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
                <div class="text-center bg-secondary/10 rounded-lg p-4">
                  <h4 class="font-cinzel font-semibold text-text-primary">Hit Points</h4>
                  <div class="text-2xl font-bold text-gold mt-2">{{ calculatedHitPoints }}</div>
                </div>
                <div class="text-center bg-secondary/10 rounded-lg p-4">
                  <h4 class="font-cinzel font-semibold text-text-primary">Armor Class</h4>
                  <div class="text-2xl font-bold text-gold mt-2">{{ calculatedArmorClass }}</div>
                </div>
                <div class="text-center bg-secondary/10 rounded-lg p-4">
                  <h4 class="font-cinzel font-semibold text-text-primary">Proficiency Bonus</h4>
                  <div class="text-2xl font-bold text-gold mt-2">+{{ d5eData.getProficiencyBonus(formData.level) }}</div>
                </div>
              </div>
            </div>

            <!-- Features Tab -->
            <div v-if="activeTab === 'features'" class="space-y-6">
              <h3 class="text-lg font-cinzel font-semibold text-text-primary">Racial Traits & Class Features</h3>
              
              <!-- Racial Traits -->
              <div v-if="racialTraits.traits.length > 0" class="bg-secondary/10 rounded-lg p-4">
                <h4 class="font-cinzel font-semibold text-text-primary mb-3">Racial Traits</h4>
                <div class="space-y-2">
                  <div
                    v-for="trait in racialTraits.traits"
                    :key="trait.name"
                    class="border-l-4 border-gold pl-3"
                  >
                    <h5 class="font-semibold text-text-primary">{{ trait.name }}</h5>
                    <p class="text-sm text-text-secondary">{{ trait.description }}</p>
                  </div>
                </div>
              </div>

              <!-- Class Proficiencies -->
              <div v-if="classProficiencies.armor?.length > 0 || classProficiencies.weapons?.length > 0" class="bg-secondary/10 rounded-lg p-4">
                <h4 class="font-cinzel font-semibold text-text-primary mb-3">Class Proficiencies</h4>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div v-if="classProficiencies.armor?.length > 0">
                    <h5 class="font-semibold text-text-primary">Armor</h5>
                    <ul class="text-sm text-text-secondary">
                      <li v-for="armor in classProficiencies.armor" :key="armor">{{ armor }}</li>
                    </ul>
                  </div>
                  <div v-if="classProficiencies.weapons?.length > 0">
                    <h5 class="font-semibold text-text-primary">Weapons</h5>
                    <ul class="text-sm text-text-secondary">
                      <li v-for="weapon in classProficiencies.weapons" :key="weapon">{{ weapon }}</li>
                    </ul>
                  </div>
                </div>
              </div>

              <!-- Languages -->
              <div v-if="racialTraits.languages.length > 0" class="bg-secondary/10 rounded-lg p-4">
                <h4 class="font-cinzel font-semibold text-text-primary mb-3">Languages</h4>
                <div class="flex flex-wrap gap-2">
                  <span
                    v-for="language in racialTraits.languages"
                    :key="language"
                    class="px-3 py-1 bg-gold/20 text-text-primary rounded-full text-sm"
                  >
                    {{ language }}
                  </span>
                </div>
              </div>
            </div>
          </div>
          
          <!-- Actions -->
          <div class="flex justify-end space-x-3 pt-4 border-t border-gold/20">
            <button
              type="button"
              @click="$emit('close')"
              class="fantasy-button-secondary"
            >
              Cancel
            </button>
            <button
              type="submit"
              :disabled="!pointBuy.isValid.value"
              class="fantasy-button disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {{ template ? 'Update' : 'Create' }} Template
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useD5eData } from '../../composables/useD5eData'
import { usePointBuy } from '../../composables/usePointBuy'

const props = defineProps({
  visible: {
    type: Boolean,
    required: true
  },
  template: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['close', 'save'])

// Composables
const d5eData = useD5eData()
const pointBuy = usePointBuy()

// State
const activeTab = ref('basic')
const tabs = [
  { id: 'basic', label: 'Basic Info' },
  { id: 'abilities', label: 'Ability Scores' },
  { id: 'features', label: 'Features & Traits' }
]

const formData = ref({
  name: '',
  race: '',
  subrace: '',
  class: '',
  subclass: '',
  level: 1,
  background: '',
  alignment: '',
  description: ''
})

// Computed properties
const subraceOptions = computed(() => {
  return formData.value.race ? d5eData.getSubraceOptions(formData.value.race) : []
})

const subclassOptions = computed(() => {
  return formData.value.class ? d5eData.getSubclassOptions(formData.value.class) : []
})

const racialBonuses = computed(() => {
  if (!formData.value.race) return {}
  
  const race = d5eData.races.value[formData.value.race]
  if (!race) return {}
  
  let bonuses = { ...race.ability_score_increase } || {}
  
  // Add subrace bonuses
  if (formData.value.subrace && race.subraces?.[formData.value.subrace]?.ability_score_increase) {
    Object.entries(race.subraces[formData.value.subrace].ability_score_increase).forEach(([ability, bonus]) => {
      bonuses[ability] = (bonuses[ability] || 0) + bonus
    })
  }
  
  return bonuses
})

const totalAbilityScores = computed(() => {
  return d5eData.calculateTotalAbilityScores(
    pointBuy.baseScores,
    formData.value.race,
    formData.value.subrace
  )
})

const calculatedHitPoints = computed(() => {
  const conModifier = d5eData.getAbilityModifier(totalAbilityScores.value.CON || 10)
  return d5eData.calculateHitPoints(formData.value.class, formData.value.level, conModifier)
})

const calculatedArmorClass = computed(() => {
  const dexModifier = d5eData.getAbilityModifier(totalAbilityScores.value.DEX || 10)
  return 10 + dexModifier // Base AC + Dex modifier
})

const classProficiencies = computed(() => {
  return d5eData.getClassProficiencies(formData.value.class)
})

const racialTraits = computed(() => {
  return d5eData.getRacialTraits(formData.value.race, formData.value.subrace)
})

// Methods
function onRaceChange() {
  formData.value.subrace = '' // Reset subrace when race changes
  calculateHitPoints()
}

function onSubraceChange() {
  calculateHitPoints()
}

function onClassChange() {
  formData.value.subclass = '' // Reset subclass when class changes
  calculateHitPoints()
}

function calculateHitPoints() {
  // This is handled by the computed property
}

function handleSave() {
  const templateData = {
    ...formData.value,
    base_stats: pointBuy.exportScores(),
    total_stats: totalAbilityScores.value,
    hit_points: calculatedHitPoints.value,
    armor_class: calculatedArmorClass.value,
    proficiency_bonus: d5eData.getProficiencyBonus(formData.value.level),
    racial_traits: racialTraits.value,
    class_proficiencies: classProficiencies.value
  }
  
  emit('save', templateData)
}

// Watch for template changes
watch(() => props.template, (newTemplate) => {
  if (newTemplate) {
    formData.value = {
      name: newTemplate.name || '',
      race: newTemplate.race || '',
      subrace: newTemplate.subrace || '',
      class: newTemplate.class || '',
      subclass: newTemplate.subclass || '',
      level: newTemplate.level || 1,
      background: newTemplate.background || '',
      alignment: newTemplate.alignment || '',
      description: newTemplate.description || ''
    }
    
    // Load ability scores into point buy system
    if (newTemplate.base_stats) {
      pointBuy.loadFromTemplate(newTemplate)
    }
  } else {
    // Reset form for new template
    formData.value = {
      name: '',
      race: '',
      subrace: '',
      class: '',
      subclass: '',
      level: 1,
      background: '',
      alignment: '',
      description: ''
    }
    pointBuy.resetScores()
  }
  activeTab.value = 'basic'
}, { immediate: true })
</script>
