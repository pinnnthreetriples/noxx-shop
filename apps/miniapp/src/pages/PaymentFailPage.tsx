import * as React from 'react'
import * as RR from 'react-router-dom'
import * as Motion from '@/shared/noxx/motion'

// Payment-failure twin of SuccessPage: red cross, retry + support actions.
export default function PaymentFailPage() {
  const nav = RR.useNavigate()
  const rootRef = React.useRef<HTMLDivElement>(null)
  React.useLayoutEffect(() => { const tl = Motion.successIn(rootRef.current); return () => { tl?.kill() } }, [])
  React.useEffect(() => { window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred?.('error') }, [])
  return (
    <div data-screen-label="Payment failed" data-self-anim="" ref={rootRef} style={{"position": "absolute", "inset": "0", "display": "flex", "flexDirection": "column", "alignItems": "center", "justifyContent": "center", "padding": "30px"}}>
      <div style={{"position": "absolute", "top": "38%", "left": "50%", "transform": "translate(-50%,-50%)", "width": "300px", "height": "300px", "background": "radial-gradient(circle,rgba(255,90,110,.14),transparent 70%)", "pointerEvents": "none"}} />
      <div style={{"position": "relative", "width": "104px", "height": "104px", "display": "flex", "alignItems": "center", "justifyContent": "center", "marginBottom": "34px"}}>
        <div style={{"position": "absolute", "inset": "0", "borderRadius": "50%", "border": "2px dashed rgba(255,120,140,.45)", "animation": "spinDash 14s linear infinite"}} />
        <div data-success-check="" style={{"width": "66px", "height": "66px", "borderRadius": "50%", "background": "radial-gradient(circle at 40% 35%,#f0566e,#c92e4a)", "display": "flex", "alignItems": "center", "justifyContent": "center", "boxShadow": "0 0 46px rgba(240,86,110,.5)"}}><svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2.6" strokeLinecap="round"><path d="M6 6l12 12M18 6L6 18" /></svg></div>
      </div>
      <div style={{"fontSize": "27px", "fontWeight": "700", "color": "#fff", "marginBottom": "14px"}}>Payment failed</div>
      <div style={{"fontSize": "16px", "color": "#9a9098", "textAlign": "center", "lineHeight": "1.5", "maxWidth": "280px", "marginBottom": "42px"}}>Your payment didn't go through. No money was taken — you can safely try again.</div>
      <button onClick={() => nav('/checkout')} style={{"width": "100%", "maxWidth": "320px", "padding": "18px", "border": "none", "borderRadius": "16px", "cursor": "pointer", "fontSize": "17px", "fontWeight": "600", "color": "#fff", "background": "linear-gradient(100deg,#d6246e,#ec5690 48%,#f6a98c)", "boxShadow": "0 14px 34px -10px rgba(240,70,140,.6)", "marginBottom": "14px"}}>Try again</button>
      <button onClick={() => nav('/support')} style={{"width": "100%", "maxWidth": "320px", "padding": "16px", "border": "1px solid rgba(255,255,255,.09)", "borderRadius": "16px", "cursor": "pointer", "fontSize": "16px", "fontWeight": "600", "color": "#cfc7cc", "background": "rgba(255,255,255,.02)"}}>Contact support</button>
    </div>
  )
}
