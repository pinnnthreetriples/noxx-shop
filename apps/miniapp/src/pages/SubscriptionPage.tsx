import * as React from 'react'
import * as NoxxVM from '@/shared/noxx/useNoxx'
import * as Motion from '@/shared/noxx/motion'

export default function SubscriptionPage() {
  const { showSubscription, backProfile, subPlans, premiumActive, premiumUntilFmt, payCrypto, payMethods, subAutoRenew, subComingSoon, subComingSoonText, subscribeNow, subscribeBusy, subscribePrice, subscribeUsd } = NoxxVM.useNoxx()
  const [payOpen, setPayOpen] = React.useState(false)
  const paySelected = (payMethods || []).find((m) => m.selected)
  return (
    <>
{(showSubscription) && (<>
    <div data-screen-label="Subscription" style={{"position": "absolute", "inset": "0", "display": "flex", "flexDirection": "column"}}>
      <div style={{"flex": "none", "display": "flex", "alignItems": "center", "gap": "16px", "padding": "16px 22px 14px"}}><div onClick={backProfile} style={{"cursor": "pointer"}}><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M19 12H5M11 18l-6-6 6-6" /></svg></div><div style={{"fontSize": "23px", "fontWeight": "600", "color": "#fff"}}>Subscription</div></div>
      <div style={{"flex": "1", "overflowY": "auto", "padding": "8px 22px 30px"}}>
        <div style={{"position": "relative", "overflow": "hidden", "borderRadius": "22px", "padding": "22px", "marginBottom": "24px", "background": "linear-gradient(120deg,#2a0f1d,#180a12)", "border": "1px solid rgba(255,90,160,.28)"}}>
          <div style={{"position": "absolute", "right": "-22px", "top": "-22px", "width": "140px", "height": "140px", "background": "radial-gradient(circle,rgba(255,90,170,.4),transparent 65%)", "filter": "blur(12px)", "pointerEvents": "none"}} />
          <div style={{"position": "relative", "display": "flex", "alignItems": "center", "gap": "13px"}}>
            <img src="/crown-icon.png" alt="" style={{"width": "36px", "height": "auto", "display": "block", "filter": "drop-shadow(0 0 8px rgba(255,90,170,.6))"}} />
            {(premiumActive) ? (
              <div style={{"flex": "1"}}><div style={{"fontSize": "13px", "color": "rgba(255,255,255,.62)"}}>Current plan</div><div style={{"fontSize": "21px", "fontWeight": "700", "color": "#fff"}}>Premium</div></div>
            ) : (
              <div style={{"flex": "1"}}><div style={{"fontSize": "13px", "color": "rgba(255,255,255,.62)"}}>NoxX Premium</div><div style={{"fontSize": "21px", "fontWeight": "700", "color": "#fff", "letterSpacing": "-.3px", "lineHeight": "1.25"}}>Every Premium video included</div></div>
            )}
          </div>
          {(premiumActive) && (<div style={{"position": "relative", "marginTop": "15px", "display": "flex", "alignItems": "center", "gap": "7px", "fontSize": "13px", "color": "rgba(255,255,255,.6)"}}><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,.5)" strokeWidth="1.7"><circle cx="12" cy="12" r="9" /><path d="M12 7.5V12l3 2" /></svg>Active until {premiumUntilFmt}</div>)}
        </div>
        <div style={{"fontSize": "15px", "fontWeight": "600", "color": "#e9e2e8", "marginBottom": "14px"}}>Choose your plan</div>
        {(subPlans||[]).map((p, _k0: number) => (<React.Fragment key={_k0}>
          <div data-press="" onClick={p.onSelect} style={p.cardStyle}>
            {(p.tag) && (<><div style={{"position": "absolute", "top": "-9px", "right": "14px", "padding": "2px 9px", "borderRadius": "999px", "background": "linear-gradient(135deg,#ff5aa0,#d63d8f)", "color": "#fff", "fontSize": "11px", "fontWeight": "700", "letterSpacing": ".3px"}}>{p.tag}</div></>)}
            <div style={p.dotStyle}>{(p.selected) && (<><div data-radio-dot="" ref={Motion.planDotPopRef} style={{"width": "10px", "height": "10px", "borderRadius": "50%", "background": "#ff5aa0"}} /></>)}</div>
            <div style={{"flex": "1"}}><div style={{"fontSize": "17px", "fontWeight": "600", "color": "#fff"}}>{p.name}</div><div style={{"fontSize": "13px", "color": "#9a9098", "marginTop": "2px"}}>{p.sub}</div></div>
            <div style={{"textAlign": "right", "flex": "none"}}><div style={{"fontSize": "18px", "fontWeight": "700", "color": "#fff", "whiteSpace": "nowrap"}}>{payCrypto ? p.usdFmt : (<>{p.priceFmt} <svg width="14" height="14" viewBox="0 0 24 24" fill="#f7b23b" style={{"display": "inline", "verticalAlign": "-2px"}}><path d="M12 2l2.95 5.98 6.6.96-4.78 4.66 1.13 6.57L12 17.98 6.1 20.16l1.13-6.57L2.45 8.94l6.6-.96z" /></svg></>)}</div>{!payCrypto && (<div style={{"fontSize": "12.5px", "color": "#8c828c", "whiteSpace": "nowrap"}}>≈ {p.usdFmt}</div>)}</div>
          </div>
        </React.Fragment>))}
        <div style={{"borderRadius": "18px", "border": "1px solid rgba(255,255,255,.06)", "background": "rgba(255,255,255,.03)", "padding": "16px 18px", "marginTop": "22px"}}>
          <div onClick={() => setPayOpen((o) => !o)} style={{"display": "flex", "alignItems": "center", "gap": "10px", "cursor": "pointer"}}>
            <div style={{"flex": "1", "fontSize": "15px", "fontWeight": "600", "color": "#e9e2e8"}}>Payment method</div>
            {!payOpen && (<span style={{"fontSize": "14px", "fontWeight": "600", "color": "#ff7ab8"}}>{paySelected?.name}</span>)}
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#8c828c" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" style={{"transform": payOpen ? 'rotate(180deg)' : 'none', "transition": "transform .25s"}}><path d="M6 9l6 6 6-6" /></svg>
          </div>
          {payOpen && (<div style={{"marginTop": "14px"}}>
          {(payMethods||[]).map((m, _kp: number) => (<React.Fragment key={_kp}>
            <div data-press="" onClick={() => { m.onSelect(); setPayOpen(false) }} style={m.cardStyle}>
              <div style={{"width": "46px", "height": "46px", "borderRadius": "50%", "background": "rgba(255,255,255,.05)", "border": "1px solid rgba(255,255,255,.08)", "display": "flex", "alignItems": "center", "justifyContent": "center", "flex": "none"}}>
                {m.crypto
                  ? <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#56dea0" strokeWidth="1.8" strokeLinecap="round"><circle cx="12" cy="12" r="9" /><path d="M12 7v10M9.5 9.5h3.6a1.9 1.9 0 0 1 0 3.8H9.5h4.1a1.9 1.9 0 0 1 0 3.8H9.5" /></svg>
                  : <svg width="24" height="24" viewBox="0 0 24 24" fill="#f7b23b"><path d="M12 2l2.95 5.98 6.6.96-4.78 4.66 1.13 6.57L12 17.98 6.1 20.16l1.13-6.57L2.45 8.94l6.6-.96z" /></svg>}
              </div>
              <div style={{"flex": "1"}}><div style={{"fontSize": "17px", "fontWeight": "600", "color": "#fff"}}>{m.name}</div><div style={{"fontSize": "13px", "color": "#8c828c", "marginTop": "2px"}}>{m.sub}</div></div>
              <div style={{"width": "20px", "height": "20px", "borderRadius": "50%", "flex": "none", "display": "flex", "alignItems": "center", "justifyContent": "center", "border": "2px solid " + (m.selected ? '#ff5aa0' : 'rgba(255,255,255,.25)')}}>{m.selected && (<div style={{"width": "10px", "height": "10px", "borderRadius": "50%", "background": "#ff5aa0"}} />)}</div>
            </div>
          </React.Fragment>))}
          </div>)}
        </div>
        {(subAutoRenew) && (<div style={{"display": "flex", "alignItems": "flex-start", "gap": "9px", "marginTop": "12px", "padding": "12px 14px", "borderRadius": "12px", "background": "rgba(247,178,59,.06)", "border": "1px solid rgba(247,178,59,.22)"}}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#f7b23b" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{"flex": "none", "marginTop": "1px"}}><path d="M23 4v6h-6M1 20v-6h6" /><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" /></svg>
          <div style={{"fontSize": "13px", "color": "#c9b48a", "lineHeight": "1.45"}}>Renews automatically every month — cancel anytime in Telegram.</div>
        </div>)}
        <div style={{"marginTop": "24px", "borderRadius": "18px", "background": "rgba(255,255,255,.03)", "border": "1px solid rgba(255,255,255,.06)", "padding": "6px 18px 6px"}}>
          <div style={{"display": "flex", "alignItems": "flex-start", "gap": "11px", "padding": "13px 0", "borderBottom": "1px solid rgba(255,255,255,.05)"}}><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#ff7ab8" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" style={{"flex": "none", "marginTop": "2px"}}><path d="M5 12.5l4 4 10-10" /></svg><div><div style={{"fontSize": "14.5px", "fontWeight": "600", "color": "#fff"}}>Every Premium video included</div><div style={{"fontSize": "13px", "color": "#9a9098", "marginTop": "2px"}}>Claim them for free while your plan is active</div></div></div>
          <div style={{"display": "flex", "alignItems": "flex-start", "gap": "11px", "padding": "13px 0"}}><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#ff7ab8" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" style={{"flex": "none", "marginTop": "2px"}}><path d="M5 12.5l4 4 10-10" /></svg><div><div style={{"fontSize": "14.5px", "fontWeight": "600", "color": "#fff"}}>New releases included</div><div style={{"fontSize": "13px", "color": "#9a9098", "marginTop": "2px"}}>Premium videos added later are included automatically</div></div></div>
        </div>
      </div>
      <div style={{"flex": "none", "padding": "14px 22px 26px"}}>
        {(subComingSoon) ? (<>
          <button disabled style={{"width": "100%", "display": "flex", "alignItems": "center", "justifyContent": "center", "padding": "18px", "border": "1px solid rgba(255,255,255,.1)", "borderRadius": "16px", "cursor": "default", "fontSize": "17px", "fontWeight": "600", "color": "#9a9098", "background": "rgba(255,255,255,.05)"}}>Coming soon</button>
          <div style={{"textAlign": "center", "fontSize": "13px", "color": "#8c828c", "marginTop": "12px", "lineHeight": "1.5"}}>{subComingSoonText}</div>
        </>) : (
          <button onClick={subscribeNow} disabled={subscribeBusy} style={{"position": "relative", "overflow": "visible", "width": "100%", "display": "flex", "alignItems": "center", "justifyContent": "center", "padding": "18px", "border": "none", "borderRadius": "16px", "cursor": "pointer", "fontSize": "17px", "fontWeight": "600", "color": "#fff", "background": "linear-gradient(100deg,#d6246e,#ec5690)", "opacity": subscribeBusy ? 0.7 : 1}}>
            <span style={{"position": "relative", "zIndex": "1"}}>{subscribeBusy ? 'Creating invoice…' : (<>Subscribe · {payCrypto ? subscribeUsd : subscribePrice}</>)}</span>
            {!payCrypto && (<img src="/stars-icon-nobg.png" alt="" style={{"position": "absolute", "right": "4px", "bottom": "-3px", "height": "96px", "width": "auto", "pointerEvents": "none", "filter": "drop-shadow(0 7px 11px rgba(120,60,0,.42))"}} />)}
          </button>
        )}
      </div>
    </div>
    </>)}
    </>
  )
}
