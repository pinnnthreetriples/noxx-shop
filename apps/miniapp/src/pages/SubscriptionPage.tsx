import * as React from 'react'
import * as NoxxVM from '@/shared/noxx/useNoxx'
import * as Motion from '@/shared/noxx/motion'

export default function SubscriptionPage() {
  const { showSubscription, backProfile, subPlans, premiumActive, premiumUntilFmt, payCrypto, subComingSoon, subComingSoonText, subscribeNow, subscribeBusy, subscribePrice, subscribeUsd } = NoxxVM.useNoxx()
  return (
    <>
{(showSubscription) && (<>
    <div data-screen-label="Subscription" style={{"position": "absolute", "inset": "0", "display": "flex", "flexDirection": "column"}}>
      <div style={{"flex": "none", "display": "flex", "alignItems": "center", "gap": "16px", "padding": "50px 22px 14px"}}><div onClick={backProfile} style={{"cursor": "pointer"}}><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M19 12H5M11 18l-6-6 6-6" /></svg></div><div style={{"fontSize": "23px", "fontWeight": "600", "color": "#fff"}}>Subscription</div></div>
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
        {(subPlans||[]).map((p: any, _k0: number) => (<React.Fragment key={_k0}>
          <div data-press="" onClick={p.onSelect} style={p.cardStyle}>
            {(p.tag) && (<><div style={{"position": "absolute", "top": "-9px", "right": "14px", "padding": "2px 9px", "borderRadius": "999px", "background": "linear-gradient(135deg,#ff5aa0,#d63d8f)", "color": "#fff", "fontSize": "11px", "fontWeight": "700", "letterSpacing": ".3px"}}>{p.tag}</div></>)}
            <div style={p.dotStyle}>{(p.selected) && (<><div data-radio-dot="" ref={Motion.planDotPopRef} style={{"width": "10px", "height": "10px", "borderRadius": "50%", "background": "#ff5aa0"}} /></>)}</div>
            <div style={{"flex": "1"}}><div style={{"fontSize": "17px", "fontWeight": "600", "color": "#fff"}}>{p.name}</div><div style={{"fontSize": "13px", "color": "#9a9098", "marginTop": "2px"}}>{p.sub}</div></div>
            <div style={{"textAlign": "right", "flex": "none"}}><div style={{"fontSize": "18px", "fontWeight": "700", "color": "#fff", "whiteSpace": "nowrap"}}>{payCrypto ? p.usdFmt : (<>{p.priceFmt} <svg width="14" height="14" viewBox="0 0 24 24" fill="#f7b23b" style={{"display": "inline", "verticalAlign": "-2px"}}><path d="M12 2l2.95 5.98 6.6.96-4.78 4.66 1.13 6.57L12 17.98 6.1 20.16l1.13-6.57L2.45 8.94l6.6-.96z" /></svg></>)}</div>{!payCrypto && (<div style={{"fontSize": "12.5px", "color": "#8c828c", "whiteSpace": "nowrap"}}>≈ {p.usdFmt}</div>)}</div>
          </div>
        </React.Fragment>))}
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
