import * as React from 'react'
import * as NoxxVM from '@/shared/noxx/useNoxx'
import * as Motion from '@/shared/noxx/motion'

export default function FavoritesPage() {
  const { showFavorites, glowOn, search, favCount, favEmpty, favHasItems, favBundleCount, favSavePct, addAllFavs, favoriteItems, goCart, hasCart, cartCount } = NoxxVM.useNoxx()
  return (
    <>
{(showFavorites) && (<>
    <div data-screen-label="Favorites" style={{"position": "absolute", "inset": "0", "display": "flex", "flexDirection": "column"}}>
      {(glowOn) && (<><div style={{"position": "absolute", "top": "40%", "right": "-70px", "width": "260px", "height": "300px", "background": "radial-gradient(circle,rgba(220,50,140,.15),transparent 70%)", "pointerEvents": "none"}} /></>)}
      <div style={{"flex": "none", "display": "flex", "alignItems": "center", "justifyContent": "space-between", "padding": "50px 22px 6px"}}>
        <div style={{"fontFamily": "'Playfair Display',Georgia,serif", "fontStyle": "italic", "fontWeight": "800", "fontSize": "31px", "lineHeight": "1", "color": "#ff4d9e", "letterSpacing": ".3px", "textShadow": "0 2px 16px rgba(255,77,158,.5)"}}>NoxX</div>
        <div onClick={search} style={{"width": "42px", "height": "42px", "borderRadius": "50%", "background": "rgba(255,255,255,.05)", "border": "1px solid rgba(255,255,255,.08)", "display": "flex", "alignItems": "center", "justifyContent": "center", "cursor": "pointer"}}><svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="#e9e2e8" strokeWidth="2" strokeLinecap="round"><circle cx="11" cy="11" r="7" /><path d="M21 21l-4.2-4.2" /></svg></div>
      </div>
      <div style={{"flex": "none", "display": "flex", "alignItems": "center", "justifyContent": "space-between", "padding": "10px 22px 12px"}}>
        <div><div style={{"fontSize": "30px", "fontWeight": "700", "color": "#fff", "letterSpacing": "-.6px"}}>Favorites</div><div style={{"fontSize": "14px", "color": "#8c828c", "marginTop": "4px"}}>Everything you love — ready to unlock</div></div>
        <div style={{"display": "flex", "alignItems": "center", "gap": "7px", "padding": "8px 14px", "borderRadius": "18px", "background": "rgba(255,255,255,.04)", "border": "1px solid rgba(255,255,255,.08)"}}><span style={{"fontSize": "16px", "fontWeight": "600", "color": "#fff"}}>{favCount}</span><svg width="17" height="17" viewBox="0 0 24 24" fill="#ff4d9e"><path d="M12 20.5C7 17 3.5 13.8 3.5 9.6 3.5 6.9 5.6 5 8 5c1.6 0 3 .9 4 2.3C13 5.9 14.4 5 16 5c2.4 0 4.5 1.9 4.5 4.6 0 4.2-3.5 7.4-8.5 10.9z" /></svg></div>
      </div>
      <div style={{"flex": "1", "overflowY": "auto", "padding": "8px 22px 184px"}}>
        {(favEmpty) && (<><div style={{"textAlign": "center", "color": "#7d747f", "padding": "70px 24px", "fontSize": "16px", "lineHeight": "1.5"}}>No favorites yet.<br />Tap the heart on anything you love and it lands here.</div></>)}

        {(favHasItems) && (<>
        <div style={{"position": "relative", "overflow": "hidden", "borderRadius": "20px", "padding": "20px", "marginBottom": "20px", "background": "linear-gradient(120deg,#2a0f1d,#180a12)", "border": "1px solid rgba(255,90,160,.3)"}}>
          <div style={{"position": "absolute", "right": "-34px", "top": "-34px", "width": "170px", "height": "170px", "background": "radial-gradient(circle,rgba(255,90,170,.45),transparent 65%)", "filter": "blur(10px)", "pointerEvents": "none"}} />
          <div style={{"position": "relative"}}>
            {(favSavePct > 0) && (<div style={{"display": "inline-block", "padding": "4px 11px", "borderRadius": "999px", "background": "linear-gradient(135deg,#f060a8,#ce3d92)", "color": "#fff", "fontSize": "12px", "fontWeight": "700", "letterSpacing": ".3px", "boxShadow": "0 6px 16px -6px rgba(240,70,160,.7)", "marginBottom": "12px"}}>SAVE {favSavePct}%</div>)}
            <div style={{"fontSize": "21px", "fontWeight": "700", "color": "#fff", "letterSpacing": "-.3px", "lineHeight": "1.25"}}>Unlock all your favorites</div>
            <div style={{"fontSize": "14px", "color": "rgba(255,255,255,.7)", "marginTop": "6px"}}>{favBundleCount} videos you love — bundled, one tap away.</div>
            <button onClick={addAllFavs} style={{"marginTop": "18px", "width": "100%", "display": "flex", "alignItems": "center", "justifyContent": "center", "gap": "9px", "padding": "15px", "border": "none", "borderRadius": "14px", "cursor": "pointer", "fontFamily": "inherit", "fontSize": "16px", "fontWeight": "700", "color": "#fff", "background": "linear-gradient(100deg,#d6246e,#ec5690 48%,#f6a98c)", "boxShadow": "0 14px 30px -10px rgba(240,70,140,.6)"}}>Add all to cart <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12h14M13 6l6 6-6 6" /></svg></button>
          </div>
        </div>
        </>)}

        <div style={{"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "14px"}}>
          {(favoriteItems||[]).map((v, _k0: number) => (<React.Fragment key={_k0}>
            <div style={{"display": "flex", "flexDirection": "column", "borderRadius": "18px", "overflow": "hidden", "background": "rgba(255,255,255,.03)", "border": "1px solid rgba(255,255,255,.06)"}}>
              <div onClick={v.onOpen} style={{"position": "relative", "width": "100%", "height": "120px", "cursor": "pointer"}}>
                <div style={v.bg} />
                <div style={{"position": "absolute", "inset": "0", "background": "linear-gradient(180deg,transparent 45%,rgba(0,0,0,.5))"}} />
                <div onClick={(e) => { Motion.heartPop(e.currentTarget); v.onFav() }} style={{"position": "absolute", "top": "9px", "right": "9px", "width": "30px", "height": "30px", "borderRadius": "50%", "background": "rgba(18,9,14,.5)", "backdropFilter": "blur(4px)", "display": "flex", "alignItems": "center", "justifyContent": "center", "cursor": "pointer"}}><svg width="16" height="16" viewBox="0 0 24 24" fill={v.heartFill} stroke={v.heartStroke} strokeWidth="1.8"><path d="M12 20.5C7 17 3.5 13.8 3.5 9.6 3.5 6.9 5.6 5 8 5c1.6 0 3 .9 4 2.3C13 5.9 14.4 5 16 5c2.4 0 4.5 1.9 4.5 4.6 0 4.2-3.5 7.4-8.5 10.9z" /></svg></div>
                <div style={{"position": "absolute", "inset": "0", "display": "flex", "alignItems": "center", "justifyContent": "center"}}><div style={{"width": "38px", "height": "38px", "borderRadius": "50%", "background": "rgba(18,9,14,.5)", "backdropFilter": "blur(4px)", "border": "1px solid rgba(255,255,255,.18)", "display": "flex", "alignItems": "center", "justifyContent": "center"}}><svg width="13" height="13" viewBox="0 0 24 24" fill="#fff"><path d="M8 5v14l11-7z" /></svg></div></div>
                {(v.duration) && (<><div style={{"position": "absolute", "left": "9px", "bottom": "8px", "display": "flex", "alignItems": "center", "gap": "4px", "color": "#fff", "fontSize": "11.5px", "fontWeight": "500", "textShadow": "0 1px 3px rgba(0,0,0,.6)"}}><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="9" /><path d="M12 7.5V12l3 2" /></svg>{v.duration}</div></>)}
              </div>
              <div style={{"padding": "11px 12px 12px", "display": "flex", "flexDirection": "column", "flex": "1"}}>
                <div onClick={v.onOpen} style={{"fontSize": "15px", "fontWeight": "600", "color": "#fff", "cursor": "pointer", "whiteSpace": "nowrap", "overflow": "hidden", "textOverflow": "ellipsis"}}>{v.title}</div>
                {(v.cardSub) && (<div style={{"fontSize": "12.5px", "color": "#8c828c", "marginTop": "3px", "whiteSpace": "nowrap", "overflow": "hidden", "textOverflow": "ellipsis"}}>{v.cardSub}</div>)}
                {(v.hasBadge) && (<div style={{"display": "flex", "alignItems": "center", "gap": "7px", "marginTop": "6px", "flexWrap": "wrap"}}><div style={v.badgeStyle}>{v.badge}</div></div>)}
                <div data-press="" onClick={v.onAdd} style={{ ...v.addStyle, marginTop: '12px' }}>
                  {(v.notInCart) && (<><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="1.8" strokeLinejoin="round"><path d="M5 8h14l-1 11.2a2 2 0 0 1-2 1.8H8a2 2 0 0 1-2-1.8Z" /><path d="M8.5 8V6.5a3.5 3.5 0 0 1 7 0V8" /></svg></>)}
                  {(v.inCart) && (<><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#ff8ec2" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12.5l4 4 10-10" /></svg></>)}
                  {v.addLabel}
                </div>
              </div>
            </div>
          </React.Fragment>))}
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