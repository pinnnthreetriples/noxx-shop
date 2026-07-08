import * as React from 'react'
import * as NoxxVM from '@/shared/noxx/useNoxx'
import * as Motion from '@/shared/noxx/motion'

export default function CatalogPage() {
  const { showCatalog, glowOn, goHome, catFilters, catalogVideos, goCart, hasCart, cartCount, productsLoading, productsError, retryProducts, catalogEmpty, payCrypto } = NoxxVM.useNoxx()
  const catWrapRef = React.useRef<HTMLDivElement>(null)
  const catActive = (catFilters || []).findIndex((p) => p.active)
  Motion.useIndicator(catWrapRef, '[data-cat-ind]', '[data-cat-item][data-active]', catActive, { vertical: true, ease: Motion.E.back16, duration: 500 })
  return (
    <>
{(showCatalog) && (<>
    <div data-screen-label="Catalog" style={{"position": "absolute", "inset": "0", "display": "flex", "flexDirection": "column"}}>
      {(glowOn) && (<><div style={{"position": "absolute", "bottom": "-40px", "left": "-60px", "width": "280px", "height": "280px", "background": "radial-gradient(circle,rgba(150,40,120,.18),transparent 70%)", "pointerEvents": "none"}} /></>)}
      <div style={{"flex": "none", "display": "flex", "alignItems": "center", "gap": "14px", "padding": "16px 22px 8px", "position": "relative", "zIndex": "2"}}>
        <div onClick={goHome} style={{"width": "44px", "height": "44px", "borderRadius": "50%", "background": "rgba(255,255,255,.05)", "border": "1px solid rgba(255,255,255,.08)", "display": "flex", "alignItems": "center", "justifyContent": "center", "cursor": "pointer"}}><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M19 12H5M11 18l-6-6 6-6" /></svg></div>
        <div style={{"fontSize": "27px", "fontWeight": "700", "color": "#fff", "letterSpacing": "-.4px"}}>Catalog</div>
        <div style={{"marginLeft": "auto", "position": "relative", "cursor": "pointer"}}><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#e9e2e8" strokeWidth="2" strokeLinecap="round"><path d="M4 7h16M6 12h12M9 17h6" /></svg><div style={{"position": "absolute", "top": "-2px", "right": "-2px", "width": "8px", "height": "8px", "borderRadius": "50%", "background": "#ff2e93"}} /></div>
      </div>
      <div data-cat-wrap="" ref={catWrapRef} style={{"position": "relative", "flex": "none", "display": "flex", "gap": "10px", "padding": "12px 22px 6px", "overflowX": "auto", "WebkitMaskImage": "linear-gradient(to right,#000 calc(100% - 24px),transparent)", "maskImage": "linear-gradient(to right,#000 calc(100% - 24px),transparent)"}}>
        <div data-cat-ind="" style={{"position": "absolute", "left": "0", "top": "0", "width": "0", "height": "0", "borderRadius": "21px", "background": "linear-gradient(135deg,#f060a8,#ce3d92)", "pointerEvents": "none", "zIndex": "0"}} />
        {(catFilters||[]).map((p, _k0: number) => (<React.Fragment key={_k0}><div data-cat-item="" data-active={p.active ? '' : undefined} onClick={p.onClick} style={p.style}>{p.label}</div></React.Fragment>))}
        <div style={{"flex": "none", "width": "26px"}} />
      </div>
      <div style={{"flex": "1", "overflowY": "auto", "padding": "10px 22px 184px"}}>
        {(productsLoading) && (<><div ref={Motion.loadingPulseRef} style={{"padding": "40px 0", "textAlign": "center", "color": "#8c828c", "fontSize": "14px"}}>Loading…</div></>)}
        {(productsError) && (<><div style={{"padding": "40px 0", "textAlign": "center"}}><div style={{"color": "#8c828c", "fontSize": "14px", "marginBottom": "12px"}}>Couldn't load videos</div><div onClick={retryProducts} style={{"display": "inline-flex", "padding": "9px 18px", "borderRadius": "999px", "background": "rgba(255,255,255,.06)", "border": "1px solid rgba(255,120,180,.35)", "color": "#ff8ec2", "fontSize": "14px", "fontWeight": "600", "cursor": "pointer"}}>Retry</div></div></>)}
        {(catalogEmpty) && (<><div style={{"padding": "40px 0", "textAlign": "center", "color": "#8c828c", "fontSize": "14px"}}>No videos yet</div></>)}
        {(catalogVideos||[]).map((v, _k1: number) => (<React.Fragment key={_k1}>
          <div onClick={v.onOpen} style={{"position": "relative", "display": "flex", "gap": "13px", "alignItems": "stretch", "padding": "11px", "borderRadius": "18px", "cursor": "pointer", "marginBottom": "12px", "background": "rgba(255,255,255,.025)", "border": "1px solid rgba(255,255,255,.06)", "overflow": "hidden", "transition": "background .2s ease,border-color .2s ease"}}>
            {(v.premium) && (<><div style={{"position": "absolute", "inset": "0", "background": "linear-gradient(120deg,rgba(150,45,105,.18),transparent 58%)", "pointerEvents": "none"}} /></>)}
            <div style={{"position": "relative", "width": "118px", "height": "104px", "borderRadius": "14px", "overflow": "hidden", "flex": "none"}}>
              <div style={v.bg} />
              <div style={{"position": "absolute", "inset": "0", "background": "linear-gradient(180deg,rgba(0,0,0,.18) 0%,transparent 36%,transparent 58%,rgba(0,0,0,.62))"}} />
              {(v.discount) && (<><div style={{"position": "absolute", "top": "7px", "right": "7px", "padding": "3px 8px", "borderRadius": "8px", "background": "linear-gradient(135deg,#ff5aa0,#d63d8f)", "color": "#fff", "fontSize": "11px", "fontWeight": "800", "letterSpacing": ".2px", "boxShadow": "0 4px 12px -4px rgba(214,61,143,.8)"}}>{v.discount}</div></>)}
              <div style={{"position": "absolute", "inset": "0", "display": "flex", "alignItems": "center", "justifyContent": "center"}}><div style={{"width": "40px", "height": "40px", "borderRadius": "50%", "background": "rgba(18,9,14,.46)", "backdropFilter": "blur(4px)", "border": "1px solid rgba(255,255,255,.22)", "display": "flex", "alignItems": "center", "justifyContent": "center", "boxShadow": "0 0 18px rgba(255,77,158,.3)"}}><svg width="13" height="13" viewBox="0 0 24 24" fill="#fff"><path d="M8 5v14l11-7z" /></svg></div></div>
              <div style={{"position": "absolute", "left": "7px", "bottom": "7px", "display": "flex", "alignItems": "center", "gap": "4px", "padding": "2px 7px", "borderRadius": "7px", "background": "rgba(0,0,0,.6)", "backdropFilter": "blur(3px)", "color": "#fff", "fontSize": "11px", "fontWeight": "600", "whiteSpace": "nowrap"}}><svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round"><path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7Z" /><circle cx="12" cy="12" r="3" /></svg>{v.views}</div>
            </div>
            <div style={{"flex": "1", "minWidth": "0", "position": "relative", "display": "flex", "flexDirection": "column", "padding": "2px 0"}}>
              <div style={{"display": "flex", "alignItems": "center", "gap": "10px"}}>
                <div style={{"flex": "1", "minWidth": "0", "fontSize": "16.5px", "fontWeight": "600", "color": "#fff", "letterSpacing": "-.2px", "whiteSpace": "nowrap", "overflow": "hidden", "textOverflow": "ellipsis"}}>{v.title}</div>
                <div style={{"flex": "none", "display": "flex", "alignItems": "center", "gap": "4px"}}>{!payCrypto && (<svg width="15" height="15" viewBox="0 0 24 24" fill="#f7b23b"><path d="M12 2l2.95 5.98 6.6.96-4.78 4.66 1.13 6.57L12 17.98 6.1 20.16l1.13-6.57L2.45 8.94l6.6-.96z" /></svg>)}<span style={{"fontSize": "16px", "fontWeight": "800", "color": "#fff", "letterSpacing": "-.3px"}}>{payCrypto ? v.usd : v.priceFmt}</span></div>
              </div>
              {(v.hasBadge) && (<><div style={{"display": "flex", "alignItems": "center", "gap": "7px", "marginTop": "9px", "flexWrap": "wrap"}}><div style={v.badgeStyle}>{v.badge}</div></div></>)}
              <div style={{"display": "flex", "alignItems": "center", "justifyContent": "space-between", "gap": "10px", "marginTop": "auto", "paddingTop": "10px"}}>
                <div style={{"display": "flex", "alignItems": "center", "gap": "13px", "minWidth": "0", "overflow": "hidden"}}>
                  <div style={{"display": "flex", "alignItems": "center", "gap": "5px", "color": "#9a9098", "fontSize": "12.5px", "whiteSpace": "nowrap"}}><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#9a9098" strokeWidth="1.7" strokeLinejoin="round"><path d="M5 8h14l-1 11.2a2 2 0 0 1-2 1.8H8a2 2 0 0 1-2-1.8Z" /><path d="M8.5 8V6.5a3.5 3.5 0 0 1 7 0V8" /></svg>{v.soldFmt}</div>
                </div>
                {(v.inCart) && (<><div data-press="" onClick={v.onAdd} style={{"flex": "none", "display": "flex", "alignItems": "center", "gap": "5px", "padding": "8px 13px", "borderRadius": "11px", "background": "rgba(126,224,192,.12)", "border": "1px solid rgba(126,224,192,.35)", "color": "#8fe8cc", "fontSize": "13px", "fontWeight": "600", "cursor": "default"}}>In cart<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#8fe8cc" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round"><path d="M20 6L9 17l-5-5" /></svg></div></>)}
                {(v.notInCart) && (<><div data-press="" onClick={v.onAdd} style={{"flex": "none", "display": "flex", "alignItems": "center", "gap": "5px", "padding": "8px 14px", "borderRadius": "11px", "background": "linear-gradient(135deg,#ff5aa0,#d63d8f)", "color": "#fff", "fontSize": "13px", "fontWeight": "700", "cursor": "pointer", "boxShadow": "0 6px 16px -7px rgba(214,61,143,.9)"}}><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round"><path d="M12 5v14M5 12h14" /></svg>Add</div></>)}
              </div>
            </div>
          </div>
        </React.Fragment>))}
      </div>
      <div onClick={goCart} style={{"position": "absolute", "right": "18px", "bottom": "100px", "width": "58px", "height": "58px", "borderRadius": "50%", "background": "linear-gradient(140deg,#ff5aa0,#d63d8f)", "display": "flex", "alignItems": "center", "justifyContent": "center", "cursor": "pointer", "boxShadow": "0 12px 32px -6px rgba(255,77,158,.7),0 0 0 1px rgba(255,255,255,.12)", "animation": "ringPulse 2.6s ease-out infinite", "zIndex": "6"}}>
        <svg width="25" height="25" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><circle cx="9.5" cy="20" r="1.3" /><circle cx="18" cy="20" r="1.3" /><path d="M3 4h2l2.2 11.2a1.5 1.5 0 0 0 1.5 1.2h8.4a1.5 1.5 0 0 0 1.5-1.2L21 7H6" /></svg>
        {(hasCart) && (<><div data-cart-badge="" style={{"position": "absolute", "top": "-4px", "right": "-4px", "minWidth": "22px", "height": "22px", "padding": "0 5px", "borderRadius": "11px", "background": "#ff2e93", "color": "#fff", "fontSize": "12px", "fontWeight": "700", "display": "flex", "alignItems": "center", "justifyContent": "center", "border": "2px solid #0a070c"}}>{cartCount}</div></>)}
      </div>

    </div>
    </>)}
    </>
  )
}