<template>
  <AppModal
    :visible="visible"
    :title="currentStepTitle"
    size="xl"
    @close="handleClose"
  >
    <template #body>
      <!-- Progress Bar -->
      <div class="mb-6">
        <div class="flex items-center justify-between mb-2">
          <span class="text-sm text-foreground/60">
            Step {{ currentStep + 1 }} of {{ steps.length }}
          </span>
          <span class="text-sm font-medium text-foreground">
            {{ steps[currentStep].label }}
          </span>
        </div>
        <div class="w-full bg-card rounded-full h-2">
          <div
            class="bg-primary h-2 rounded-full transition-all duration-300"
            :style="{ width: `${((currentStep + 1) / steps.length) * 100}%` }"
          />
        </div>
      </div>

      <!-- Step Content -->
      <div class="min-h-[400px]">
        <!-- Step 1: Content Pack Selection -->
        <div v-if="currentStep === 0" class="space-y-4">
          <div class="text-center mb-6">
            <h3 class="text-xl font-cinzel font-semibold text-foreground mb-2">
              Choose Your Content
            </h3>
            <p class="text-foreground/60">
              Select the content packs that will be available for this
              character. This determines which races, classes, spells, and items
              you can choose.
            </p>
          </div>

          <div v-if="contentPacksLoading" class="text-center py-8">
            <BaseLoader size="lg" />
            <p class="text-foreground/60 mt-2">Loading content packs...</p>
          </div>

          <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <label
              v-for="pack in availableContentPacks"
              :key="pack.id"
              class="relative"
            >
              <input
                v-model="formData.content_pack_ids"
                type="checkbox"
                :value="pack.id"
                class="sr-only peer"
              />
              <div
                class="border-2 rounded-lg p-4 cursor-pointer transition-all peer-checked:border-primary peer-checked:bg-primary/5 hover:border-border"
                :class="{
                  'border-border/40': !formData.content_pack_ids.includes(
                    pack.id
                  ),
                }"
              >
                <div class="flex items-start space-x-3">
                  <div
                    class="w-5 h-5 rounded border-2 flex-shrink-0 mt-0.5 transition-all peer-checked:bg-primary peer-checked:border-primary"
                    :class="{
                      'border-border': !formData.content_pack_ids.includes(
                        pack.id
                      ),
                    }"
                  >
                    <svg
                      v-if="formData.content_pack_ids.includes(pack.id)"
                      class="w-3 h-3 text-primary-foreground m-0.5"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path
                        fill-rule="evenodd"
                        d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                        clip-rule="evenodd"
                      />
                    </svg>
                  </div>
                  <div class="flex-1">
                    <h4 class="font-semibold text-foreground">
                      {{ pack.name }}
                    </h4>
                    <p class="text-sm text-foreground/60 mt-1">
                      {{ pack.description || 'No description available' }}
                    </p>
                    <div class="flex flex-wrap gap-2 mt-2">
                      <BaseBadge
                        v-if="pack.stats?.races"
                        variant="secondary"
                        size="sm"
                      >
                        {{ pack.stats.races }} Races
                      </BaseBadge>
                      <BaseBadge
                        v-if="pack.stats?.classes"
                        variant="secondary"
                        size="sm"
                      >
                        {{ pack.stats.classes }} Classes
                      </BaseBadge>
                      <BaseBadge
                        v-if="pack.stats?.spells"
                        variant="secondary"
                        size="sm"
                      >
                        {{ pack.stats.spells }} Spells
                      </BaseBadge>
                    </div>
                  </div>
                </div>
              </div>
            </label>
          </div>

          <BaseAlert
            v-if="formData.content_pack_ids.length === 0"
            variant="warning"
          >
            You must select at least one content pack to create a character.
          </BaseAlert>
        </div>

        <!-- Step 2: Basic Information -->
        <div v-else-if="currentStep === 1" class="space-y-4">
          <AppFormSection title="Character Basics">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <AppInput
                v-model="formData.name"
                label="Character Name"
                placeholder="Enter character name"
                :error="errors.name"
              />

              <AppSelect
                v-model="formData.alignment"
                label="Alignment"
                :options="alignmentOptions"
                :error="errors.alignment"
              />
            </div>

            <AppSelect
              v-model="formData.background"
              label="Background"
              :options="backgroundOptions"
              :error="errors.background"
              :loading="d5eDataLoading"
            >
              <template #option="{ option }">
                <div class="flex items-center justify-between">
                  <span>{{ option.label }}</span>
                  <ContentPackBadge
                    v-if="option.metadata?.content_pack_id"
                    :pack-id="option.metadata.content_pack_id"
                    size="sm"
                  />
                </div>
              </template>
            </AppSelect>

            <AppTextarea
              v-model="formData.backstory"
              label="Backstory (Optional)"
              placeholder="Tell us about your character's history..."
              rows="4"
            />
          </AppFormSection>
        </div>

        <!-- Step 3: Race & Class Selection -->
        <div v-else-if="currentStep === 2" class="space-y-6">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <!-- Race Selection -->
            <AppFormSection title="Choose Your Race">
              <AppSelect
                v-model="formData.race"
                label="Race"
                :options="raceOptions"
                :error="errors.race"
                :loading="d5eDataLoading"
              >
                <template #option="{ option }">
                  <div class="flex items-center justify-between">
                    <span>{{ option.label }}</span>
                    <ContentPackBadge
                      v-if="option.metadata?.content_pack_id"
                      :pack-id="option.metadata.content_pack_id"
                      size="sm"
                    />
                  </div>
                </template>
              </AppSelect>

              <div
                v-if="selectedRaceDetails"
                class="mt-4 p-4 bg-card rounded-lg"
              >
                <h4 class="font-semibold text-foreground mb-2">
                  Racial Traits
                </h4>
                <ul class="text-sm text-foreground/60 space-y-1">
                  <li v-for="trait in selectedRaceDetails.traits" :key="trait">
                    • {{ trait }}
                  </li>
                </ul>
              </div>
            </AppFormSection>

            <!-- Class Selection -->
            <AppFormSection title="Choose Your Class">
              <AppSelect
                v-model="formData.char_class"
                label="Class"
                :options="classOptions"
                :error="errors.char_class"
                :loading="d5eDataLoading"
              >
                <template #option="{ option }">
                  <div class="flex items-center justify-between">
                    <span>{{ option.label }}</span>
                    <ContentPackBadge
                      v-if="option.metadata?.content_pack_id"
                      :pack-id="option.metadata.content_pack_id"
                      size="sm"
                    />
                  </div>
                </template>
              </AppSelect>

              <AppNumberInput
                v-model="formData.level"
                label="Starting Level"
                :min="1"
                :max="20"
                :error="errors.level"
              />

              <div
                v-if="selectedClassDetails"
                class="mt-4 p-4 bg-card rounded-lg"
              >
                <h4 class="font-semibold text-foreground mb-2">
                  Class Features
                </h4>
                <ul class="text-sm text-foreground/60 space-y-1">
                  <li>Hit Die: d{{ selectedClassDetails.hit_die }}</li>
                  <li>
                    Primary Ability: {{ selectedClassDetails.primary_ability }}
                  </li>
                  <li v-if="selectedClassDetails.spellcasting">
                    Spellcasting:
                    {{ selectedClassDetails.spellcasting_ability }}
                  </li>
                </ul>
              </div>
            </AppFormSection>
          </div>
        </div>

        <!-- Step 4: Ability Scores -->
        <div v-else-if="currentStep === 3" class="space-y-4">
          <AppFormSection title="Determine Ability Scores">
            <div class="mb-4">
              <AppTabs
                v-model:active-tab="abilityScoreMethod"
                :tabs="abilityScoreTabs"
              />
            </div>

            <!-- Point Buy Method -->
            <div v-if="abilityScoreMethod === 'point-buy'" class="space-y-4">
              <div class="text-center mb-4">
                <p class="text-lg font-semibold">
                  Points Remaining:
                  <span
                    :class="
                      pointBuyRemaining < 0 ? 'text-red-500' : 'text-primary'
                    "
                  >
                    {{ pointBuyRemaining }}
                  </span>
                </p>
              </div>

              <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                <div
                  v-for="ability in abilities"
                  :key="ability.key"
                  class="space-y-2"
                >
                  <label class="text-sm font-medium text-foreground">
                    {{ ability.name }}
                  </label>
                  <AppNumberInput
                    v-model="formData.ability_scores[ability.key]"
                    :min="8"
                    :max="15"
                    :error="errors[`ability_scores.${ability.key}`]"
                  />
                  <p class="text-xs text-foreground/60">
                    Cost:
                    {{ getPointBuyCost(formData.ability_scores[ability.key]) }}
                    | Modifier:
                    {{
                      getAbilityModifier(formData.ability_scores[ability.key])
                    }}
                  </p>
                </div>
              </div>
            </div>

            <!-- Standard Array Method -->
            <div
              v-else-if="abilityScoreMethod === 'standard'"
              class="space-y-4"
            >
              <BaseAlert variant="info">
                Assign these scores to your abilities: 15, 14, 13, 12, 10, 8
              </BaseAlert>

              <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                <div
                  v-for="ability in abilities"
                  :key="ability.key"
                  class="space-y-2"
                >
                  <AppSelect
                    v-model="formData.ability_scores[ability.key]"
                    :label="ability.name"
                    :options="standardArrayOptions"
                    :error="errors[`ability_scores.${ability.key}`]"
                  />
                </div>
              </div>
            </div>

            <!-- Roll Method -->
            <div v-else-if="abilityScoreMethod === 'roll'" class="space-y-4">
              <div class="text-center mb-4">
                <AppButton :disabled="hasRolled" @click="rollAbilityScores">
                  {{ hasRolled ? 'Scores Rolled' : 'Roll Ability Scores' }}
                </AppButton>
              </div>

              <div
                v-if="hasRolled"
                class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
              >
                <div
                  v-for="ability in abilities"
                  :key="ability.key"
                  class="space-y-2"
                >
                  <label class="text-sm font-medium text-foreground">
                    {{ ability.name }}
                  </label>
                  <div class="text-2xl font-bold text-primary">
                    {{ formData.ability_scores[ability.key] }}
                  </div>
                  <p class="text-xs text-foreground/60">
                    Modifier:
                    {{
                      getAbilityModifier(formData.ability_scores[ability.key])
                    }}
                  </p>
                </div>
              </div>
            </div>
          </AppFormSection>
        </div>

        <!-- Step 5: Skills & Proficiencies -->
        <div v-else-if="currentStep === 4" class="space-y-4">
          <AppFormSection title="Skills & Proficiencies">
            <!-- Skill Proficiencies -->
            <div class="space-y-4">
              <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <!-- Skills Available from Class -->
                <div class="space-y-3">
                  <h4 class="font-semibold text-foreground">
                    Class Skills
                    <span class="text-xs text-foreground/60 ml-2">
                      (Choose
                      {{
                        availableClassSkills.length > 0 ? classSkillChoices : 0
                      }})
                    </span>
                  </h4>
                  <AppCheckboxGroup
                    v-model="formData.skills"
                    :options="availableClassSkills"
                    :max-selections="classSkillChoices"
                    columns="1"
                  />
                </div>

                <!-- Background Skills (automatically granted) -->
                <div class="space-y-3">
                  <h4 class="font-semibold text-foreground">
                    Background Skills
                  </h4>
                  <div class="space-y-2">
                    <div
                      v-for="skill in backgroundSkills"
                      :key="skill.value"
                      class="flex items-center space-x-2 p-2 bg-card rounded-lg"
                    >
                      <div
                        class="w-4 h-4 bg-primary rounded-sm flex items-center justify-center"
                      >
                        <svg
                          class="w-2.5 h-2.5 text-primary-foreground"
                          fill="currentColor"
                          viewBox="0 0 20 20"
                        >
                          <path
                            fill-rule="evenodd"
                            d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                            clip-rule="evenodd"
                          />
                        </svg>
                      </div>
                      <span class="text-sm text-foreground">{{
                        skill.label
                      }}</span>
                      <span class="text-xs text-foreground/60"
                        >(From Background)</span
                      >
                    </div>
                  </div>
                </div>
              </div>

              <!-- Expertise Selection (for applicable classes) -->
              <div v-if="canChooseExpertise" class="space-y-3">
                <h4 class="font-semibold text-foreground">
                  Expertise
                  <span class="text-xs text-foreground/60 ml-2">
                    (Choose {{ expertiseChoices }} skills to double proficiency
                    bonus)
                  </span>
                </h4>
                <AppCheckboxGroup
                  v-model="formData.expertises"
                  :options="availableExpertiseSkills"
                  :max-selections="expertiseChoices"
                  columns="2"
                />
              </div>

              <!-- Languages & Other Proficiencies -->
              <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <!-- Languages -->
                <div class="space-y-3">
                  <h4 class="font-semibold text-foreground">Languages</h4>
                  <div class="space-y-2">
                    <div
                      v-for="language in grantedLanguages"
                      :key="language"
                      class="flex items-center space-x-2 p-2 bg-card rounded-lg"
                    >
                      <div
                        class="w-4 h-4 bg-primary rounded-sm flex items-center justify-center"
                      >
                        <svg
                          class="w-2.5 h-2.5 text-primary-foreground"
                          fill="currentColor"
                          viewBox="0 0 20 20"
                        >
                          <path
                            fill-rule="evenodd"
                            d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                            clip-rule="evenodd"
                          />
                        </svg>
                      </div>
                      <span class="text-sm text-foreground">{{
                        language
                      }}</span>
                    </div>
                  </div>
                </div>

                <!-- Tool Proficiencies -->
                <div class="space-y-3">
                  <h4 class="font-semibold text-foreground">
                    Tool Proficiencies
                  </h4>
                  <div class="space-y-2">
                    <div
                      v-for="tool in grantedTools"
                      :key="tool"
                      class="flex items-center space-x-2 p-2 bg-card rounded-lg"
                    >
                      <div
                        class="w-4 h-4 bg-primary rounded-sm flex items-center justify-center"
                      >
                        <svg
                          class="w-2.5 h-2.5 text-primary-foreground"
                          fill="currentColor"
                          viewBox="0 0 20 20"
                        >
                          <path
                            fill-rule="evenodd"
                            d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                            clip-rule="evenodd"
                          />
                        </svg>
                      </div>
                      <span class="text-sm text-foreground">{{ tool }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </AppFormSection>
        </div>

        <!-- Step 6: Equipment & Spells -->
        <div v-else-if="currentStep === 5" class="space-y-4">
          <AppFormSection title="Equipment & Spells">
            <div class="space-y-6">
              <!-- Starting Equipment Choice -->
              <div class="space-y-4">
                <h4 class="font-semibold text-foreground">
                  Starting Equipment
                </h4>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <label class="relative">
                    <input
                      v-model="equipmentMethod"
                      type="radio"
                      value="standard"
                      class="sr-only peer"
                    />
                    <div
                      class="border-2 rounded-lg p-4 cursor-pointer transition-all peer-checked:border-primary peer-checked:bg-primary/5 hover:border-border"
                    >
                      <h5 class="font-medium text-foreground">
                        Standard Equipment
                      </h5>
                      <p class="text-sm text-foreground/60 mt-1">
                        Receive the standard starting equipment for your class
                        and background.
                      </p>
                    </div>
                  </label>

                  <label class="relative">
                    <input
                      v-model="equipmentMethod"
                      type="radio"
                      value="gold"
                      class="sr-only peer"
                    />
                    <div
                      class="border-2 rounded-lg p-4 cursor-pointer transition-all peer-checked:border-primary peer-checked:bg-primary/5 hover:border-border"
                    >
                      <h5 class="font-medium text-foreground">Starting Gold</h5>
                      <p class="text-sm text-foreground/60 mt-1">
                        Receive starting gold to purchase your own equipment.
                      </p>
                    </div>
                  </label>
                </div>
              </div>

              <!-- Equipment Lists -->
              <div v-if="equipmentMethod === 'standard'" class="space-y-4">
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div class="space-y-3">
                    <h4 class="font-semibold text-foreground">
                      Class Equipment
                    </h4>
                    <div class="space-y-2">
                      <div
                        v-for="item in classEquipment"
                        :key="item"
                        class="flex items-center space-x-2 p-2 bg-card rounded-lg"
                      >
                        <div
                          class="w-4 h-4 bg-primary rounded-sm flex items-center justify-center"
                        >
                          <svg
                            class="w-2.5 h-2.5 text-primary-foreground"
                            fill="currentColor"
                            viewBox="0 0 20 20"
                          >
                            <path
                              fill-rule="evenodd"
                              d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                              clip-rule="evenodd"
                            />
                          </svg>
                        </div>
                        <span class="text-sm text-foreground">{{ item }}</span>
                      </div>
                    </div>
                  </div>

                  <div class="space-y-3">
                    <h4 class="font-semibold text-foreground">
                      Background Equipment
                    </h4>
                    <div class="space-y-2">
                      <div
                        v-for="item in backgroundEquipment"
                        :key="item"
                        class="flex items-center space-x-2 p-2 bg-card rounded-lg"
                      >
                        <div
                          class="w-4 h-4 bg-primary rounded-sm flex items-center justify-center"
                        >
                          <svg
                            class="w-2.5 h-2.5 text-primary-foreground"
                            fill="currentColor"
                            viewBox="0 0 20 20"
                          >
                            <path
                              fill-rule="evenodd"
                              d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                              clip-rule="evenodd"
                            />
                          </svg>
                        </div>
                        <span class="text-sm text-foreground">{{ item }}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Spell Selection (for spellcasting classes) -->
              <div v-if="isSpellcaster" class="space-y-4">
                <h4 class="font-semibold text-foreground">Spell Selection</h4>

                <!-- Cantrips -->
                <div v-if="cantripsKnown > 0" class="space-y-3">
                  <h5 class="font-medium text-foreground">
                    Cantrips
                    <span class="text-xs text-foreground/60 ml-2">
                      (Choose {{ cantripsKnown }})
                    </span>
                  </h5>
                  <AppCheckboxGroup
                    v-model="formData.cantrips"
                    :options="availableCantrips"
                    :max-selections="cantripsKnown"
                    columns="2"
                  />
                </div>

                <!-- 1st Level Spells -->
                <div v-if="spellsKnown > 0" class="space-y-3">
                  <h5 class="font-medium text-foreground">
                    1st Level Spells
                    <span class="text-xs text-foreground/60 ml-2">
                      (Choose {{ spellsKnown }})
                    </span>
                  </h5>
                  <AppCheckboxGroup
                    v-model="formData.spells"
                    :options="availableFirstLevelSpells"
                    :max-selections="spellsKnown"
                    columns="2"
                  />
                </div>
              </div>
            </div>
          </AppFormSection>
        </div>

        <!-- Step 7: Review & Confirm -->
        <div v-else-if="currentStep === 6" class="space-y-4">
          <AppFormSection title="Review Your Character">
            <div class="space-y-6">
              <!-- Character Summary -->
              <div class="bg-card rounded-lg p-6">
                <div class="flex items-center justify-between mb-4">
                  <h3 class="text-2xl font-cinzel font-bold text-foreground">
                    {{ formData.name }}
                  </h3>
                  <BaseBadge variant="secondary">
                    Level {{ formData.level }}
                  </BaseBadge>
                </div>

                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <!-- Basic Information -->
                  <div class="space-y-3">
                    <h4 class="font-semibold text-foreground">
                      Basic Information
                    </h4>
                    <div class="space-y-2 text-sm">
                      <div class="flex justify-between">
                        <span class="text-foreground/60">Race:</span>
                        <span class="text-foreground">{{
                          getRaceDisplayName(formData.race)
                        }}</span>
                      </div>
                      <div class="flex justify-between">
                        <span class="text-foreground/60">Class:</span>
                        <span class="text-foreground">{{
                          getClassDisplayName(formData.char_class)
                        }}</span>
                      </div>
                      <div class="flex justify-between">
                        <span class="text-foreground/60">Background:</span>
                        <span class="text-foreground">{{
                          getBackgroundDisplayName(formData.background)
                        }}</span>
                      </div>
                      <div class="flex justify-between">
                        <span class="text-foreground/60">Alignment:</span>
                        <span class="text-foreground">{{
                          getAlignmentDisplayName(formData.alignment)
                        }}</span>
                      </div>
                    </div>
                  </div>

                  <!-- Ability Scores -->
                  <div class="space-y-3">
                    <h4 class="font-semibold text-foreground">
                      Ability Scores
                    </h4>
                    <div class="grid grid-cols-2 gap-2 text-sm">
                      <div
                        v-for="ability in abilities"
                        :key="ability.key"
                        class="flex justify-between"
                      >
                        <span class="text-foreground/60"
                          >{{ ability.name }}:</span
                        >
                        <span class="text-foreground">
                          {{ formData.ability_scores[ability.key] }}
                          ({{
                            getAbilityModifier(
                              formData.ability_scores[ability.key]
                            )
                          }})
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Content Packs Used -->
              <div class="space-y-3">
                <h4 class="font-semibold text-foreground">Content Packs</h4>
                <div class="flex flex-wrap gap-2">
                  <BaseBadge
                    v-for="packId in formData.content_pack_ids"
                    :key="packId"
                    variant="primary"
                  >
                    {{ getContentPackName(packId) }}
                  </BaseBadge>
                </div>
              </div>

              <!-- Validation Summary -->
              <div v-if="validationIssues.length > 0" class="space-y-3">
                <h4 class="font-semibold text-foreground">Validation Issues</h4>
                <BaseAlert
                  v-for="issue in validationIssues"
                  :key="issue"
                  variant="warning"
                >
                  {{ issue }}
                </BaseAlert>
              </div>

              <!-- Success Message -->
              <BaseAlert v-if="validationIssues.length === 0" variant="success">
                Your character is complete and ready to be created!
              </BaseAlert>
            </div>
          </AppFormSection>
        </div>

        <!-- Steps 8+ placeholder -->
        <div v-else class="text-center py-8">
          <p class="text-foreground/60">This step is under construction...</p>
        </div>
      </div>
    </template>

    <template #footer>
      <div class="flex justify-between">
        <AppButton
          variant="secondary"
          :disabled="currentStep === 0"
          @click="previousStep"
        >
          Previous
        </AppButton>

        <div class="flex gap-2">
          <AppButton variant="secondary" @click="handleClose">
            Cancel
          </AppButton>

          <AppButton
            v-if="currentStep < steps.length - 1"
            :disabled="!canProceed"
            @click="nextStep"
          >
            Next
          </AppButton>

          <AppButton v-else :disabled="!canProceed" @click="saveCharacter">
            Create Character
          </AppButton>
        </div>
      </div>
    </template>
  </AppModal>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useContentStore } from '@/stores/contentStore'
