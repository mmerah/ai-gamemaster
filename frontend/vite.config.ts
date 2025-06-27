import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [
    vue({
      script: {
        defineModel: true,
        propsDestructure: true
      }
    })
  ],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
      '@/types': resolve(__dirname, 'src/types/index'),
      '@/components': resolve(__dirname, 'src/components'),
      '@/stores': resolve(__dirname, 'src/stores'),
      '@/services': resolve(__dirname, 'src/services'),
      '@/utils': resolve(__dirname, 'src/utils')
    }
  },
  esbuild: {
    target: 'es2020',
    logOverride: { 'this-is-undefined-in-esm': 'silent' }
  },
  build: {
    outDir: '../static/dist',
    emptyOutDir: true,
    chunkSizeWarningLimit: 1000, // Increase warning limit to 1MB for rich applications
    rollupOptions: {
      input: {
        main: resolve(__dirname, 'index.html')
      },
      output: {
        manualChunks: {
          // Vendor libraries
          'vendor-vue': ['vue', 'vue-router', 'pinia'],
          'vendor-ui': ['axios'],
          
          // Large components that can be lazy loaded
          'content-management': [
            './src/views/ContentManagerView.vue',
            './src/views/ContentPackDetailView.vue',
            './src/components/content/RAGTester.vue'
          ],
          'campaign-templates': [
            './src/components/campaign/CampaignTemplateModal.vue'
          ],
          'character-creation': [
            './src/components/campaign/CharacterCreationWizard.vue'
          ]
        }
      }
    }
  },
  base: './',
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true
      }
    }
  }
})
