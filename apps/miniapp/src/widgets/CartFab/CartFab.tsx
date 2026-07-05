import { useNavigate } from 'react-router-dom'
import { useAppStore } from '@/shared/lib/store'
/** Floating cart action button with a live item-count badge. */
export function CartFab() {
  const navigate = useNavigate()
  const count = useAppStore((s) => s.cartItems.reduce((n, i) => n + i.quantity, 0))

  return (
    <div className="fab" onClick={() => navigate('/cart')} role="button" aria-label="Cart">
      <svg width="25" height="25" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="9.5" cy="20" r="1.3" />
        <circle cx="18" cy="20" r="1.3" />
        <path d="M3 4h2l2.2 11.2a1.5 1.5 0 0 0 1.5 1.2h8.4a1.5 1.5 0 0 0 1.5-1.2L21 7H6" />
      </svg>
      {count > 0 && <div className="badge">{count}</div>}
    </div>
  )
}
