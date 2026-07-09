import * as React from 'react'
import * as NoxxVM from '@/shared/noxx/useNoxx'
import * as Motion from '@/shared/noxx/motion'

export default function HomePage() {
  const { showHome, glowOn, search, seeAll, offerCountdown, homeVideos, goSubscription, goCart, hasCart, cartCount, productsLoading, productsError, retryProducts, homeEmpty, payCrypto } = NoxxVM.useNoxx()
  return (
    <>
{(showHome) && (<>
    <div data-screen-label="Home" style={{"position": "absolute", "inset": "0", "display": "flex", "flexDirection": "column"}}>
      {(glowOn) && (<><div style={{"position": "absolute", "top": "-90px", "right": "-70px", "width": "320px", "height": "320px", "background": "radial-gradient(circle,rgba(240,70,150,.16),transparent 70%)", "pointerEvents": "none"}} /></>)}
      <div style={{"flex": "none", "display": "flex", "alignItems": "center", "justifyContent": "space-between", "padding": "16px 22px 12px", "position": "relative", "zIndex": "2"}}>
        <div style={{"fontFamily": "'Playfair Display',Georgia,serif", "fontStyle": "italic", "fontWeight": "800", "fontSize": "31px", "lineHeight": "1", "color": "#ff4d9e", "letterSpacing": ".3px", "textShadow": "0 2px 16px rgba(255,77,158,.5)"}}>NoxX</div>
        <div onClick={search} style={{"width": "42px", "height": "42px", "borderRadius": "50%", "background": "rgba(255,255,255,.05)", "border": "1px solid rgba(255,255,255,.08)", "display": "flex", "alignItems": "center", "justifyContent": "center", "cursor": "pointer"}}><svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="#e9e2e8" strokeWidth="2" strokeLinecap="round"><circle cx="11" cy="11" r="7" /><path d="M21 21l-4.2-4.2" /></svg></div>
      </div>
      <div style={{"flex": "1", "overflowY": "auto", "padding": "6px 22px 184px", "position": "relative", "zIndex": "1"}}>
        <div data-press="" onClick={seeAll} style={{"position": "relative", "borderRadius": "22px", "overflow": "hidden", "minHeight": "186px", "cursor": "pointer", "background": "url(\"/offer-bg.webp\") center / cover no-repeat"}}>
          <div style={{"position": "relative", "padding": "22px"}}>
            <div style={{"display": "inline-flex", "alignItems": "center", "padding": "5px 12px", "borderRadius": "999px", "background": "rgba(255,255,255,.55)", "border": "1px solid rgba(176,21,86,.4)", "backdropFilter": "blur(4px)", "fontSize": "10.5px", "fontWeight": "700", "letterSpacing": ".8px", "color": "#a8164f", "maxWidth": "calc(100% - 108px)", "whiteSpace": "normal", "lineHeight": "1.25"}}>WELCOME OFFER</div>
            <div style={{"fontSize": "54px", "fontWeight": "900", "color": "#9c1450", "lineHeight": "1", "letterSpacing": "-1.5px", "marginTop": "14px", "textShadow": "0 1px 2px rgba(255,255,255,.45)"}}>−10%</div>
            <div style={{"fontSize": "14px", "fontWeight": "600", "color": "#7a2a48", "marginTop": "6px", "letterSpacing": ".2px"}}>off your first video</div>
            <div style={{"display": "flex", "alignItems": "center", "gap": "11px", "marginTop": "18px"}}>
              <div style={{"display": "inline-flex", "alignItems": "center", "gap": "8px", "padding": "12px 20px", "borderRadius": "13px", "background": "linear-gradient(100deg,#d6246e,#ec5690 55%,#f6a98c)", "color": "#fff", "fontSize": "15px", "fontWeight": "700", "boxShadow": "0 12px 26px -10px rgba(240,70,140,.7)"}}>Claim now <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12h14M13 6l6 6-6 6" /></svg></div>
            </div>
          </div>
          <div style={{"position": "absolute", "top": "18px", "right": "18px", "zIndex": "2", "display": "inline-flex", "alignItems": "center", "gap": "6px", "padding": "8px 12px", "borderRadius": "11px", "background": "rgba(255,255,255,.62)", "backdropFilter": "blur(4px)", "border": "1px solid rgba(176,21,86,.35)"}}>
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#c41e6f" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="9" /><path d="M12 7.5V12l3 2" /></svg>
            <span style={{"fontSize": "12.5px", "fontWeight": "600", "color": "#a8164f", "fontVariantNumeric": "tabular-nums"}}>{offerCountdown}</span>
          </div>
        </div>
        <div style={{"display": "flex", "alignItems": "center", "justifyContent": "space-between", "margin": "30px 2px 14px"}}>
          <div style={{"fontSize": "22px", "fontWeight": "700", "color": "#fff", "letterSpacing": "-.4px"}}>New videos</div>
          <div onClick={seeAll} style={{"display": "flex", "alignItems": "center", "gap": "5px", "color": "#ff539d", "fontSize": "14.5px", "fontWeight": "500", "cursor": "pointer"}}>See all <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#ff539d" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round"><path d="M9 6l6 6-6 6" /></svg></div>
        </div>
        {(productsLoading) && (<><div ref={Motion.loadingPulseRef} style={{"padding": "28px 0", "textAlign": "center", "color": "#8c828c", "fontSize": "14px"}}>Loading…</div></>)}
        {(productsError) && (<><div style={{"padding": "28px 0", "textAlign": "center"}}><div style={{"color": "#8c828c", "fontSize": "14px", "marginBottom": "12px"}}>Couldn't load videos</div><div onClick={retryProducts} style={{"display": "inline-flex", "padding": "9px 18px", "borderRadius": "999px", "background": "rgba(255,255,255,.06)", "border": "1px solid rgba(255,120,180,.35)", "color": "#ff8ec2", "fontSize": "14px", "fontWeight": "600", "cursor": "pointer"}}>Retry</div></div></>)}
        {(homeEmpty) && (<><div style={{"padding": "28px 0", "textAlign": "center", "color": "#8c828c", "fontSize": "14px"}}>No videos yet</div></>)}
        {(homeVideos||[]).map((v, _k0: number) => (<React.Fragment key={_k0}>
          <div onClick={v.onOpen} style={{"display": "flex", "gap": "14px", "alignItems": "center", "padding": "12px", "borderRadius": "18px", "cursor": "pointer", "marginBottom": "12px", "background": "rgba(255,255,255,.025)", "border": "1px solid rgba(255,255,255,.1)"}}>
            <div style={{"position": "relative", "width": "118px", "height": "84px", "borderRadius": "14px", "overflow": "hidden", "flex": "none"}}>
              <div style={v.bg} />
              {(v.duration) && (<><div style={{"position": "absolute", "top": "7px", "right": "8px", "padding": "2px 7px", "borderRadius": "7px", "background": "rgba(0,0,0,.55)", "color": "#fff", "fontSize": "11px", "fontWeight": "500", "backdropFilter": "blur(3px)"}}>{v.duration}</div></>)}
              <div style={{"position": "absolute", "inset": "0", "display": "flex", "alignItems": "center", "justifyContent": "center"}}><div style={{"width": "30px", "height": "30px", "borderRadius": "50%", "background": "rgba(18,9,14,.5)", "backdropFilter": "blur(4px)", "border": "1px solid rgba(255,255,255,.18)", "display": "flex", "alignItems": "center", "justifyContent": "center", "boxShadow": "0 0 14px rgba(255,77,158,.3)"}}><svg width="11" height="11" viewBox="0 0 24 24" fill="#fff"><path d="M8 5v14l11-7z" /></svg></div></div>
            </div>
            <div style={{"flex": "1", "minWidth": "0"}}>
              <div style={{"fontSize": "17px", "fontWeight": "600", "color": "#fff", "letterSpacing": "-.2px"}}>{v.title}</div>
              {(v.hasBadge) && (<><div style={{"display": "flex", "alignItems": "center", "gap": "7px", "marginTop": "4px", "flexWrap": "wrap"}}><div style={v.badgeStyle}>{v.badge}</div></div></>)}
              <div style={{"display": "flex", "alignItems": "center", "gap": "12px", "marginTop": "8px"}}>
                <div style={{"display": "flex", "alignItems": "center", "gap": "4px", "color": "#8c828c", "fontSize": "12.5px"}}><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#8c828c" strokeWidth="1.7" strokeLinejoin="round"><path d="M5 8h14l-1 11.2a2 2 0 0 1-2 1.8H8a2 2 0 0 1-2-1.8Z" /><path d="M8.5 8V6.5a3.5 3.5 0 0 1 7 0V8" /></svg>{v.purchases}</div>
                <div style={{"display": "flex", "alignItems": "center", "gap": "4px", "color": "#8c828c", "fontSize": "12.5px"}}><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#8c828c" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round"><path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7Z" /><circle cx="12" cy="12" r="3" /></svg>{v.views}</div>
                <div style={{"display": "flex", "alignItems": "center", "gap": "4px", "marginLeft": "auto"}}>{!payCrypto && (<svg width="16" height="16" viewBox="0 0 24 24" fill="#f7b23b"><path d="M12 2l2.95 5.98 6.6.96-4.78 4.66 1.13 6.57L12 17.98 6.1 20.16l1.13-6.57L2.45 8.94l6.6-.96z" /></svg>)}<span style={{"fontSize": "15px", "fontWeight": "600", "color": "#f2e9ef"}}>{payCrypto ? v.usd : v.stars}</span></div>
              </div>
            </div>
          </div>
        </React.Fragment>))}
        {((homeVideos||[]).length > 0) && (<><div data-press="" onClick={seeAll} style={{"display": "flex", "alignItems": "center", "justifyContent": "center", "gap": "6px", "marginTop": "2px", "padding": "14px", "borderRadius": "16px", "background": "rgba(255,255,255,.04)", "border": "1px solid rgba(255,120,180,.35)", "color": "#ff8ec2", "fontSize": "15px", "fontWeight": "600", "cursor": "pointer"}}>All videos <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#ff8ec2" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round"><path d="M9 6l6 6-6 6" /></svg></div></>)}
        <div data-press="" onClick={goSubscription} style={{"position": "relative", "borderRadius": "22px", "overflow": "hidden", "padding": "22px", "marginTop": "18px", "minHeight": "120px", "cursor": "pointer", "border": "1px solid rgba(255,80,160,.22)", "background": "#241019"}}>
          <div style={{"position": "absolute", "inset": "-26px", "background": "url(\"/premium-bg.webp\") center / cover no-repeat", "filter": "blur(9px)"}} />
          <div style={{"position": "absolute", "inset": "0", "background": "linear-gradient(90deg,rgba(20,8,14,.82),rgba(20,8,14,.4) 55%,rgba(20,8,14,.08))"}} />
          <div style={{"position": "absolute", "right": "-10px", "top": "-10px", "width": "170px", "height": "150px", "background": "radial-gradient(circle at 60% 45%,rgba(255,120,170,.4),transparent 65%)", "filter": "blur(8px)"}} />
          <div style={{"position": "relative", "maxWidth": "62%"}}>
            <div style={{"fontSize": "22px", "fontWeight": "700", "color": "#fff"}}>Premium</div>
            <div style={{"fontSize": "14px", "color": "rgba(255,255,255,.72)", "marginTop": "3px"}}>Exclusive content.</div>
            <div style={{"display": "inline-flex", "marginTop": "16px", "padding": "9px 18px", "borderRadius": "20px", "background": "rgba(255,255,255,.06)", "border": "1px solid rgba(255,120,180,.35)", "color": "#ff8ec2", "fontSize": "14px", "fontWeight": "600"}}>Learn more</div>
          </div>
          <div style={{"position": "absolute", "right": "34px", "top": "50%", "transform": "translateY(-50%)", "width": "84px", "height": "84px", "borderRadius": "50%", "background": "radial-gradient(circle at 38% 32%,#ff6ab2,#b23a86)", "display": "flex", "alignItems": "center", "justifyContent": "center", "boxShadow": "0 0 34px rgba(255,90,170,.6)"}}><img src="/crown-icon.png" alt="Premium" style={{"width": "54px", "height": "auto", "display": "block", "filter": "drop-shadow(0 0 10px rgba(255,90,170,.7))"}} /></div>
        </div>
      </div>
      <div onClick={goCart} style={{"position": "absolute", "right": "18px", "bottom": "106px", "width": "58px", "height": "58px", "borderRadius": "50%", "background": "linear-gradient(140deg,#ff5aa0,#d63d8f)", "display": "flex", "alignItems": "center", "justifyContent": "center", "cursor": "pointer", "boxShadow": "0 12px 32px -6px rgba(255,77,158,.7),0 0 0 1px rgba(255,255,255,.12)", "zIndex": "6", "animation": "ringPulse 2.6s ease-out infinite"}}>
        <svg width="25" height="25" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><circle cx="9.5" cy="20" r="1.3" /><circle cx="18" cy="20" r="1.3" /><path d="M3 4h2l2.2 11.2a1.5 1.5 0 0 0 1.5 1.2h8.4a1.5 1.5 0 0 0 1.5-1.2L21 7H6" /></svg>
        {(hasCart) && (<><div data-cart-badge="" style={{"position": "absolute", "top": "-4px", "right": "-4px", "minWidth": "22px", "height": "22px", "padding": "0 5px", "borderRadius": "11px", "background": "#ff2e93", "color": "#fff", "fontSize": "12px", "fontWeight": "700", "display": "flex", "alignItems": "center", "justifyContent": "center", "border": "2px solid #0a070c"}}>{cartCount}</div></>)}
      </div>

    </div>
    </>)}
    </>
  )
}