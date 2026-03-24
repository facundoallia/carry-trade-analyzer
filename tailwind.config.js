/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        navy: {
          50: '#eff6ff',
          100: '#dbeafe',
          200: '#bfdbfe',
          600: '#2a5298',
          700: '#1e3c72',
          800: '#1a3560',
          900: '#152b4e',
        }
      },
      fontFamily: {
        sans: ['Source Sans 3', 'system-ui', 'sans-serif'],
      }
    }
  },
  plugins: []
}
