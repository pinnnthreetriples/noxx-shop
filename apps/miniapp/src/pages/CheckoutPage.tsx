import * as React from 'react'
import * as NoxxVM from '@/shared/noxx/useNoxx'

export default function CheckoutPage() {
  const { showCheckout, glowOn, checkoutBack, coItems, coTotalFmt, coTotalUsd, coInsufficient, doPay, payCrypto, payMethods, paySecureNote, coDiscountRows, coHasDiscount, coSubtotalFmt, coSubtotalUsd, promoValue, promoOnChange, promoApply, promoAppliedCode, promoInvalid, promoRemove, promoBusy } = NoxxVM.useNoxx()
  const [payOpen, setPayOpen] = React.useState(false)
  const paySelected = (payMethods || []).find((m) => m.selected)
  return (
    <>
{(showCheckout) && (<>
    <div data-screen-label="Checkout" style={{"position": "absolute", "inset": "0", "display": "flex", "flexDirection": "column"}}>
      {(glowOn) && (<><div style={{"position": "absolute", "top": "160px", "left": "50%", "transform": "translateX(-50%)", "width": "360px", "height": "200px", "background": "radial-gradient(ellipse closest-side,rgba(240,70,150,.14),transparent)", "filter": "blur(20px)", "pointerEvents": "none"}} /></>)}
      <div style={{"flex": "none", "display": "flex", "alignItems": "center", "justifyContent": "center", "padding": "14px 0 6px"}}><div style={{"width": "48px", "height": "6px", "borderRadius": "3px", "background": "rgba(255,255,255,.14)"}} /></div>
      <div style={{"flex": "none", "display": "flex", "alignItems": "center", "padding": "8px 22px 16px", "position": "relative", "zIndex": "2"}}>
        <div onClick={checkoutBack} style={{"width": "44px", "height": "44px", "borderRadius": "50%", "background": "rgba(255,255,255,.05)", "border": "1px solid rgba(255,255,255,.08)", "display": "flex", "alignItems": "center", "justifyContent": "center", "cursor": "pointer"}}><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M19 12H5M11 18l-6-6 6-6" /></svg></div>
        <div style={{"flex": "1", "textAlign": "center", "fontSize": "24px", "fontWeight": "600", "color": "#fff", "marginLeft": "-44px", "paddingLeft": "44px", "pointerEvents": "none"}}>Checkout</div>
      </div>
      <div style={{"flex": "1", "overflowY": "auto", "padding": "6px 22px 18px", "position": "relative", "zIndex": "1"}}>
        <div style={{"borderRadius": "22px", "border": "1px solid rgba(255,90,160,.18)", "background": "rgba(255,255,255,.03)", "padding": "22px 20px", "boxShadow": "0 -1px 30px -10px rgba(255,80,150,.4)"}}>
          <div style={{"fontSize": "20px", "fontWeight": "600", "color": "#fff", "marginBottom": "8px"}}>Order summary</div>
          {(coItems||[]).map((v, _k0: number) => (<React.Fragment key={_k0}>
            <div style={{"display": "flex", "alignItems": "center", "gap": "14px", "padding": "16px 0", "borderBottom": "1px solid rgba(255,255,255,.06)"}}>
              <div style={{"width": "56px", "height": "56px", "borderRadius": "13px", "overflow": "hidden", "flex": "none", "position": "relative"}}><div style={v.bg} /></div>
              <div style={{"flex": "1", "minWidth": "0"}}><div style={{"fontSize": "17px", "fontWeight": "600", "color": "#fff"}}>{v.title}</div><div style={{"fontSize": "13px", "color": "#8c828c", "marginTop": "2px"}}>{v.tagline}</div></div>
              <div style={{"display": "flex", "alignItems": "center", "gap": "7px"}}>{!payCrypto && (<svg width="19" height="19" viewBox="0 0 24 24" fill="#f7b23b"><path d="M12 2l2.95 5.98 6.6.96-4.78 4.66 1.13 6.57L12 17.98 6.1 20.16l1.13-6.57L2.45 8.94l6.6-.96z" /></svg>)}<span style={{"fontSize": "18px", "fontWeight": "600", "color": "#f2e9ef"}}>{payCrypto ? v.usd : v.stars}</span></div>
            </div>
          </React.Fragment>))}
          {promoAppliedCode ? (
            <div style={{"display": "flex", "alignItems": "center", "gap": "9px", "marginTop": "16px", "padding": "12px 14px", "borderRadius": "12px", "background": "rgba(126,224,192,.07)", "border": "1px solid rgba(126,224,192,.3)"}}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#7ee0c0" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12.5l4 4 10-10" /></svg>
              <span style={{"flex": "1", "fontSize": "14.5px", "fontWeight": "600", "color": "#7ee0c0"}}>{promoAppliedCode} applied</span>
              <div onClick={promoRemove} style={{"cursor": "pointer", "padding": "2px"}}><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#8c828c" strokeWidth="2.2" strokeLinecap="round"><path d="M6 6l12 12M18 6L6 18" /></svg></div>
            </div>
          ) : (<>
            <div style={{"display": "flex", "gap": "10px", "marginTop": "16px"}}>
              <input value={promoValue} onChange={promoOnChange} onKeyDown={(e) => { if (e.key === 'Enter') promoApply() }} placeholder="Promo code" style={{"flex": "1", "minWidth": "0", "padding": "12px 14px", "borderRadius": "12px", "border": "1px solid " + (promoInvalid ? 'rgba(255,122,147,.5)' : 'rgba(255,255,255,.1)'), "background": "rgba(255,255,255,.04)", "color": "#fff", "fontSize": "15px", "fontFamily": "inherit", "outline": "none"}} />
              <button onClick={promoApply} disabled={promoBusy} style={{"padding": "12px 18px", "borderRadius": "12px", "border": "1px solid rgba(255,90,160,.4)", "background": "rgba(255,90,160,.12)", "color": "#ff7ab8", "fontSize": "15px", "fontWeight": "600", "fontFamily": "inherit", "cursor": "pointer", "opacity": promoBusy ? 0.6 : 1}}>{promoBusy ? '…' : 'Apply'}</button>
            </div>
            {(promoInvalid) && (<div style={{"marginTop": "8px", "fontSize": "13px", "color": "#ff7a93"}}>This code can't be applied — invalid, expired or already used.</div>)}
          </>)}
          {(coHasDiscount) && (<>
            <div style={{"display": "flex", "alignItems": "baseline", "justifyContent": "space-between", "paddingTop": "16px"}}><span style={{"fontSize": "15px", "color": "#8c828c"}}>Subtotal</span><span style={{"fontSize": "15px", "color": "#b3a9b0"}}>{payCrypto ? coSubtotalUsd : coSubtotalFmt}</span></div>
            {(coDiscountRows||[]).map((r, _k2: number) => (
              <div key={_k2} style={{"display": "flex", "alignItems": "baseline", "justifyContent": "space-between", "paddingTop": "8px"}}><span style={{"fontSize": "15px", "color": "#ff7ab8"}}>{r.label} −{r.pct}%</span><span style={{"fontSize": "15px", "fontWeight": "600", "color": "#ff7ab8"}}>{payCrypto ? r.usd : r.stars}</span></div>
            ))}
          </>)}
          <div style={{"display": "flex", "alignItems": "baseline", "justifyContent": "space-between", "paddingTop": coHasDiscount ? "12px" : "18px"}}><span style={{"fontSize": "18px", "color": "#b3a9b0"}}>Total</span><div><span data-total="" style={{"fontSize": "26px", "fontWeight": "700", "color": "#fff", "display": "inline-block"}}>{payCrypto ? coTotalUsd : coTotalFmt}</span> {!payCrypto && (<><span style={{"fontSize": "15px", "color": "#8c828c"}}>Stars</span> <span style={{"fontSize": "14px", "color": "#6a616b"}}>≈ {coTotalUsd}</span></>)}</div></div>
        </div>
        <div style={{"borderRadius": "22px", "border": "1px solid rgba(255,255,255,.06)", "background": "rgba(255,255,255,.02)", "padding": "20px", "marginTop": "22px"}}>
          <div onClick={() => setPayOpen((o) => !o)} style={{"display": "flex", "alignItems": "center", "gap": "10px", "cursor": "pointer"}}>
            <div style={{"flex": "1", "fontSize": "20px", "fontWeight": "600", "color": "#fff"}}>Payment method</div>
            {!payOpen && (<span style={{"fontSize": "14.5px", "fontWeight": "600", "color": "#ff7ab8"}}>{paySelected?.name}</span>)}
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#8c828c" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" style={{"transform": payOpen ? 'rotate(180deg)' : 'none', "transition": "transform .25s"}}><path d="M6 9l6 6 6-6" /></svg>
          </div>
          {payOpen && (<div style={{"marginTop": "16px"}}>
          {(payMethods||[]).map((m, _k1: number) => (<React.Fragment key={_k1}>
          <div onClick={() => { m.onSelect(); setPayOpen(false) }} style={m.cardStyle}>
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
      </div>
      <div style={{"flex": "none", "padding": "16px 22px 26px"}}>
        {(coInsufficient) && (<><div style={{"display": "flex", "alignItems": "center", "justifyContent": "center", "gap": "7px", "marginBottom": "12px", "color": "#ff7a93", "fontSize": "13.5px", "fontWeight": "600"}}>Insufficient Stars balance</div></>)}
        <button onClick={doPay} style={{"position": "relative", "width": "100%", "height": "66px", "border": "none", "borderRadius": "18px", "cursor": "pointer", "overflow": "visible", "background": "linear-gradient(100deg,#d6246e,#ec5690 48%,#f6a98c)", "boxShadow": "0 16px 38px -10px rgba(240,70,140,.65)"}}>
          <span style={{"fontSize": "19px", "fontWeight": "600", "color": "#fff"}}>Pay</span>
          <img src="/stars-icon-nobg.png" alt="" style={{"position": "absolute", "height": "100px", "width": "auto", "pointerEvents": "none", "filter": "drop-shadow(0 7px 11px rgba(120,60,0,.42))", "left": "calc(50% + 26px)", "top": "-17px"}} />
        </button>
        <div style={{"display": "flex", "alignItems": "center", "justifyContent": "center", "gap": "7px", "marginTop": "16px", "color": "#6a616b", "fontSize": "13px"}}><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#6a616b" strokeWidth="1.6" strokeLinejoin="round"><path d="M12 3l7 2.5V11c0 4.4-3 7.3-7 8.8C8 18.3 5 15.4 5 11V5.5z" /><path d="M9 11.5l2 2 4-4" /></svg>{paySecureNote}</div>
      </div>
    </div>
    </>)}
    </>
  )
}
