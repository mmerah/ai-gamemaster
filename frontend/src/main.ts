import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router'
import './styles/main.css'
import App from './App.vue'

// Import views
import LaunchScreen from './views/LaunchScreen.vue'
import GameView from './views/GameView.vue'
import CampaignManagerView from './views/CampaignManagerView.vue'
import CharactersManagerScreen from './views/CharactersManagerScreen.vue'
import ConfigurationScreen from './views/ConfigurationScreen.vue'

// Import stores for initialization
import { useCampaignStore } from './stores/campaignStore'
import { useChatStore } from './stores/chatStore'

// Define routes with proper typing
const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'launch',
    component: LaunchScreen
  },
  {
    path: '/game',
    name: 'game',
    component: GameView
  },
  {
    path: '/campaigns',
    name: 'campaign-manager',
    component: CampaignManagerView
  },
  {
    path: '/characters',
    name: 'characters-manager',
    component: CharactersManagerScreen
  },
  {
    path: '/configuration',
    name: 'configuration',
    component: ConfigurationScreen
  }
]

// Create router
const router = createRouter({
  history: createWebHistory(),
  routes
})

// Create pinia
const pinia = createPinia()

// Create app
const app = createApp(App)

// Use plugins
app.use(pinia)
app.use(router)

// Initialize app data after stores are available
app.provide('initializeApp', async () => {
  try {
    const campaignStore = useCampaignStore()
    const chatStore = useChatStore()

    // Initialize the chat store and SSE connection
    chatStore.initialize()

    // Load all essential data for campaign manager and template creation
    await Promise.all([
      campaignStore.loadCampaigns(),
      campaignStore.loadTemplates(),
      campaignStore.loadD5eRaces(),
      campaignStore.loadD5eClasses()
    ])

    // REMOVED: Auto-load last played campaign logic from here.
    // GameView.vue will handle its own game state loading.

  } catch (error) {
    console.error('Failed to initialize app data:', error)
  }
})

// Mount app
app.mount('#app')