import { useD5eData } from '@/composables/useD5eData'
import type { CharacterTemplateModel } from '@/types/unified'
import AppModal from '@/components/base/AppModal.vue'
import AppButton from '@/components/base/AppButton.vue'
import AppInput from '@/components/base/AppInput.vue'
import AppSelect from '@/components/base/AppSelect.vue'
import AppTextarea from '@/components/base/AppTextarea.vue'
import AppNumberInput from '@/components/base/AppNumberInput.vue'
import AppTabs from '@/components/base/AppTabs.vue'
import AppFormSection from '@/components/base/AppFormSection.vue'
import BaseAlert from '@/components/base/BaseAlert.vue'
import BaseLoader from '@/components/base/BaseLoader.vue'
import BaseBadge from '@/components/base/BaseBadge.vue'
import ContentPackBadge from '@/components/campaign/ContentPackBadge.vue'

interface Props {
  visible: boolean
  initialData?: Partial<CharacterTemplateModel>
}

const props = withDefaults(defineProps<Props>(), {
  visible: false,
  initialData: undefined,
})

const emit = defineEmits<{
  close: []
  save: [character: Partial<CharacterTemplateModel>]
}>()

// Stores
const contentStore = useContentStore()

// Form Data
const formData = ref({
  name: '',
  content_pack_ids: ['dnd_5e_srd'] as string[],
  race: '',
  char_class: '',
  background: '',
  alignment: 'true_neutral',
  level: 1,
  ability_scores: {
    strength: 10,
    dexterity: 10,
    constitution: 10,
    intelligence: 10,
    wisdom: 10,
    charisma: 10,
  },
  skills: [] as string[],
  expertises: [] as string[],
  cantrips: [] as string[],
  equipment: [] as string[],
  spells: [] as string[],
  backstory: '',
  ...props.initialData,
})

