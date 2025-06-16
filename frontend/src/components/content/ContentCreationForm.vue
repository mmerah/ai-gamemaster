<template>
  <div class="space-y-6">
    <!-- Spell Form -->
    <div v-if="contentType === 'spells'" class="space-y-4">
      <h3 class="text-lg font-semibold text-text-primary">Create Spell</h3>
      
      <!-- Basic Info -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label class="block text-sm font-medium text-text-primary mb-1">Name *</label>
          <input v-model="spell.name" type="text" required class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold" />
        </div>
        <div>
          <label class="block text-sm font-medium text-text-primary mb-1">Level *</label>
          <select v-model.number="spell.level" required class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold">
            <option :value="0">Cantrip</option>
            <option v-for="level in 9" :key="level" :value="level">Level {{ level }}</option>
          </select>
        </div>
      </div>

      <!-- School -->
      <div>
        <label class="block text-sm font-medium text-text-primary mb-1">School *</label>
        <select v-model="spell.school" required class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold">
          <option value="">Select School...</option>
          <option value="abjuration">Abjuration</option>
          <option value="conjuration">Conjuration</option>
          <option value="divination">Divination</option>
          <option value="enchantment">Enchantment</option>
          <option value="evocation">Evocation</option>
          <option value="illusion">Illusion</option>
          <option value="necromancy">Necromancy</option>
          <option value="transmutation">Transmutation</option>
        </select>
      </div>

      <!-- Casting Time & Duration -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label class="block text-sm font-medium text-text-primary mb-1">Casting Time *</label>
          <input v-model="spell.casting_time" type="text" required placeholder="1 action" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold" />
        </div>
        <div>
          <label class="block text-sm font-medium text-text-primary mb-1">Duration *</label>
          <input v-model="spell.duration" type="text" required placeholder="Instantaneous" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold" />
        </div>
      </div>

      <!-- Range -->
      <div>
        <label class="block text-sm font-medium text-text-primary mb-1">Range *</label>
        <input v-model="spell.range" type="text" required placeholder="30 feet" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold" />
      </div>

      <!-- Components -->
      <div>
        <label class="block text-sm font-medium text-text-primary mb-1">Components *</label>
        <div class="flex gap-4">
          <label class="flex items-center">
            <input type="checkbox" value="V" v-model="spell.components" class="mr-2" />
            Verbal (V)
          </label>
          <label class="flex items-center">
            <input type="checkbox" value="S" v-model="spell.components" class="mr-2" />
            Somatic (S)
          </label>
          <label class="flex items-center">
            <input type="checkbox" value="M" v-model="spell.components" class="mr-2" />
            Material (M)
          </label>
        </div>
      </div>

      <!-- Material Components -->
      <div v-if="spell.components.includes('M')">
        <label class="block text-sm font-medium text-text-primary mb-1">Material Components</label>
        <input v-model="spell.material" type="text" placeholder="a bit of fur and a rod of amber" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold" />
      </div>

      <!-- Ritual & Concentration -->
      <div class="flex gap-6">
        <label class="flex items-center">
          <input type="checkbox" v-model="spell.ritual" class="mr-2" />
          Ritual
        </label>
        <label class="flex items-center">
          <input type="checkbox" v-model="spell.concentration" class="mr-2" />
          Concentration
        </label>
      </div>

      <!-- Description -->
      <div>
        <label class="block text-sm font-medium text-text-primary mb-1">Description *</label>
        <textarea v-model="spell.desc" rows="4" required placeholder="Spell description..." class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold"></textarea>
      </div>

      <!-- Higher Level -->
      <div>
        <label class="block text-sm font-medium text-text-primary mb-1">At Higher Levels</label>
        <textarea v-model="spell.higher_level" rows="2" placeholder="When you cast this spell using a spell slot of 2nd level or higher..." class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold"></textarea>
      </div>

      <!-- Classes -->
      <div>
        <label class="block text-sm font-medium text-text-primary mb-1">Available to Classes</label>
        <div class="grid grid-cols-2 md:grid-cols-3 gap-2">
          <label v-for="cls in availableClasses" :key="cls" class="flex items-center">
            <input type="checkbox" :value="cls" v-model="spell.classes" class="mr-2" />
            {{ cls }}
          </label>
        </div>
      </div>
    </div>

    <!-- Monster Form -->
    <div v-if="contentType === 'monsters'" class="space-y-4">
      <h3 class="text-lg font-semibold text-text-primary">Create Monster</h3>
      
      <!-- Basic Info -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label class="block text-sm font-medium text-text-primary mb-1">Name *</label>
          <input v-model="monster.name" type="text" required class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold" />
        </div>
        <div>
          <label class="block text-sm font-medium text-text-primary mb-1">Size *</label>
          <select v-model="monster.size" required class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold">
            <option value="Tiny">Tiny</option>
            <option value="Small">Small</option>
            <option value="Medium">Medium</option>
            <option value="Large">Large</option>
            <option value="Huge">Huge</option>
            <option value="Gargantuan">Gargantuan</option>
          </select>
        </div>
      </div>

      <!-- Type & Alignment -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label class="block text-sm font-medium text-text-primary mb-1">Type *</label>
          <input v-model="monster.type" type="text" required placeholder="beast, humanoid, etc." class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold" />
        </div>
        <div>
          <label class="block text-sm font-medium text-text-primary mb-1">Alignment *</label>
          <input v-model="monster.alignment" type="text" required placeholder="neutral evil" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold" />
        </div>
      </div>

      <!-- Combat Stats -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <label class="block text-sm font-medium text-text-primary mb-1">Armor Class *</label>
          <input v-model.number="monster.armor_class" type="number" required class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold" />
        </div>
        <div>
          <label class="block text-sm font-medium text-text-primary mb-1">Hit Points *</label>
          <input v-model.number="monster.hit_points" type="number" required class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold" />
        </div>
        <div>
          <label class="block text-sm font-medium text-text-primary mb-1">Hit Dice *</label>
          <input v-model="monster.hit_dice" type="text" required placeholder="3d8+3" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold" />
        </div>
      </div>

      <!-- Speed -->
      <div>
        <label class="block text-sm font-medium text-text-primary mb-1">Speed *</label>
        <input v-model="monster.speed" type="text" required placeholder="30 ft., fly 60 ft." class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold" />
      </div>

      <!-- Abilities -->
      <div>
        <label class="block text-sm font-medium text-text-primary mb-1">Ability Scores *</label>
        <div class="grid grid-cols-3 md:grid-cols-6 gap-2">
          <div>
            <label class="text-xs">STR</label>
            <input v-model.number="monster.strength" type="number" required min="1" max="30" class="w-full px-2 py-1 border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-gold" />
          </div>
          <div>
            <label class="text-xs">DEX</label>
            <input v-model.number="monster.dexterity" type="number" required min="1" max="30" class="w-full px-2 py-1 border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-gold" />
          </div>
          <div>
            <label class="text-xs">CON</label>
            <input v-model.number="monster.constitution" type="number" required min="1" max="30" class="w-full px-2 py-1 border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-gold" />
          </div>
          <div>
            <label class="text-xs">INT</label>
            <input v-model.number="monster.intelligence" type="number" required min="1" max="30" class="w-full px-2 py-1 border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-gold" />
          </div>
          <div>
            <label class="text-xs">WIS</label>
            <input v-model.number="monster.wisdom" type="number" required min="1" max="30" class="w-full px-2 py-1 border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-gold" />
          </div>
          <div>
            <label class="text-xs">CHA</label>
            <input v-model.number="monster.charisma" type="number" required min="1" max="30" class="w-full px-2 py-1 border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-gold" />
          </div>
        </div>
      </div>

      <!-- Challenge Rating -->
      <div>
        <label class="block text-sm font-medium text-text-primary mb-1">Challenge Rating *</label>
        <input v-model.number="monster.challenge_rating" type="number" required min="0" step="0.125" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold" />
      </div>

      <!-- Languages -->
      <div>
        <label class="block text-sm font-medium text-text-primary mb-1">Languages</label>
        <input v-model="monster.languages" type="text" placeholder="Common, Draconic" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold" />
      </div>

      <!-- Senses -->
      <div>
        <label class="block text-sm font-medium text-text-primary mb-1">Senses</label>
        <input v-model="monster.senses" type="text" placeholder="darkvision 60 ft., passive Perception 13" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold" />
      </div>

      <!-- Actions (simplified) -->
      <div>
        <label class="block text-sm font-medium text-text-primary mb-1">Actions</label>
        <textarea v-model="monster.actions" rows="4" placeholder="Multiattack. The monster makes two claw attacks.&#10;&#10;Claw. Melee Weapon Attack: +5 to hit, reach 5 ft., one target. Hit: 8 (1d6 + 3) slashing damage." class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold font-mono text-sm"></textarea>
      </div>
    </div>

    <!-- Equipment Form -->
    <div v-if="contentType === 'equipment'" class="space-y-4">
      <h3 class="text-lg font-semibold text-text-primary">Create Equipment</h3>
      
      <!-- Basic Info -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label class="block text-sm font-medium text-text-primary mb-1">Name *</label>
          <input v-model="equipment.name" type="text" required class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold" />
        </div>
        <div>
          <label class="block text-sm font-medium text-text-primary mb-1">Category *</label>
          <select v-model="equipment.equipment_category" required class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold">
            <option value="">Select Category...</option>
            <option value="Weapon">Weapon</option>
            <option value="Armor">Armor</option>
            <option value="Adventuring Gear">Adventuring Gear</option>
            <option value="Tools">Tools</option>
          </select>
        </div>
      </div>

      <!-- Cost & Weight -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label class="block text-sm font-medium text-text-primary mb-1">Cost *</label>
          <div class="flex gap-2">
            <input v-model.number="equipment.cost_quantity" type="number" required placeholder="50" class="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold" />
            <select v-model="equipment.cost_unit" required class="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold">
              <option value="cp">cp</option>
              <option value="sp">sp</option>
              <option value="ep">ep</option>
              <option value="gp">gp</option>
              <option value="pp">pp</option>
            </select>
          </div>
        </div>
        <div>
          <label class="block text-sm font-medium text-text-primary mb-1">Weight (lbs)</label>
          <input v-model.number="equipment.weight" type="number" step="0.1" placeholder="3" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold" />
        </div>
      </div>

      <!-- Weapon Specific -->
      <div v-if="equipment.equipment_category === 'Weapon'" class="space-y-4">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-text-primary mb-1">Weapon Category *</label>
            <select v-model="equipment.weapon_category" required class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold">
              <option value="Simple">Simple</option>
              <option value="Martial">Martial</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-text-primary mb-1">Weapon Range *</label>
            <select v-model="equipment.weapon_range" required class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold">
              <option value="Melee">Melee</option>
              <option value="Ranged">Ranged</option>
            </select>
          </div>
        </div>

        <div>
          <label class="block text-sm font-medium text-text-primary mb-1">Damage *</label>
          <div class="flex gap-2">
            <input v-model="equipment.damage_dice" type="text" required placeholder="1d8" class="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold" />
            <select v-model="equipment.damage_type" required class="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold">
              <option value="">Damage Type...</option>
              <option value="Slashing">Slashing</option>
              <option value="Piercing">Piercing</option>
              <option value="Bludgeoning">Bludgeoning</option>
            </select>
          </div>
        </div>
      </div>

      <!-- Description -->
      <div>
        <label class="block text-sm font-medium text-text-primary mb-1">Description</label>
        <textarea v-model="equipment.desc" rows="3" placeholder="Item description..." class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold"></textarea>
      </div>
    </div>

    <!-- Race Form -->
    <div v-if="contentType === 'races'" class="space-y-4">
      <h3 class="text-lg font-semibold text-text-primary">Create Race</h3>
      
      <!-- Basic Info -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label class="block text-sm font-medium text-text-primary mb-1">Name *</label>
          <input v-model="race.name" type="text" required class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold" />
        </div>
        <div>
          <label class="block text-sm font-medium text-text-primary mb-1">Size *</label>
          <select v-model="race.size" required class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold">
            <option value="Tiny">Tiny</option>
            <option value="Small">Small</option>
            <option value="Medium">Medium</option>
            <option value="Large">Large</option>
            <option value="Huge">Huge</option>
            <option value="Gargantuan">Gargantuan</option>
          </select>
        </div>
      </div>

      <!-- Speed & Alignment -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label class="block text-sm font-medium text-text-primary mb-1">Speed (feet) *</label>
          <input v-model.number="race.speed" type="number" required placeholder="30" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold" />
        </div>
        <div>
          <label class="block text-sm font-medium text-text-primary mb-1">Typical Alignment *</label>
          <input v-model="race.alignment" type="text" required placeholder="Any alignment" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold" />
        </div>
      </div>

      <!-- Ability Score Bonuses -->
      <div>
        <label class="block text-sm font-medium text-text-primary mb-1">Ability Score Bonuses</label>
        <div class="grid grid-cols-3 md:grid-cols-6 gap-2">
          <div v-for="ability in ['STR', 'DEX', 'CON', 'INT', 'WIS', 'CHA']" :key="ability">
            <label class="text-xs">{{ ability }}</label>
            <input 
              v-model.number="race.ability_bonuses[ability]" 
              type="number" 
              min="-5" 
              max="5" 
              placeholder="0"
              class="w-full px-2 py-1 border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-gold" 
            />
          </div>
        </div>
      </div>

      <!-- Age & Size Description -->
      <div>
        <label class="block text-sm font-medium text-text-primary mb-1">Age Description *</label>
        <textarea v-model="race.age" rows="2" required placeholder="Members of this race reach adulthood at..." class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold"></textarea>
      </div>

      <div>
        <label class="block text-sm font-medium text-text-primary mb-1">Size Description *</label>
        <textarea v-model="race.size_description" rows="2" required placeholder="Members of this race are typically..." class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold"></textarea>
      </div>

      <!-- Languages -->
      <div>
        <label class="block text-sm font-medium text-text-primary mb-1">Languages *</label>
        <input v-model="race.languages" type="text" required placeholder="Common, Elvish" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold" />
      </div>
    </div>

    <!-- Background Form -->
    <div v-if="contentType === 'backgrounds'" class="space-y-4">
      <h3 class="text-lg font-semibold text-text-primary">Create Background</h3>
      
      <!-- Basic Info -->
      <div>
        <label class="block text-sm font-medium text-text-primary mb-1">Name *</label>
        <input v-model="background.name" type="text" required class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold" />
      </div>

      <!-- Feature -->
      <div>
        <label class="block text-sm font-medium text-text-primary mb-1">Feature Name *</label>
        <input v-model="background.feature_name" type="text" required placeholder="Military Rank" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold" />
      </div>

      <div>
        <label class="block text-sm font-medium text-text-primary mb-1">Feature Description *</label>
        <textarea v-model="background.feature_desc" rows="3" required placeholder="Description of the background feature..." class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold"></textarea>
      </div>

      <!-- Starting Proficiencies -->
      <div>
        <label class="block text-sm font-medium text-text-primary mb-1">Starting Proficiencies</label>
        <input v-model="background.proficiencies" type="text" placeholder="Skill: Athletics, Skill: Intimidation" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold" />
      </div>

      <!-- Languages -->
      <div>
        <label class="block text-sm font-medium text-text-primary mb-1">Number of Languages to Choose</label>
        <input v-model.number="background.language_choices" type="number" min="0" placeholder="1" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold" />
      </div>
    </div>

    <!-- Feat Form -->
    <div v-if="contentType === 'feats'" class="space-y-4">
      <h3 class="text-lg font-semibold text-text-primary">Create Feat</h3>
      
      <!-- Basic Info -->
      <div>
        <label class="block text-sm font-medium text-text-primary mb-1">Name *</label>
        <input v-model="feat.name" type="text" required class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold" />
      </div>

      <!-- Prerequisites -->
      <div>
        <label class="block text-sm font-medium text-text-primary mb-1">Prerequisites</label>
        <input v-model="feat.prerequisites" type="text" placeholder="Strength 13 or higher" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold" />
      </div>

      <!-- Description -->
      <div>
        <label class="block text-sm font-medium text-text-primary mb-1">Description *</label>
        <textarea v-model="feat.desc" rows="4" required placeholder="Feat benefits and mechanics..." class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold"></textarea>
      </div>
    </div>

    <!-- Trait Form -->
    <div v-if="contentType === 'traits'" class="space-y-4">
      <h3 class="text-lg font-semibold text-text-primary">Create Trait</h3>
      
      <!-- Basic Info -->
      <div>
        <label class="block text-sm font-medium text-text-primary mb-1">Name *</label>
        <input v-model="trait.name" type="text" required class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold" />
      </div>

      <!-- Associated Races -->
      <div>
        <label class="block text-sm font-medium text-text-primary mb-1">Associated Races *</label>
        <input v-model="trait.races" type="text" required placeholder="Dwarf, Elf, Halfling" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold" />
      </div>

      <!-- Description -->
      <div>
        <label class="block text-sm font-medium text-text-primary mb-1">Description *</label>
        <textarea v-model="trait.desc" rows="3" required placeholder="Trait description..." class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold"></textarea>
      </div>
    </div>

    <!-- Skill Form -->
    <div v-if="contentType === 'skills'" class="space-y-4">
      <h3 class="text-lg font-semibold text-text-primary">Create Skill</h3>
      
      <!-- Basic Info -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label class="block text-sm font-medium text-text-primary mb-1">Name *</label>
          <input v-model="skill.name" type="text" required class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold" />
        </div>
        <div>
          <label class="block text-sm font-medium text-text-primary mb-1">Ability Score *</label>
          <select v-model="skill.ability_score" required class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold">
            <option value="STR">Strength</option>
            <option value="DEX">Dexterity</option>
            <option value="CON">Constitution</option>
            <option value="INT">Intelligence</option>
            <option value="WIS">Wisdom</option>
            <option value="CHA">Charisma</option>
          </select>
        </div>
      </div>

      <!-- Description -->
      <div>
        <label class="block text-sm font-medium text-text-primary mb-1">Description *</label>
        <textarea v-model="skill.desc" rows="3" required placeholder="When this skill is used..." class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold"></textarea>
      </div>
    </div>

    <!-- Condition Form -->
    <div v-if="contentType === 'conditions'" class="space-y-4">
      <h3 class="text-lg font-semibold text-text-primary">Create Condition</h3>
      
      <!-- Basic Info -->
      <div>
        <label class="block text-sm font-medium text-text-primary mb-1">Name *</label>
        <input v-model="condition.name" type="text" required class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold" />
      </div>

      <!-- Description -->
      <div>
        <label class="block text-sm font-medium text-text-primary mb-1">Effects *</label>
        <textarea v-model="condition.desc" rows="4" required placeholder="List each effect on a new line..." class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold"></textarea>
      </div>
    </div>

    <!-- Alignments Form -->
    <div v-if="contentType === 'alignments'" class="space-y-4">
      <h3 class="text-lg font-semibold text-text-primary">Create Alignment</h3>
      
      <!-- Basic Info -->
      <div>
        <label class="block text-sm font-medium text-text-primary mb-1">Name *</label>
        <input v-model="alignment.name" type="text" required placeholder="e.g., Chaotic Good" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold" />
      </div>

      <!-- Abbreviation -->
      <div>
        <label class="block text-sm font-medium text-text-primary mb-1">Abbreviation *</label>
        <input v-model="alignment.abbreviation" type="text" required placeholder="e.g., CG" maxlength="2" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold" />
      </div>

      <!-- Description -->
      <div>
        <label class="block text-sm font-medium text-text-primary mb-1">Description *</label>
        <textarea v-model="alignment.desc" rows="4" required placeholder="Describe the moral and ethical philosophy..." class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold"></textarea>
      </div>
    </div>

    <!-- Damage Types Form -->
    <div v-if="contentType === 'damage-types'" class="space-y-4">
      <h3 class="text-lg font-semibold text-text-primary">Create Damage Type</h3>
      
      <!-- Basic Info -->
      <div>
        <label class="block text-sm font-medium text-text-primary mb-1">Name *</label>
        <input v-model="damageType.name" type="text" required placeholder="e.g., Psychic" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold" />
      </div>

      <!-- Description -->
      <div>
        <label class="block text-sm font-medium text-text-primary mb-1">Description *</label>
        <textarea v-model="damageType.desc" rows="3" required placeholder="Describe what causes this type of damage..." class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold"></textarea>
      </div>
    </div>

    <!-- Weapon Properties Form -->
    <div v-if="contentType === 'weapon-properties'" class="space-y-4">
      <h3 class="text-lg font-semibold text-text-primary">Create Weapon Property</h3>
      
      <!-- Basic Info -->
      <div>
        <label class="block text-sm font-medium text-text-primary mb-1">Name *</label>
        <input v-model="weaponProperty.name" type="text" required placeholder="e.g., Finesse" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold" />
      </div>

      <!-- Description -->
      <div>
        <label class="block text-sm font-medium text-text-primary mb-1">Description *</label>
        <textarea v-model="weaponProperty.desc" rows="3" required placeholder="Describe the weapon property effect..." class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold"></textarea>
      </div>
    </div>

    <!-- Ability Scores Form -->
    <div v-if="contentType === 'ability-scores'" class="space-y-4">
      <h3 class="text-lg font-semibold text-text-primary">Create Ability Score</h3>
      
      <!-- Basic Info -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label class="block text-sm font-medium text-text-primary mb-1">Name (Abbreviation) *</label>
          <input v-model="abilityScore.name" type="text" required placeholder="e.g., STR" maxlength="3" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold" />
        </div>
        <div>
          <label class="block text-sm font-medium text-text-primary mb-1">Full Name *</label>
          <input v-model="abilityScore.full_name" type="text" required placeholder="e.g., Strength" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold" />
        </div>
      </div>

      <!-- Description -->
      <div>
        <label class="block text-sm font-medium text-text-primary mb-1">Description *</label>
        <textarea v-model="abilityScore.desc" rows="4" required placeholder="Describe what this ability represents..." class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold"></textarea>
      </div>

      <!-- Skills -->
      <div>
        <label class="block text-sm font-medium text-text-primary mb-1">Associated Skills</label>
        <input v-model="abilityScore.skills" type="text" placeholder="e.g., Athletics (comma-separated if multiple)" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold" />
      </div>
    </div>

    <!-- Languages Form -->
    <div v-if="contentType === 'languages'" class="space-y-4">
      <h3 class="text-lg font-semibold text-text-primary">Create Language</h3>
      
      <!-- Basic Info -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label class="block text-sm font-medium text-text-primary mb-1">Name *</label>
          <input v-model="language.name" type="text" required placeholder="e.g., Draconic" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold" />
        </div>
        <div>
          <label class="block text-sm font-medium text-text-primary mb-1">Type *</label>
          <select v-model="language.type" required class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold">
            <option value="">Select type...</option>
            <option value="Standard">Standard</option>
            <option value="Exotic">Exotic</option>
          </select>
        </div>
      </div>

      <!-- Script -->
      <div>
        <label class="block text-sm font-medium text-text-primary mb-1">Script</label>
        <input v-model="language.script" type="text" placeholder="e.g., Draconic" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold" />
      </div>

      <!-- Typical Speakers -->
      <div>
        <label class="block text-sm font-medium text-text-primary mb-1">Typical Speakers</label>
        <input v-model="language.typical_speakers" type="text" placeholder="e.g., Dragons, Dragonborn (comma-separated)" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold" />
      </div>
    </div>

    <!-- Proficiencies Form -->
    <div v-if="contentType === 'proficiencies'" class="space-y-4">
      <h3 class="text-lg font-semibold text-text-primary">Create Proficiency</h3>
      
      <!-- Basic Info -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label class="block text-sm font-medium text-text-primary mb-1">Name *</label>
          <input v-model="proficiency.name" type="text" required placeholder="e.g., Light Armor" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold" />
        </div>
        <div>
          <label class="block text-sm font-medium text-text-primary mb-1">Type *</label>
          <select v-model="proficiency.type" required class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold">
            <option value="">Select type...</option>
            <option value="Armor">Armor</option>
            <option value="Weapons">Weapons</option>
            <option value="Tools">Tools</option>
            <option value="Skills">Skills</option>
            <option value="Saving Throws">Saving Throws</option>
            <option value="Other">Other</option>
          </select>
        </div>
      </div>

      <!-- Classes -->
      <div>
        <label class="block text-sm font-medium text-text-primary mb-1">Classes that grant this</label>
        <input v-model="proficiency.classes" type="text" placeholder="e.g., Fighter, Paladin (comma-separated)" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold" />
      </div>

      <!-- Races -->
      <div>
        <label class="block text-sm font-medium text-text-primary mb-1">Races that grant this</label>
        <input v-model="proficiency.races" type="text" placeholder="e.g., Dwarf (comma-separated)" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold" />
      </div>
    </div>

    <!-- Rules Form -->
    <div v-if="contentType === 'rules'" class="space-y-4">
      <h3 class="text-lg font-semibold text-text-primary">Create Rule</h3>
      
      <!-- Basic Info -->
      <div>
        <label class="block text-sm font-medium text-text-primary mb-1">Name *</label>
        <input v-model="rule.name" type="text" required placeholder="e.g., Advantage and Disadvantage" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold" />
      </div>

      <!-- Description -->
      <div>
        <label class="block text-sm font-medium text-text-primary mb-1">Description *</label>
        <textarea v-model="rule.desc" rows="6" required placeholder="Explain the rule in detail..." class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold"></textarea>
      </div>

      <!-- Subsections -->
      <div>
        <label class="block text-sm font-medium text-text-primary mb-1">Subsections</label>
        <input v-model="rule.subsections" type="text" placeholder="Related rule sections (comma-separated)" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold" />
      </div>
    </div>

    <!-- Equipment Categories Form -->
    <div v-if="contentType === 'equipment-categories'" class="space-y-4">
      <h3 class="text-lg font-semibold text-text-primary">Create Equipment Category</h3>
      
      <!-- Basic Info -->
      <div>
        <label class="block text-sm font-medium text-text-primary mb-1">Name *</label>
        <input v-model="equipmentCategory.name" type="text" required placeholder="e.g., Adventuring Gear" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold" />
      </div>

      <!-- Equipment List -->
      <div>
        <label class="block text-sm font-medium text-text-primary mb-1">Equipment in this category</label>
        <textarea v-model="equipmentCategory.equipment" rows="4" placeholder="List equipment items in this category (one per line)..." class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold"></textarea>
      </div>
    </div>

    <!-- Magic Schools Form -->
    <div v-if="contentType === 'magic-schools'" class="space-y-4">
      <h3 class="text-lg font-semibold text-text-primary">Create Magic School</h3>
      
      <!-- Basic Info -->
      <div>
        <label class="block text-sm font-medium text-text-primary mb-1">Name *</label>
        <input v-model="magicSchool.name" type="text" required placeholder="e.g., Necromancy" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold" />
      </div>

      <!-- Description -->
      <div>
        <label class="block text-sm font-medium text-text-primary mb-1">Description *</label>
        <textarea v-model="magicSchool.desc" rows="4" required placeholder="Describe this school of magic..." class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold"></textarea>
      </div>
    </div>

    <!-- Rule Sections Form -->
    <div v-if="contentType === 'rule-sections'" class="space-y-4">
      <h3 class="text-lg font-semibold text-text-primary">Create Rule Section</h3>
      
      <!-- Basic Info -->
      <div>
        <label class="block text-sm font-medium text-text-primary mb-1">Name *</label>
        <input v-model="ruleSection.name" type="text" required placeholder="e.g., Combat" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold" />
      </div>

      <!-- Description -->
      <div>
        <label class="block text-sm font-medium text-text-primary mb-1">Description *</label>
        <textarea v-model="ruleSection.desc" rows="6" required placeholder="Describe this rule section..." class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold"></textarea>
      </div>
    </div>

    <!-- Features Form -->
    <div v-if="contentType === 'features'" class="space-y-4">
      <h3 class="text-lg font-semibold text-text-primary">Create Feature</h3>
      
      <!-- Basic Info -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label class="block text-sm font-medium text-text-primary mb-1">Name *</label>
          <input v-model="feature.name" type="text" required placeholder="e.g., Action Surge" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold" />
        </div>
        <div>
          <label class="block text-sm font-medium text-text-primary mb-1">Level *</label>
          <input v-model.number="feature.level" type="number" required min="1" max="20" placeholder="1" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold" />
        </div>
      </div>

      <!-- Class & Subclass -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label class="block text-sm font-medium text-text-primary mb-1">Class *</label>
          <select v-model="feature.class_ref" required class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold">
            <option value="">Select class...</option>
            <option v-for="cls in availableClasses" :key="cls" :value="cls">{{ cls }}</option>
          </select>
        </div>
        <div>
          <label class="block text-sm font-medium text-text-primary mb-1">Subclass</label>
          <input v-model="feature.subclass" type="text" placeholder="e.g., Champion (optional)" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold" />
        </div>
      </div>

      <!-- Description -->
      <div>
        <label class="block text-sm font-medium text-text-primary mb-1">Description *</label>
        <textarea v-model="feature.desc" rows="4" required placeholder="Describe what this feature does..." class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold"></textarea>
      </div>
    </div>

    <!-- Levels Form -->
    <div v-if="contentType === 'levels'" class="space-y-4">
      <h3 class="text-lg font-semibold text-text-primary">Create Level</h3>
      
      <!-- Basic Info -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <label class="block text-sm font-medium text-text-primary mb-1">Level *</label>
          <input v-model.number="level.level" type="number" required min="1" max="20" placeholder="1" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold" />
        </div>
        <div>
          <label class="block text-sm font-medium text-text-primary mb-1">Ability Score Bonuses</label>
          <input v-model.number="level.ability_score_bonuses" type="number" min="0" placeholder="0" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold" />
        </div>
        <div>
          <label class="block text-sm font-medium text-text-primary mb-1">Proficiency Bonus *</label>
          <input v-model.number="level.prof_bonus" type="number" required min="2" max="6" placeholder="2" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold" />
        </div>
      </div>

      <!-- Class -->
      <div>
        <label class="block text-sm font-medium text-text-primary mb-1">Class *</label>
        <select v-model="level.class_ref" required class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold">
          <option value="">Select class...</option>
          <option v-for="cls in availableClasses" :key="cls" :value="cls">{{ cls }}</option>
        </select>
      </div>

      <!-- Features -->
      <div>
        <label class="block text-sm font-medium text-text-primary mb-1">Features gained at this level</label>
        <textarea v-model="level.features" rows="3" placeholder="List features gained (one per line)..." class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold"></textarea>
      </div>

      <!-- Subclass -->
      <div>
        <label class="block text-sm font-medium text-text-primary mb-1">Subclass</label>
        <input v-model="level.subclass" type="text" placeholder="e.g., Champion (optional)" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold" />
      </div>
    </div>

    <!-- Magic Items Form -->
    <div v-if="contentType === 'magic-items'" class="space-y-4">
      <h3 class="text-lg font-semibold text-text-primary">Create Magic Item</h3>
      
      <!-- Basic Info -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label class="block text-sm font-medium text-text-primary mb-1">Name *</label>
          <input v-model="magicItem.name" type="text" required placeholder="e.g., Ring of Protection" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold" />
        </div>
        <div>
          <label class="block text-sm font-medium text-text-primary mb-1">Rarity *</label>
          <select v-model="magicItem.rarity" required class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold">
            <option value="">Select rarity...</option>
            <option value="Common">Common</option>
            <option value="Uncommon">Uncommon</option>
            <option value="Rare">Rare</option>
            <option value="Very Rare">Very Rare</option>
            <option value="Legendary">Legendary</option>
            <option value="Artifact">Artifact</option>
          </select>
        </div>
      </div>

      <!-- Type & Attunement -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label class="block text-sm font-medium text-text-primary mb-1">Type</label>
          <input v-model="magicItem.type" type="text" placeholder="e.g., Ring, Wondrous item" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold" />
        </div>
        <div class="flex items-center">
          <input v-model="magicItem.requires_attunement" type="checkbox" id="attunement" class="mr-2" />
          <label for="attunement" class="text-sm font-medium text-text-primary">Requires Attunement</label>
        </div>
      </div>

      <!-- Description -->
      <div>
        <label class="block text-sm font-medium text-text-primary mb-1">Description *</label>
        <textarea v-model="magicItem.desc" rows="6" required placeholder="Describe the item's appearance, properties, and effects..." class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold"></textarea>
      </div>
    </div>

    <!-- Subclasses Form -->
    <div v-if="contentType === 'subclasses'" class="space-y-4">
      <h3 class="text-lg font-semibold text-text-primary">Create Subclass</h3>
      
      <!-- Basic Info -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label class="block text-sm font-medium text-text-primary mb-1">Name *</label>
          <input v-model="subclass.name" type="text" required placeholder="e.g., Champion" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold" />
        </div>
        <div>
          <label class="block text-sm font-medium text-text-primary mb-1">Parent Class *</label>
          <select v-model="subclass.class_ref" required class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold">
            <option value="">Select class...</option>
            <option v-for="cls in availableClasses" :key="cls" :value="cls">{{ cls }}</option>
          </select>
        </div>
      </div>

      <!-- Description -->
      <div>
        <label class="block text-sm font-medium text-text-primary mb-1">Description *</label>
        <textarea v-model="subclass.desc" rows="4" required placeholder="Describe the subclass and its theme..." class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold"></textarea>
      </div>

      <!-- Features -->
      <div>
        <label class="block text-sm font-medium text-text-primary mb-1">Subclass Features</label>
        <textarea v-model="subclass.features" rows="6" placeholder="List the unique features this subclass gains (one per line with level)..." class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold"></textarea>
      </div>
    </div>

    <!-- Subraces Form -->
    <div v-if="contentType === 'subraces'" class="space-y-4">
      <h3 class="text-lg font-semibold text-text-primary">Create Subrace</h3>
      
      <!-- Basic Info -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label class="block text-sm font-medium text-text-primary mb-1">Name *</label>
          <input v-model="subrace.name" type="text" required placeholder="e.g., Hill Dwarf" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold" />
        </div>
        <div>
          <label class="block text-sm font-medium text-text-primary mb-1">Parent Race *</label>
          <input v-model="subrace.race" type="text" required placeholder="e.g., Dwarf" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold" />
        </div>
      </div>

      <!-- Description -->
      <div>
        <label class="block text-sm font-medium text-text-primary mb-1">Description *</label>
        <textarea v-model="subrace.desc" rows="4" required placeholder="Describe the subrace and its unique characteristics..." class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold"></textarea>
      </div>

      <!-- Ability Bonuses -->
      <div>
        <label class="block text-sm font-medium text-text-primary mb-1">Additional Ability Bonuses</label>
        <div class="grid grid-cols-3 md:grid-cols-6 gap-2">
          <div v-for="ability in ['STR', 'DEX', 'CON', 'INT', 'WIS', 'CHA']" :key="ability" class="text-center">
            <label class="block text-xs text-text-primary mb-1">{{ ability }}</label>
            <input v-model.number="subrace.ability_bonuses[ability]" type="number" min="0" max="2" class="w-full px-2 py-1 border border-gray-300 rounded text-center" />
          </div>
        </div>
      </div>

      <!-- Racial Traits -->
      <div>
        <label class="block text-sm font-medium text-text-primary mb-1">Additional Racial Traits</label>
        <textarea v-model="subrace.racial_traits" rows="4" placeholder="List additional traits this subrace gains (one per line)..." class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold"></textarea>
      </div>
    </div>

    <!-- Classes Form -->
    <div v-if="contentType === 'classes'" class="space-y-4">
      <h3 class="text-lg font-semibold text-text-primary">Create Class</h3>
      
      <!-- Basic Info -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label class="block text-sm font-medium text-text-primary mb-1">Name *</label>
          <input v-model="charClass.name" type="text" required placeholder="e.g., Artificer" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold" />
        </div>
        <div>
          <label class="block text-sm font-medium text-text-primary mb-1">Hit Die *</label>
          <select v-model.number="charClass.hit_die" required class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold">
            <option value="">Select hit die...</option>
            <option value="6">d6</option>
            <option value="8">d8</option>
            <option value="10">d10</option>
            <option value="12">d12</option>
          </select>
        </div>
      </div>

      <!-- Proficiencies -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label class="block text-sm font-medium text-text-primary mb-1">Proficiencies *</label>
          <textarea v-model="charClass.proficiencies" rows="3" required placeholder="List proficiencies (one per line)..." class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold"></textarea>
        </div>
        <div>
          <label class="block text-sm font-medium text-text-primary mb-1">Saving Throws *</label>
          <input v-model="charClass.saving_throws" type="text" required placeholder="e.g., Constitution, Intelligence" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold" />
        </div>
      </div>

      <!-- Starting Equipment -->
      <div>
        <label class="block text-sm font-medium text-text-primary mb-1">Starting Equipment</label>
        <textarea v-model="charClass.starting_equipment" rows="4" placeholder="List starting equipment and choices..." class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold"></textarea>
      </div>

      <!-- Class Features -->
      <div>
        <label class="block text-sm font-medium text-text-primary mb-1">Class Features by Level</label>
        <textarea v-model="charClass.class_levels" rows="8" placeholder="List class features by level (format: Level X: Feature Name - Description)..." class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold"></textarea>
      </div>

      <!-- Spellcasting -->
      <div class="flex items-center mb-4">
        <input v-model="charClass.is_spellcaster" type="checkbox" id="spellcaster" class="mr-2" />
        <label for="spellcaster" class="text-sm font-medium text-text-primary">Is Spellcaster</label>
      </div>

      <div v-if="charClass.is_spellcaster" class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label class="block text-sm font-medium text-text-primary mb-1">Spellcasting Ability</label>
          <select v-model="charClass.spellcasting_ability" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold">
            <option value="">Select ability...</option>
            <option value="INT">Intelligence</option>
            <option value="WIS">Wisdom</option>
            <option value="CHA">Charisma</option>
          </select>
        </div>
        <div>
          <label class="block text-sm font-medium text-text-primary mb-1">Spellcasting Level</label>
          <input v-model.number="charClass.spellcasting_level" type="number" min="1" max="20" placeholder="Level when spellcasting begins" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold" />
        </div>
      </div>
    </div>

    <!-- Submit Button -->
    <div class="flex justify-end">
      <button
        @click="generateJSON"
        :disabled="!isValid"
        class="fantasy-button px-6 py-2"
      >
        Generate JSON
      </button>
    </div>

    <!-- Generated JSON -->
    <div v-if="generatedJSON" class="mt-6">
      <h3 class="text-lg font-semibold text-text-primary mb-2">Generated JSON</h3>
      <div class="relative">
        <pre class="bg-gray-100 p-4 rounded-lg overflow-x-auto text-sm">{{ generatedJSON }}</pre>
        <button
          @click="copyJSON"
          class="absolute top-2 right-2 px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700"
        >
          {{ copied ? 'Copied!' : 'Copy' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

// Props
const props = defineProps<{
  contentType: string
}>()

// Convert content type to match our internal format
const contentTypeInternal = computed(() => {
  // Convert from frontend format (underscored) to match our checks
  return props.contentType.replace(/_/g, '-')
})

// Emits
const emit = defineEmits<{
  'json-generated': [json: string]
}>()

// Data models
const spell = ref({
  name: '',
  level: 1,
  school: '',
  casting_time: '',
  duration: '',
  range: '',
  components: [] as string[],
  material: '',
  ritual: false,
  concentration: false,
  desc: '',
  higher_level: '',
  classes: [] as string[]
})

const monster = ref({
  name: '',
  size: 'Medium',
  type: '',
  alignment: '',
  armor_class: 10,
  hit_points: 10,
  hit_dice: '',
  speed: '',
  strength: 10,
  dexterity: 10,
  constitution: 10,
  intelligence: 10,
  wisdom: 10,
  charisma: 10,
  challenge_rating: 1,
  languages: '',
  senses: '',
  actions: ''
})

const equipment = ref({
  name: '',
  equipment_category: '',
  cost_quantity: 0,
  cost_unit: 'gp',
  weight: 0,
  weapon_category: '',
  weapon_range: '',
  damage_dice: '',
  damage_type: '',
  desc: ''
})

const race = ref({
  name: '',
  speed: 30,
  size: 'Medium',
  alignment: '',
  age: '',
  size_description: '',
  languages: '',
  ability_bonuses: {
    STR: 0,
    DEX: 0,
    CON: 0,
    INT: 0,
    WIS: 0,
    CHA: 0
  }
})

const background = ref({
  name: '',
  feature_name: '',
  feature_desc: '',
  proficiencies: '',
  language_choices: 0
})

const feat = ref({
  name: '',
  prerequisites: '',
  desc: ''
})

const trait = ref({
  name: '',
  races: '',
  desc: ''
})

const skill = ref({
  name: '',
  ability_score: 'STR',
  desc: ''
})

const condition = ref({
  name: '',
  desc: ''
})

const alignment = ref({
  name: '',
  abbreviation: '',
  desc: ''
})

const damageType = ref({
  name: '',
  desc: ''
})

const weaponProperty = ref({
  name: '',
  desc: ''
})

const abilityScore = ref({
  name: '',
  full_name: '',
  desc: '',
  skills: ''
})

const language = ref({
  name: '',
  type: '',
  script: '',
  typical_speakers: ''
})

const proficiency = ref({
  name: '',
  type: '',
  classes: '',
  races: ''
})

const rule = ref({
  name: '',
  desc: '',
  subsections: ''
})

const equipmentCategory = ref({
  name: '',
  equipment: ''
})

const magicSchool = ref({
  name: '',
  desc: ''
})

const ruleSection = ref({
  name: '',
  desc: ''
})

const feature = ref({
  name: '',
  level: 1,
  class_ref: '',
  subclass: '',
  desc: ''
})

const level = ref({
  level: 1,
  ability_score_bonuses: 0,
  prof_bonus: 2,
  class_ref: '',
  subclass: '',
  features: ''
})

const magicItem = ref({
  name: '',
  rarity: '',
  type: '',
  requires_attunement: false,
  desc: ''
})

const subclass = ref({
  name: '',
  class_ref: '',
  desc: '',
  features: ''
})

const subrace = ref({
  name: '',
  race: '',
  desc: '',
  ability_bonuses: {
    STR: 0,
    DEX: 0,
    CON: 0,
    INT: 0,
    WIS: 0,
    CHA: 0
  },
  racial_traits: ''
})

const charClass = ref({
  name: '',
  hit_die: '',
  proficiencies: '',
  saving_throws: '',
  starting_equipment: '',
  class_levels: '',
  is_spellcaster: false,
  spellcasting_ability: '',
  spellcasting_level: 1
})

// Constants
const availableClasses = [
  'Barbarian', 'Bard', 'Cleric', 'Druid', 'Fighter', 'Monk',
  'Paladin', 'Ranger', 'Rogue', 'Sorcerer', 'Warlock', 'Wizard'
]

// State
const generatedJSON = ref('')
const copied = ref(false)

// Computed
const isValid = computed(() => {
  if (props.contentType === 'spells') {
    return spell.value.name && spell.value.school && spell.value.casting_time && 
           spell.value.duration && spell.value.range && spell.value.desc && 
           spell.value.components.length > 0
  } else if (props.contentType === 'monsters') {
    return monster.value.name && monster.value.type && monster.value.alignment &&
           monster.value.hit_dice && monster.value.speed
  } else if (props.contentType === 'equipment') {
    return equipment.value.name && equipment.value.equipment_category && 
           equipment.value.cost_quantity > 0
  } else if (props.contentType === 'races') {
    return race.value.name && race.value.age && race.value.size_description && 
           race.value.languages && race.value.alignment
  } else if (props.contentType === 'backgrounds') {
    return background.value.name && background.value.feature_name && 
           background.value.feature_desc
  } else if (props.contentType === 'feats') {
    return feat.value.name && feat.value.desc
  } else if (props.contentType === 'traits') {
    return trait.value.name && trait.value.races && trait.value.desc
  } else if (props.contentType === 'skills') {
    return skill.value.name && skill.value.ability_score && skill.value.desc
  } else if (props.contentType === 'conditions') {
    return condition.value.name && condition.value.desc
  } else if (props.contentType === 'alignments') {
    return alignment.value.name && alignment.value.abbreviation && alignment.value.desc
  } else if (props.contentType === 'damage-types') {
    return damageType.value.name && damageType.value.desc
  } else if (props.contentType === 'weapon-properties') {
    return weaponProperty.value.name && weaponProperty.value.desc
  } else if (props.contentType === 'ability-scores') {
    return abilityScore.value.name && abilityScore.value.full_name && abilityScore.value.desc
  } else if (props.contentType === 'languages') {
    return language.value.name && language.value.type
  } else if (props.contentType === 'proficiencies') {
    return proficiency.value.name && proficiency.value.type
  } else if (props.contentType === 'rules') {
    return rule.value.name && rule.value.desc
  } else if (props.contentType === 'equipment-categories') {
    return equipmentCategory.value.name
  } else if (props.contentType === 'magic-schools') {
    return magicSchool.value.name && magicSchool.value.desc
  } else if (props.contentType === 'rule-sections') {
    return ruleSection.value.name && ruleSection.value.desc
  } else if (props.contentType === 'features') {
    return feature.value.name && feature.value.level && feature.value.class_ref && feature.value.desc
  } else if (props.contentType === 'levels') {
    return level.value.level && level.value.prof_bonus && level.value.class_ref
  } else if (props.contentType === 'magic-items') {
    return magicItem.value.name && magicItem.value.rarity && magicItem.value.desc
  } else if (props.contentType === 'subclasses') {
    return subclass.value.name && subclass.value.class_ref && subclass.value.desc
  } else if (props.contentType === 'subraces') {
    return subrace.value.name && subrace.value.race && subrace.value.desc
  } else if (props.contentType === 'classes') {
    return charClass.value.name && charClass.value.hit_die && charClass.value.proficiencies && charClass.value.saving_throws
  }
  return false
})

// Methods
function generateJSON() {
  let data: any = {}
  
  if (props.contentType === 'spells') {
    const index = spell.value.name.toLowerCase().replace(/\s+/g, '-')
    data = {
      index: `custom-${index}`,
      name: spell.value.name,
      desc: [spell.value.desc],
      higher_level: spell.value.higher_level ? [spell.value.higher_level] : [],
      range: spell.value.range,
      components: spell.value.components,
      material: spell.value.material || undefined,
      ritual: spell.value.ritual,
      duration: spell.value.duration,
      concentration: spell.value.concentration,
      casting_time: spell.value.casting_time,
      level: spell.value.level,
      school: {
        index: spell.value.school,
        name: spell.value.school.charAt(0).toUpperCase() + spell.value.school.slice(1),
        url: `/api/magic-schools/${spell.value.school}`
      },
      classes: spell.value.classes.map(cls => ({
        index: cls.toLowerCase(),
        name: cls,
        url: `/api/classes/${cls.toLowerCase()}`
      })),
      url: `/api/spells/${index}`
    }
  } else if (contentTypeInternal.value === 'monsters') {
    const index = monster.value.name.toLowerCase().replace(/\s+/g, '-')
    const hitPointsRoll = `${monster.value.hit_dice}${monster.value.constitution > 10 ? '+' + Math.floor((monster.value.constitution - 10) / 2) * parseInt(monster.value.hit_dice) : ''}`
    
    // Parse speed
    const speedObj: any = {}
    const speedParts = monster.value.speed.split(',').map(s => s.trim())
    speedParts.forEach(part => {
      const match = part.match(/(\w+)?\s*(\d+)\s*ft\.?/)
      if (match) {
        const type = match[1] ? match[1].toLowerCase() : 'walk'
        speedObj[type] = `${match[2]} ft.`
      }
    })
    
    // Parse senses
    const sensesObj: any = {}
    if (monster.value.senses) {
      const sensesParts = monster.value.senses.split(',').map(s => s.trim())
      sensesParts.forEach(part => {
        const match = part.match(/(\w+\s*\w*)\s+(\d+)\s*ft\.?/)
        if (match) {
          sensesObj[match[1].replace(/\s+/g, '_')] = `${match[2]} ft.`
        } else if (part.includes('passive Perception')) {
          const ppMatch = part.match(/passive Perception (\d+)/)
          if (ppMatch) {
            sensesObj.passive_perception = parseInt(ppMatch[1])
          }
        }
      })
    }
    
    // Calculate proficiency bonus based on CR
    const proficiencyBonus = Math.floor((monster.value.challenge_rating - 1) / 4) + 2
    
    // Calculate XP based on CR
    const crToXP: Record<number, number> = {
      0: 10, 0.125: 25, 0.25: 50, 0.5: 100,
      1: 200, 2: 450, 3: 700, 4: 1100,
      5: 1800, 6: 2300, 7: 2900, 8: 3900,
      9: 5000, 10: 5900, 11: 7200, 12: 8400,
      13: 10000, 14: 11500, 15: 13000, 16: 15000,
      17: 18000, 18: 20000, 19: 22000, 20: 25000
    }
    
    data = {
      index: `custom-${index}`,
      name: monster.value.name,
      size: monster.value.size,
      type: monster.value.type.toLowerCase(),
      alignment: monster.value.alignment,
      armor_class: [{
        type: "natural",
        value: monster.value.armor_class
      }],
      hit_points: monster.value.hit_points,
      hit_dice: monster.value.hit_dice,
      hit_points_roll: hitPointsRoll,
      speed: speedObj,
      strength: monster.value.strength,
      dexterity: monster.value.dexterity,
      constitution: monster.value.constitution,
      intelligence: monster.value.intelligence,
      wisdom: monster.value.wisdom,
      charisma: monster.value.charisma,
      proficiencies: [],
      damage_vulnerabilities: [],
      damage_resistances: [],
      damage_immunities: [],
      condition_immunities: [],
      senses: sensesObj,
      languages: monster.value.languages || "—",
      challenge_rating: monster.value.challenge_rating,
      proficiency_bonus: proficiencyBonus,
      xp: crToXP[monster.value.challenge_rating] || 0,
      actions: parseActions(monster.value.actions),
      url: `/api/monsters/${index}`
    }
  } else if (contentTypeInternal.value === 'equipment') {
    const index = equipment.value.name.toLowerCase().replace(/\s+/g, '-')
    data = {
      index: `custom-${index}`,
      name: equipment.value.name,
      equipment_category: {
        index: equipment.value.equipment_category.toLowerCase().replace(/\s+/g, '-'),
        name: equipment.value.equipment_category,
        url: `/api/equipment-categories/${equipment.value.equipment_category.toLowerCase().replace(/\s+/g, '-')}`
      },
      cost: {
        quantity: equipment.value.cost_quantity,
        unit: equipment.value.cost_unit
      },
      weight: equipment.value.weight || undefined,
      desc: equipment.value.desc ? [equipment.value.desc] : undefined,
      url: `/api/equipment/${index}`
    }
    
    if (equipment.value.equipment_category === 'Weapon') {
      data.weapon_category = equipment.value.weapon_category
      data.weapon_range = equipment.value.weapon_range
      data.category_range = `${equipment.value.weapon_category} ${equipment.value.weapon_range}`
      data.damage = {
        damage_dice: equipment.value.damage_dice,
        damage_type: {
          index: equipment.value.damage_type.toLowerCase(),
          name: equipment.value.damage_type,
          url: `/api/damage-types/${equipment.value.damage_type.toLowerCase()}`
        }
      }
      data.range = equipment.value.weapon_range === 'Melee' ? { normal: 5 } : { normal: 80, long: 320 }
    }
  } else if (props.contentType === 'races') {
    const index = race.value.name.toLowerCase().replace(/\s+/g, '-')
    
    // Build ability bonuses array
    const abilityBonuses: any[] = []
    Object.entries(race.value.ability_bonuses).forEach(([ability, bonus]) => {
      if (bonus !== 0) {
        abilityBonuses.push({
          ability_score: ability,
          bonus: bonus
        })
      }
    })
    
    data = {
      index: `custom-${index}`,
      name: race.value.name,
      speed: race.value.speed,
      ability_bonuses: abilityBonuses,
      alignment: race.value.alignment,
      age: race.value.age,
      size: race.value.size,
      size_description: race.value.size_description,
      starting_proficiencies: [],
      languages: race.value.languages.split(',').map(lang => lang.trim()),
      language_desc: `You can speak, read, and write ${race.value.languages}.`,
      traits: [],
      subraces: [],
      url: `/api/races/${index}`
    }
  } else if (props.contentType === 'backgrounds') {
    const index = background.value.name.toLowerCase().replace(/\s+/g, '-')
    
    // Parse proficiencies
    const proficiencies = background.value.proficiencies 
      ? background.value.proficiencies.split(',').map(prof => prof.trim())
      : []
    
    data = {
      index: `custom-${index}`,
      name: background.value.name,
      starting_proficiencies: proficiencies,
      language_options: background.value.language_choices > 0 ? {
        choose: background.value.language_choices,
        type: "languages",
        from: { options: [] }
      } : undefined,
      starting_equipment: [],
      starting_equipment_options: [],
      feature: {
        name: background.value.feature_name,
        desc: [background.value.feature_desc]
      },
      personality_traits: {
        choose: 2,
        type: "personality_traits",
        from: { options: [] }
      },
      ideals: {
        choose: 1,
        type: "ideals",
        from: { options: [] }
      },
      bonds: {
        choose: 1,
        type: "bonds",
        from: { options: [] }
      },
      flaws: {
        choose: 1,
        type: "flaws",
        from: { options: [] }
      },
      url: `/api/backgrounds/${index}`
    }
  } else if (props.contentType === 'feats') {
    const index = feat.value.name.toLowerCase().replace(/\s+/g, '-')
    
    data = {
      index: `custom-${index}`,
      name: feat.value.name,
      prerequisites: feat.value.prerequisites ? [feat.value.prerequisites] : [],
      desc: feat.value.desc.split('\n').filter(line => line.trim()),
      url: `/api/feats/${index}`
    }
  } else if (props.contentType === 'traits') {
    const index = trait.value.name.toLowerCase().replace(/\s+/g, '-')
    
    data = {
      index: `custom-${index}`,
      name: trait.value.name,
      races: trait.value.races.split(',').map(r => r.trim()),
      subraces: [],
      desc: [trait.value.desc],
      proficiencies: [],
      url: `/api/traits/${index}`
    }
  } else if (props.contentType === 'skills') {
    const index = skill.value.name.toLowerCase().replace(/\s+/g, '-')
    
    data = {
      index: `custom-${index}`,
      name: skill.value.name,
      desc: [skill.value.desc],
      ability_score: skill.value.ability_score,
      url: `/api/skills/${index}`
    }
  } else if (props.contentType === 'conditions') {
    const index = condition.value.name.toLowerCase().replace(/\s+/g, '-')
    
    data = {
      index: `custom-${index}`,
      name: condition.value.name,
      desc: condition.value.desc.split('\n').filter(line => line.trim()),
      url: `/api/conditions/${index}`
    }
  } else if (props.contentType === 'alignments') {
    const index = alignment.value.name.toLowerCase().replace(/\s+/g, '-')
    
    data = {
      index: `custom-${index}`,
      name: alignment.value.name,
      abbreviation: alignment.value.abbreviation,
      desc: alignment.value.desc,
      url: `/api/alignments/${index}`
    }
  } else if (props.contentType === 'damage-types') {
    const index = damageType.value.name.toLowerCase().replace(/\s+/g, '-')
    
    data = {
      index: `custom-${index}`,
      name: damageType.value.name,
      desc: damageType.value.desc.split('\n').filter(line => line.trim()),
      url: `/api/damage-types/${index}`
    }
  } else if (props.contentType === 'weapon-properties') {
    const index = weaponProperty.value.name.toLowerCase().replace(/\s+/g, '-')
    
    data = {
      index: `custom-${index}`,
      name: weaponProperty.value.name,
      desc: weaponProperty.value.desc.split('\n').filter(line => line.trim()),
      url: `/api/weapon-properties/${index}`
    }
  } else if (props.contentType === 'ability-scores') {
    const index = abilityScore.value.name.toLowerCase().replace(/\s+/g, '-')
    
    data = {
      index: `custom-${index}`,
      name: abilityScore.value.name,
      full_name: abilityScore.value.full_name,
      desc: abilityScore.value.desc.split('\n').filter(line => line.trim()),
      skills: abilityScore.value.skills ? abilityScore.value.skills.split(',').map(s => ({
        index: s.trim().toLowerCase().replace(/\s+/g, '-'),
        name: s.trim(),
        url: `/api/skills/${s.trim().toLowerCase().replace(/\s+/g, '-')}`
      })) : [],
      url: `/api/ability-scores/${index}`
    }
  } else if (props.contentType === 'languages') {
    const index = language.value.name.toLowerCase().replace(/\s+/g, '-')
    
    data = {
      index: `custom-${index}`,
      name: language.value.name,
      type: language.value.type,
      script: language.value.script || undefined,
      typical_speakers: language.value.typical_speakers ? 
        language.value.typical_speakers.split(',').map(s => s.trim()) : [],
      url: `/api/languages/${index}`
    }
  } else if (props.contentType === 'proficiencies') {
    const index = proficiency.value.name.toLowerCase().replace(/\s+/g, '-')
    
    data = {
      index: `custom-${index}`,
      name: proficiency.value.name,
      type: proficiency.value.type,
      classes: proficiency.value.classes ? proficiency.value.classes.split(',').map(c => ({
        index: c.trim().toLowerCase(),
        name: c.trim(),
        url: `/api/classes/${c.trim().toLowerCase()}`
      })) : [],
      races: proficiency.value.races ? proficiency.value.races.split(',').map(r => ({
        index: r.trim().toLowerCase().replace(/\s+/g, '-'),
        name: r.trim(),
        url: `/api/races/${r.trim().toLowerCase().replace(/\s+/g, '-')}`
      })) : [],
      url: `/api/proficiencies/${index}`
    }
  } else if (props.contentType === 'rules') {
    const index = rule.value.name.toLowerCase().replace(/\s+/g, '-')
    
    data = {
      index: `custom-${index}`,
      name: rule.value.name,
      desc: rule.value.desc,
      subsections: rule.value.subsections ? rule.value.subsections.split(',').map(s => ({
        index: s.trim().toLowerCase().replace(/\s+/g, '-'),
        name: s.trim(),
        url: `/api/rule-sections/${s.trim().toLowerCase().replace(/\s+/g, '-')}`
      })) : [],
      url: `/api/rules/${index}`
    }
  } else if (props.contentType === 'equipment-categories') {
    const index = equipmentCategory.value.name.toLowerCase().replace(/\s+/g, '-')
    
    data = {
      index: `custom-${index}`,
      name: equipmentCategory.value.name,
      equipment: equipmentCategory.value.equipment ? 
        equipmentCategory.value.equipment.split('\n').filter(line => line.trim()).map(item => ({
          index: item.trim().toLowerCase().replace(/\s+/g, '-'),
          name: item.trim(),
          url: `/api/equipment/${item.trim().toLowerCase().replace(/\s+/g, '-')}`
        })) : [],
      url: `/api/equipment-categories/${index}`
    }
  } else if (props.contentType === 'magic-schools') {
    const index = magicSchool.value.name.toLowerCase().replace(/\s+/g, '-')
    
    data = {
      index: `custom-${index}`,
      name: magicSchool.value.name,
      desc: magicSchool.value.desc,
      url: `/api/magic-schools/${index}`
    }
  } else if (props.contentType === 'rule-sections') {
    const index = ruleSection.value.name.toLowerCase().replace(/\s+/g, '-')
    
    data = {
      index: `custom-${index}`,
      name: ruleSection.value.name,
      desc: ruleSection.value.desc,
      url: `/api/rule-sections/${index}`
    }
  } else if (props.contentType === 'features') {
    const index = feature.value.name.toLowerCase().replace(/\s+/g, '-')
    
    data = {
      index: `custom-${index}`,
      name: feature.value.name,
      level: feature.value.level,
      class: {
        index: feature.value.class_ref.toLowerCase(),
        name: feature.value.class_ref,
        url: `/api/classes/${feature.value.class_ref.toLowerCase()}`
      },
      subclass: feature.value.subclass ? {
        index: feature.value.subclass.toLowerCase().replace(/\s+/g, '-'),
        name: feature.value.subclass,
        url: `/api/subclasses/${feature.value.subclass.toLowerCase().replace(/\s+/g, '-')}`
      } : undefined,
      desc: feature.value.desc.split('\n').filter(line => line.trim()),
      url: `/api/features/${index}`
    }
  } else if (props.contentType === 'levels') {
    const index = `${level.value.class_ref.toLowerCase()}-${level.value.level}`
    
    data = {
      level: level.value.level,
      ability_score_bonuses: level.value.ability_score_bonuses,
      prof_bonus: level.value.prof_bonus,
      features: level.value.features ? level.value.features.split('\n').filter(line => line.trim()).map(feat => ({
        index: feat.trim().toLowerCase().replace(/\s+/g, '-'),
        name: feat.trim(),
        url: `/api/features/${feat.trim().toLowerCase().replace(/\s+/g, '-')}`
      })) : [],
      class: {
        index: level.value.class_ref.toLowerCase(),
        name: level.value.class_ref,
        url: `/api/classes/${level.value.class_ref.toLowerCase()}`
      },
      subclass: level.value.subclass ? {
        index: level.value.subclass.toLowerCase().replace(/\s+/g, '-'),
        name: level.value.subclass,
        url: `/api/subclasses/${level.value.subclass.toLowerCase().replace(/\s+/g, '-')}`
      } : undefined,
      class_specific: {},
      url: `/api/levels/${index}`
    }
  } else if (props.contentType === 'magic-items') {
    const index = magicItem.value.name.toLowerCase().replace(/\s+/g, '-')
    
    data = {
      index: `custom-${index}`,
      name: magicItem.value.name,
      equipment_category: {
        index: "wondrous-items",
        name: "Wondrous Items",
        url: "/api/equipment-categories/wondrous-items"
      },
      rarity: {
        name: magicItem.value.rarity
      },
      variants: [],
      variant: false,
      desc: magicItem.value.desc.split('\n').filter(line => line.trim()),
      special: [],
      url: `/api/magic-items/${index}`
    }
    
    // Add type if specified
    if (magicItem.value.type) {
      data.equipment_category = {
        index: magicItem.value.type.toLowerCase().replace(/\s+/g, '-'),
        name: magicItem.value.type,
        url: `/api/equipment-categories/${magicItem.value.type.toLowerCase().replace(/\s+/g, '-')}`
      }
    }
    
    // Add attunement requirement if specified
    if (magicItem.value.requires_attunement) {
      data.special = ["Requires Attunement"]
    }
  } else if (props.contentType === 'subclasses') {
    const index = subclass.value.name.toLowerCase().replace(/\s+/g, '-')
    
    data = {
      index: `custom-${index}`,
      name: subclass.value.name,
      class: {
        index: subclass.value.class_ref.toLowerCase(),
        name: subclass.value.class_ref,
        url: `/api/classes/${subclass.value.class_ref.toLowerCase()}`
      },
      desc: subclass.value.desc.split('\n').filter(line => line.trim()),
      subclass_flavor: subclass.value.desc.split('\n')[0] || subclass.value.name,
      subclass_levels: subclass.value.features ? 
        subclass.value.features.split('\n').filter(line => line.trim()).map((feat, idx) => ({
          level: idx + 3, // Start at level 3 typically
          features: [{
            name: feat.split(':')[0]?.trim() || feat,
            desc: feat.split(':')[1]?.trim() || feat
          }]
        })) : [],
      url: `/api/subclasses/${index}`
    }
  } else if (props.contentType === 'subraces') {
    const index = subrace.value.name.toLowerCase().replace(/\s+/g, '-')
    
    // Build ability bonuses array
    const abilityBonuses = []
    for (const [ability, bonus] of Object.entries(subrace.value.ability_bonuses)) {
      if (bonus > 0) {
        abilityBonuses.push({
          ability_score: {
            index: ability.toLowerCase(),
            name: ability,
            url: `/api/ability-scores/${ability.toLowerCase()}`
          },
          bonus: bonus
        })
      }
    }
    
    data = {
      index: `custom-${index}`,
      name: subrace.value.name,
      race: {
        index: subrace.value.race.toLowerCase().replace(/\s+/g, '-'),
        name: subrace.value.race,
        url: `/api/races/${subrace.value.race.toLowerCase().replace(/\s+/g, '-')}`
      },
      desc: subrace.value.desc,
      ability_bonuses: abilityBonuses,
      starting_proficiencies: [],
      languages: [],
      racial_traits: subrace.value.racial_traits ? 
        subrace.value.racial_traits.split('\n').filter(line => line.trim()).map(trait => ({
          name: trait.split(':')[0]?.trim() || trait,
          desc: trait.split(':')[1]?.trim() || trait
        })) : [],
      url: `/api/subraces/${index}`
    }
  } else if (props.contentType === 'classes') {
    const index = charClass.value.name.toLowerCase().replace(/\s+/g, '-')
    
    data = {
      index: `custom-${index}`,
      name: charClass.value.name,
      hit_die: charClass.value.hit_die,
      proficiencies: charClass.value.proficiencies ? 
        charClass.value.proficiencies.split('\n').filter(line => line.trim()).map(prof => ({
          index: prof.trim().toLowerCase().replace(/\s+/g, '-'),
          name: prof.trim(),
          url: `/api/proficiencies/${prof.trim().toLowerCase().replace(/\s+/g, '-')}`
        })) : [],
      proficiency_choices: [],
      saving_throws: charClass.value.saving_throws ? 
        charClass.value.saving_throws.split(',').map(save => ({
          index: save.trim().toLowerCase().slice(0, 3),
          name: save.trim(),
          url: `/api/ability-scores/${save.trim().toLowerCase().slice(0, 3)}`
        })) : [],
      starting_equipment: charClass.value.starting_equipment ? 
        charClass.value.starting_equipment.split('\n').filter(line => line.trim()).map(equip => ({
          equipment: {
            index: equip.trim().toLowerCase().replace(/\s+/g, '-'),
            name: equip.trim(),
            url: `/api/equipment/${equip.trim().toLowerCase().replace(/\s+/g, '-')}`
          },
          quantity: 1
        })) : [],
      starting_equipment_options: [],
      class_levels: charClass.value.class_levels ? 
        charClass.value.class_levels.split('\n').filter(line => line.trim()).map((levelText, idx) => ({
          level: idx + 1,
          ability_score_bonuses: idx % 4 === 3 ? 1 : 0, // Every 4th level
          prof_bonus: Math.floor((idx + 7) / 4), // +2 at 1-4, +3 at 5-8, etc.
          features: [{
            name: levelText.split(':')[0]?.trim() || levelText,
            desc: levelText.split(':')[1]?.trim() || levelText
          }],
          class_specific: {}
        })) : [],
      multi_classing: {
        prerequisites: [],
        proficiencies: []
      },
      subclasses: [],
      url: `/api/classes/${index}`
    }
    
    // Add spellcasting if applicable
    if (charClass.value.is_spellcaster && charClass.value.spellcasting_ability) {
      data.spellcasting = {
        level: charClass.value.spellcasting_level || 1,
        spellcasting_ability: {
          index: charClass.value.spellcasting_ability.toLowerCase(),
          name: charClass.value.spellcasting_ability,
          url: `/api/ability-scores/${charClass.value.spellcasting_ability.toLowerCase()}`
        },
        info: [{
          name: "Spells Known",
          desc: ["You know a number of spells based on your level in this class."]
        }]
      }
    }
  }
  
  // Clean up undefined values
  Object.keys(data).forEach(key => {
    if (data[key] === undefined) {
      delete data[key]
    }
  })
  
  generatedJSON.value = JSON.stringify([data], null, 2)
  
  // Emit the generated JSON
  emit('json-generated', generatedJSON.value)
}

function parseActions(actionsText: string): any[] {
  if (!actionsText) return []
  
  const actions: any[] = []
  const actionBlocks = actionsText.split('\n\n').filter(block => block.trim())
  
  actionBlocks.forEach(block => {
    const lines = block.trim().split('. ')
    if (lines.length > 0) {
      const namePart = lines[0]
      const desc = block
      
      actions.push({
        name: namePart,
        desc: desc
      })
    }
  })
  
  return actions
}

function copyJSON() {
  navigator.clipboard.writeText(generatedJSON.value)
  copied.value = true
  setTimeout(() => {
    copied.value = false
  }, 2000)
}
</script>