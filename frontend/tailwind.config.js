/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./campaigns.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Fantasy theme colors adapted from current CSS
        parchment: '#f4f1e8',
        'parchment-dark': '#e8e0d0',
        gold: '#d4af37',
        'gold-light': '#f0d55a',
        'gold-dark': '#b8941f',
        crimson: '#dc2626',
        'crimson-light': '#ef4444',
        'crimson-dark': '#b91c1c',
        'royal-blue': '#2563eb',
        'royal-blue-light': '#3b82f6',
        'royal-blue-dark': '#1d4ed8',
        'forest-light': '#16a34a',
        'forest-dark': '#15803d',
        primary: '#2563eb',
        'primary-dark': '#1e40af',
        secondary: '#64748b',
        'secondary-light': '#94a3b8',
        'secondary-dark': '#334155',
        accent: '#f59e0b',
        'text-primary': '#1f2937',
        'text-secondary': '#6b7280',
        'fantasy-brown': '#8b4513',
        'fantasy-brown-dark': '#654321',
      },
      fontFamily: {
        'fantasy': ['Cinzel', 'serif'],
        'body': ['Crimson Text', 'serif'],
        'cinzel': ['Cinzel', 'serif'],
      },
      backgroundImage: {
        'parchment': "url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHZpZXdCb3g9IjAgMCA0MCA0MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZGVmcz48cGF0dGVybiBpZD0iZ3JpZCIgd2lkdGg9IjQwIiBoZWlnaHQ9IjQwIiBwYXR0ZXJuVW5pdHM9InVzZXJTcGFjZU9uVXNlIj48cGF0aCBkPSJNIDQwIDAgTCAwIDAgMCA0MCIgZmlsbD0ibm9uZSIgc3Ryb2tlPSIjZjRmMWU4IiBzdHJva2Utd2lkdGg9IjEiLz48L3BhdHRlcm4+PC9kZWZzPjxyZWN0IHdpZHRoPSIxMDAlIiBoZWlnaHQ9IjEwMCUiIGZpbGw9InVybCgjZ3JpZCkiLz48L3N2Zz4=')",
      }
    },
  },
  plugins: [],
}