// Wizard state
const currentStep = ref(0)
const errors = ref<Record<string, string>>({})

// Step definitions
const steps = [
  { id: 'content-packs', label: 'Content Selection' },
  { id: 'basic-info', label: 'Basic Information' },
  { id: 'race-class', label: 'Race & Class' },
  { id: 'abilities', label: 'Ability Scores' },
  { id: 'skills', label: 'Skills & Proficiencies' },
  { id: 'equipment', label: 'Equipment & Spells' },
  { id: 'review', label: 'Review & Confirm' },
]

// Content packs
const contentPacksLoading = ref(false)
const availableContentPacks = computed(() =>
  contentStore.contentPacks.filter(pack => pack.is_active !== false)
)

// D5E Data with content pack filtering
const {
  getRaceOptions,
  getClassOptions,
  getBackgroundOptions,
  isLoading: d5eDataLoading,
} = useD5eData({ contentPackIds: formData.value.content_pack_ids })

// Computed options from D5E data
const raceOptions = computed(() => getRaceOptions())
const classOptions = computed(() => getClassOptions())
const backgroundOptions = computed(() => getBackgroundOptions())

// Ability score methods
const abilityScoreMethod = ref<'point-buy' | 'standard' | 'roll'>('point-buy')
const hasRolled = ref(false)

