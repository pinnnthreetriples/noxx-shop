/**
 * Typed, defensive wrapper around the Telegram WebApp SDK.
 * Every accessor is safe to call outside Telegram (returns undefined / no-op),
 * so the app also runs in a normal browser during development.
 */

type ThemeParams = Record<string, string>

export interface TelegramWebApp {
  initData: string
  colorScheme: 'light' | 'dark'
  themeParams: ThemeParams
  isExpanded: boolean
  viewportHeight: number
  viewportStableHeight: number
  ready: () => void
  expand: () => void
  close: () => void
  setHeaderColor: (color: string) => void
  setBackgroundColor: (color: string) => void
  onEvent: (event: string, cb: () => void) => void
  offEvent: (event: string, cb: () => void) => void
  HapticFeedback?: {
    impactOccurred: (style: 'light' | 'medium' | 'heavy' | 'rigid' | 'soft') => void
    notificationOccurred: (type: 'error' | 'success' | 'warning') => void
    selectionChanged: () => void
  }
  MainButton?: {
    text: string
    isVisible: boolean
    show: () => void
    hide: () => void
    enable: () => void
    disable: () => void
    showProgress: (leaveActive?: boolean) => void
    hideProgress: () => void
    setText: (text: string) => void
    onClick: (cb: () => void) => void
    offClick: (cb: () => void) => void
  }
}

export function getTelegram(): TelegramWebApp | undefined {
  if (typeof window === 'undefined') return undefined
  return (window as unknown as { Telegram?: { WebApp?: TelegramWebApp } }).Telegram?.WebApp
}

export function isInTelegram(): boolean {
  return Boolean(getTelegram()?.initData)
}

/** Map Telegram themeParams (snake_case) onto our --tg-theme-* CSS variables. */
export function applyTelegramTheme(): 'light' | 'dark' {
  const tg = getTelegram()
  const root = document.documentElement
  const scheme = tg?.colorScheme ?? 'dark'
  root.classList.toggle('dark', scheme === 'dark')
  root.classList.toggle('light', scheme === 'light')

  const params = tg?.themeParams
  if (params) {
    for (const [key, value] of Object.entries(params)) {
      root.style.setProperty(`--tg-theme-${key.replace(/_/g, '-')}`, value)
    }
  }
  return scheme
}

/** Initialise the Mini App: ready + expand + theme sync. Returns cleanup. */
export function initTelegram(): () => void {
  const tg = getTelegram()
  if (!tg) {
    applyTelegramTheme()
    return () => {}
  }
  tg.ready()
  tg.expand()
  applyTelegramTheme()
  // Pin the frame to Telegram's real visible height. In the iOS webview 100vh is
  // taller than the visible area, so a bottom-anchored nav lands off-screen —
  // track viewportStableHeight into --tg-vh instead (see .noxx-frame).
  const applyViewport = () => {
    const h = tg.viewportStableHeight || tg.viewportHeight
    if (h) document.documentElement.style.setProperty('--tg-vh', `${h}px`)
  }
  applyViewport()
  const onThemeChanged = () => applyTelegramTheme()
  tg.onEvent('themeChanged', onThemeChanged)
  tg.onEvent('viewportChanged', applyViewport)
  return () => {
    tg.offEvent('themeChanged', onThemeChanged)
    tg.offEvent('viewportChanged', applyViewport)
  }
}

export type HapticStyle = 'light' | 'medium' | 'heavy' | 'rigid' | 'soft'

/** Fire a haptic impact, safely no-op outside Telegram. */
export function haptic(style: HapticStyle = 'light'): void {
  getTelegram()?.HapticFeedback?.impactOccurred(style)
}

export function hapticNotify(type: 'error' | 'success' | 'warning'): void {
  getTelegram()?.HapticFeedback?.notificationOccurred(type)
}
