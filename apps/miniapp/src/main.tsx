import React from 'react'
import ReactDOM from 'react-dom/client'
import * as Sentry from '@sentry/react'
import App from './app/App'
import { AppProviders } from './app/providers'
import '@fontsource/inter/400.css'
import '@fontsource/inter/500.css'
import '@fontsource/inter/600.css'
import '@fontsource/inter/700.css'
import '@fontsource/inter/800.css'
import '@fontsource/inter/900.css'
import '@fontsource/playfair-display/800-italic.css'
import '@fontsource/playfair-display/900-italic.css'
import './app/index.css'
import './app/noxx.css'
import './app/i18n'

// Errors-only monitoring. No-op unless VITE_SENTRY_DSN is set at build time.
if (import.meta.env.VITE_SENTRY_DSN) {
  Sentry.init({ dsn: import.meta.env.VITE_SENTRY_DSN, environment: import.meta.env.MODE })
}

const root = ReactDOM.createRoot(document.getElementById('root')!)
const app = (
  <React.StrictMode>
    <AppProviders>
      <App />
    </AppProviders>
  </React.StrictMode>
)

// Paint once the app fonts are ready, so text renders in Inter/Playfair from the
// first frame instead of flashing a fallback and swapping in (FOUT). A short
// timeout is the safety valve so a slow/failed font load never blocks the UI.
let started = false
const start = () => { if (!started) { started = true; root.render(app) } }
const weights = [
  '400 1em Inter', '500 1em Inter', '600 1em Inter', '700 1em Inter', '800 1em Inter', '900 1em Inter',
  '800 italic 1em "Playfair Display"', '900 italic 1em "Playfair Display"',
]
if (document.fonts?.load) {
  Promise.all(weights.map((w) => document.fonts.load(w))).catch(() => {}).finally(start)
  setTimeout(start, 1000)
} else {
  start()
}