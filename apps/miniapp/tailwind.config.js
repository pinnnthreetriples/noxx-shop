/** @type {import('tailwindcss').Config} */
// NoxX design tokens mapped onto Tailwind. The source of truth is the CSS
// variable layer in src/app/index.css — these utilities just reference it.
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        surface: {
          0: 'var(--noxx-surface)',
          1: 'var(--surface-1)',
          2: 'var(--surface-2)',
          3: 'var(--surface-3)',
          4: 'var(--surface-4)',
          pink: 'var(--surface-pink)',
        },
        ink: {
          900: 'var(--ink-900)', 800: 'var(--ink-800)', 700: 'var(--ink-700)',
          600: 'var(--ink-600)', 500: 'var(--ink-500)', 400: 'var(--ink-400)',
          350: 'var(--ink-350)', 300: 'var(--ink-300)', 200: 'var(--ink-200)',
        },
        pink: {
          300: 'var(--pink-300)', 350: 'var(--pink-350)', 400: 'var(--pink-400)',
          500: 'var(--pink-500)', hot: 'var(--pink-hot)', link: 'var(--pink-link)',
        },
        gold: { 500: 'var(--gold-500)', ink: 'var(--gold-ink)' },
        ok: 'var(--ok-text)',
        hairline: { DEFAULT: 'var(--hairline)', strong: 'var(--hairline-strong)', soft: 'var(--hairline-soft)' },
      },
      borderRadius: {
        sm: 'var(--r-sm)', md: 'var(--r-md)', lg: 'var(--r-lg)', xl: 'var(--r-xl)',
        '2xl': 'var(--r-2xl)', '3xl': 'var(--r-3xl)', pill: 'var(--r-pill)',
      },
      fontFamily: { sans: 'var(--font-sans)' },
      boxShadow: {
        cta: 'var(--shadow-cta)', 'cta-tall': 'var(--shadow-cta-tall)',
        secondary: 'var(--shadow-secondary)', fab: 'var(--shadow-fab)',
        badge: 'var(--shadow-badge)', frame: 'var(--shadow-frame)',
      },
      backgroundImage: {
        'grad-primary': 'var(--grad-primary)', 'grad-primary-2': 'var(--grad-primary-2)',
        'grad-secondary': 'var(--grad-secondary)', 'grad-pill': 'var(--grad-pill)',
        'grad-fab': 'var(--grad-fab)', 'grad-crown': 'var(--grad-crown)',
        'grad-app-bg': 'var(--grad-app-bg)',
      },
      maxWidth: { frame: 'var(--frame-w)' },
    },
  },
  plugins: [],
}