// Equipment method
const equipmentMethod = ref<'standard' | 'gold'>('standard')

const abilityScoreTabs = [
  { id: 'point-buy', label: 'Point Buy' },
  { id: 'standard', label: 'Standard Array' },
  { id: 'roll', label: 'Roll Dice' },
]

const abilities = [
  { key: 'strength', name: 'Strength' },
  { key: 'dexterity', name: 'Dexterity' },
  { key: 'constitution', name: 'Constitution' },
  { key: 'intelligence', name: 'Intelligence' },
  { key: 'wisdom', name: 'Wisdom' },
  { key: 'charisma', name: 'Charisma' },
]

const alignmentOptions = [
  { value: 'lawful_good', label: 'Lawful Good' },
  { value: 'neutral_good', label: 'Neutral Good' },
  { value: 'chaotic_good', label: 'Chaotic Good' },
  { value: 'lawful_neutral', label: 'Lawful Neutral' },
  { value: 'true_neutral', label: 'True Neutral' },
  { value: 'chaotic_neutral', label: 'Chaotic Neutral' },
  { value: 'lawful_evil', label: 'Lawful Evil' },
  { value: 'neutral_evil', label: 'Neutral Evil' },
  { value: 'chaotic_evil', label: 'Chaotic Evil' },
]

