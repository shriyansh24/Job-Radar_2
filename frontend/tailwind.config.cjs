const path = require('path')

/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    path.join(__dirname, 'index.html'),
    path.join(__dirname, 'src/**/*.{js,ts,jsx,tsx}'),
  ],
  theme: {
    extend: {
      fontFamily: {
        ui: ['Geist', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
        mono: ['Geist Mono', 'monospace'],
      },
      colors: {
        base: '#000000',
        surface: '#0a0a0a',
        elevated: '#111111',
        border: '#333333',
        'text-primary': '#EDEDED',
        'text-secondary': '#888888',
        accent: '#0070F3',
        'accent-green': '#10B981',
        'accent-amber': '#F5A623',
        'accent-red': '#E00000',
        'accent-cyan': '#3291FF',
      },
    },
  },
  plugins: [],
}
