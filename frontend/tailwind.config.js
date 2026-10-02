/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: '#F1F5F9', // Page Grey
        surface: '#FFFFFF', // White
        'surface-secondary': '#EFF6FF', // Light Blue for selected/informational
        'text-primary': '#111827', // Primary Text
        'text-secondary': '#475569', // Secondary Text
        'text-muted': '#64748B', // Muted Text
        border: '#E2E8F0', // Border
        primary: '#2563EB', // Primary Blue
        'primary-dark': '#1D4ED8', // Dark Blue
        'primary-light': '#EFF6FF', // Light Blue
        accent: '#F97316', // Primary Orange
        'accent-dark': '#EA580C', // Dark Orange
        'accent-light': '#FFF7ED', // Light Orange
        success: '#16A34A', // Success
        warning: '#F97316',
        error: '#EF4444',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
