// @ts-nocheck — vendored NoxX design-system component (inline styles)
import * as React from 'react'
import starsIconUrl from '@/assets/stars-icon.png'

export interface ButtonProps {
  children?: React.ReactNode;
  /** Visual style. `primary` = magenta→peach CTA; `secondary` = purple→magenta (Add to cart); `outline` = subtle pink-link; `ghost` = small inline accent chip. */
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost';
  /** `lg` is the 66px-tall Pay/Subscribe button; `md` is the 18px-padded default. */
  size?: 'md' | 'lg';
  /** Full-width (default true). */
  block?: boolean;
  disabled?: boolean;
  /** Overflow the oversized Stars cluster off the top-right edge (Pay / Subscribe). */
  star?: boolean;
  /** Path to the copied assets/stars-icon.png, relative to the consuming page. */
  starSrc?: string;
  leadingIcon?: React.ReactNode;
  trailingIcon?: React.ReactNode;
  onClick?: (e: React.MouseEvent<HTMLButtonElement>) => void;
  style?: React.CSSProperties;
}

/**
 * NoxX primary action button. Gradient fills with a colored bloom shadow.
 * The signature "subscribe/pay" treatment overflows an oversized 3-D Stars
 * cluster off the top-right edge — enable with `star` (point `starSrc` at your
 * copied assets/stars-icon.png).
 */
export function Button({
  children,
  variant = 'primary',   // 'primary' | 'secondary' | 'outline' | 'ghost'
  size = 'md',           // 'md' | 'lg'
  block = true,
  disabled = false,
  star = false,
  starSrc = starsIconUrl,
  leadingIcon = null,
  trailingIcon = null,
  onClick,
  style = {},
  ...rest
}: ButtonProps) {
  const pad = size === 'lg' ? '0' : '18px';
  const height = size === 'lg' ? 66 : undefined;

  const base = {
    position: 'relative',
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '10px',
    width: block ? '100%' : 'auto',
    height,
    padding: pad,
    border: 'none',
    borderRadius: variant === 'outline' || variant === 'ghost' ? 16 : 18,
    cursor: disabled ? 'not-allowed' : 'pointer',
    fontFamily: 'var(--font-sans)',
    fontSize: size === 'lg' ? 19 : 17,
    fontWeight: 600,
    color: '#fff',
    overflow: star ? 'visible' : 'hidden',
    WebkitTapHighlightColor: 'transparent',
    transition: 'filter .2s ease',
  };

  const variants = {
    primary:   { background: 'var(--grad-primary)',   boxShadow: size === 'lg' ? 'var(--shadow-cta-tall)' : 'var(--shadow-cta)' },
    secondary: { background: 'var(--grad-secondary)',  boxShadow: 'var(--shadow-secondary)' },
    outline:   { background: 'var(--surface-2)', color: 'var(--pink-link)', border: '1px solid var(--hairline-strong)', boxShadow: 'none' },
    ghost:     { background: 'var(--surface-3)', color: 'var(--pink-300)', border: '1px solid var(--border-pink-bright)', borderRadius: 14, fontSize: 14, padding: '10px 16px', boxShadow: 'none' },
  };

  const disabledStyle = disabled
    ? { background: 'var(--surface-3)', color: 'var(--ink-200)', boxShadow: 'none', border: 'none' }
    : {};

  return (
    <button
      type="button"
      onClick={disabled ? undefined : onClick}
      style={{ ...base, ...variants[variant], ...disabledStyle, ...style }}
      {...rest}
    >
      {leadingIcon}
      <span style={{ position: 'relative', zIndex: 1 }}>{children}</span>
      {trailingIcon}
      {star && !disabled && (
        <img
          src={starSrc}
          alt=""
          style={{
            position: 'absolute',
            right: 6,
            bottom: -3,
            height: size === 'lg' ? 100 : 92,
            width: 'auto',
            pointerEvents: 'none',
            filter: 'drop-shadow(0 7px 11px rgba(120,60,0,.42))',
          }}
        />
      )}
    </button>
  );
}
