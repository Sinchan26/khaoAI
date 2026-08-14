/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        background: '#0c0e14',
        surface: '#151923',
        surfaceLight: '#1d2332',
        surfaceBorder: '#273043',
        brand: {
          50: '#fff7ed',
          100: '#ffedd5',
          200: '#fed7aa',
          300: '#fdba74',
          400: '#fb923c',
          500: '#f97316', // Vibrant Orange
          600: '#ea580c',
          700: '#c2410c',
        },
        tomato: {
          DEFAULT: '#E23744',
          light: '#ff4f5e',
          dark: '#b5212d',
          badge: '#fee2e2'
        },
        twiggy: {
          DEFAULT: '#FC8019',
          light: '#ff9a42',
          dark: '#d66304',
          badge: '#ffedd5'
        },
        accentGold: '#f59e0b',
        success: '#10b981'
      },
      fontFamily: {
        sans: ['Plus Jakarta Sans', 'Inter', 'system-ui', 'sans-serif'],
        display: ['Outfit', 'Plus Jakarta Sans', 'sans-serif']
      },
      boxShadow: {
        glass: '0 8px 32px 0 rgba(0, 0, 0, 0.37)',
        glow: '0 0 24px -4px rgba(249, 115, 22, 0.35)',
        glowTomato: '0 0 20px -4px rgba(226, 55, 68, 0.4)',
        glowTwiggy: '0 0 20px -4px rgba(252, 128, 25, 0.4)',
      },
      animation: {
        'pulse-subtle': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'fade-in': 'fadeIn 0.3s ease-out forwards',
        'slide-up': 'slideUp 0.4s ease-out forwards',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' }
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(16px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' }
        }
      }
    },
  },
  plugins: [],
}
