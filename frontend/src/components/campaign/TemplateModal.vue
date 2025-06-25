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
            class="text-text-secondary hover:text-text-primary"
            @click="$emit('close')"
          >
            <svg
              class="w-6 h-6"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>

        <!-- Loading State -->
        <div v-if="d5eData.isLoading.value" class="text-center py-8">
          <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-gold" />
          <p class="mt-2 text-text-secondary">
            Loading D&D 5e data...
          </p>
        </div>

        <!-- Form -->
        <form v-else class="space-y-8" @submit.prevent="handleSave">
          <!-- Tab Navigation -->
          <div class="border-b border-gold/20">
            <nav class="flex space-x-8">
              <button
                v-for="tab in tabs"
                :key="tab.id"
                type="button"
                :class="[
                  'pb-2 font-medium text-sm transition-colors',
                  activeTab === tab.id
                    ? 'text-gold border-b-2 border-gold'
                    : 'text-text-secondary hover:text-gold'
                ]"
                @click="activeTab = tab.id"
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
                <h3 class="text-lg font-cinzel font-semibold text-text-primary">
                  Character Details
                </h3>

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
                  >
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
                    <option value="">
                      Select a race...
                    </option>
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
                    <option value="">
                      Select a subrace...
                    </option>
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
                    v-model="formData.char_class"
                    required
                    class="fantasy-input w-full"
                    @change="onClassChange"
                  >
                    <option value="">
                      Select a class...
                    </option>
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
                    <option value="">
                      Select a subclass...
                    </option>
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
                <h3 class="text-lg font-cinzel font-semibold text-text-primary">
                  Character Basics
                </h3>

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
                  >
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
                    <option value="">
                      Select a background...
                    </option>
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
                    <option value="">
                      Select alignment...
                    </option>
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
                  />
                </div>
              </div>
            </div>

            <!-- Ability Scores Tab -->
            <div v-if="activeTab === 'abilities'" class="space-y-6">
              <div class="flex justify-between items-center">
                <h3 class="text-lg font-cinzel font-semibold text-text-primary">
                  Ability Scores
                </h3>
                <div class="flex space-x-2">
                  <button
                    type="button"
                    class="fantasy-button-secondary text-sm"
                    @click="pointBuy.resetScores()"
                  >
                    Reset
                  </button>
                  <button
                    type="button"
                    class="fantasy-button-secondary text-sm"
                    @click="pointBuy.applyStandardArray()"
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
                        :disabled="!pointBuy.canDecrease(key)"
                        class="w-8 h-8 rounded-full bg-red-600 text-white disabled:bg-gray-400 disabled:cursor-not-allowed hover:bg-red-700 transition-colors"
                        @click="pointBuy.decreaseAbility(key)"
                      >
                        -
                      </button>
                      <div class="w-16 text-center">
                        <input
                          :value="ability"
                          type="number"
                          :min="pointBuy.MIN_SCORE"
                          :max="pointBuy.MAX_SCORE"
                          class="w-full text-center fantasy-input"
                          @input="(e) => pointBuy.setAbilityScore(key, parseInt(e.target.value) || 8)"
                        >
                      </div>
                      <button
                        type="button"
                        :disabled="!pointBuy.canIncrease(key)"
                        class="w-8 h-8 rounded-full bg-green-600 text-white disabled:bg-gray-400 disabled:cursor-not-allowed hover:bg-green-700 transition-colors"
                        @click="pointBuy.increaseAbility(key)"
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
                  <h4 class="font-cinzel font-semibold text-text-primary">
                    Hit Points
                  </h4>
                  <div class="text-2xl font-bold text-gold mt-2">
                    {{ calculatedHitPoints }}
                  </div>
                </div>
                <div class="text-center bg-secondary/10 rounded-lg p-4">
                  <h4 class="font-cinzel font-semibold text-text-primary">
                    Armor Class
                  </h4>
                  <div class="text-2xl font-bold text-gold mt-2">
                    {{ calculatedArmorClass }}
                  </div>
                </div>
                <div class="text-center bg-secondary/10 rounded-lg p-4">
                  <h4 class="font-cinzel font-semibold text-text-primary">
                    Proficiency Bonus
                  </h4>
                  <div class="text-2xl font-bold text-gold mt-2">
                    +{{ d5eData.getProficiencyBonus(formData.level) }}
                  </div>
                </div>
              </div>
            </div>

            <!-- Features Tab -->
            <div v-if="activeTab === 'features'" class="space-y-6">
              <h3 class="text-lg font-cinzel font-semibold text-text-primary">
                Racial Traits & Class Features
              </h3>

              <!-- Racial Traits -->
              <div v-if="racialTraits.traits.length > 0" class="bg-secondary/10 rounded-lg p-4">
                <h4 class="font-cinzel font-semibold text-text-primary mb-3">
                  Racial Traits
                </h4>
                <div class="space-y-2">
                  <div
                    v-for="trait in racialTraits.traits"
                    :key="trait.name"
                    class="border-l-4 border-gold pl-3"
                  >
                    <h5 class="font-semibold text-text-primary">
                      {{ trait.name }}
                    </h5>
                    <p class="text-sm text-text-secondary">
                      {{ trait.description }}
                    </p>
                  </div>
                </div>
              </div>

              <!-- Class Proficiencies -->
              <div v-if="classProficiencies.armor?.length > 0 || classProficiencies.weapons?.length > 0" class="bg-secondary/10 rounded-lg p-4">
                <h4 class="font-cinzel font-semibold text-text-primary mb-3">
                  Class Proficiencies
                </h4>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div v-if="classProficiencies.armor?.length > 0">
                    <h5 class="font-semibold text-text-primary">
                      Armor
                    </h5>
                    <ul class="text-sm text-text-secondary">
                      <li v-for="armor in classProficiencies.armor" :key="armor">
                        {{ armor }}
                      </li>
                    </ul>
                  </div>
                  <div v-if="classProficiencies.weapons?.length > 0">
                    <h5 class="font-semibold text-text-primary">
                      Weapons
                    </h5>
                    <ul class="text-sm text-text-secondary">
                      <li v-for="weapon in classProficiencies.weapons" :key="weapon">
                        {{ weapon }}
                      </li>
                    </ul>
                  </div>
                </div>
              </div>

              <!-- Languages -->
              <div v-if="racialTraits.languages.length > 0" class="bg-secondary/10 rounded-lg p-4">
                <h4 class="font-cinzel font-semibold text-text-primary mb-3">
                  Languages
                </h4>
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

            <!-- Spells & Magic Tab -->
            <div v-if="activeTab === 'spells'" class="space-y-6">
              <h3 class="text-lg font-cinzel font-semibold text-text-primary">
                Spells & Magical Abilities
              </h3>

              <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
                <!-- Left Column - Cantrips & Spells -->
                <div class="space-y-6">
                  <!-- Cantrips Known -->
                  <div>
                    <label class="block text-sm font-medium text-text-primary mb-2">
                      Cantrips Known
                    </label>
                    <div class="space-y-2">
                      <div v-for="(cantrip, index) in formData.cantrips_known" :key="`cantrip-${index}`" class="flex space-x-2">
                        <input
                          v-model="formData.cantrips_known[index]"
                          type="text"
                          class="fantasy-input flex-1"
                          placeholder="Cantrip name..."
                        >
                        <button
                          type="button"
                          class="fantasy-button-secondary px-3"
                          @click="formData.cantrips_known.splice(index, 1)"
                        >
                          Remove
                        </button>
                      </div>
                      <button
                        type="button"
                        class="fantasy-button-secondary w-full"
                        @click="formData.cantrips_known.push('')"
                      >
                        Add Cantrip
                      </button>
                    </div>
                  </div>

                  <!-- Spells Known -->
                  <div>
                    <label class="block text-sm font-medium text-text-primary mb-2">
                      Spells Known
                    </label>
                    <div class="space-y-2">
                      <div v-for="(spell, index) in formData.spells_known" :key="`spell-${index}`" class="flex space-x-2">
                        <input
                          v-model="formData.spells_known[index]"
                          type="text"
                          class="fantasy-input flex-1"
                          placeholder="Spell name..."
                        >
                        <button
                          type="button"
                          class="fantasy-button-secondary px-3"
                          @click="formData.spells_known.splice(index, 1)"
                        >
                          Remove
                        </button>
                      </div>
                      <button
                        type="button"
                        class="fantasy-button-secondary w-full"
                        @click="formData.spells_known.push('')"
                      >
                        Add Spell
                      </button>
                    </div>
                  </div>

                  <!-- Languages -->
                  <div>
                    <label class="block text-sm font-medium text-text-primary mb-2">
                      Languages
                    </label>
                    <div class="space-y-2">
                      <div v-for="(language, index) in formData.languages" :key="`language-${index}`" class="flex space-x-2">
                        <input
                          v-model="formData.languages[index]"
                          type="text"
                          class="fantasy-input flex-1"
                          placeholder="Language name..."
                        >
                        <button
                          type="button"
                          class="fantasy-button-secondary px-3"
                          @click="formData.languages.splice(index, 1)"
                        >
                          Remove
                        </button>
                      </div>
                      <button
                        type="button"
                        class="fantasy-button-secondary w-full"
                        @click="formData.languages.push('')"
                      >
                        Add Language
                      </button>
                    </div>
                  </div>
                </div>

                <!-- Right Column - Class Features -->
                <div class="space-y-6">
                  <!-- Class Features -->
                  <div>
                    <label class="block text-sm font-medium text-text-primary mb-2">
                      Class Features
                    </label>
                    <div class="space-y-2">
                      <div v-for="(feature, index) in formData.class_features" :key="`feature-${index}`" class="bg-secondary/10 rounded-lg p-3">
                        <div class="grid grid-cols-2 gap-2 mb-2">
                          <input
                            v-model="feature.name"
                            type="text"
                            class="fantasy-input"
                            placeholder="Feature name..."
                          >
                          <div class="flex space-x-2">
                            <input
                              v-model.number="feature.level_acquired"
                              type="number"
                              min="1"
                              max="20"
                              class="fantasy-input flex-1"
                              placeholder="Level"
                            >
                            <button
                              type="button"
                              class="fantasy-button-secondary px-3"
                              @click="formData.class_features.splice(index, 1)"
                            >
                              Remove
                            </button>
                          </div>
                        </div>
                        <textarea
                          v-model="feature.description"
                          rows="3"
                          class="fantasy-input w-full resize-none"
                          placeholder="Feature description..."
                        />
                      </div>
                      <button
                        type="button"
                        class="fantasy-button-secondary w-full"
                        @click="formData.class_features.push({ name: '', description: '', level_acquired: 1 })"
                      >
                        Add Class Feature
                      </button>
                    </div>
                  </div>

                  <!-- Racial Traits (Editable) -->
                  <div>
                    <label class="block text-sm font-medium text-text-primary mb-2">
                      Additional Racial Traits
                    </label>
                    <div class="space-y-2">
                      <div v-for="(trait, index) in formData.racial_traits" :key="`racial-trait-${index}`" class="bg-secondary/10 rounded-lg p-3">
                        <div class="flex justify-between items-start mb-2">
                          <input
                            v-model="trait.name"
                            type="text"
                            class="fantasy-input flex-1 mr-2"
                            placeholder="Trait name..."
                          >
                          <button
                            type="button"
                            class="fantasy-button-secondary px-3"
                            @click="formData.racial_traits.splice(index, 1)"
                          >
                            Remove
                          </button>
                        </div>
                        <textarea
                          v-model="trait.description"
                          rows="3"
                          class="fantasy-input w-full resize-none"
                          placeholder="Trait description..."
                        />
                      </div>
                      <button
                        type="button"
                        class="fantasy-button-secondary w-full"
                        @click="formData.racial_traits.push({ name: '', description: '' })"
                      >
                        Add Racial Trait
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Personality & Background Tab -->
            <div v-if="activeTab === 'personality'" class="space-y-6">
              <h3 class="text-lg font-cinzel font-semibold text-text-primary">
                Personality & Background
              </h3>

              <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
                <!-- Left Column -->
                <div class="space-y-6">
                  <!-- Personality Traits -->
                  <div>
                    <label class="block text-sm font-medium text-text-primary mb-2">
                      Personality Traits
                    </label>
                    <div class="space-y-2">
                      <input
                        v-model="formData.personality_traits[0]"
                        type="text"
                        class="fantasy-input w-full"
                        placeholder="First personality trait..."
                      >
                      <input
                        v-model="formData.personality_traits[1]"
                        type="text"
                        class="fantasy-input w-full"
                        placeholder="Second personality trait..."
                      >
                    </div>
                  </div>

                  <!-- Ideals -->
                  <div>
                    <label class="block text-sm font-medium text-text-primary mb-2">
                      Ideals
                    </label>
                    <div class="space-y-2">
                      <div v-for="(ideal, index) in formData.ideals" :key="`ideal-${index}`" class="flex space-x-2">
                        <input
                          v-model="formData.ideals[index]"
                          type="text"
                          class="fantasy-input flex-1"
                          placeholder="Character ideal..."
                        >
                        <button
                          type="button"
                          class="fantasy-button-secondary px-3"
                          @click="formData.ideals.splice(index, 1)"
                        >
                          Remove
                        </button>
                      </div>
                      <button
                        type="button"
                        class="fantasy-button-secondary w-full"
                        @click="formData.ideals.push('')"
                      >
                        Add Ideal
                      </button>
                    </div>
                  </div>

                  <!-- Bonds -->
                  <div>
                    <label class="block text-sm font-medium text-text-primary mb-2">
                      Bonds
                    </label>
                    <div class="space-y-2">
                      <div v-for="(bond, index) in formData.bonds" :key="`bond-${index}`" class="flex space-x-2">
                        <input
                          v-model="formData.bonds[index]"
                          type="text"
                          class="fantasy-input flex-1"
                          placeholder="Character bond..."
                        >
                        <button
                          type="button"
                          class="fantasy-button-secondary px-3"
                          @click="formData.bonds.splice(index, 1)"
                        >
                          Remove
                        </button>
                      </div>
                      <button
                        type="button"
                        class="fantasy-button-secondary w-full"
                        @click="formData.bonds.push('')"
                      >
                        Add Bond
                      </button>
                    </div>
                  </div>

                  <!-- Flaws -->
                  <div>
                    <label class="block text-sm font-medium text-text-primary mb-2">
                      Flaws
                    </label>
                    <div class="space-y-2">
                      <div v-for="(flaw, index) in formData.flaws" :key="`flaw-${index}`" class="flex space-x-2">
                        <input
                          v-model="formData.flaws[index]"
                          type="text"
                          class="fantasy-input flex-1"
                          placeholder="Character flaw..."
                        >
                        <button
                          type="button"
                          class="fantasy-button-secondary px-3"
                          @click="formData.flaws.splice(index, 1)"
                        >
                          Remove
                        </button>
                      </div>
                      <button
                        type="button"
                        class="fantasy-button-secondary w-full"
                        @click="formData.flaws.push('')"
                      >
                        Add Flaw
                      </button>
                    </div>
                  </div>
                </div>

                <!-- Right Column -->
                <div class="space-y-6">
                  <!-- Portrait Path -->
                  <div>
                    <label class="block text-sm font-medium text-text-primary mb-2">
                      Portrait Path
                    </label>
                    <input
                      v-model="formData.portrait_path"
                      type="text"
                      class="fantasy-input w-full"
                      placeholder="e.g., /static/images/portraits/character.jpg"
                    >
                    <p class="text-xs text-text-secondary mt-1">
                      Path to character portrait image
                    </p>
                  </div>

                  <!-- Appearance -->
                  <div>
                    <label class="block text-sm font-medium text-text-primary mb-2">
                      Appearance
                    </label>
                    <textarea
                      v-model="formData.appearance"
                      rows="4"
                      class="fantasy-input w-full resize-none"
                      placeholder="Describe the character's physical appearance..."
                    />
                  </div>

                  <!-- Backstory -->
                  <div>
                    <label class="block text-sm font-medium text-text-primary mb-2">
                      Backstory
                    </label>
                    <textarea
                      v-model="formData.backstory"
                      rows="8"
                      class="fantasy-input w-full resize-none"
                      placeholder="Character's history and background story..."
                    />
                  </div>
                </div>
              </div>
            </div>

            <!-- Equipment & Proficiencies Tab -->
            <div v-if="activeTab === 'equipment'" class="space-y-6">
              <h3 class="text-lg font-cinzel font-semibold text-text-primary">
                Equipment & Proficiencies
              </h3>

              <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
                <!-- Left Column - Equipment -->
                <div class="space-y-6">
                  <!-- Starting Gold -->
                  <div>
                    <label class="block text-sm font-medium text-text-primary mb-2">
                      Starting Gold
                    </label>
                    <input
                      v-model.number="formData.starting_gold"
                      type="number"
                      min="0"
                      class="fantasy-input w-full"
                      placeholder="0"
                    >
                  </div>

                  <!-- Starting Equipment -->
                  <div>
                    <label class="block text-sm font-medium text-text-primary mb-2">
                      Starting Equipment
                    </label>
                    <div class="space-y-2">
                      <div v-for="(item, index) in formData.starting_equipment" :key="`equipment-${index}`" class="bg-secondary/10 rounded-lg p-3">
                        <div class="grid grid-cols-2 gap-2 mb-2">
                          <input
                            v-model="item.name"
                            type="text"
                            class="fantasy-input"
                            placeholder="Item name..."
                          >
                          <div class="flex space-x-2">
                            <input
                              v-model.number="item.quantity"
                              type="number"
                              min="1"
                              class="fantasy-input flex-1"
                              placeholder="Qty"
                            >
                            <button
                              type="button"
                              class="fantasy-button-secondary px-3"
                              @click="formData.starting_equipment.splice(index, 1)"
                            >
                              Remove
                            </button>
                          </div>
                        </div>
                        <textarea
                          v-model="item.description"
                          rows="2"
                          class="fantasy-input w-full resize-none"
                          placeholder="Item description..."
                        />
                        <input
                          v-model="item.id"
                          type="text"
                          class="fantasy-input w-full mt-2"
                          placeholder="Item ID (e.g., longsword, leather_armor)..."
                        >
                      </div>
                      <button
                        type="button"
                        class="fantasy-button-secondary w-full"
                        @click="formData.starting_equipment.push({ id: '', name: '', description: '', quantity: 1 })"
                      >
                        Add Equipment
                      </button>
                    </div>
                  </div>

                  <!-- Feats -->
                  <div>
                    <label class="block text-sm font-medium text-text-primary mb-2">
                      Feats
                    </label>
                    <div class="space-y-2">
                      <div v-for="(feat, index) in formData.feats" :key="`feat-${index}`" class="bg-secondary/10 rounded-lg p-3">
                        <div class="flex justify-between items-start mb-2">
                          <input
                            v-model="feat.name"
                            type="text"
                            class="fantasy-input flex-1 mr-2"
                            placeholder="Feat name..."
                          >
                          <button
                            type="button"
                            class="fantasy-button-secondary px-3"
                            @click="formData.feats.splice(index, 1)"
                          >
                            Remove
                          </button>
                        </div>
                        <textarea
                          v-model="feat.description"
                          rows="3"
                          class="fantasy-input w-full resize-none"
                          placeholder="Feat description..."
                        />
                      </div>
                      <button
                        type="button"
                        class="fantasy-button-secondary w-full"
                        @click="formData.feats.push({ name: '', description: '' })"
                      >
                        Add Feat
                      </button>
                    </div>
                  </div>
                </div>

                <!-- Right Column - Proficiencies -->
                <div class="space-y-6">
                  <!-- Armor Proficiencies -->
                  <div>
                    <label class="block text-sm font-medium text-text-primary mb-2">
                      Armor Proficiencies
                    </label>
                    <div class="space-y-2">
                      <div v-for="(armor, index) in formData.proficiencies.armor" :key="`armor-${index}`" class="flex space-x-2">
                        <input
                          v-model="formData.proficiencies.armor[index]"
                          type="text"
                          class="fantasy-input flex-1"
                          placeholder="Armor type..."
                        >
                        <button
                          type="button"
                          class="fantasy-button-secondary px-3"
                          @click="formData.proficiencies.armor.splice(index, 1)"
                        >
                          Remove
                        </button>
                      </div>
                      <button
                        type="button"
                        class="fantasy-button-secondary w-full"
                        @click="formData.proficiencies.armor.push('')"
                      >
                        Add Armor Proficiency
                      </button>
                    </div>
                  </div>

                  <!-- Weapon Proficiencies -->
                  <div>
                    <label class="block text-sm font-medium text-text-primary mb-2">
                      Weapon Proficiencies
                    </label>
                    <div class="space-y-2">
                      <div v-for="(weapon, index) in formData.proficiencies.weapons" :key="`weapon-${index}`" class="flex space-x-2">
                        <input
                          v-model="formData.proficiencies.weapons[index]"
                          type="text"
                          class="fantasy-input flex-1"
                          placeholder="Weapon type..."
                        >
                        <button
                          type="button"
                          class="fantasy-button-secondary px-3"
                          @click="formData.proficiencies.weapons.splice(index, 1)"
                        >
                          Remove
                        </button>
                      </div>
                      <button
                        type="button"
                        class="fantasy-button-secondary w-full"
                        @click="formData.proficiencies.weapons.push('')"
                      >
                        Add Weapon Proficiency
                      </button>
                    </div>
                  </div>

                  <!-- Skill Proficiencies -->
                  <div>
                    <label class="block text-sm font-medium text-text-primary mb-2">
                      Skill Proficiencies
                    </label>
                    <div class="space-y-2 max-h-48 overflow-y-auto">
                      <div
                        v-for="skill in availableSkills"
                        :key="skill"
                        class="flex items-center"
                      >
                        <input
                          :id="`skill-${skill}`"
                          v-model="formData.proficiencies.skills"
                          type="checkbox"
                          :value="skill"
                          class="mr-2"
                        >
                        <label :for="`skill-${skill}`" class="text-sm text-text-primary">
                          {{ skill }}
                        </label>
                      </div>
                    </div>
                  </div>

                  <!-- Tool Proficiencies -->
                  <div>
                    <label class="block text-sm font-medium text-text-primary mb-2">
                      Tool Proficiencies
                    </label>
                    <div class="space-y-2">
                      <div v-for="(tool, index) in formData.proficiencies.tools" :key="`tool-${index}`" class="flex space-x-2">
                        <input
                          v-model="formData.proficiencies.tools[index]"
                          type="text"
                          class="fantasy-input flex-1"
                          placeholder="Tool proficiency..."
                        >
                        <button
                          type="button"
                          class="fantasy-button-secondary px-3"
                          @click="formData.proficiencies.tools.splice(index, 1)"
                        >
                          Remove
                        </button>
                      </div>
                      <button
                        type="button"
                        class="fantasy-button-secondary w-full"
                        @click="formData.proficiencies.tools.push('')"
                      >
                        Add Tool Proficiency
                      </button>
                    </div>
                  </div>

                  <!-- Saving Throw Proficiencies -->
                  <div>
                    <label class="block text-sm font-medium text-text-primary mb-2">
                      Saving Throw Proficiencies
                    </label>
                    <div class="grid grid-cols-2 gap-2">
                      <div v-for="ability in ['STR', 'DEX', 'CON', 'INT', 'WIS', 'CHA']" :key="ability" class="flex items-center">
                        <input
                          :id="`save-${ability}`"
                          v-model="formData.proficiencies.saving_throws"
                          type="checkbox"
                          :value="ability"
                          class="mr-2"
                        >
                        <label :for="`save-${ability}`" class="text-sm text-text-primary">
                          {{ ability }}
                        </label>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Actions -->
          <div class="flex justify-end space-x-3 pt-4 border-t border-gold/20">
            <button
              type="button"
              class="fantasy-button-secondary"
              @click="$emit('close')"
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

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useD5eData } from '../../composables/useD5eData'
import { usePointBuy } from '../../composables/usePointBuy'
import type { CharacterTemplateModel, ItemModel, TraitModel, ClassFeatureModel } from '../../types/unified'

