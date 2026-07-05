import type { ReactNode } from 'react'

interface AppFrameProps {
  children: ReactNode
  /** Scopes page-specific CSS (.pg-detail / .pg-sub). Omit for the home vocabulary. */
  scope?: 'detail' | 'sub'
  /** Render the ambient pink glow behind the content. */
  glow?: boolean
}

export function AppFrame({ children, scope, glow = true }: AppFrameProps) {
  const cls = ['frame', scope ? `pg-${scope}` : ''].filter(Boolean).join(' ')
  return (
    <div className={cls}>
      <div className="screen">
        {glow && <div className="glow" />}
        {children}
      </div>
    </div>
  )
}
