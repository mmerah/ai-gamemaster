<template>
  <div class="launch-screen min-h-screen bg-parchment">
    <!-- Header -->
    <div class="bg-primary-dark shadow-xl">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <h1 class="text-3xl font-cinzel font-bold text-gold text-center">
          AI Game Master
        </h1>
        <p class="text-center text-text-secondary mt-2 font-crimson">
          Your intelligent companion for tabletop adventures
        </p>
      </div>
    </div>

    <!-- Main Content -->
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
        <!-- Campaigns Card -->
        <div class="fantasy-card hover:shadow-xl transition-shadow cursor-pointer" @click="navigateTo('campaigns')">
          <div class="p-8 text-center">
            <div class="mb-4">
              <svg class="w-16 h-16 mx-auto text-gold" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
              </svg>
            </div>
            <h2 class="text-2xl font-cinzel font-semibold text-text-primary mb-3">
              Campaigns
            </h2>
            <p class="text-text-secondary font-crimson">
              Create, manage, and continue your epic adventures
            </p>
            <div class="mt-6">
              <span class="text-sm text-gold font-semibold">
                {{ campaignCount }} Active Campaigns
              </span>
            </div>
          </div>
        </div>

        <!-- Characters Card -->
        <div class="fantasy-card hover:shadow-xl transition-shadow cursor-pointer" @click="navigateTo('characters')">
          <div class="p-8 text-center">
            <div class="mb-4">
              <svg class="w-16 h-16 mx-auto text-gold" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"></path>
              </svg>
            </div>
            <h2 class="text-2xl font-cinzel font-semibold text-text-primary mb-3">
              Characters
            </h2>
            <p class="text-text-secondary font-crimson">
              Design heroes and track their journeys across campaigns
            </p>
            <div class="mt-6">
              <span class="text-sm text-gold font-semibold">
                {{ characterCount }} Character Templates
              </span>
            </div>
          </div>
        </div>

        <!-- Configuration Card -->
        <div class="fantasy-card hover:shadow-xl transition-shadow cursor-pointer" @click="navigateTo('configuration')">
          <div class="p-8 text-center">
            <div class="mb-4">
              <svg class="w-16 h-16 mx-auto text-gold" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"></path>
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
              </svg>
            </div>
            <h2 class="text-2xl font-cinzel font-semibold text-text-primary mb-3">
              Configuration
            </h2>
            <p class="text-text-secondary font-crimson">
              View AI settings, storage options, and system preferences
            </p>
            <div class="mt-6">
              <span class="text-sm text-gold font-semibold">
                System Settings
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Quick Actions -->
      <div class="mt-12 text-center">
        <h3 class="text-xl font-cinzel font-semibold text-text-primary mb-6">
          Quick Actions
        </h3>
        <div class="flex flex-wrap justify-center gap-4">
          <button
            v-if="lastPlayedCampaign"
            @click="continueLastCampaign"
            class="fantasy-button px-6 py-3"
          >
            <svg class="w-5 h-5 inline mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"></path>
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
            </svg>
            Continue: {{ lastPlayedCampaign.name }}
          </button>
          <button
            @click="navigateTo('campaigns', 'new')"
            class="fantasy-button-secondary px-6 py-3"
          >
            <svg class="w-5 h-5 inline mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path>
            </svg>
            New Campaign
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useCampaignStore } from '../stores/campaignStore'
import { campaignApi } from '../services/campaignApi'

const router = useRouter()
const campaignStore = useCampaignStore()

// Character templates state
const characterTemplates = ref([])

// Computed properties
const campaignCount = computed(() => campaignStore.campaigns.length)
const characterCount = computed(() => characterTemplates.value.length)
const lastPlayedCampaign = computed(() => {
  // Get the most recently played campaign (or created if never played)
  const campaigns = [...campaignStore.campaigns]
  return campaigns.sort((a, b) => {
    const dateA = new Date(a.last_played || a.created_date)
    const dateB = new Date(b.last_played || b.created_date)
    return dateB - dateA
  })[0] || null
})

// Load character templates
async function loadCharacterTemplates() {
  try {
    const response = await campaignApi.getTemplates()
    characterTemplates.value = response.data.templates || []
  } catch (error) {
    console.error('Failed to load character templates:', error)
    characterTemplates.value = []
  }
}

// Load data on mount
onMounted(async () => {
  try {
    await Promise.all([
      campaignStore.loadCampaigns(),
      loadCharacterTemplates()
    ])
  } catch (error) {
    console.error('Failed to load launch screen data:', error)
  }
})

// Navigation methods
function navigateTo(section, action = null) {
  switch (section) {
    case 'campaigns':
      router.push({ name: 'campaign-manager', query: action ? { action } : {} })
      break
    case 'characters':
      router.push({ name: 'characters-manager' })
      break
    case 'configuration':
      router.push({ name: 'configuration' })
      break
  }
}

function continueLastCampaign() {
  if (lastPlayedCampaign.value) {
    campaignStore.startCampaign(lastPlayedCampaign.value.id)
  }
}
</script>

<style scoped>
.launch-screen {
  min-height: 100vh;
}
</style>
