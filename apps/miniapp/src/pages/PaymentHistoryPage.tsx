import * as React from 'react'
import * as NoxxVM from '@/shared/noxx/useNoxx'

const STAR = (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="#f7b23b" style={{"verticalAlign": "-2px"}}><path d="M12 2l2.95 5.98 6.6.96-4.78 4.66 1.13 6.57L12 17.98 6.1 20.16l1.13-6.57L2.45 8.94l6.6-.96z" /></svg>
)

export default function PaymentHistoryPage() {
  const { showPayments, backProfile, payHistory, payTotalStars, payTotalUsd, paymentsLoading, paymentsEmpty, payCrypto } = NoxxVM.useNoxx()
  return (
    <>
{(showPayments) && (<>
    <div data-screen-label="Payment history" style={{"position": "absolute", "inset": "0", "display": "flex", "flexDirection": "column"}}>
      <div style={{"flex": "none", "display": "flex", "alignItems": "center", "gap": "16px", "padding": "16px 22px 14px"}}><div onClick={backProfile} style={{"cursor": "pointer"}}><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M19 12H5M11 18l-6-6 6-6" /></svg></div><div style={{"fontSize": "23px", "fontWeight": "600", "color": "#fff"}}>Payment history</div></div>
      <div style={{"flex": "1", "overflowY": "auto", "padding": "8px 22px 30px"}}>
        <div style={{"display": "flex", "alignItems": "center", "justifyContent": "space-between", "borderRadius": "18px", "padding": "18px 20px", "marginBottom": "22px", "background": "linear-gradient(120deg,#241019,#160a11)", "border": "1px solid rgba(255,90,160,.22)"}}>
          <div><div style={{"fontSize": "13px", "color": "rgba(255,255,255,.6)"}}>Total spent</div><div style={{"fontSize": "24px", "fontWeight": "700", "color": "#fff", "marginTop": "3px"}}>{payCrypto ? payTotalUsd : (<>{payTotalStars} {STAR}</>)}</div></div>
          {!payCrypto && (<div style={{"textAlign": "right"}}><div style={{"fontSize": "13px", "color": "rgba(255,255,255,.6)"}}>Approx.</div><div style={{"fontSize": "18px", "fontWeight": "600", "color": "#ff8ec2", "marginTop": "4px"}}>≈ {payTotalUsd}</div></div>)}
        </div>
        {(paymentsLoading) && (<><div style={{"padding": "30px 0", "textAlign": "center", "color": "#8c828c", "fontSize": "14px"}}>Loading…</div></>)}
        {(paymentsEmpty) && (<><div style={{"padding": "30px 0", "textAlign": "center", "color": "#8c828c", "fontSize": "14px"}}>No payments yet</div></>)}
        {(payHistory||[]).map((g, _k0: number) => (<React.Fragment key={_k0}>
        <div style={{"fontSize": "12.5px", "fontWeight": "600", "color": "#8c828c", "letterSpacing": ".5px", "margin": (_k0 === 0 ? "4px 2px 8px" : "20px 2px 8px")}}>{g.label}</div>
        {(g.items||[]).map((p, _k1: number) => (<React.Fragment key={_k1}>
        <div style={{"display": "flex", "alignItems": "center", "gap": "14px", "padding": "14px 0", "borderBottom": "1px solid rgba(255,255,255,.05)"}}>
          <div style={{"width": "42px", "height": "42px", "borderRadius": "12px", "background": "rgba(255,90,160,.1)", "border": "1px solid rgba(255,90,160,.22)", "display": "flex", "alignItems": "center", "justifyContent": "center", "flex": "none"}}><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#ff8ec2" strokeWidth="1.7" strokeLinejoin="round"><rect x="2.5" y="5" width="19" height="14" rx="2.5" /><path d="M2.5 9.5h19" /></svg></div>
          <div style={{"flex": "1", "minWidth": "0"}}><div style={{"fontSize": "16px", "fontWeight": "600", "color": "#fff", "whiteSpace": "nowrap", "overflow": "hidden", "textOverflow": "ellipsis"}}>{p.title}</div><div style={{"fontSize": "13px", "color": "#8c828c", "marginTop": "2px"}}>{p.date} · <span style={{"color": p.statusColor}}>{p.statusLabel}</span></div></div>
          <div style={{"textAlign": "right"}}><div style={{"fontSize": "16px", "fontWeight": "700", "color": "#fff"}}>{payCrypto ? p.usd : (<>{p.stars} {STAR}</>)}</div>{!payCrypto && (<div style={{"fontSize": "12px", "color": "#8c828c"}}>≈ {p.usd}</div>)}</div>
        </div>
        </React.Fragment>))}
        </React.Fragment>))}
      </div>
    </div>
    </>)}
    </>
  )
}
