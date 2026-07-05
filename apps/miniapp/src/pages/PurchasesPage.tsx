import * as React from 'react'
import * as NoxxVM from '@/shared/noxx/useNoxx'
import * as Motion from '@/shared/noxx/motion'

export default function PurchasesPage() {
  const { showPurchases, glowOn, goHome, pTabs, purchaseItems, purchasesEmpty, promoVisible, explore, dismissPromo } = NoxxVM.useNoxx()
  const ptabWrapRef = React.useRef<HTMLDivElement>(null)
  const ptabActive = (pTabs || []).findIndex((t) => t.active)
  Motion.useIndicator(ptabWrapRef, '[data-ptab-ind]', '[data-ptab-item][data-active]', ptabActive, { ease: Motion.E.back16, duration: 500 })
  return (
    <>
{(showPurchases) && (<>
    <div data-screen-label="Purchases" style={{"position": "absolute", "inset": "0", "display": "flex", "flexDirection": "column"}}>
      {(glowOn) && (<><div style={{"position": "absolute", "bottom": "30px", "left": "-50px", "width": "240px", "height": "240px", "background": "radial-gradient(circle,rgba(220,50,140,.16),transparent 70%)", "pointerEvents": "none"}} /></>)}
      <div style={{"flex": "none", "display": "flex", "alignItems": "center", "justifyContent": "space-between", "padding": "50px 22px 14px"}}>
        <div onClick={goHome} style={{"width": "44px", "height": "44px", "borderRadius": "50%", "background": "rgba(255,255,255,.05)", "border": "1px solid rgba(255,255,255,.08)", "display": "flex", "alignItems": "center", "justifyContent": "center", "cursor": "pointer"}}><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M19 12H5M11 18l-6-6 6-6" /></svg></div>
        <div style={{"fontSize": "23px", "fontWeight": "600", "color": "#fff"}}>My purchases</div>
        <div style={{"cursor": "pointer"}}><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#e9e2e8" strokeWidth="2" strokeLinecap="round"><path d="M4 7h16M7 12h10M10 17h4" /></svg></div>
      </div>
      <div data-ptab-wrap="" ref={ptabWrapRef} style={{"position": "relative", "flex": "none", "display": "flex", "gap": "6px", "margin": "8px 22px 6px", "padding": "5px", "borderRadius": "16px", "background": "rgba(255,255,255,.05)"}}>
        <div data-ptab-ind="" style={{"position": "absolute", "top": "5px", "bottom": "5px", "left": "0", "width": "0", "borderRadius": "12px", "background": "linear-gradient(135deg,#f060a8,#ce3d92)", "boxShadow": "0 6px 16px -6px rgba(240,70,160,.7)", "pointerEvents": "none", "zIndex": "0"}} />
        {(pTabs||[]).map((t, _k0: number) => (<React.Fragment key={_k0}><div data-ptab-item="" data-active={t.active ? '' : undefined} onClick={t.onClick} style={t.style}>{t.label}</div></React.Fragment>))}
      </div>
      <div style={{"flex": "1", "overflowY": "auto", "padding": "12px 22px 100px"}}>
        {(purchasesEmpty) && (<><div style={{"padding": "34px 0", "textAlign": "center", "color": "#8c828c", "fontSize": "14px"}}>No videos yet</div></>)}
        {(purchaseItems||[]).map((v, _k1: number) => (<React.Fragment key={_k1}>
          <div style={{"display": "flex", "alignItems": "center", "gap": "15px", "padding": "13px", "borderRadius": "18px", "background": "rgba(255,255,255,.03)", "border": "1px solid rgba(255,255,255,.06)", "marginBottom": "14px"}}>
            <div onClick={v.onOpen} style={{"position": "relative", "width": "108px", "height": "74px", "borderRadius": "13px", "overflow": "hidden", "flex": "none", "cursor": "pointer"}}>
              <div style={v.bg} />
              <div style={{"position": "absolute", "inset": "0", "display": "flex", "alignItems": "center", "justifyContent": "center"}}><div style={{"width": "38px", "height": "38px", "borderRadius": "50%", "background": "rgba(18,9,14,.5)", "backdropFilter": "blur(4px)", "border": "1px solid rgba(255,255,255,.18)", "display": "flex", "alignItems": "center", "justifyContent": "center"}}><svg width="13" height="13" viewBox="0 0 24 24" fill="#fff"><path d="M8 5v14l11-7z" /></svg></div></div>
            </div>
            <div style={{"flex": "1", "minWidth": "0"}}>
              <div style={{"display": "flex", "alignItems": "flex-start", "justifyContent": "space-between"}}><div style={{"fontSize": "17px", "fontWeight": "600", "color": "#fff"}}>{v.title}</div><svg width="20" height="20" viewBox="0 0 24 24" fill="#8c828c" style={{"flex": "none"}}><circle cx="12" cy="5" r="1.6" /><circle cx="12" cy="12" r="1.6" /><circle cx="12" cy="19" r="1.6" /></svg></div>
              <div style={{"fontSize": "13px", "color": "#8c828c", "margin": "4px 0 12px"}}>{v.tagline}</div>
              <div style={{"display": "flex", "alignItems": "center", "gap": "7px"}}>
                <span style={v.statusStyle}>{v.status}</span>
                {(v.downloaded) && (<><svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="#ff539d" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="9" /><path d="M8 12.2l2.6 2.6L16 9.4" /></svg></>)}
                {(v.available) && (<><svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="#9a9098" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round"><path d="M7 16a4.5 4.5 0 0 1-.9-8.9A6 6 0 0 1 18 8a4 4 0 0 1-.5 8" /><path d="M12 11v7M9 15l3 3 3-3" /></svg></>)}
              </div>
            </div>
          </div>
        </React.Fragment>))}
        {(promoVisible) && (<>
        <div style={{"position": "relative", "padding": "18px", "borderRadius": "18px", "marginTop": "6px", "border": "1px solid rgba(255,90,170,.3)", "background": "linear-gradient(120deg,rgba(150,40,110,.3),rgba(60,28,60,.2))", "overflow": "hidden"}}>
          <div style={{"position": "absolute", "left": "30px", "top": "28px", "width": "60px", "height": "60px", "borderRadius": "50%", "background": "radial-gradient(circle,rgba(255,90,170,.6),transparent 70%)", "filter": "blur(6px)"}} />
          <div style={{"position": "relative", "display": "flex", "alignItems": "center", "gap": "16px"}}>
            <div style={{"width": "50px", "height": "50px", "borderRadius": "50%", "background": "linear-gradient(140deg,#ff5aa6,#c83b9a)", "display": "flex", "alignItems": "center", "justifyContent": "center", "flex": "none", "boxShadow": "0 0 22px rgba(255,90,170,.6)"}}><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="1.5" strokeLinejoin="round"><path d="M5 4h14l3 5-10 11L2 9z" /><path d="M2 9h20M9 4 7 9l5 11 5-11-2-5" /></svg></div>
            <div style={{"flex": "1", "minWidth": "0", "paddingRight": "26px"}}><div style={{"fontSize": "16px", "fontWeight": "600", "color": "#fff"}}>Love this content?</div><div style={{"fontSize": "13px", "color": "#b3a9b0", "marginTop": "2px", "lineHeight": "1.4"}}>Check out new videos we think you will enjoy.</div></div>
          </div>
          <div data-press="" onClick={explore} style={{"position": "relative", "marginTop": "14px", "padding": "11px 16px", "borderRadius": "14px", "background": "rgba(255,255,255,.06)", "border": "1px solid rgba(255,120,180,.4)", "color": "#ff8ec2", "fontSize": "13.5px", "fontWeight": "600", "cursor": "pointer", "textAlign": "center"}}>Explore now</div>
          <div onClick={dismissPromo} style={{"position": "absolute", "top": "12px", "right": "12px", "cursor": "pointer"}}><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#b3a9b0" strokeWidth="2" strokeLinecap="round"><path d="M18 6L6 18M6 6l12 12" /></svg></div>
        </div>
        </>)}
      </div>

    </div>
    </>)}
    </>
  )
}