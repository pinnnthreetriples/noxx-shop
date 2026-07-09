import * as React from 'react'
import { useTranslation } from 'react-i18next'
import * as NoxxVM from '@/shared/noxx/useNoxx'
import type { SupportTicket } from '@/shared/noxx/useNoxx'

// Form topic chips: value sent to the backend -> i18n key
const TOPICS = [
  { value: 'payment', key: 'supportTopicPayment' },
  { value: 'download', key: 'supportTopicDownload' },
  { value: 'other', key: 'supportTopicOther' },
]
// A ticket's topic arrives as the backend enum value ("Payment issue") -> i18n key
const TOPIC_KEY: Record<string, string> = {
  'Payment issue': 'supportTopicPayment',
  'Download issue': 'supportTopicDownload',
  Other: 'supportTopicOther',
}

const STATUS_STYLE: Record<string, { key: string; color: string }> = {
  open: { key: 'supportStatusOpen', color: '#ff8ec2' },
  answered: { key: 'supportStatusAnswered', color: '#7ee0c0' },
  closed: { key: 'supportStatusClosed', color: '#9a9098' },
}

const fmtTime = (iso: string, locale?: string) =>
  new Date(iso).toLocaleString(locale || undefined, { month: 'short', day: '2-digit', hour: '2-digit', minute: '2-digit' })

