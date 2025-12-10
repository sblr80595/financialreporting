/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#ffebee',
          100: '#ffd4d9',
          200: '#ffaab3',
          300: '#ff7f8d',
          400: '#ff5566',
          500: '#ff2a40',
          600: '#8b0010',  // Brand red: rgb(139, 0, 16)
          700: '#6e000d',  // Darker variant for hover
          800: '#52000a',
          900: '#350007',
        },
        brand: {
          red: '#8b0010',
          'red-hover': '#6e000d',
          'red-light': '#ffebee',
        },
        secondary: {
          50: '#f8fafc',
          100: '#f1f5f9',
          200: '#e2e8f0',
          300: '#cbd5e1',
          400: '#94a3b8',
          500: '#64748b',
          600: '#475569',
          700: '#334155',
          800: '#1e293b',
          900: '#0f172a',
        }
      },
      fontFamily: {
        sans: ['Satoshi', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
