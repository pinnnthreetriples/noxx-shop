import * as React from 'react'
import * as NoxxVM from '@/shared/noxx/useNoxx'
import * as Motion from '@/shared/noxx/motion'

export default function AgeConfirmPage() {
  const { showGate, toggleGate, gateOk, gateNo, enter, gateBtnStyle } = NoxxVM.useNoxx()
  const rootRef = React.useRef<HTMLDivElement>(null)
  React.useLayoutEffect(() => { const tl = Motion.gateIn(rootRef.current); return () => { tl?.kill() } }, [])
  return (
    <>
{(showGate) && (<>
    <div data-screen-label="Age gate" data-self-anim="" ref={rootRef} style={{"position": "absolute", "inset": "0", "display": "flex", "flexDirection": "column", "alignItems": "center", "justifyContent": "center", "padding": "34px", "background": "radial-gradient(120% 70% at 50% 30%,#3a1226 0%,#160910 55%,#0a070c 100%)"}}>
      <div style={{"position": "relative", "width": "150px", "height": "150px", "display": "flex", "alignItems": "center", "justifyContent": "center", "marginBottom": "42px"}}>
        <div style={{"position": "absolute", "inset": "0", "borderRadius": "50%", "background": "radial-gradient(circle,rgba(255,60,150,.35),transparent 70%)", "boxShadow": "0 0 70px rgba(255,60,150,.45)"}} />
        <div data-gate-ring="" style={{"position": "absolute", "inset": "14px", "borderRadius": "50%", "border": "2px dashed rgba(255,120,180,.5)"}} />
        <div style={{"fontSize": "46px", "fontWeight": "700", "color": "#fff", "letterSpacing": "-1px"}}>18+</div>
      </div>
      <div style={{"fontSize": "25px", "fontWeight": "700", "color": "#fff", "textAlign": "center", "marginBottom": "14px"}}>This app contains adult content</div>
      <div style={{"fontSize": "16px", "color": "#9a9098", "textAlign": "center", "lineHeight": "1.5", "maxWidth": "300px", "marginBottom": "40px"}}>You must be at least 18 years old to continue.</div>
      <div data-press="" onClick={toggleGate} style={{"display": "flex", "alignItems": "center", "gap": "13px", "cursor": "pointer", "marginBottom": "30px", "alignSelf": "flex-start", "paddingLeft": "6px"}}>
        {(gateOk) && (<><div ref={Motion.planDotPopRef} style={{"width": "24px", "height": "24px", "borderRadius": "7px", "background": "linear-gradient(135deg,#f060a8,#ce3d92)", "display": "flex", "alignItems": "center", "justifyContent": "center", "flex": "none"}}><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12.5l4.5 4.5L19 7" /></svg></div></>)}
        {(gateNo) && (<><div style={{"width": "24px", "height": "24px", "borderRadius": "7px", "border": "2px solid rgba(255,255,255,.25)", "flex": "none"}} /></>)}
        <span style={{"fontSize": "15.5px", "color": "#cfc7cc"}}>I confirm that I am 18 years or older</span>
      </div>
      <button onClick={enter} style={gateBtnStyle}>Enter app</button>
    </div>
    </>)}
    </>
  )
}
