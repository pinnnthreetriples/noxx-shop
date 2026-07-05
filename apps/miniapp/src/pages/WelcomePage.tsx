import * as NoxxVM from '@/shared/noxx/useNoxx'

export default function WelcomePage() {
  const { showWelcome, goHome } = NoxxVM.useNoxx()
  return (
    <>
{(showWelcome) && (<>
    <div data-screen-label="Welcome" style={{"position": "absolute", "inset": "0", "overflowY": "auto", "display": "flex", "flexDirection": "column", "padding": "64px 30px 36px", "background": "radial-gradient(122% 72% at 50% 12%,#531636 0%,#1d0a14 52%,#07050a 100%)"}}>
      <div style={{"position": "absolute", "top": "-70px", "right": "-60px", "width": "320px", "height": "320px", "background": "radial-gradient(circle,rgba(255,95,175,.55),transparent 68%)", "pointerEvents": "none", "filter": "blur(6px)"}} />
      <div style={{"position": "absolute", "bottom": "30px", "left": "-80px", "width": "300px", "height": "300px", "background": "radial-gradient(circle,rgba(214,61,143,.42),transparent 70%)", "pointerEvents": "none", "filter": "blur(8px)"}} />

      <div style={{"position": "relative", "textAlign": "center", "marginBottom": "28px"}}>
        <div style={{"fontSize": "13px", "fontWeight": "700", "letterSpacing": "3px", "color": "#ff8ec2", "marginBottom": "11px"}}>WELCOME TO</div>
        <div style={{"fontFamily": "'Playfair Display',Georgia,serif", "fontStyle": "italic", "fontWeight": "900", "fontSize": "72px", "lineHeight": "1", "letterSpacing": ".5px", "margin": "6px 0 0", "background": "linear-gradient(100deg,#ff7ab8,#ec5690 45%,#f6a98c)", "WebkitBackgroundClip": "text", "backgroundClip": "text", "WebkitTextFillColor": "transparent", "color": "transparent", "filter": "drop-shadow(0 6px 22px rgba(255,45,130,.4))"}}>NoxX</div>
        <div style={{"fontSize": "26px", "fontWeight": "700", "color": "#fff", "letterSpacing": "-.4px", "marginTop": "18px", "textWrap": "balance"}}>The best, all in one place.</div>
        <div style={{"fontSize": "15px", "lineHeight": "1.55", "color": "#b3a9b0", "margin": "11px auto 0", "maxWidth": "322px", "textWrap": "pretty"}}>The rarest scenes and the finest moments ever filmed — handpicked into one collection. Stop searching. It's all already here.</div>
      </div>

      <div style={{"display": "flex", "flexDirection": "column", "gap": "11px", "marginBottom": "auto"}}>
        <div data-shine="" style={{"position": "relative", "overflow": "hidden", "display": "flex", "alignItems": "center", "gap": "14px", "padding": "14px 16px", "borderRadius": "16px", "background": "rgba(255,255,255,.04)", "border": "1px solid rgba(255,255,255,.07)"}}>
          <div style={{"width": "46px", "height": "46px", "borderRadius": "13px", "flex": "none", "display": "flex", "alignItems": "center", "justifyContent": "center", "background": "linear-gradient(140deg,#ff5aa0,#d63d8f)", "boxShadow": "0 9px 22px -6px rgba(255,77,158,.7)"}}><svg width="23" height="23" viewBox="0 0 24 24" fill="#fff"><path d="M12 2l1.7 6.3L20 10l-6.3 1.7L12 18l-1.7-6.3L4 10l6.3-1.7z" /><path d="M18.5 13l.6 2.1 2.1.6-2.1.6-.6 2.1-.6-2.1-2.1-.6 2.1-.6z" /></svg></div>
          <div><div style={{"fontSize": "16px", "fontWeight": "700", "color": "#fff"}}>Only the rarest scenes</div><div style={{"fontSize": "13px", "color": "#9a9098", "marginTop": "2px"}}>Exclusive content you won't find anywhere else</div></div>
        </div>
        <div data-shine="" style={{"position": "relative", "overflow": "hidden", "display": "flex", "alignItems": "center", "gap": "14px", "padding": "14px 16px", "borderRadius": "16px", "background": "rgba(255,255,255,.04)", "border": "1px solid rgba(255,255,255,.07)"}}>
          <div style={{"width": "46px", "height": "46px", "borderRadius": "13px", "flex": "none", "display": "flex", "alignItems": "center", "justifyContent": "center", "background": "linear-gradient(140deg,#ec5690,#9d3ba8)", "boxShadow": "0 9px 22px -6px rgba(190,70,165,.65)"}}><svg width="22" height="22" viewBox="0 0 24 24" fill="#fff"><path d="M12 2l2.95 5.98 6.6.96-4.78 4.66 1.13 6.57L12 17.98 6.1 20.16l1.13-6.57L2.45 8.94l6.6-.96z" /></svg></div>
          <div><div style={{"fontSize": "16px", "fontWeight": "700", "color": "#fff"}}>The all-time best, curated</div><div style={{"fontSize": "13px", "color": "#9a9098", "marginTop": "2px"}}>Every highlight worth watching, in one place</div></div>
        </div>
        <div data-shine="" style={{"position": "relative", "overflow": "hidden", "display": "flex", "alignItems": "center", "gap": "14px", "padding": "14px 16px", "borderRadius": "16px", "background": "rgba(255,255,255,.04)", "border": "1px solid rgba(255,255,255,.07)"}}>
          <div style={{"width": "46px", "height": "46px", "borderRadius": "13px", "flex": "none", "display": "flex", "alignItems": "center", "justifyContent": "center", "background": "linear-gradient(140deg,#f6a98c,#ec5690)", "boxShadow": "0 9px 22px -6px rgba(240,120,140,.6)"}}><svg width="22" height="22" viewBox="0 0 24 24" fill="#fff"><path d="M13 2L4.5 13.5H11l-1 8.5L19.5 10H13z" /></svg></div>
          <div><div style={{"fontSize": "16px", "fontWeight": "700", "color": "#fff"}}>Zero time wasted</div><div style={{"fontSize": "13px", "color": "#9a9098", "marginTop": "2px"}}>No endless scrolling — it's all right here</div></div>
        </div>
      </div>

      <div style={{"marginTop": "26px"}}>
        <button onClick={goHome} style={{"width": "100%", "padding": "18px", "border": "none", "borderRadius": "16px", "cursor": "pointer", "fontFamily": "inherit", "fontSize": "17px", "fontWeight": "700", "color": "#fff", "background": "linear-gradient(100deg,#d6246e,#ec5690 48%,#f6a98c)", "boxShadow": "0 16px 38px -10px rgba(240,70,140,.6)", "display": "flex", "alignItems": "center", "justifyContent": "center", "gap": "9px"}} data-cta-nudge="">Start watching <svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" data-cta-arrow=""><path d="M5 12h14M13 6l6 6-6 6" /></svg></button>
        <div style={{"textAlign": "center", "fontSize": "13px", "color": "#8c828c", "marginTop": "14px"}}>New scenes added every week</div>
      </div>
    </div>
    </>)}
    </>
  )
}
