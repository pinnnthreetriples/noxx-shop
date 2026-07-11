import * as React from 'react'
import * as RR from 'react-router-dom'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import api from '../shared/api/client'
import * as Motion from '../shared/noxx/motion'

interface Coin { code: string; ticker: string; name: string; network: string; color: string }
interface PayState {
  order_id: number
  status: string
  paid: boolean
  amount_usd: number
  pay_currency?: string | null
  pay_amount?: string | null
  address?: string | null
  qr?: string | null
  expires_at?: number | null
  coins: Coin[]
}

const notify = (t: 'error' | 'success' | 'warning') =>
  window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred?.(t)
const tap = () => window.Telegram?.WebApp?.HapticFeedback?.selectionChanged?.()

function errMsg(e: unknown): string {
  const detail = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail
  return detail || 'Something went wrong. Please try again.'
}

async function copyText(text: string): Promise<boolean> {
  try {
    if (navigator.clipboard?.writeText) { await navigator.clipboard.writeText(text); return true }
  } catch { /* fall through to legacy path */ }
  try {
    const ta = document.createElement('textarea')
    ta.value = text; ta.style.position = 'fixed'; ta.style.opacity = '0'
    document.body.appendChild(ta); ta.focus(); ta.select()
    const ok = document.execCommand('copy'); document.body.removeChild(ta)
    return ok
  } catch { return false }
}

function fmtCountdown(ms: number): string {
  const s = Math.max(0, Math.floor(ms / 1000))
  return `${String(Math.floor(s / 60)).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}`
}

const CARD: React.CSSProperties = {
  borderRadius: '20px', border: '1px solid rgba(255,255,255,.07)',
  background: 'rgba(255,255,255,.03)', padding: '18px 18px',
}

function Spinner({ size = 18 }: { size?: number }) {
  return (
    <span style={{
      width: size, height: size, borderRadius: '50%', flex: 'none', display: 'inline-block',
      border: '2px solid rgba(255,255,255,.2)', borderTopColor: '#ff5aa0',
      animation: 'noxx-spin .8s linear infinite',
    }} />
  )
}

