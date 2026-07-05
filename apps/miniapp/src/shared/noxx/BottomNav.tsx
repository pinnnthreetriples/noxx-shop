import * as React from 'react'
import * as RR from 'react-router-dom'
import * as Motion from './motion'

const PINK = '#ff4d9e'
const GREY = '#8c828c'

type TabKey = 'fav' | 'home' | 'purch' | 'prof'

export default function BottomNav() {
  const nav = RR.useNavigate()
  const loc = RR.useLocation()
  const p = loc.pathname
  const navRef = React.useRef<HTMLDivElement>(null)

  let active: TabKey = 'home'
  if (p.startsWith('/favorites')) active = 'fav'
  else if (p.startsWith('/purchases')) active = 'purch'
  else if (p.startsWith('/profile')) active = 'prof'
  else if (p === '/' || p.startsWith('/catalog') || p.startsWith('/product')) active = 'home'

  // Measure the active item and center the dash under it — hardcoded px offsets
  // drift on any width other than the 402px design (space-around + real fonts).
  Motion.useIndicator(navRef, '[data-nav-ind]', '[data-nav-item][data-active="true"]', active, {
    width: false,
    center: true,
    ease: Motion.E.back15,
    duration: 550,
  })

  const isOn = (k: TabKey) => active === k
  const col = (k: TabKey) => (isOn(k) ? PINK : GREY)
  const fill = (k: TabKey) => (isOn(k) ? PINK : 'none')
  const lbl = (k: TabKey): React.CSSProperties => ({
    fontSize: '10px',
    fontWeight: isOn(k) ? 700 : 500,
    color: col(k),
    letterSpacing: '.2px',
    whiteSpace: 'nowrap', // long labels (tr/de) must not wrap under the icon
  })

  const item: React.CSSProperties = {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: '6px',
    cursor: 'pointer',
    width: '60px',
  }

  return (
    <div
      ref={navRef}
      data-nav=""
      style={{
        position: 'absolute',
        left: 0,
        right: 0,
        bottom: 0,
        display: 'flex',
        alignItems: 'flex-start',
        justifyContent: 'space-around',
        padding: '13px 14px 26px',
        background: 'rgba(10,7,12,.86)',
        backdropFilter: 'blur(18px)',
        WebkitBackdropFilter: 'blur(18px)',
        borderTop: '1px solid rgba(255,255,255,.05)',
        zIndex: 7,
      }}
    >
      <div
        data-nav-ind=""
        style={{
          position: 'absolute',
          top: '5px',
          left: 0,
          width: '26px',
          height: '3px',
          borderRadius: '2px',
          background: PINK,
          boxShadow: '0 0 8px rgba(255,77,158,.7)',
          // position is measured + animated by Motion.useIndicator (gsap)
        }}
      />

      <div data-nav-item="" data-active={isOn('fav') || undefined} data-press="" onClick={() => nav('/favorites')} style={item}>
        <svg width="23" height="23" viewBox="0 0 24 24" fill={fill('fav')} stroke={col('fav')} strokeWidth="1.7">
          <path d="M12 20.5C7 17 3.5 13.8 3.5 9.6 3.5 6.9 5.6 5 8 5c1.6 0 3 .9 4 2.3C13 5.9 14.4 5 16 5c2.4 0 4.5 1.9 4.5 4.6 0 4.2-3.5 7.4-8.5 10.9z" />
        </svg>
        <span style={lbl('fav')}>Favorites</span>
      </div>

      <div data-nav-item="" data-active={isOn('home') || undefined} data-press="" onClick={() => nav('/')} style={item}>
        <svg width="23" height="23" viewBox="0 0 24 24" fill={fill('home')} stroke={col('home')} strokeWidth="1.7" strokeLinejoin="round">
          <path d="M4 11l8-6.5 8 6.5v8a1.4 1.4 0 0 1-1.4 1.4H5.4A1.4 1.4 0 0 1 4 19z" />
        </svg>
        <span style={lbl('home')}>Home</span>
      </div>

      <div data-nav-item="" data-active={isOn('purch') || undefined} data-press="" onClick={() => nav('/purchases')} style={item}>
        <svg width="23" height="23" viewBox="0 0 24 24" fill={fill('purch')} stroke={col('purch')} strokeWidth="1.7" strokeLinejoin="round">
          <path d="M5 8h14l-1 11.2a2 2 0 0 1-2 1.8H8a2 2 0 0 1-2-1.8Z" />
          <path d="M8.5 8V6.5a3.5 3.5 0 0 1 7 0V8" fill="none" />
        </svg>
        <span style={lbl('purch')}>Purchases</span>
      </div>

      <div data-nav-item="" data-active={isOn('prof') || undefined} data-press="" onClick={() => nav('/profile')} style={item}>
        <svg width="23" height="23" viewBox="0 0 24 24" fill="none" stroke={col('prof')} strokeWidth="1.7">
          <circle cx="12" cy="8" r="3.6" />
          <path d="M5 20c0-3.6 3.1-5.6 7-5.6s7 2 7 5.6" />
        </svg>
        <span style={lbl('prof')}>Profile</span>
      </div>
    </div>
  )
}