export default function SupportPage() {
  const { t, i18n } = useTranslation()
  const {
    showSupport, backProfile, supportTopics, sendSupport, supportBusy,
    supportTickets, supportLoading, supportError, replySupport, replyBusy,
  } = NoxxVM.useNoxx()
  const [faqOpen, setFaqOpen] = React.useState(false)
  const [formOpen, setFormOpen] = React.useState(false)
  const [topic, setTopic] = React.useState('other')
  const [message, setMessage] = React.useState('')
  const [err, setErr] = React.useState(false)
  const [openId, setOpenId] = React.useState<number | null>(null)
  const [replyText, setReplyText] = React.useState('')
  const [replyErr, setReplyErr] = React.useState(false)

  const submit = async () => {
    if (!message.trim() || supportBusy) return
    setErr(false)
    try {
      const created = await sendSupport(topic, message.trim())
      setMessage('')
      setFormOpen(false)
      // Reveal the freshly-created thread so the user sees their message landed —
      // otherwise the form just collapses and it's unclear whether it sent.
      if (created?.id) setOpenId(created.id)
      window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred?.('success')
    } catch {
      setErr(true)
    }
  }

  const toggleTicket = (id: number) => {
    setOpenId((cur) => (cur === id ? null : id))
    setReplyText('')
    setReplyErr(false)
  }

  const sendReply = async (id: number) => {
    const text = replyText.trim()
    if (!text || replyBusy) return
    setReplyErr(false)
    try {
      await replySupport(id, text)
      setReplyText('')
      window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred?.('success')
    } catch {
      setReplyErr(true)
    }
  }

  const rowStyle: React.CSSProperties = { display: 'flex', alignItems: 'center', gap: '15px', padding: '18px', borderRadius: '16px', background: 'rgba(255,255,255,.03)', border: '1px solid rgba(255,255,255,.06)', marginBottom: '14px', cursor: 'pointer' }
  const iconStyle: React.CSSProperties = { width: '40px', height: '40px', borderRadius: '50%', border: '1px solid rgba(255,90,160,.35)', display: 'flex', alignItems: 'center', justifyContent: 'center', flex: 'none' }
  const bubbleBase: React.CSSProperties = { maxWidth: '82%', padding: '9px 13px', borderRadius: '14px', fontSize: '14px', lineHeight: '1.45', wordBreak: 'break-word' }

  return (
    <>
{(showSupport) && (<>
    <div data-screen-label="Support" style={{"position": "absolute", "inset": "0", "display": "flex", "flexDirection": "column"}}>
      <div style={{"flex": "none", "display": "flex", "alignItems": "center", "gap": "16px", "padding": "16px 22px 14px"}}><div onClick={backProfile} style={{"cursor": "pointer"}}><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M19 12H5M11 18l-6-6 6-6" /></svg></div><div style={{"fontSize": "23px", "fontWeight": "600", "color": "#fff"}}>{t('support')}</div></div>
      <div style={{"flex": "1", "overflowY": "auto", "padding": "14px 22px 30px"}}>
        <div style={{"fontSize": "19px", "color": "#e9e2e8", "marginBottom": "22px"}}>{t('supportHowCanWeHelp')}</div>

        <div onClick={() => setFaqOpen((o) => !o)} style={rowStyle}><div style={iconStyle}><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#ff8ec2" strokeWidth="1.7"><circle cx="12" cy="12" r="9" /><path d="M9.2 9.2a2.8 2.8 0 0 1 5.5.8c0 1.9-2.7 2.2-2.7 4" /><circle cx="12" cy="17" r="0.6" fill="#ff8ec2" /></svg></div><span style={{"flex": "1", "fontSize": "16px", "fontWeight": "500", "color": "#fff"}}>{t('supportFaq')}</span><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#6a616b" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{"transform": faqOpen ? 'rotate(90deg)' : 'none', "transition": "transform .25s"}}><path d="M9 6l6 6-6 6" /></svg></div>
        {faqOpen && (supportTopics || []).map((t2, k: number) => (
          <div key={k} style={{"padding": "0 6px 18px"}}><div style={{"fontSize": "14.5px", "fontWeight": "600", "color": "#fff", "marginBottom": "5px"}}>{t2.head}</div><div style={{"fontSize": "13.5px", "lineHeight": "1.55", "color": "#9a9098"}}>{t2.body}</div></div>
        ))}

        {(supportLoading || supportError || supportTickets.length > 0) && (
        <div style={{"margin": "8px 2px 12px", "fontSize": "13px", "fontWeight": 700, "letterSpacing": ".04em", "textTransform": "uppercase", "color": "#8c828c"}}>{t('supportConversations')}</div>
        )}
        {supportLoading && (<div style={{"padding": "18px 0", "textAlign": "center", "color": "#8c828c", "fontSize": "14px"}}>{t('supportLoading')}</div>)}
        {supportError && (<div style={{"padding": "18px 0", "textAlign": "center", "color": "#8c828c", "fontSize": "14px"}}>{t('supportLoadError')}</div>)}
        {(supportTickets as SupportTicket[]).map((tk) => {
          const st = STATUS_STYLE[tk.status] ?? { key: '', color: '#9a9098' }
          const isOpen = openId === tk.id
          return (
          <div key={tk.id} style={{"borderRadius": "16px", "background": "rgba(255,255,255,.03)", "border": "1px solid rgba(255,255,255,.06)", "marginBottom": "14px", "overflow": "hidden"}}>
            <div onClick={() => toggleTicket(tk.id)} style={{"display": "flex", "alignItems": "center", "gap": "12px", "padding": "15px 16px", "cursor": "pointer"}}>
              <div style={{"flex": "1", "minWidth": 0}}>
                <div style={{"fontSize": "15px", "fontWeight": "600", "color": "#fff", "whiteSpace": "nowrap", "overflow": "hidden", "textOverflow": "ellipsis"}}>{TOPIC_KEY[tk.topic] ? t(TOPIC_KEY[tk.topic]) : tk.topic}</div>
                <div style={{"marginTop": "3px", "fontSize": "12px", "fontWeight": 600, "color": st.color}}>{st.key ? t(st.key) : tk.status}</div>
              </div>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#6a616b" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{"flex": "none", "transform": isOpen ? 'rotate(90deg)' : 'none', "transition": "transform .25s"}}><path d="M9 6l6 6-6 6" /></svg>
            </div>
            {isOpen && (
            <div style={{"padding": "0 16px 16px"}}>
              <div style={{"display": "flex", "flexDirection": "column", "gap": "10px", "marginBottom": "14px"}}>
                {tk.messages.map((m) => {
                  const mine = m.sender_type === 'user'
                  return (
                  <div key={m.id} style={{"display": "flex", "flexDirection": "column", "alignItems": mine ? 'flex-end' : 'flex-start'}}>
                    <div style={{ ...bubbleBase, color: mine ? '#fff' : '#e9e2e8', background: mine ? 'linear-gradient(120deg,#ff5aa0,#ff2e93)' : 'rgba(255,255,255,.06)' }}>{m.text}</div>
                    <div style={{"marginTop": "4px", "fontSize": "11px", "color": "#6a616b"}}>{(mine ? t('supportYou') : t('support')) + ' · ' + fmtTime(m.created_at, i18n.language)}</div>
                  </div>
                  )
                })}
              </div>
              {tk.status !== 'closed' && (<>
              <div style={{"display": "flex", "gap": "8px", "alignItems": "flex-end"}}>
                <input value={replyText} onChange={(e) => setReplyText(e.target.value)} onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); sendReply(tk.id) } }} placeholder={t('supportReplyPlaceholder')} style={{"flex": "1", "padding": "12px 14px", "borderRadius": "12px", "border": "1px solid rgba(255,255,255,.1)", "background": "rgba(255,255,255,.04)", "color": "#fff", "fontSize": "15px", "fontFamily": "inherit", "outline": "none"}} />
                <button onClick={() => sendReply(tk.id)} disabled={replyBusy || !replyText.trim()} style={{"flex": "none", "width": "46px", "height": "46px", "border": "none", "borderRadius": "12px", "cursor": "pointer", "display": "flex", "alignItems": "center", "justifyContent": "center", "background": "linear-gradient(100deg,#d6246e,#ec5690)", "opacity": replyBusy || !replyText.trim() ? 0.5 : 1}} aria-label={t('send')}><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 2 11 13M22 2l-7 20-4-9-9-4z" /></svg></button>
              </div>
              {replyErr && (<div style={{"marginTop": "8px", "fontSize": "13px", "color": "#ff7a93"}}>{t('supportSendError')}</div>)}
              </>)}
            </div>
            )}
          </div>
          )
        })}

        {!formOpen && (
        <div onClick={() => setFormOpen(true)} style={{ ...rowStyle, marginBottom: 0 }}><div style={iconStyle}><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#ff8ec2" strokeWidth="1.6" strokeLinejoin="round"><path d="M4 5h16v11H8l-4 3z" /></svg></div><span style={{"flex": "1", "fontSize": "16px", "fontWeight": "500", "color": "#fff"}}>{t('supportContact')}</span><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#6a616b" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M9 6l6 6-6 6" /></svg></div>
        )}

        {formOpen && (
        <div style={{"borderRadius": "16px", "background": "rgba(255,255,255,.03)", "border": "1px solid rgba(255,255,255,.06)", "padding": "18px"}}>
          <div style={{"display": "flex", "gap": "8px", "flexWrap": "wrap", "marginBottom": "14px"}}>
            {TOPICS.map((tp) => (
              <div key={tp.value} onClick={() => setTopic(tp.value)} style={{"padding": "8px 14px", "borderRadius": "999px", "fontSize": "13px", "fontWeight": 600, "cursor": "pointer", "color": topic === tp.value ? '#fff' : '#b7adb5', "background": topic === tp.value ? 'rgba(255,90,160,.18)' : 'rgba(255,255,255,.04)', "border": '1px solid ' + (topic === tp.value ? 'rgba(255,90,160,.5)' : 'rgba(255,255,255,.08)')}}>{t(tp.key)}</div>
            ))}
          </div>
          <textarea value={message} onChange={(e) => setMessage(e.target.value)} placeholder={t('supportDescribePlaceholder')} rows={4} style={{"width": "100%", "padding": "12px 14px", "borderRadius": "12px", "border": "1px solid rgba(255,255,255,.1)", "background": "rgba(255,255,255,.04)", "color": "#fff", "fontSize": "15px", "fontFamily": "inherit", "outline": "none", "resize": "vertical"}} />
          {err && (<div style={{"marginTop": "8px", "fontSize": "13px", "color": "#ff7a93"}}>{t('supportSendError')}</div>)}
          <button onClick={submit} disabled={supportBusy || !message.trim()} style={{"marginTop": "12px", "width": "100%", "padding": "14px", "border": "none", "borderRadius": "14px", "cursor": "pointer", "fontSize": "16px", "fontWeight": "600", "color": "#fff", "background": "linear-gradient(100deg,#d6246e,#ec5690)", "opacity": supportBusy || !message.trim() ? 0.6 : 1}}>{supportBusy ? t('supportSending') : t('supportSendMessage')}</button>
        </div>
        )}

        <div style={{"display": "flex", "alignItems": "center", "justifyContent": "center", "gap": "8px", "marginTop": "40px", "color": "#6a616b", "fontSize": "13.5px"}}><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#6a616b" strokeWidth="1.7"><circle cx="12" cy="12" r="9" /><path d="M12 7.5V12l3 2" /></svg>{t('supportReplyWithin')}</div>
      </div>
    </div>
    </>)}
    </>
  )
}
