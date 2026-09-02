/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        industrial: {
          950: '#fafafa', // App background (warm off-white)
          900: '#f4f4f5', // Surface / Sidebar
          850: '#e4e4e7', // Borders / dividers
          800: '#d4d4d8', // Stronger borders
          700: '#a1a1aa', // Muted text
          600: '#71717a', // Secondary text
          500: '#52525b', 
          400: '#3f3f46', 
          300: '#27272a',
          200: '#18181b', // Headings / strong text
          100: '#09090b', // Primary text
          50: '#000000',  // Pure black
        },
        safety: {
          critical: '#000000', // Black
          high: '#52525b', // Dark grey
          review: '#a1a1aa', // Medium grey
          routine: '#e4e4e7', // Very light grey
          info: '#ffffff', // White
        },
        // Inverted Semantic Colors for elegant, subtle badges in Light Mode
        red: { 950: '#fef2f2', 900: '#fee2e2', 800: '#fecaca', 700: '#fca5a5', 600: '#f87171', 500: '#ef4444', 400: '#dc2626', 300: '#b91c1c', 200: '#991b1b', 100: '#7f1d1d', 50: '#450a0a' },
        amber: { 950: '#fffbeb', 900: '#fef3c7', 800: '#fde68a', 700: '#fcd34d', 600: '#fbbf24', 500: '#f59e0b', 400: '#d97706', 300: '#b45309', 200: '#92400e', 100: '#78350f', 50: '#451a03' },
        emerald: { 950: '#ecfdf5', 900: '#d1fae5', 800: '#a7f3d0', 700: '#6ee7b7', 600: '#34d399', 500: '#10b981', 400: '#059669', 300: '#047857', 200: '#065f46', 100: '#064e3b', 50: '#022c22' },
        blue: { 950: '#eff6ff', 900: '#dbeafe', 800: '#bfdbfe', 700: '#93c5fd', 600: '#60a5fa', 500: '#3b82f6', 400: '#2563eb', 300: '#1d4ed8', 200: '#1e40af', 100: '#1e3a8a', 50: '#172554' },
        orange: { 950: '#fff7ed', 900: '#ffedd5', 800: '#fed7aa', 700: '#fdba74', 600: '#fb923c', 500: '#f97316', 400: '#ea580c', 300: '#c2410c', 200: '#9a3412', 100: '#7c2d12', 50: '#431407' },
        // Keep offensive colors as grayscale
        purple: { 950: '#f4f4f5', 900: '#e4e4e7', 800: '#d4d4d8', 700: '#a1a1aa', 600: '#71717a', 500: '#52525b', 400: '#3f3f46', 300: '#27272a', 200: '#18181b', 100: '#09090b', 50: '#000000' },
        green: { 950: '#f4f4f5', 900: '#e4e4e7', 800: '#d4d4d8', 700: '#a1a1aa', 600: '#71717a', 500: '#52525b', 400: '#3f3f46', 300: '#27272a', 200: '#18181b', 100: '#09090b', 50: '#000000' },
        cyan: { 950: '#f4f4f5', 900: '#e4e4e7', 800: '#d4d4d8', 700: '#a1a1aa', 600: '#71717a', 500: '#52525b', 400: '#3f3f46', 300: '#27272a', 200: '#18181b', 100: '#09090b', 50: '#000000' },
        teal: { 950: '#f4f4f5', 900: '#e4e4e7', 800: '#d4d4d8', 700: '#a1a1aa', 600: '#71717a', 500: '#52525b', 400: '#3f3f46', 300: '#27272a', 200: '#18181b', 100: '#09090b', 50: '#000000' },
      },
      fontFamily: {
        mono: ['ui-sans-serif', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'Helvetica Neue', 'Arial', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
