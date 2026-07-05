// @ts-nocheck — vendored NoxX design-system component (inline styles)
import * as React from 'react'

export interface FeatureItemProps {
  /** The benefit label, or — when `sub` is set — the bold benefit title. */
  children?: React.ReactNode;
  /** Optional supporting line below the title (muted). Switches to the two-line row. */
  sub?: React.ReactNode;
  /** Bottom hairline divider (set false on the last item). */
  divider?: boolean;
  style?: React.CSSProperties;
}

/**
 * Feature line for benefit lists (subscription perks). Two forms:
 *  - label only: <FeatureItem>Unlimited streaming</FeatureItem>
 *  - title + supporting line: <FeatureItem sub="…">Title</FeatureItem>
 * Stack several inside a translucent card with hairline dividers.
 */
export function FeatureItem({ children, sub, divider = true, style = {} }: FeatureItemProps) {
  return (
    <div style={{
      display: 'flex', alignItems: sub ? 'flex-start' : 'center', gap: 11,
      padding: sub ? '13px 0' : '12px 0',
      borderBottom: divider ? '1px solid var(--hairline-soft)' : 'none',
      fontFamily: 'var(--font-sans)', ...style,
    }}>
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--pink-350)" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" style={{ flex: 'none', marginTop: sub ? 2 : 0 }}>
        <path d="M5 12.5l4 4 10-10" />
      </svg>
      {sub ? (
        <div>
          <div style={{ fontSize: 14.5, fontWeight: 600, color: 'var(--ink-900)' }}>{children}</div>
          <div style={{ fontSize: 13, color: 'var(--ink-400)', marginTop: 2 }}>{sub}</div>
        </div>
      ) : (
        <span style={{ fontSize: 14.5, color: 'var(--ink-600)' }}>{children}</span>
      )}
    </div>
  );
}
