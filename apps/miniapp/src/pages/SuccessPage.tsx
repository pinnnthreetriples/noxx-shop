import * as React from 'react'
import * as RR from 'react-router-dom'
import * as NoxxVM from '@/shared/noxx/useNoxx'
import * as Motion from '@/shared/noxx/motion'

export default function SuccessPage() {
  const { showSuccess, glowOn, goSuccessPurch, backHome } = NoxxVM.useNoxx()
  const isSub = !!(RR.useLocation().state as { sub?: boolean } | null)?.sub
  const rootRef = React.useRef<HTMLDivElement>(null)
  React.useLayoutEffect(() => { const tl = Motion.successIn(rootRef.current); return () => { tl?.kill() } }, [])
  return (
    <>
{(showSuccess) && (<>
    <div data-screen-label="Payment success" data-self-anim="" ref={rootRef} style={{"position": "absolute", "inset": "0", "display": "flex", "flexDirection": "column", "alignItems": "center", "justifyContent": "center", "padding": "30px"}}>
      {(glowOn) && (<><div style={{"position": "absolute", "top": "38%", "left": "50%", "transform": "translate(-50%,-50%)", "width": "300px", "height": "300px", "background": "radial-gradient(circle,rgba(90,210,140,.16),transparent 70%)", "pointerEvents": "none"}} /></>)}
      <div style={{"position": "relative", "width": "104px", "height": "104px", "display": "flex", "alignItems": "center", "justifyContent": "center", "marginBottom": "34px"}}>
        <div style={{"position": "absolute", "inset": "0", "borderRadius": "50%", "border": "2px dashed rgba(120,220,160,.45)", "animation": "spinDash 14s linear infinite"}} />
        <div data-success-check="" style={{"width": "66px", "height": "66px", "borderRadius": "50%", "background": "radial-gradient(circle at 40% 35%,#46c984,#2e9d62)", "display": "flex", "alignItems": "center", "justifyContent": "center", "boxShadow": "0 0 46px rgba(80,200,130,.5)"}}><svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12.5l4.5 4.5L19 7" /></svg></div>
      </div>
      <div style={{"fontSize": "27px", "fontWeight": "700", "color": "#fff", "marginBottom": "14px"}}>Payment successful!</div>
      <div style={{"fontSize": "16px", "color": "#9a9098", "textAlign": "center", "lineHeight": "1.5", "maxWidth": "280px", "marginBottom": "42px"}}>{isSub ? (<>Your Premium subscription is now active</>) : (<>Your videos are now available in <span style={{"color": "#e9e2e8", "fontWeight": "600"}}>My purchases</span></>)}</div>
      <button onClick={goSuccessPurch} style={{"width": "100%", "maxWidth": "320px", "padding": "18px", "border": "none", "borderRadius": "16px", "cursor": "pointer", "fontSize": "17px", "fontWeight": "600", "color": "#fff", "background": "linear-gradient(100deg,#d6246e,#ec5690 48%,#f6a98c)", "boxShadow": "0 14px 34px -10px rgba(240,70,140,.6)", "marginBottom": "14px"}}>Go to purchases</button>
      <button onClick={backHome} style={{"width": "100%", "maxWidth": "320px", "padding": "16px", "border": "1px solid rgba(255,255,255,.09)", "borderRadius": "16px", "cursor": "pointer", "fontSize": "16px", "fontWeight": "600", "color": "#cfc7cc", "background": "rgba(255,255,255,.02)"}}>Back to home</button>
    </div>
    </>)}
    </>
  )
}
