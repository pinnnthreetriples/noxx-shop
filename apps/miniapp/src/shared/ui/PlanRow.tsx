import * as React from 'react'
import * as Motion from '@/shared/noxx/motion'

export interface PlanRowProps {
  /** Plan name, e.g. "Yearly". */
  name: string;
  /** Billing sub-label, e.g. "Billed every year". */
  sub: string;
  /** Price in Stars. */
  amount: number;
  /** Selected = pink border + tinted fill + filled radio dot. */
  selected?: boolean;
  /** Optional floating tag, e.g. "BEST VALUE · −30%". */
  tag?: string;
  onSelect?: () => void;
  style?: React.CSSProperties;
}

import { StarPrice } from './StarPrice';
import { Badge } from './Badge';

/**
 * Subscription plan radio row. Selected state swaps to a pink border + tinted
 * fill and fills the radio dot. An optional floating tag marks the best value.
 */
export function PlanRow({ name, sub, amount, selected = false, tag = '', onSelect, style = {} }: PlanRowProps) {
  const dotRef = React.useRef(null)
  React.useEffect(() => { if (selected) Motion.planDotPop(dotRef.current) }, [selected])
  return (
    <div
      onClick={onSelect}
      style={{
        position: 'relative',
        display: 'flex',
        alignItems: 'center',
        gap: 13,
        borderRadius: 16,
        padding: '16px 18px',
        marginBottom: 12,
        cursor: 'pointer',
        fontFamily: 'var(--font-sans)',
        transition: 'background .25s ease, border-color .25s ease',
        background: selected ? 'var(--surface-pink)' : 'var(--surface-2)',
        border: selected ? '1.5px solid var(--border-pink-strong)' : '1px solid var(--hairline-strong)',
        ...style,
      }}
    >
      {tag && (
        <div style={{ position: 'absolute', top: -9, right: 14 }}>
          <Badge variant="value">{tag}</Badge>
        </div>
      )}
      <div style={{
        width: 22, height: 22, borderRadius: '50%', flex: 'none',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        border: selected ? '2px solid var(--pink-400)' : '2px solid rgba(255,255,255,.25)',
      }}>
        {selected && <div ref={dotRef} style={{ width: 10, height: 10, borderRadius: '50%', background: 'var(--pink-400)' }} />}
      </div>
      <div style={{ flex: 1 }}>
        <div style={{ fontSize: 17, fontWeight: 600, color: 'var(--ink-900)' }}>{name}</div>
        <div style={{ fontSize: 13, color: 'var(--ink-400)', marginTop: 2 }}>{sub}</div>
      </div>
      <StarPrice amount={amount} size="lg" usd />
    </div>
  );
}