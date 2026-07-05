import * as React from 'react'
import * as Store from '@/shared/lib/store'
import * as Motion from '@/shared/noxx/motion'
import { LANGUAGES } from '@/features/language-switcher'
import { FlagIcon } from '@/shared/ui'
import type { FlagCode } from '@/shared/ui'

export default function LanguageSelectPage() {
  const setLanguage = Store.useAppStore((s) => s.setLanguage)
  const setLangChosen = Store.useAppStore((s) => s.setLangChosen)
  const rootRef = React.useRef<HTMLDivElement>(null)
  React.useLayoutEffect(() => { const tl = Motion.gateIn(rootRef.current); return () => { tl?.kill() } }, [])
  const pick = (code: string) => {
    setLanguage(code)
    setLangChosen(true)
    window.Telegram?.WebApp?.HapticFeedback?.selectionChanged?.()
  }
  return (
    <div data-screen-label="Language select" data-self-anim="" ref={rootRef} style={{"position": "absolute", "inset": "0", "display": "flex", "flexDirection": "column", "alignItems": "center", "justifyContent": "center", "padding": "34px 28px", "background": "radial-gradient(120% 70% at 50% 30%,#3a1226 0%,#160910 55%,#0a070c 100%)"}}>
      <div style={{"position": "relative", "width": "96px", "height": "96px", "display": "flex", "alignItems": "center", "justifyContent": "center", "marginBottom": "28px"}}>
        <div style={{"position": "absolute", "inset": "0", "borderRadius": "50%", "background": "radial-gradient(circle,rgba(255,60,150,.35),transparent 70%)", "boxShadow": "0 0 60px rgba(255,60,150,.45)"}} />
        <svg width="52" height="52" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="1.5"><circle cx="12" cy="12" r="9" /><path d="M3 12h18M12 3c2.5 2.4 3.8 5.6 3.8 9s-1.3 6.6-3.8 9c-2.5-2.4-3.8-5.6-3.8-9S9.5 5.4 12 3z" /></svg>
      </div>
      <div style={{"fontSize": "24px", "fontWeight": "700", "color": "#fff", "textAlign": "center", "marginBottom": "8px"}}>Choose your language</div>
      <div style={{"fontSize": "15px", "color": "#9a9098", "textAlign": "center", "marginBottom": "30px"}}>You can change it later in settings</div>
      <div style={{"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "10px", "width": "100%", "maxWidth": "360px"}}>
        {LANGUAGES.map((lang) => (
          <div key={lang.code} data-press="" onClick={() => pick(lang.code)} style={{"display": "flex", "alignItems": "center", "gap": "10px", "padding": "13px 14px", "borderRadius": "14px", "cursor": "pointer", "background": "rgba(255,255,255,.04)", "border": "1px solid rgba(255,255,255,.09)"}}>
            <FlagIcon code={lang.code as FlagCode} size={24} />
            <span style={{"fontSize": "14.5px", "fontWeight": "600", "color": "#fff", "whiteSpace": "nowrap", "overflow": "hidden", "textOverflow": "ellipsis"}}>{lang.label}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
