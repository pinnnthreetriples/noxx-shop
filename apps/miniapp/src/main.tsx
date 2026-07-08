import React from 'react'
import ReactDOM from 'react-dom/client'
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

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <AppProviders>
      <App />
    </AppProviders>
  </React.StrictMode>,
)