import * as React from 'react'
import * as NoxxVM from '@/shared/noxx/useNoxx'
import * as Motion from '@/shared/noxx/motion'

export default function CartPage() {
  const { showCart, cartClose, cartEmpty, cartItems, cartTotalFmt, cartTotalUsd, goCheckout, continueShop, payCrypto } = NoxxVM.useNoxx()
  return (
    <>
{(showCart) && (<>
    <div data-screen-label="Cart" style={{"position": "absolute", "inset": "0", "display": "flex", "flexDirection": "column"}}>
      <div style={{"flex": "none", "display": "flex", "alignItems": "center", "justifyContent": "space-between", "padding": "46px 24px 16px"}}>
        <div style={{"fontSize": "28px", "fontWeight": "700", "color": "#fff", "letterSpacing": "-.4px"}}>Your cart</div>
        <div onClick={cartClose} style={{"color": "#ff539d", "fontSize": "18px", "fontWeight": "500", "cursor": "pointer"}}>Close</div>
      </div>
      <div style={{"flex": "1", "overflowY": "auto", "padding": "6px 22px 18px"}}>
        {(cartEmpty) && (<><div style={{"textAlign": "center", "color": "#7d747f", "padding": "80px 20px", "fontSize": "16px"}}>Your cart is empty.</div></>)}
        {(cartItems||[]).map((v, _k0: number) => (<React.Fragment key={_k0}>
          <div style={{"display": "flex", "gap": "16px", "padding": "16px", "borderRadius": "22px", "background": "rgba(255,255,255,.03)", "border": "1px solid rgba(255,255,255,.06)", "marginBottom": "16px"}}>
            <div style={{"position": "relative", "width": "106px", "height": "106px", "borderRadius": "18px", "overflow": "hidden", "flex": "none"}}>
              <div style={v.bg} />
              <div style={{"position": "absolute", "inset": "0", "display": "flex", "alignItems": "center", "justifyContent": "center"}}><div style={{"width": "30px", "height": "30px", "borderRadius": "50%", "background": "rgba(18,9,14,.5)", "backdropFilter": "blur(3px)", "border": "1px solid rgba(255,255,255,.18)", "display": "flex", "alignItems": "center", "justifyContent": "center"}}><svg width="12" height="12" viewBox="0 0 24 24" fill="#fff"><path d="M8 5v14l11-7z" /></svg></div></div>
            </div>
            <div style={{"flex": "1", "minWidth": "0", "display": "flex", "flexDirection": "column", "justifyContent": "space-between", "padding": "2px 0"}}>
              <div>
                <div style={{"fontSize": "18px", "fontWeight": "600", "color": "#fff", "whiteSpace": "nowrap", "overflow": "hidden", "textOverflow": "ellipsis"}}>{v.title}</div>
                <div style={{"fontSize": "13.5px", "color": "#8c828c", "marginTop": "5px"}}>{v.tagline}</div>
              </div>
              <div style={{"display": "flex", "alignItems": "center", "justifyContent": "space-between", "gap": "10px"}}>
                <div style={{"display": "flex", "alignItems": "center", "gap": "6px"}}>{!payCrypto && (<svg width="18" height="18" viewBox="0 0 24 24" fill="#f7b23b"><path d="M12 2l2.95 5.98 6.6.96-4.78 4.66 1.13 6.57L12 17.98 6.1 20.16l1.13-6.57L2.45 8.94l6.6-.96z" /></svg>)}<span style={{"fontSize": "17px", "fontWeight": "600", "color": "#f2e9ef"}}>{payCrypto ? v.usd : v.stars}</span></div>
                <div style={{"position": "relative", "flex": "none"}}>
                  <div data-press="" onClick={v.onMenu} style={{"width": "40px", "height": "40px", "borderRadius": "12px", "display": "flex", "alignItems": "center", "justifyContent": "center", "cursor": "pointer", "border": "1px solid rgba(255,255,255,.08)", "background": "rgba(255,255,255,.05)"}}><svg width="20" height="20" viewBox="0 0 24 24" fill="#cfc7cc"><circle cx="12" cy="5" r="1.7" /><circle cx="12" cy="12" r="1.7" /><circle cx="12" cy="19" r="1.7" /></svg></div>
                  {(v.menuOpen) && (<><div ref={Motion.popInRef} onClick={v.onRemove} data-cart-remove="" style={{"position": "absolute", "right": "0", "bottom": "48px", "zIndex": "30", "display": "flex", "alignItems": "center", "gap": "9px", "padding": "11px 15px", "borderRadius": "13px", "cursor": "pointer", "whiteSpace": "nowrap", "background": "#1c0f17", "border": "1px solid rgba(255,255,255,.1)", "boxShadow": "0 16px 34px -12px rgba(0,0,0,.7)"}}><svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="#ff7a93" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M4 7h16M9 7V5a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v2M6 7l1 13a2 2 0 0 0 2 1.8h6a2 2 0 0 0 2-1.8L18 7" /></svg><span style={{"fontSize": "15px", "fontWeight": "600", "color": "#ff7a93"}}>Remove</span></div></>)}
                </div>
              </div>
            </div>
          </div>
        </React.Fragment>))}
      </div>
      <div style={{"flex": "none", "padding": "18px 22px 26px", "background": "rgba(255,255,255,.02)", "borderTop": "1px solid rgba(255,255,255,.06)"}}>
        <div style={{"display": "flex", "alignItems": "baseline", "justifyContent": "space-between", "marginBottom": "18px"}}>
          <span style={{"fontSize": "18px", "color": "#b3a9b0"}}>Total</span>
          <div><span data-total="" style={{"fontSize": "30px", "fontWeight": "700", "color": "#fff", "display": "inline-block"}}>{payCrypto ? cartTotalUsd : cartTotalFmt}</span> {!payCrypto && (<><span style={{"fontSize": "15px", "color": "#8c828c"}}>Stars</span> <span style={{"fontSize": "14px", "color": "#6a616b"}}>≈ {cartTotalUsd}</span></>)}</div>
        </div>
        <button onClick={goCheckout} style={{"width": "100%", "display": "flex", "alignItems": "center", "justifyContent": "center", "gap": "10px", "padding": "18px", "border": "none", "borderRadius": "16px", "cursor": "pointer", "fontSize": "17px", "fontWeight": "600", "color": "#fff", "background": "linear-gradient(100deg,#d6246e,#ec5690 48%,#f6a98c)", "boxShadow": "0 14px 34px -10px rgba(240,70,140,.6)", "marginBottom": "12px", "position": "relative"}}>Checkout <span style={{"position": "absolute", "right": "16px", "width": "30px", "height": "30px", "borderRadius": "50%", "background": "rgba(255,255,255,.25)", "display": "flex", "alignItems": "center", "justifyContent": "center"}}><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12h14M13 6l6 6-6 6" /></svg></span></button>
        <button onClick={continueShop} style={{"width": "100%", "display": "flex", "alignItems": "center", "justifyContent": "center", "gap": "10px", "padding": "16px", "border": "1px solid rgba(255,255,255,.09)", "borderRadius": "16px", "cursor": "pointer", "fontSize": "16px", "fontWeight": "600", "color": "#ff539d", "background": "rgba(255,255,255,.02)", "position": "relative"}}>Continue shopping <span style={{"position": "absolute", "right": "16px", "width": "30px", "height": "30px", "borderRadius": "50%", "background": "rgba(255,255,255,.05)", "display": "flex", "alignItems": "center", "justifyContent": "center"}}><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#cfc7cc" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round"><path d="M5 8h14l-1 11.2a2 2 0 0 1-2 1.8H8a2 2 0 0 1-2-1.8Z" /><path d="M8.5 8V6.5a3.5 3.5 0 0 1 7 0V8" /></svg></span></button>
        <div style={{"display": "flex", "alignItems": "center", "justifyContent": "center", "gap": "7px", "marginTop": "16px", "color": "#6a616b", "fontSize": "13px"}}><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#6a616b" strokeWidth="1.6" strokeLinejoin="round"><path d="M12 3l7 2.5V11c0 4.4-3 7.3-7 8.8C8 18.3 5 15.4 5 11V5.5z" /><path d="M9 11.5l2 2 4-4" /></svg>Secure payment via Telegram</div>
      </div>
    </div>
    </>)}
    </>
  )
}
