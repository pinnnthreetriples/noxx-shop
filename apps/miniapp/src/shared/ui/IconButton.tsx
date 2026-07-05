import * as React from 'react'

export interface IconButtonProps {
  /** Inline SVG glyph (24×24, stroke 1.7–2, round caps). */
  children?: React.ReactNode;
  /** `surface` = solid translucent (header buttons); `glass` = blurred over media (detail back/fav); `fab` = pink-gradient floating cart button. */
  variant?: 'surface' | 'glass' | 'fab';
  /** Diameter in px. 42 (header), 40 (glass), 58 (fab). */
  size?: number;
  /** Continuous pink ring pulse — used on the cart FAB. */
  pulse?: boolean;
  /** Count badge (top-right). Number or string; omit to hide. */
  badge?: React.ReactNode;
  onClick?: (e: React.MouseEvent<HTMLButtonElement>) => void;
  style?: React.CSSProperties;
}

/**
 * Circular icon button on the dark canvas — search, back, favorite, language,
 * and the floating cart FAB. Children should be an inline SVG (24×24, stroke 1.7–2).
 */
export function IconButton({
  children,
  variant = 'surface',  // 'surface' | 'glass' | 'fab'
  size = 42,
  pulse = false,
  badge = null,
  onClick,
  style = {},
  ...rest
}: IconButtonProps) {
  const variants = {
    surface: { background: 'var(--surface-3)', border: '1px solid var(--hairline-strong)' },
    glass:   { background: 'rgba(18,10,16,.42)', border: '1px solid var(--hairline-strong)', backdropFilter: 'blur(6px)' },
    fab:     { background: 'var(--grad-fab)', border: 'none', boxShadow: 'var(--shadow-fab)' },
  };
  return (
    <button
      type="button"
      onClick={onClick}
      style={{
        position: 'relative',
        width: size,
        height: size,
        borderRadius: '50%',
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        cursor: 'pointer',
        padding: 0,
        WebkitTapHighlightColor: 'transparent',
        animation: pulse ? 'noxx-ring-pulse 2.6s ease-out infinite' : undefined,
        ...variants[variant],
        ...style,
      }}
      {...rest}
    >
      {children}
      {badge != null && (
        <span style={{
          position: 'absolute', top: -4, right: -4, minWidth: 22, height: 22,
          padding: '0 5px', borderRadius: 11, background: 'var(--pink-hot)',
          color: '#fff', fontSize: 12, fontWeight: 700, fontFamily: 'var(--font-sans)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          border: '2px solid var(--noxx-surface)',
        }}>{badge}</span>
      )}
    </button>
  );
}