const standardArrayOptions = [
  { value: 15, label: '15' },
  { value: 14, label: '14' },
  { value: 13, label: '13' },
  { value: 12, label: '12' },
  { value: 10, label: '10' },
  { value: 8, label: '8' },
]

// Computed properties
const currentStepTitle = computed(() => {
  return `Create Character - ${steps[currentStep.value].label}`
})

const selectedRaceDetails = computed(() => {
  // TODO: Fetch race details based on selection
  return null
})

const selectedClassDetails = computed(() => {
  // TODO: Fetch class details based on selection
  return null
})

const pointBuyRemaining = computed(() => {
  if (abilityScoreMethod.value !== 'point-buy') return 0

  const costs: Record<number, number> = {
    8: 0,
    9: 1,
    10: 2,
    11: 3,
    12: 4,
    13: 5,
    14: 7,
    15: 9,
  }

  let total = 27 // Standard point buy budget
  for (const score of Object.values(formData.value.ability_scores)) {
    total -= costs[score as number] || 0
  }

  return total
})

// Skills & Proficiencies computed properties
const availableClassSkills = computed(() => {
  // TODO: Get from selected class data
  const baseSkills = [
    { value: 'athletics', label: 'Athletics' },
    { value: 'intimidation', label: 'Intimidation' },
    { value: 'insight', label: 'Insight' },
    { value: 'perception', label: 'Perception' },
  ]
  return baseSkills
})