const props = defineProps({
  visible: {
    type: Boolean,
    required: true
  },
  template: {
    type: Object as () => CharacterTemplateModel | null,
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
  { id: 'features', label: 'Features & Traits' },
  { id: 'spells', label: 'Spells & Magic' },
  { id: 'personality', label: 'Personality & Background' },
  { id: 'equipment', label: 'Equipment & Proficiencies' }
]

const formData = ref({
  name: '',
  race: '',
  subrace: '',
  char_class: '', // Correct field name for unified model
  subclass: '',
  level: 1,
  background: '',
  alignment: '',
  description: '',
  // Personality & Background
  personality_traits: ['', ''],
  ideals: [],
  bonds: [],
  flaws: [],
  appearance: '',
  backstory: '',
  portrait_path: '',
  // Equipment & Gold
  starting_gold: 0,
  starting_equipment: [] as ItemModel[],
  // Languages
  languages: ['Common'],
  // Proficiencies structure matching unified model
  proficiencies: {
    armor: [] as string[],
    weapons: [] as string[],
    tools: [] as string[],
    saving_throws: [] as string[],
    skills: [] as string[]
  },
  // Racial traits as structured objects
  racial_traits: [] as TraitModel[],
  // Class features as structured objects
  class_features: [] as ClassFeatureModel[],
  // Feats as structured objects
  feats: [] as TraitModel[],
  // Spells
  spells_known: [] as string[],
  cantrips_known: [] as string[]
})

// Computed properties
const subraceOptions = computed(() => {
  return formData.value.race ? d5eData.getSubraceOptions(formData.value.race) : []
})

const subclassOptions = computed(() => {
  return formData.value.char_class ? d5eData.getSubclassOptions(formData.value.char_class) : []
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
  return d5eData.calculateHitPoints(formData.value.char_class, formData.value.level, conModifier)
})

const calculatedArmorClass = computed(() => {
  const dexModifier = d5eData.getAbilityModifier(totalAbilityScores.value.DEX || 10)
  return 10 + dexModifier // Base AC + Dex modifier
})

const classProficiencies = computed(() => {
  return d5eData.getClassProficiencies(formData.value.char_class)
})

const racialTraits = computed(() => {
  return d5eData.getRacialTraits(formData.value.race, formData.value.subrace)
})

const availableSkills = computed(() => {
  return [
    'Acrobatics',
    'Animal Handling',
    'Arcana',
    'Athletics',
    'Deception',
    'History',
    'Insight',
    'Intimidation',
    'Investigation',
    'Medicine',
    'Nature',
    'Perception',
    'Performance',
    'Persuasion',
    'Religion',
    'Sleight of Hand',
    'Stealth',
    'Survival'
  ]
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
    // Include calculated values for compatibility
    total_stats: totalAbilityScores.value,
    hit_points: calculatedHitPoints.value,
    armor_class: calculatedArmorClass.value,
    proficiency_bonus: d5eData.getProficiencyBonus(formData.value.level),
    // Merge displayed racial traits with user-added ones
    racial_traits: [...racialTraits.value.traits, ...formData.value.racial_traits],
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
      char_class: newTemplate.char_class || newTemplate.class || '', // Handle both field names
      subclass: newTemplate.subclass || '',
      level: newTemplate.level || 1,
      background: newTemplate.background || '',
      alignment: newTemplate.alignment || '',
      description: newTemplate.description || '',
      // Personality & Background
      personality_traits: newTemplate.personality_traits || ['', ''],
      ideals: newTemplate.ideals || [],
      bonds: newTemplate.bonds || [],
      flaws: newTemplate.flaws || [],
      appearance: newTemplate.appearance || '',
      backstory: newTemplate.backstory || '',
      portrait_path: newTemplate.portrait_path || '',
      // Equipment & Gold
      starting_gold: newTemplate.starting_gold || 0,
      starting_equipment: Array.isArray(newTemplate.starting_equipment)
        ? newTemplate.starting_equipment.map(item =>
            typeof item === 'string'
              ? { id: item.toLowerCase().replace(/\s+/g, '_'), name: item, description: item, quantity: 1 }
              : { id: item.id || '', name: item.name || '', description: item.description || '', quantity: item.quantity || 1 }
          )
        : [],
      // Languages
      languages: newTemplate.languages || ['Common'],
      // Proficiencies - handle both old and new structure
      proficiencies: {
        armor: newTemplate.proficiencies?.armor || [],
        weapons: newTemplate.proficiencies?.weapons || [],
        tools: newTemplate.proficiencies?.tools || [],
        saving_throws: newTemplate.proficiencies?.saving_throws || [],
        skills: newTemplate.proficiencies?.skills || newTemplate.skill_proficiencies || []
      },
      // Traits and Features
      racial_traits: Array.isArray(newTemplate.racial_traits)
        ? newTemplate.racial_traits.filter(trait => typeof trait === 'object' && trait.name)
        : [],
      class_features: Array.isArray(newTemplate.class_features)
        ? newTemplate.class_features.map(feature => ({
            name: feature.name || '',
            description: feature.description || '',
            level_acquired: feature.level_acquired || 1
          }))
        : [],
      feats: Array.isArray(newTemplate.feats)
        ? newTemplate.feats.map(feat =>
            typeof feat === 'string'
              ? { name: feat, description: '' }
              : { name: feat.name || '', description: feat.description || '' }
          )
        : [],
      // Spells
      spells_known: newTemplate.spells_known || [],
      cantrips_known: newTemplate.cantrips_known || []
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
      char_class: '',
      subclass: '',
      level: 1,
      background: '',
      alignment: '',
      description: '',
      // Personality & Background
      personality_traits: ['', ''],
      ideals: [],
      bonds: [],
      flaws: [],
      appearance: '',
      backstory: '',
      portrait_path: '',
      // Equipment & Gold
      starting_gold: 0,
      starting_equipment: [],
      // Languages
      languages: ['Common'],
      // Proficiencies
      proficiencies: {
        armor: [],
        weapons: [],
        tools: [],
        saving_throws: [],
        skills: []
      },
      // Traits and Features
      racial_traits: [],
      class_features: [],
      feats: [],
      // Spells
      spells_known: [],
      cantrips_known: []
    }
    pointBuy.resetScores()
  }
  activeTab.value = 'basic'
}, { immediate: true })
</script>
