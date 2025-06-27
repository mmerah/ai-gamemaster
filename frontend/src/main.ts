import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router'
import './styles/main.css'
import App from './App.vue'

// Import only the main launch screen eagerly, lazy load the rest
import LaunchScreen from './views/LaunchScreen.vue'

// Import stores for initialization
import { useCampaignStore } from './stores/campaignStore'
import { useChatStore } from './stores/chatStore'

// Define routes with lazy loading for better performance
const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'launch',
    component: LaunchScreen,
  },
  {
    path: '/game',
    name: 'game',
    component: () => import('./views/GameView.vue'),
  },
  {
    path: '/campaigns',
    name: 'campaign-manager',
    component: () => import('./views/CampaignManagerView.vue'),
  },
  {
    path: '/characters',
    name: 'characters-manager',
    component: () => import('./views/CharactersManagerScreen.vue'),
  },
  {
    path: '/configuration',
    name: 'configuration',
    component: () => import('./views/ConfigurationScreen.vue'),
  },
  {
    path: '/content',
    name: 'content-manager',
    component: () => import('./views/ContentManagerView.vue'),
  },
  {
    path: '/content/:packId',
    name: 'content-pack-detail',
    component: () => import('./views/ContentPackDetailView.vue'),
  },
]

// Create router
const router = createRouter({
  history: createWebHistory(),
  routes,
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
      campaignStore.loadD5eClasses(),
    ])

    // REMOVED: Auto-load last played campaign logic from here.
    // GameView.vue will handle its own game state loading.
  } catch (error) {
    console.error('Failed to initialize app data:', error)
  }
})

// Mount app
app.mount('#app')
