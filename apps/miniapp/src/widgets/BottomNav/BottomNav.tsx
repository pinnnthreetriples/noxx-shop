import { useLocation, useNavigate } from 'react-router-dom'
interface NavIconProps { active: boolean }

const stroke = (a: boolean) => (a ? 'var(--pink-500)' : '#827a85')
const fill = (a: boolean) => (a ? 'var(--pink-500)' : 'none')

function HeartIcon({ active }: NavIconProps) {
  return (
    <svg width="23" height="23" viewBox="0 0 24 24" fill={fill(active)} stroke={stroke(active)} strokeWidth="1.7">
      <path d="M12 20.5C7 17 3.5 13.8 3.5 9.6 3.5 6.9 5.6 5 8 5c1.6 0 3 .9 4 2.3C13 5.9 14.4 5 16 5c2.4 0 4.5 1.9 4.5 4.6 0 4.2-3.5 7.4-8.5 10.9z" />
    </svg>
  )
}
function HomeIcon({ active }: NavIconProps) {
  return (
    <svg width="23" height="23" viewBox="0 0 24 24" fill={fill(active)} stroke={stroke(active)} strokeWidth="1.7" strokeLinejoin="round">
      <path d="M4 11l8-6.5 8 6.5v8a1.4 1.4 0 0 1-1.4 1.4H5.4A1.4 1.4 0 0 1 4 19z" />
    </svg>
  )
}
function BagIcon({ active }: NavIconProps) {
  return (
    <svg width="23" height="23" viewBox="0 0 24 24" fill={fill(active)} stroke={stroke(active)} strokeWidth="1.7" strokeLinejoin="round">
      <path d="M5 8h14l-1 11.2a2 2 0 0 1-2 1.8H8a2 2 0 0 1-2-1.8Z" />
      <path d="M8.5 8V6.5a3.5 3.5 0 0 1 7 0V8" fill="none" stroke={stroke(active)} />
    </svg>
  )
}
function UserIcon({ active }: NavIconProps) {
  return (
    <svg width="23" height="23" viewBox="0 0 24 24" fill={fill(active)} stroke={stroke(active)} strokeWidth="1.7">
      <circle cx="12" cy="8" r="3.6" />
      <path d="M5 20c0-3.6 3.1-5.6 7-5.6s7 2 7 5.6" fill="none" stroke={stroke(active)} />
    </svg>
  )
}

const ITEMS = [
  { label: 'Favorites', path: '/favorites', Icon: HeartIcon },
  { label: 'Home', path: '/', Icon: HomeIcon },
  { label: 'Purchases', path: '/purchases', Icon: BagIcon },
  { label: 'Profile', path: '/profile', Icon: UserIcon },
] as const

/** Frosted bottom tab bar with an animated active indicator. */
export function BottomNav() {
  const navigate = useNavigate()
  const { pathname } = useLocation()
  const activeIndex = ITEMS.findIndex((it) => it.path === pathname)

  return (
    <div className="nav">
      {activeIndex >= 0 && (
        <div
          className="ind"
          style={{ left: `calc(${(activeIndex + 0.5) * 25}% - 13px)`, transform: 'none' }}
        />
      )}
      {ITEMS.map((it, i) => {
        const active = i === activeIndex
        const { Icon } = it
        return (
          <div
            key={it.path}
            className={active ? 'ni active' : 'ni'}
            onClick={() => navigate(it.path)}
          >
            <Icon active={active} />
            <span>{it.label}</span>
          </div>
        )
      })}
    </div>
  )
}
