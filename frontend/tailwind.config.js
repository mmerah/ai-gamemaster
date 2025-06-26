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
        // Theme colors using CSS variables for light/dark mode support
        background: 'rgb(var(--color-background) / <alpha-value>)',
        foreground: 'rgb(var(--color-foreground) / <alpha-value>)',
        primary: {
          DEFAULT: 'rgb(var(--color-primary) / <alpha-value>)',
          foreground: 'rgb(var(--color-primary-foreground) / <alpha-value>)',
        },
        accent: {
          DEFAULT: 'rgb(var(--color-accent) / <alpha-value>)',
          foreground: 'rgb(var(--color-accent-foreground) / <alpha-value>)',
        },
        card: 'rgb(var(--color-card) / <alpha-value>)',
        border: 'rgb(var(--color-border) / <alpha-value>)',
        
        // Legacy colors kept for backward compatibility
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
        'primary-dark': '#1e40af',
        secondary: '#64748b',
        'secondary-light': '#94a3b8',
        'secondary-dark': '#334155',
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
      borderRadius: {
        lg: '0.75rem',
        md: '0.5rem',
        sm: '0.25rem',
      },
      backgroundImage: {
        'parchment': "url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHZpZXdCb3g9IjAgMCA0MCA0MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZGVmcz48cGF0dGVybiBpZD0iZ3JpZCIgd2lkdGg9IjQwIiBoZWlnaHQ9IjQwIiBwYXR0ZXJuVW5pdHM9InVzZXJTcGFjZU9uVXNlIj48cGF0aCBkPSJNIDQwIDAgTCAwIDAgMCA0MCIgZmlsbD0ibm9uZSIgc3Ryb2tlPSIjZjRmMWU4IiBzdHJva2Utd2lkdGg9IjEiLz48L3BhdHRlcm4+PC9kZWZzPjxyZWN0IHdpZHRoPSIxMDAlIiBoZWlnaHQ9IjEwMCUiIGZpbGw9InVybCgjZ3JpZCkiLz48L3N2Zz4=')",
      }
    },
  },
  plugins: [],
}
