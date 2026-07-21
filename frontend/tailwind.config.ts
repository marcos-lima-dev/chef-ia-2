import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        terracotta: '#D97A5C',
        wood: '#8B6B4A',
        cream: '#FDF6F0',
        'dark-wood': '#5E3C1A',
        'light-cream': '#FFF8F2',
      },
      fontFamily: {
        sans: ['Geist', 'Manrope', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
export default config