export default function PaymentPage() {
  const nav = RR.useNavigate()
  const { orderId } = RR.useParams()
  const qc = useQueryClient()
  const id = Number(orderId)

  const stateQ = useQuery({
    queryKey: ['payment', id],
    queryFn: async () => (await api.get<PayState>(`/orders/${id}/payment`)).data,
    enabled: Number.isFinite(id) && id > 0,
    refetchOnWindowFocus: false,
  })

  const [sel, setSel] = React.useState<PayState | null>(null)      // chosen-coin details
  const [selecting, setSelecting] = React.useState<string | null>(null)
  const [err, setErr] = React.useState('')
  const [copied, setCopied] = React.useState<'addr' | 'amt' | null>(null)
  const [now, setNow] = React.useState(() => Date.now())
  const [paid, setPaid] = React.useState(false)
  const listRef = React.useRef<HTMLDivElement>(null)

  const coins = stateQ.data?.coins ?? []
  const amountUsd = (sel ?? stateQ.data)?.amount_usd ?? 0

  // Hydrate from server: already paid → success; a coin already reserved → resume.
  React.useEffect(() => {
    const d = stateQ.data
    if (!d) return
    if (d.paid) { setPaid(true); return }
    if (d.address && d.pay_currency) setSel(d)
  }, [stateQ.data])

  // Countdown ticker (only while awaiting payment for a chosen coin).
  React.useEffect(() => {
    if (!sel?.expires_at || paid) return
    const t = setInterval(() => setNow(Date.now()), 1000)
    return () => clearInterval(t)
  }, [sel?.expires_at, paid])

  // Poll our backend (which checks OrbChain with the merchant key) for confirmation.
  React.useEffect(() => {
    if (!sel || paid) return
    let stop = false
    const tick = async () => {
      try {
        const r = await api.post<{ paid: boolean }>(`/orders/${id}/check-payment`)
        if (r.data?.paid && !stop) {
          qc.invalidateQueries({ queryKey: ['orders'] })
          qc.invalidateQueries({ queryKey: ['profile'] }) // subscription orders flip premium status
          setPaid(true)
          return
        }
      } catch { /* keep polling */ }
      if (!stop) setTimeout(tick, 5000)
    }
    const h = setTimeout(tick, 5000)
    return () => { stop = true; clearTimeout(h) }
  }, [sel, paid, id, qc])

  // On confirmation: haptic + short celebratory beat, then to the success screen.
  React.useEffect(() => {
    if (!paid) return
    notify('success')
    const t = setTimeout(() => nav('/success', { replace: true }), 1500)
    return () => clearTimeout(t)
  }, [paid, nav])

  // Entrance for the coin list.
  React.useEffect(() => {
    if (!sel && !stateQ.isLoading) Motion.popIn(listRef.current, 'top center')
  }, [sel, stateQ.isLoading])

  const pickCoin = async (coin: Coin) => {
    tap(); setErr(''); setSelecting(coin.code)
    try {
      const r = await api.post<PayState>(`/orders/${id}/select-coin`, { coin: coin.code })
      setSel(r.data)
    } catch (e) {
      notify('error'); setErr(errMsg(e))
    } finally {
      setSelecting(null)
    }
  }

  const doCopy = async (which: 'addr' | 'amt', text?: string | null) => {
    if (!text) return
    if (await copyText(text)) { setCopied(which); notify('success'); setTimeout(() => setCopied(null), 1600) }
  }

  const remaining = sel?.expires_at ? sel.expires_at * 1000 - now : 0
  const expired = !!sel?.expires_at && remaining <= 0 && !paid

  // Step back inside the payment screen first; otherwise return to wherever the
  // payment was started from (product checkout or the subscription screen).
  const back = () => { if (sel) { setSel(null); setErr('') } else nav(-1) }

  return (
    <div data-screen-label="Payment" style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column' }}>
      <style>{'@keyframes noxx-spin{to{transform:rotate(360deg)}}@keyframes noxx-fade{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}'}</style>

      {/* soft glow */}
      <div style={{ position: 'absolute', top: '150px', left: '50%', transform: 'translateX(-50%)', width: '360px', height: '200px', background: 'radial-gradient(ellipse closest-side,rgba(240,70,150,.14),transparent)', filter: 'blur(20px)', pointerEvents: 'none' }} />

      {/* header */}
      <div style={{ flex: 'none', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '14px 0 6px' }}>
        <div style={{ width: '48px', height: '6px', borderRadius: '3px', background: 'rgba(255,255,255,.14)' }} />
      </div>
      <div style={{ flex: 'none', display: 'flex', alignItems: 'center', padding: '8px 22px 12px', position: 'relative', zIndex: 2 }}>
        <div onClick={back} style={{ width: '44px', height: '44px', borderRadius: '50%', background: 'rgba(255,255,255,.05)', border: '1px solid rgba(255,255,255,.08)', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer' }}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M19 12H5M11 18l-6-6 6-6" /></svg>
        </div>
        <div style={{ flex: 1, textAlign: 'center', fontSize: '22px', fontWeight: 600, color: '#fff', marginLeft: '-44px', paddingLeft: '44px', pointerEvents: 'none' }}>
          {sel ? 'Send payment' : 'Choose currency'}
        </div>
      </div>

      <div style={{ flex: 1, overflowY: 'auto', padding: '4px 22px 26px', position: 'relative', zIndex: 1 }}>
        {/* amount banner */}
        <div style={{ textAlign: 'center', margin: '6px 0 18px' }}>
          <div style={{ fontSize: '13px', color: '#8c828c' }}>Total to pay</div>
          <div style={{ fontSize: '30px', fontWeight: 700, color: '#fff', marginTop: '2px' }}>${amountUsd.toFixed(2)}</div>
          {!sel && <div style={{ fontSize: '12.5px', color: '#6a616b', marginTop: '2px' }}>Pay with any of 25 cryptocurrencies</div>}
        </div>

        {stateQ.isLoading && (
          <div style={{ display: 'flex', justifyContent: 'center', padding: '40px 0' }}><Spinner size={26} /></div>
        )}
        {stateQ.isError && (
          <div style={{ textAlign: 'center', color: '#ff7a93', fontSize: '14px', padding: '24px 0' }}>
            Couldn’t load payment. <span onClick={() => stateQ.refetch()} style={{ color: '#ff5aa0', textDecoration: 'underline', cursor: 'pointer' }}>Retry</span>
          </div>
        )}

        {/* ---- COIN PICKER ---- */}
        {!sel && !paid && !stateQ.isLoading && !stateQ.isError && (
          <div ref={listRef} style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {err && <div style={{ color: '#ff7a93', fontSize: '13px', textAlign: 'center', marginBottom: '2px' }}>{err}</div>}
            {coins.map((c) => {
              const busy = selecting === c.code
              return (
                <div key={c.code} onClick={() => !selecting && pickCoin(c)}
                  style={{ display: 'flex', alignItems: 'center', gap: '13px', padding: '13px 15px', borderRadius: '16px', cursor: selecting ? 'default' : 'pointer', border: '1px solid rgba(255,255,255,.07)', background: 'rgba(255,255,255,.03)', opacity: selecting && !busy ? 0.5 : 1, transition: 'opacity .2s' }}>
                  <div style={{ width: '40px', height: '40px', borderRadius: '50%', flex: 'none', display: 'flex', alignItems: 'center', justifyContent: 'center', background: c.color, color: '#fff', fontSize: c.ticker.length > 3 ? '10px' : '12px', fontWeight: 700, boxShadow: `0 4px 14px -4px ${c.color}` }}>{c.ticker}</div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: '15.5px', fontWeight: 600, color: '#fff' }}>{c.name}</div>
                    <div style={{ fontSize: '12.5px', color: '#8c828c', marginTop: '1px' }}>{c.network}</div>
                  </div>
                  {busy ? <Spinner /> : (
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#6a616b" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M9 18l6-6-6-6" /></svg>
                  )}
                </div>
              )
            })}
          </div>
        )}

        {/* ---- SEND PAYMENT ---- */}
        {sel && !paid && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', animation: 'noxx-fade .3s ease' }}>
            {/* exact amount */}
            <div style={CARD}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                <span style={{ fontSize: '13.5px', color: '#ff8fbf', fontWeight: 700, textDecoration: 'underline', textUnderlineOffset: '2px' }}>Send exactly</span>
                <span style={{ fontSize: '12.5px', color: '#8c828c' }}>{sel.pay_currency}</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <div style={{ flex: 1, minWidth: 0, fontSize: '22px', fontWeight: 700, color: '#fff', wordBreak: 'break-all' }}>{sel.pay_amount}</div>
                <button onClick={() => doCopy('amt', sel.pay_amount)} style={{ flex: 'none', padding: '9px 14px', borderRadius: '11px', border: '1px solid rgba(255,90,160,.4)', background: 'rgba(255,90,160,.08)', color: '#ff8fbf', fontSize: '13px', fontWeight: 700, cursor: 'pointer' }}>{copied === 'amt' ? 'Copied' : 'Copy'}</button>
              </div>
            </div>

            {/* address + QR */}
            <div style={CARD}>
              <div style={{ fontSize: '13.5px', color: '#8c828c', marginBottom: '12px' }}>To this {sel.pay_currency} address</div>
              {sel.qr && (
                <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '14px' }}>
                  <img src={sel.qr} alt="address QR" width={168} height={168} style={{ borderRadius: '12px', background: '#fff', padding: '8px' }} />
                </div>
              )}
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <div style={{ flex: 1, minWidth: 0, fontFamily: 'ui-monospace,SFMono-Regular,Menlo,monospace', fontSize: '13px', color: '#e7dee6', wordBreak: 'break-all', lineHeight: 1.45 }}>{sel.address}</div>
                <button onClick={() => doCopy('addr', sel.address)} style={{ flex: 'none', padding: '9px 14px', borderRadius: '11px', border: '1px solid rgba(255,90,160,.4)', background: 'rgba(255,90,160,.08)', color: '#ff8fbf', fontSize: '13px', fontWeight: 700, cursor: 'pointer' }}>{copied === 'addr' ? 'Copied' : 'Copy'}</button>
              </div>
            </div>

            {/* status / countdown */}
            {expired ? (
              <div style={{ textAlign: 'center' }}>
                <div style={{ color: '#ffb26b', fontSize: '14px', fontWeight: 600, marginBottom: '10px' }}>This address expired.</div>
                <button onClick={() => { setSel(null); stateQ.refetch() }} style={{ padding: '11px 20px', borderRadius: '13px', border: 'none', background: 'linear-gradient(100deg,#d6246e,#ec5690 48%,#f6a98c)', color: '#fff', fontSize: '14px', fontWeight: 700, cursor: 'pointer' }}>Choose currency again</button>
              </div>
            ) : (
              <>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '10px', padding: '14px 16px', borderRadius: '16px', background: 'rgba(96,165,250,.08)', border: '1px solid rgba(96,165,250,.2)' }}>
                  <Spinner />
                  <span style={{ fontSize: '14px', fontWeight: 600, color: '#9ec5ff' }}>Waiting for your payment…</span>
                </div>
                <div style={{ textAlign: 'center', fontSize: '12.5px', color: '#8c828c', lineHeight: 1.5 }}>
                  Send the exact amount in a single transfer. This screen unlocks automatically once the network confirms it{sel.expires_at ? <> — address active for <b style={{ color: '#c9bfc7' }}>{fmtCountdown(remaining)}</b></> : ''}.
                </div>
                <div onClick={back} style={{ textAlign: 'center', fontSize: '13px', color: '#8c828c', textDecoration: 'underline', cursor: 'pointer', marginTop: '2px' }}>Change currency</div>
              </>
            )}
          </div>
        )}
      </div>

      {/* ---- PAID overlay ---- */}
      {paid && (
        <div style={{ position: 'absolute', inset: 0, zIndex: 5, background: 'rgba(10,8,12,.92)', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '18px', animation: 'noxx-fade .3s ease' }}>
          <div style={{ width: '86px', height: '86px', borderRadius: '50%', background: 'linear-gradient(135deg,#2ecb7f,#22a466)', display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 16px 44px -10px rgba(46,203,127,.6)' }}>
            <svg width="42" height="42" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><path d="M20 6L9 17l-5-5" /></svg>
          </div>
          <div style={{ fontSize: '20px', fontWeight: 700, color: '#fff' }}>Payment received</div>
          <div style={{ fontSize: '13.5px', color: '#8c828c' }}>Unlocking your purchase…</div>
        </div>
      )}
    </div>
  )
}