const classSkillChoices = computed(() => {
  // TODO: Get from selected class data
  return 2
})

const backgroundSkills = computed(() => {
  // TODO: Get from selected background data
  return [
    { value: 'history', label: 'History' },
    { value: 'religion', label: 'Religion' },
  ]
})

const canChooseExpertise = computed(() => {
  // TODO: Check if selected class can choose expertise (e.g., Rogue, Bard)
  return (
    formData.value.char_class === 'rogue' ||
    formData.value.char_class === 'bard'
  )
})

const expertiseChoices = computed(() => {
  // TODO: Get from class data
  return 2
})

const availableExpertiseSkills = computed(() => {
  // Can only choose expertise in skills you're proficient in
  const allProficientSkills = [
    ...availableClassSkills.value.filter(skill =>
      formData.value.skills.includes(skill.value)
    ),
    ...backgroundSkills.value,
  ]
  return allProficientSkills
})

const grantedLanguages = computed(() => {
  // TODO: Get from race and background data
  return ['Common', 'Elvish']
})

const grantedTools = computed(() => {
  // TODO: Get from background data
  return ["Smith's Tools", "Thieves' Tools"]
})

// Equipment computed properties
const classEquipment = computed(() => {
  // TODO: Get from selected class data
  return ['Leather Armor', 'Shortsword', 'Simple Weapon', "Dungeoneer's Pack"]
})

