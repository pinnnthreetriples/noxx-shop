import { useNavigate } from 'react-router-dom'
import { IconButton } from '@/shared/ui'
import type { ReactNode } from 'react'
interface AppHeaderProps {
  /** Title text. Defaults to the NoxX wordmark treatment. */
  title?: string
  /** Show a back chevron that pops the router stack. */
  showBack?: boolean
  /** Render the title as the brand wordmark (gradient) instead of plain text. */
  brand?: boolean
  /** Optional right-aligned action(s). */
  right?: ReactNode
}

const BackIcon = (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#e9e2e8" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
    <path d="M15 5l-7 7 7 7" />
  </svg>
)

export function AppHeader({ title = 'NoxX', showBack = false, brand = false, right }: AppHeaderProps) {
  const navigate = useNavigate()
  return (
    <div className="hdr">
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, minWidth: 0 }}>
        {showBack && (
          <IconButton aria-label="Back" onClick={() => navigate(-1)}>{BackIcon}</IconButton>
        )}
        {brand || title === 'NoxX' ? (
          <div className="logo">{title}</div>
        ) : (
          <div style={{ fontSize: 20, fontWeight: 800, color: 'var(--ink-900)', letterSpacing: '-.3px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{title}</div>
        )}
      </div>
      {right}
    </div>
  )
}
