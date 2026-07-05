// @ts-nocheck — vendored NoxX design-system component (inline styles)
import * as React from 'react'

export interface StarPriceProps {
  /** Amount in Telegram Stars. */
  amount: number;
  /** Glyph + numeral size. `sm` list, `md` default, `lg` summary, `xl` detail hero. */
  size?: 'sm' | 'md' | 'lg' | 'xl';
  /** Show the muted "≈ $x.xx" approximation. */
  usd?: boolean;
  /** Place the ≈USD on the same line (default: stacked below, right-aligned). */
  usdInline?: boolean;
  /** Stars→USD rate (default 0.02). */
  rate?: number;
  style?: React.CSSProperties;
}

const STAR = (px) => (
  <svg width={px} height={px} viewBox="0 0 24 24" fill="var(--gold-500)" style={{ flex: 'none' }}>
    <path d="M12 2l2.95 5.98 6.6.96-4.78 4.66 1.13 6.57L12 17.98 6.1 20.16l1.13-6.57L2.45 8.94l6.6-.96z" />
  </svg>
);

/**
 * The NoxX price unit: a filled gold star + the Stars amount, with an optional
 * muted ≈USD approximation. Used in lists, cart totals, plan rows, and history.
 */
export function StarPrice({
  amount,
  size = 'md',           // 'sm' | 'md' | 'lg' | 'xl'
  usd = false,           // show "≈ $x.xx" (rate 0.02)
  usdInline = false,     // place the ≈USD on the same line (else below, right-aligned)
  rate = 0.02,
  style = {},
}: StarPriceProps) {
  const map = {
    sm: { star: 14, num: 13 },
    md: { star: 17, num: 15 },
    lg: { star: 19, num: 18 },
    xl: { star: 24, num: 30 },
  };
  const { star, num } = map[size];
  const fmt = Number(amount).toLocaleString('en-US');
  const usdStr = '≈ $' + (Number(amount) * rate).toFixed(2);

  const line = (
    <span style={{ display: 'inline-flex', alignItems: 'center', gap: size === 'xl' ? 10 : 6 }}>
      {STAR(star)}
      <span style={{ fontSize: num, fontWeight: size === 'sm' ? 700 : 600, color: 'var(--gold-ink)', fontVariantNumeric: 'tabular-nums' }}>{fmt}</span>
      {usd && usdInline && (
        <span style={{ fontSize: 14, color: 'var(--ink-200)', marginLeft: 4 }}>{usdStr}</span>
      )}
    </span>
  );

  if (usd && !usdInline) {
    return (
      <span style={{ display: 'inline-flex', flexDirection: 'column', alignItems: 'flex-end', fontFamily: 'var(--font-sans)', ...style }}>
        {line}
        <span style={{ fontSize: 12.5, color: 'var(--ink-350)', marginTop: 2 }}>{usdStr}</span>
      </span>
    );
  }
  return <span style={{ fontFamily: 'var(--font-sans)', ...style }}>{line}</span>;
}
