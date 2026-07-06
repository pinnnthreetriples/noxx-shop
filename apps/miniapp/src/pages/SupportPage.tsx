import * as React from 'react'
import * as NoxxVM from '@/shared/noxx/useNoxx'

// Backend SupportTopic enum names -> display labels
const TOPICS = [
  { value: 'payment', label: 'Payment issue' },
  { value: 'download', label: 'Download issue' },
  { value: 'other', label: 'Other' },
]

export default function SupportPage() {
  const { showSupport, backProfile, supportTopics, sendSupport, supportBusy } = NoxxVM.useNoxx()
  const [faqOpen, setFaqOpen] = React.useState(false)
  const [formOpen, setFormOpen] = React.useState(false)
  const [topic, setTopic] = React.useState('other')
  const [message, setMessage] = React.useState('')
  const [sent, setSent] = React.useState(false)
  const [err, setErr] = React.useState(false)
  const submit = async () => {
    if (!message.trim() || supportBusy) return
    setErr(false)
    try {
      await sendSupport(topic, message.trim())
      setSent(true)
      window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred?.('success')
    } catch {
      setErr(true)
    }
  }
  const rowStyle: React.CSSProperties = { display: 'flex', alignItems: 'center', gap: '15px', padding: '18px', borderRadius: '16px', background: 'rgba(255,255,255,.03)', border: '1px solid rgba(255,255,255,.06)', marginBottom: '14px', cursor: 'pointer' }
  const iconStyle: React.CSSProperties = { width: '40px', height: '40px', borderRadius: '50%', border: '1px solid rgba(255,90,160,.35)', display: 'flex', alignItems: 'center', justifyContent: 'center', flex: 'none' }
  return (
    <>
{(showSupport) && (<>
    <div data-screen-label="Support" style={{"position": "absolute", "inset": "0", "display": "flex", "flexDirection": "column"}}>
      <div style={{"flex": "none", "display": "flex", "alignItems": "center", "gap": "16px", "padding": "16px 22px 14px"}}><div onClick={backProfile} style={{"cursor": "pointer"}}><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M19 12H5M11 18l-6-6 6-6" /></svg></div><div style={{"fontSize": "23px", "fontWeight": "600", "color": "#fff"}}>Support</div></div>
      <div style={{"flex": "1", "overflowY": "auto", "padding": "14px 22px 30px"}}>
        <div style={{"fontSize": "19px", "color": "#e9e2e8", "marginBottom": "22px"}}>How can we help you?</div>

        <div onClick={() => setFaqOpen((o) => !o)} style={rowStyle}><div style={iconStyle}><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#ff8ec2" strokeWidth="1.7"><circle cx="12" cy="12" r="9" /><path d="M9.2 9.2a2.8 2.8 0 0 1 5.5.8c0 1.9-2.7 2.2-2.7 4" /><circle cx="12" cy="17" r="0.6" fill="#ff8ec2" /></svg></div><span style={{"flex": "1", "fontSize": "16px", "fontWeight": "500", "color": "#fff"}}>Frequently asked questions</span><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#6a616b" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{"transform": faqOpen ? 'rotate(90deg)' : 'none', "transition": "transform .25s"}}><path d="M9 6l6 6-6 6" /></svg></div>
        {faqOpen && (supportTopics || []).map((t, k: number) => (
          <div key={k} style={{"padding": "0 6px 18px"}}><div style={{"fontSize": "14.5px", "fontWeight": "600", "color": "#fff", "marginBottom": "5px"}}>{t.head}</div><div style={{"fontSize": "13.5px", "lineHeight": "1.55", "color": "#9a9098"}}>{t.body}</div></div>
        ))}

        {(!formOpen && !sent) && (
        <div onClick={() => setFormOpen(true)} style={{ ...rowStyle, marginBottom: 0 }}><div style={iconStyle}><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#ff8ec2" strokeWidth="1.6" strokeLinejoin="round"><path d="M4 5h16v11H8l-4 3z" /></svg></div><span style={{"flex": "1", "fontSize": "16px", "fontWeight": "500", "color": "#fff"}}>Contact support</span><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#6a616b" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M9 6l6 6-6 6" /></svg></div>
        )}

        {(formOpen && !sent) && (
        <div style={{"borderRadius": "16px", "background": "rgba(255,255,255,.03)", "border": "1px solid rgba(255,255,255,.06)", "padding": "18px"}}>
          <div style={{"display": "flex", "gap": "8px", "flexWrap": "wrap", "marginBottom": "14px"}}>
            {TOPICS.map((t) => (
              <div key={t.value} onClick={() => setTopic(t.value)} style={{"padding": "8px 14px", "borderRadius": "999px", "fontSize": "13px", "fontWeight": 600, "cursor": "pointer", "color": topic === t.value ? '#fff' : '#b7adb5', "background": topic === t.value ? 'rgba(255,90,160,.18)' : 'rgba(255,255,255,.04)', "border": '1px solid ' + (topic === t.value ? 'rgba(255,90,160,.5)' : 'rgba(255,255,255,.08)')}}>{t.label}</div>
            ))}
          </div>
          <textarea value={message} onChange={(e) => setMessage(e.target.value)} placeholder="Describe your issue…" rows={4} style={{"width": "100%", "padding": "12px 14px", "borderRadius": "12px", "border": "1px solid rgba(255,255,255,.1)", "background": "rgba(255,255,255,.04)", "color": "#fff", "fontSize": "15px", "fontFamily": "inherit", "outline": "none", "resize": "vertical"}} />
          {err && (<div style={{"marginTop": "8px", "fontSize": "13px", "color": "#ff7a93"}}>Something went wrong. Please try again.</div>)}
          <button onClick={submit} disabled={supportBusy || !message.trim()} style={{"marginTop": "12px", "width": "100%", "padding": "14px", "border": "none", "borderRadius": "14px", "cursor": "pointer", "fontSize": "16px", "fontWeight": "600", "color": "#fff", "background": "linear-gradient(100deg,#d6246e,#ec5690)", "opacity": supportBusy || !message.trim() ? 0.6 : 1}}>{supportBusy ? 'Sending…' : 'Send message'}</button>
        </div>
        )}

        {sent && (
        <div style={{"borderRadius": "16px", "background": "rgba(126,224,192,.07)", "border": "1px solid rgba(126,224,192,.3)", "padding": "18px", "display": "flex", "alignItems": "center", "gap": "11px"}}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#7ee0c0" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12.5l4 4 10-10" /></svg>
          <span style={{"fontSize": "14.5px", "fontWeight": "600", "color": "#7ee0c0"}}>Message sent — we'll reply in the bot chat</span>
        </div>
        )}

        <div style={{"display": "flex", "alignItems": "center", "justifyContent": "center", "gap": "8px", "marginTop": "40px", "color": "#6a616b", "fontSize": "13.5px"}}><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#6a616b" strokeWidth="1.7"><circle cx="12" cy="12" r="9" /><path d="M12 7.5V12l3 2" /></svg>We usually reply within 24 hours</div>
      </div>
    </div>
    </>)}
    </>
  )
}