const backgroundEquipment = computed(() => {
  // TODO: Get from selected background data
  return ["Artisan's Tools", 'Set of Fine Clothes', 'Belt Pouch with 15 gp']
})

// Spellcasting computed properties
const isSpellcaster = computed(() => {
  // TODO: Check if selected class is a spellcaster
  const spellcastingClasses = [
    'wizard',
    'sorcerer',
    'cleric',
    'druid',
    'bard',
    'warlock',
  ]
  return spellcastingClasses.includes(formData.value.char_class)
})

const cantripsKnown = computed(() => {
  // TODO: Get from class progression data
  if (!isSpellcaster.value) return 0
  return 2 // Default for level 1 casters
})

const spellsKnown = computed(() => {
  // TODO: Get from class progression data
  if (!isSpellcaster.value) return 0
  return 2 // Default for level 1 casters
})

const availableCantrips = computed(() => {
  // TODO: Get from selected class spell list
  return [
    { value: 'mage_hand', label: 'Mage Hand' },
    { value: 'prestidigitation', label: 'Prestidigitation' },
    { value: 'fire_bolt', label: 'Fire Bolt' },
    { value: 'light', label: 'Light' },
  ]
})

const availableFirstLevelSpells = computed(() => {
  // TODO: Get from selected class spell list
  return [
    { value: 'magic_missile', label: 'Magic Missile' },
    { value: 'shield', label: 'Shield' },
    { value: 'detect_magic', label: 'Detect Magic' },
    { value: 'burning_hands', label: 'Burning Hands' },
  ]
})

// Review step computed properties
const validationIssues = computed(() => {
  const issues: string[] = []

  // Check required fields
  if (!formData.value.name.trim()) {
    issues.push('Character name is required')
  }
  if (!formData.value.race) {
    issues.push('Race selection is required')
  }
  if (!formData.value.char_class) {
    issues.push('Class selection is required')
  }

  // Check skill selection count
  if (formData.value.skills.length < classSkillChoices.value) {
    issues.push(`Must select ${classSkillChoices.value} class skills`)
  }

  // Check spell selection for spellcasters
  if (isSpellcaster.value) {
    if (
      cantripsKnown.value > 0 &&
      formData.value.cantrips.length < cantripsKnown.value
    ) {
      issues.push(`Must select ${cantripsKnown.value} cantrips`)
    }
    if (
      spellsKnown.value > 0 &&
      formData.value.spells.length < spellsKnown.value
    ) {
      issues.push(`Must select ${spellsKnown.value} first level spells`)
    }
  }

  return issues
})

function validateCurrentStep(): boolean {
  errors.value = {}

  switch (currentStep.value) {
    case 0: // Content packs
      if (formData.value.content_pack_ids.length === 0) {
        errors.value.content_packs = 'Select at least one content pack'
        return false
      }
      return true

    case 1: // Basic info
      if (!formData.value.name.trim()) {
        errors.value.name = 'Character name is required'
        return false
      }
      if (!formData.value.alignment) {
        errors.value.alignment = 'Alignment is required'
        return false
      }
      return true

    case 2: // Race & Class
      if (!formData.value.race) {
        errors.value.race = 'Race is required'
        return false
      }
      if (!formData.value.char_class) {
        errors.value.char_class = 'Class is required'
        return false
      }
      return true

    case 3: // Ability scores
      if (
        abilityScoreMethod.value === 'point-buy' &&
        pointBuyRemaining.value < 0
      ) {
        return false
      }
      if (abilityScoreMethod.value === 'roll' && !hasRolled.value) {
        return false
      }
      return true

    case 4: // Skills & Proficiencies
      if (formData.value.skills.length < classSkillChoices.value) {
        errors.value.skills = `Must select ${classSkillChoices.value} class skills`
        return false
      }
      if (
        canChooseExpertise.value &&
        formData.value.expertises.length < expertiseChoices.value
      ) {
        errors.value.expertises = `Must select ${expertiseChoices.value} skills for expertise`
        return false
      }
      return true

    case 5: // Equipment & Spells
      if (isSpellcaster.value) {
        if (
          cantripsKnown.value > 0 &&
          formData.value.cantrips.length < cantripsKnown.value
        ) {
          errors.value.cantrips = `Must select ${cantripsKnown.value} cantrips`
          return false
        }
        if (
          spellsKnown.value > 0 &&
          formData.value.spells.length < spellsKnown.value
        ) {
          errors.value.spells = `Must select ${spellsKnown.value} first level spells`
          return false
        }
      }
      return true

    case 6: // Review
      return validationIssues.value.length === 0

    default:
      return true
  }
}

