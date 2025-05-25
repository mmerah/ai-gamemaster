<script setup>
import { onMounted, inject } from 'vue'

// Get the initialization function from main.js
const initializeApp = inject('initializeApp')

onMounted(async () => {
  if (initializeApp) {
    await initializeApp()
  }
})
</script>

<template>
  <div id="app" class="min-h-screen bg-parchment">
    <!-- Navigation -->
    <nav class="bg-primary-dark shadow-lg">
      <div class="max-w-7xl mx-auto px-4">
        <div class="flex justify-between h-16">
          <div class="flex items-center">
            <router-link 
              to="/" 
              class="text-gold font-cinzel text-xl font-bold hover:text-gold-light transition-colors"
            >
              AI Game Master
            </router-link>
          </div>
          <div class="flex items-center space-x-4">
            <router-link 
              to="/" 
              class="text-parchment hover:text-gold transition-colors px-3 py-2 rounded-md text-sm font-medium"
              :class="{ 'bg-primary text-gold': $route.name === 'game' }"
            >
              Game
            </router-link>
            <router-link 
              to="/campaign-manager" 
              class="text-parchment hover:text-gold transition-colors px-3 py-2 rounded-md text-sm font-medium"
              :class="{ 'bg-primary text-gold': $route.name === 'campaign-manager' }"
            >
              Campaign Manager
            </router-link>
          </div>
        </div>
      </div>
    </nav>

    <!-- Main content -->
    <main class="flex-1">
      <router-view />
    </main>
  </div>
</template>

<style scoped>
/* Component-specific styles can go here */
</style>
