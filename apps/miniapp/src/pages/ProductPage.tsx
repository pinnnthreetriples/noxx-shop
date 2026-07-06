import * as React from 'react'
import * as NoxxVM from '@/shared/noxx/useNoxx'
import * as Motion from '@/shared/noxx/motion'

export default function ProductPage() {
  const { showDetail, glowOn, detail, detailUsd, detailBack, payCrypto, paySecureNote, goCart, goPurchases } = NoxxVM.useNoxx()
  const heroRef = React.useRef<HTMLDivElement>(null)
  const [playing, setPlaying] = React.useState(false)
  const detailId = detail && detail.id
  const detailTitle = detail && detail.title
  React.useEffect(() => { setPlaying(false) }, [detailId])
  const startPreview = () => { if (detail.previewUrl) setPlaying(true) }
  React.useLayoutEffect(() => {
    if (showDetail) Motion.heroIn(heroRef.current)
  }, [showDetail, detailTitle])
  return (
    <>
{(showDetail) && (<>
    <div data-screen-label="Video detail" style={{"position": "absolute", "inset": "0", "display": "flex", "flexDirection": "column"}}>
      {(glowOn) && (<><div style={{"position": "absolute", "bottom": "60px", "right": "-50px", "width": "240px", "height": "240px", "background": "radial-gradient(circle,rgba(240,70,150,.16),transparent 70%)", "pointerEvents": "none"}} /></>)}
      <div style={{"position": "absolute", "inset": "0", "overflowY": "auto"}}>
        <div style={{"position": "relative", "height": "404px", "overflow": "hidden"}}>
          <div data-detail-hero="" ref={heroRef} style={detail.bg} />
          {playing && detail.previewUrl && (
            <video key={detail.previewUrl} src={detail.previewUrl} autoPlay controls playsInline style={{"position": "absolute", "inset": "0", "width": "100%", "height": "100%", "objectFit": "contain", "background": "#000"}} />
          )}
          <div style={{"position": "absolute", "top": "0", "left": "0", "right": "0", "height": "165px", "background": "linear-gradient(180deg,rgba(0,0,0,.5),rgba(0,0,0,0))", "pointerEvents": "none"}} />
          {!playing && detail.previewUrl && (
          <div onClick={startPreview} style={{"position": "absolute", "inset": "0", "display": "flex", "alignItems": "center", "justifyContent": "center", "cursor": "pointer"}}><div style={{"width": "78px", "height": "78px", "borderRadius": "50%", "background": "rgba(20,10,16,.6)", "backdropFilter": "blur(4px)", "border": "1px solid rgba(255,255,255,.16)", "display": "flex", "alignItems": "center", "justifyContent": "center", "boxShadow": "0 0 0 6px rgba(255,77,158,.1),0 0 44px rgba(255,77,158,.5)"}}><svg width="28" height="28" viewBox="0 0 24 24" fill="#fff"><path d="M8 5v14l11-7z" /></svg></div></div>
          )}
        </div>
        <div style={{"padding": "20px 22px 26px"}}>
        <div style={{"fontSize": "30px", "fontWeight": "700", "color": "#fff", "margin": "0 0 14px", "letterSpacing": "-.6px"}}>{detail.title}</div>
        <div style={{"display": "flex", "gap": "9px", "marginBottom": "18px"}}>
          {(detail.tagObjs||[]).map((t, _k0: number) => (<React.Fragment key={_k0}><div style={t.style}>{t.label}</div></React.Fragment>))}
        </div>
        <div style={{"display": "flex", "alignItems": "center", "gap": "10px", "color": "#8c828c", "fontSize": "14px", "marginBottom": "16px"}}>
          <div style={{"display": "flex", "alignItems": "center", "gap": "6px"}}><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#8c828c" strokeWidth="1.7"><path d="M2 12s3.6-6.5 10-6.5S22 12 22 12s-3.6 6.5-10 6.5S2 12 2 12z" /><circle cx="12" cy="12" r="2.6" /></svg>{detail.viewsFull} views</div>
          
          <div style={{"display": "flex", "alignItems": "center", "gap": "6px"}}><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#8c828c" strokeWidth="1.7"><path d="M5 8h14l-1 11.2a2 2 0 0 1-2 1.8H8a2 2 0 0 1-2-1.8Z" /><path d="M8.5 8V6.5a3.5 3.5 0 0 1 7 0V8" /></svg>{detail.purchases} purchases</div>
        </div>
        <div style={{"fontSize": "16px", "lineHeight": "1.55", "color": "#b3a9b0", "marginBottom": "24px", "textWrap": "pretty"}}>{detail.desc}</div>
        <div style={{"display": "flex", "alignItems": "center", "gap": "13px", "background": "rgba(255,255,255,.04)", "border": "1px solid rgba(255,255,255,.07)", "borderRadius": "16px", "padding": "18px 20px", "marginBottom": "16px"}}>
          <svg width="32" height="32" viewBox="0 0 24 24"><defs><linearGradient id="veriStar" x1="4" y1="3" x2="20" y2="21" gradientUnits="userSpaceOnUse"><stop offset="0" stopColor="#ffe9f5" /><stop offset=".5" stopColor="#ff6ab2" /><stop offset="1" stopColor="#c25fd6" /></linearGradient></defs><path fill="url(#veriStar)" d="M12 2l2.95 5.98 6.6.96-4.78 4.66 1.13 6.57L12 17.98 6.1 20.16l1.13-6.57L2.45 8.94l6.6-.96z" /></svg>
          <span style={{"fontSize": "30px", "fontWeight": "700", "color": "#fff"}}>{payCrypto ? detailUsd : detail.stars}</span>
          {!payCrypto && (<><span style={{"fontSize": "16px", "color": "#8c828c"}}>Stars</span><span style={{"fontSize": "15px", "color": "#6a616b", "marginLeft": "9px"}}>≈ {detailUsd}</span></>)}
        </div>
        {detail.owned ? (
          <button onClick={goPurchases} style={{"width": "100%", "display": "flex", "alignItems": "center", "justifyContent": "center", "gap": "10px", "padding": "18px", "border": "1px solid rgba(255,255,255,.14)", "borderRadius": "16px", "cursor": "pointer", "fontSize": "17px", "fontWeight": "600", "color": "#fff", "background": "rgba(255,255,255,.08)"}}>In My purchases <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#56dea0" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12.5l4.5 4.5L19 7" /></svg><span style={{"color": "#b7adb5", "fontWeight": 500}}>· Open</span></button>
        ) : detail.canClaim ? (
          <button onClick={detail.onClaim} disabled={detail.claimBusy} style={{"width": "100%", "display": "flex", "alignItems": "center", "justifyContent": "center", "gap": "10px", "padding": "18px", "border": "none", "borderRadius": "16px", "cursor": "pointer", "fontSize": "17px", "fontWeight": "600", "color": "#fff", "background": "linear-gradient(100deg,#d6246e,#ec5690 48%,#f6a98c)", "boxShadow": "0 14px 34px -10px rgba(240,70,140,.6)", "opacity": detail.claimBusy ? 0.7 : 1}}><img src="/crown-icon.png" alt="" style={{"width": "22px", "height": "auto"}} />{detail.claimBusy ? 'Adding…' : 'Get with Premium'}</button>
        ) : (<>
        <button onClick={detail.inCart ? goCart : detail.onAdd} style={{"width": "100%", "display": "flex", "alignItems": "center", "justifyContent": "center", "gap": "10px", "padding": "18px", "border": detail.inCart ? "1px solid rgba(255,255,255,.14)" : "none", "borderRadius": "16px", "cursor": "pointer", "fontSize": "17px", "fontWeight": "600", "color": "#fff", "background": detail.inCart ? "rgba(255,255,255,.08)" : "linear-gradient(100deg,#9d3ba8,#c54d8d)", "boxShadow": detail.inCart ? "none" : "0 12px 30px -14px rgba(190,70,165,.55)", "marginBottom": "13px"}}>{detail.inCart ? (<>In cart <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#56dea0" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12.5l4.5 4.5L19 7" /></svg><span style={{"color": "#b7adb5", "fontWeight": 500}}>· View cart</span></>) : (<>Add to cart <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M5 8h14l-1 11.2a2 2 0 0 1-2 1.8H8a2 2 0 0 1-2-1.8Z" /><path d="M8.5 8V6.5a3.5 3.5 0 0 1 7 0V8" /></svg></>)}</button>
        <button onClick={detail.onBuy} style={{"width": "100%", "display": "flex", "alignItems": "center", "justifyContent": "center", "gap": "10px", "padding": "18px", "border": "none", "borderRadius": "16px", "cursor": "pointer", "fontSize": "17px", "fontWeight": "600", "color": "#fff", "background": "linear-gradient(100deg,#d6246e,#ec5690 48%,#f6a98c)", "boxShadow": "0 14px 34px -10px rgba(240,70,140,.6)"}}>Buy now <svg width="20" height="20" viewBox="0 0 24 24" fill="#fff"><path d="M13 2 4 14h6l-1 8 10-12h-7z" /></svg></button>
        </>)}
        <div style={{"display": "flex", "alignItems": "center", "justifyContent": "center", "gap": "7px", "marginTop": "18px", "color": "#6a616b", "fontSize": "13px"}}><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#6a616b" strokeWidth="1.6" strokeLinejoin="round"><path d="M12 3l7 2.5V11c0 4.4-3 7.3-7 8.8C8 18.3 5 15.4 5 11V5.5z" /><path d="M9 11.5l2 2 4-4" /></svg>{paySecureNote}</div>
        </div>
      </div>
      <div style={{"position": "absolute", "top": "0", "left": "0", "right": "0", "display": "flex", "alignItems": "center", "justifyContent": "space-between", "padding": "16px 20px 12px", "zIndex": "5"}}>
        <div onClick={detailBack} style={{"cursor": "pointer", "width": "40px", "height": "40px", "borderRadius": "50%", "background": "rgba(18,10,16,.42)", "backdropFilter": "blur(6px)", "border": "1px solid rgba(255,255,255,.1)", "display": "flex", "alignItems": "center", "justifyContent": "center"}}><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M19 12H5M11 18l-6-6 6-6" /></svg></div>
        <div style={{"display": "flex", "alignItems": "center", "gap": "12px"}}>
          <div onClick={(e) => { Motion.heartPop(e.currentTarget); detail.onFav() }} style={{"cursor": "pointer", "width": "40px", "height": "40px", "borderRadius": "50%", "background": "rgba(18,10,16,.42)", "backdropFilter": "blur(6px)", "border": "1px solid rgba(255,255,255,.1)", "display": "flex", "alignItems": "center", "justifyContent": "center"}}><svg width="22" height="22" viewBox="0 0 24 24" fill={detail.heartFill} stroke={detail.heartStroke} strokeWidth="1.8"><path d="M12 20.5C7 17 3.5 13.8 3.5 9.6 3.5 6.9 5.6 5 8 5c1.6 0 3 .9 4 2.3C13 5.9 14.4 5 16 5c2.4 0 4.5 1.9 4.5 4.6 0 4.2-3.5 7.4-8.5 10.9z" /></svg></div>
          {detail.previewUrl && (<div data-press="" onClick={startPreview} style={{"padding": "9px 16px", "borderRadius": "13px", "background": "rgba(18,10,16,.5)", "backdropFilter": "blur(6px)", "border": "1px solid rgba(255,255,255,.14)", "color": "#fff", "fontSize": "13px", "fontWeight": "600", "cursor": "pointer"}}>Preview</div>)}
        </div>
      </div>
    </div>
    </>)}
    </>
  )
}