const canProceed = computed(() => {
  switch (currentStep.value) {
    case 0: // Content packs
      return formData.value.content_pack_ids.length > 0

    case 1: // Basic info
      return (
        formData.value.name.trim().length > 0 && formData.value.alignment !== ''
      )

    case 2: // Race & Class
      return formData.value.race !== '' && formData.value.char_class !== ''

    case 3: // Ability scores
      if (abilityScoreMethod.value === 'point-buy') {
        return pointBuyRemaining.value >= 0
      }
      if (abilityScoreMethod.value === 'roll') {
        return hasRolled.value
      }
      return true

    case 4: // Skills & Proficiencies
      return formData.value.skills.length >= classSkillChoices.value

    case 5: // Equipment & Spells
      if (isSpellcaster.value) {
        return (
          formData.value.cantrips.length >= cantripsKnown.value &&
          formData.value.spells.length >= spellsKnown.value
        )
      }
      return true

    case 6: // Review
      return validationIssues.value.length === 0

    default:
      return true
  }
})

// Methods
function handleClose() {
  if (
    confirm(
      'Are you sure you want to cancel character creation? All progress will be lost.'
    )
  ) {
    emit('close')
  }
}

function nextStep() {
  if (validateCurrentStep() && currentStep.value < steps.length - 1) {
    currentStep.value++
  }
}

function previousStep() {
  if (currentStep.value > 0) {
    currentStep.value--
  }
}

function getPointBuyCost(score: number): number {
  const costs: Record<number, number> = {
    8: 0,
    9: 1,
    10: 2,
    11: 3,
    12: 4,
    13: 5,
    14: 7,
    15: 9,
  }
  return costs[score] || 0
}

function getAbilityModifier(score: number): string {
  const modifier = Math.floor((score - 10) / 2)
  return modifier >= 0 ? `+${modifier}` : `${modifier}`
}

function rollAbilityScores() {
  hasRolled.value = true

  // Roll 4d6, drop lowest, for each ability
  for (const ability of abilities) {
    const rolls = Array.from(
      { length: 4 },
      () => Math.floor(Math.random() * 6) + 1
    )
    rolls.sort((a, b) => b - a)
    formData.value.ability_scores[
      ability.key as keyof typeof formData.value.ability_scores
    ] = rolls[0] + rolls[1] + rolls[2]
  }
}

// Helper methods for display names
function getRaceDisplayName(raceKey: string): string {
  const race = raceOptions.value.find(r => r.value === raceKey)
  return race?.label || raceKey
}

function getClassDisplayName(classKey: string): string {
  const charClass = classOptions.value.find(c => c.value === classKey)
  return charClass?.label || classKey
}

function getBackgroundDisplayName(backgroundKey: string): string {
  const background = backgroundOptions.value.find(
    b => b.value === backgroundKey
  )
  return background?.label || backgroundKey
}

function getAlignmentDisplayName(alignmentKey: string): string {
  const alignment = alignmentOptions.find(a => a.value === alignmentKey)
  return alignment?.label || alignmentKey
}

function getContentPackName(packId: string): string {
  const pack = availableContentPacks.value.find(p => p.id === packId)
  return pack?.name || packId
}

async function saveCharacter() {
  if (!validateCurrentStep()) return

  // Transform form data to match CharacterTemplateModel
  const characterData: Partial<CharacterTemplateModel> = {
    ...formData.value,
    // Add any additional transformations needed
  }

  emit('save', characterData)
}

// Load content packs on mount
onMounted(async () => {
  contentPacksLoading.value = true
  try {
    await contentStore.loadContentPacks()
  } finally {
    contentPacksLoading.value = false
  }
})

// Reset ability score method when changing it
watch(abilityScoreMethod, () => {
  hasRolled.value = false
  // Reset to default scores
  formData.value.ability_scores = {
    strength: 10,
    dexterity: 10,
    constitution: 10,
    intelligence: 10,
    wisdom: 10,
    charisma: 10,
  }
})
</script>
