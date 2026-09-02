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
          950: '#0b0f17',
          900: '#0f172a',
          850: '#151e2e',
          800: '#1e293b',
          700: '#2a374a',
          600: '#334155',
          500: '#475569',
          400: '#64748b',
          300: '#94a3b8',
          200: '#cbd5e1',
          100: '#f1f5f9',
        },
        safety: {
          critical: '#ef4444',
          high: '#f97316',
          review: '#f59e0b',
          routine: '#10b981',
          info: '#3b82f6',
        }
      },
      fontFamily: {
        mono: ['ui-monospace', 'SFMono-Regular', 'Menlo', 'Monaco', 'Consolas', 'monospace'],
      }
    },
  },
  plugins: [],
}
