// @ts-nocheck — vendored NoxX design-system component (inline styles)
import * as React from 'react'

export interface BadgeProps {
  children?: React.ReactNode;
  /**
   * `discount` — pink gradient "−15%" chip on a thumbnail.
   * `value` — floating "BEST VALUE · −30%" plan tag (position it top:-9px right:14px).
   * `premium` / `new` — small glassy corner badge on a catalog thumbnail.
   * `tagPremium` / `tag` — larger pill chips under a video title (Premium vs neutral).
   */
  variant?: 'discount' | 'value' | 'premium' | 'new' | 'tagPremium' | 'tag';
  style?: React.CSSProperties;
}

/**
 * Small status / label pill used across NoxX: discount chips, the "BEST VALUE"
 * plan tag, Premium/New thumbnail badges, and payment status text.
 */
export function Badge({ children, variant = 'discount', style = {}, ...rest }: BadgeProps) {
  const variants = {
    // Pink gradient pill — "−15%" discount, sits on a thumbnail.
    discount: { padding: '3px 9px', borderRadius: 999, background: 'var(--grad-pill)', color: '#fff', fontSize: 11, fontWeight: 700, letterSpacing: '.3px', boxShadow: 'var(--shadow-badge)' },
    // Floating "BEST VALUE · −30%" tag on the recommended plan (place top:-9px).
    value: { padding: '2px 9px', borderRadius: 999, background: 'var(--grad-pill)', color: '#fff', fontSize: 11, fontWeight: 700, letterSpacing: '.3px' },
    // Corner badge on a catalog thumbnail — Premium (pink) / New (green).
    premium: { padding: '2px 7px', borderRadius: 7, background: 'rgba(20,8,14,.6)', backdropFilter: 'blur(4px)', color: 'var(--pink-350)', fontSize: 10, fontWeight: 600, letterSpacing: '.2px' },
    new: { padding: '2px 7px', borderRadius: 7, background: 'rgba(20,8,14,.6)', backdropFilter: 'blur(4px)', color: 'var(--ok-text)', fontSize: 10, fontWeight: 600, letterSpacing: '.2px' },
    // Detail-screen tag chip — Premium (pink) vs neutral.
    tagPremium: { padding: '9px 18px', borderRadius: 20, background: 'rgba(255,80,160,.1)', border: '1px solid var(--border-pink-bright)', color: 'var(--pink-350)', fontSize: 14, fontWeight: 600 },
    tag: { padding: '9px 18px', borderRadius: 20, background: 'var(--surface-3)', border: '1px solid var(--hairline-strong)', color: 'var(--ink-600)', fontSize: 14, fontWeight: 500 },
  };
  return (
    <span style={{ display: 'inline-flex', alignItems: 'center', fontFamily: 'var(--font-sans)', whiteSpace: 'nowrap', ...variants[variant], ...style }} {...rest}>
      {children}
    </span>
  );
}
