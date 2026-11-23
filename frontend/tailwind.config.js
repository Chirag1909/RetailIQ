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
        background: '#070b13',
        surface: {
          DEFAULT: '#0d1527',
          light: '#131f38',
          lighter: '#1a2b4c',
          border: '#1e2e4f'
        },
        brand: {
          cyan: '#06b6d4',
          cyanLight: '#38bdf8',
          blue: '#2563eb',
          blueDark: '#1d4ed8'
        },
        accent: {
          emerald: '#10b981',
          amber: '#f59e0b',
          rose: '#f43f5e',
          purple: '#8b5cf6'
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'Courier New', 'monospace'],
      }
    },
  },
  plugins: [],
}
