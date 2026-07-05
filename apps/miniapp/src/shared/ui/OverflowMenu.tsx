import * as React from 'react'

export interface OverflowMenuItem {
  label: React.ReactNode;
  /** Optional leading glyph (e.g. the exported TrashIcon, which inherits color). */
  icon?: React.ReactNode;
  /** Render in the danger color (e.g. Remove). */
  danger?: boolean;
  onClick?: () => void;
}

export interface OverflowMenuProps {
  items: OverflowMenuItem[];
  /** `up` opens the popover above the trigger (cart row); `down` opens below. */
  align?: 'up' | 'down';
  /** Start open (for demos / controlled first paint). */
  defaultOpen?: boolean;
  style?: React.CSSProperties;
}

const KEBAB = (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="#cfc7cc">
    <circle cx="12" cy="5" r="1.7" /><circle cx="12" cy="12" r="1.7" /><circle cx="12" cy="19" r="1.7" />
  </svg>
);

/** Trash glyph for a destructive menu item (inherits the row's color). */
export const TrashIcon = (
  <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <path d="M4 7h16M9 7V5a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v2M6 7l1 13a2 2 0 0 0 2 1.8h6a2 2 0 0 0 2-1.8L18 7" />
  </svg>
);

/**
 * Kebab (⋮) trigger that opens a small pop-in action menu — the cart row's
 * "Remove" overflow, generalized. Pops from its corner (WAAPI), closes on
 * outside click. NoxX sells per-item, so this replaces any quantity stepper.
 */
export function OverflowMenu({ items = [], align = 'up', defaultOpen = false, style = {} }: OverflowMenuProps) {
  const [open, setOpen] = React.useState(defaultOpen);
  const wrapRef = React.useRef<HTMLDivElement>(null);
  const popRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    if (!open) return;
    const pop = popRef.current;
    if (pop && pop.animate) {
      const oy = align === 'up' ? '6px' : '-6px';
      pop.animate(
        [{ opacity: 0, transform: `scale(.92) translateY(${oy})` }, { opacity: 1, transform: 'scale(1) translateY(0)' }],
        { duration: 190, easing: 'cubic-bezier(.2,.7,.3,1)' }
      );
    }
    const onDoc = (e: PointerEvent) => { if (wrapRef.current && !wrapRef.current.contains(e.target as Node)) setOpen(false); };
    document.addEventListener('pointerdown', onDoc);
    return () => document.removeEventListener('pointerdown', onDoc);
  }, [open, align]);

  const vertical = align === 'up' ? { bottom: 48 } : { top: 48 };
  const origin = align === 'up' ? 'right bottom' : 'right top';

  return (
    <div ref={wrapRef} style={{ position: 'relative', flex: 'none', ...style }}>
      <div
        onClick={() => setOpen(o => !o)}
        style={{ width: 40, height: 40, borderRadius: 12, display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', border: '1px solid rgba(255,255,255,.08)', background: 'rgba(255,255,255,.05)' }}
      >
        {KEBAB}
      </div>
      {open && (
        <div
          ref={popRef}
          style={{ position: 'absolute', right: 0, ...vertical, zIndex: 30, minWidth: 132, transformOrigin: origin, padding: 6, borderRadius: 13, background: '#1c0f17', border: '1px solid rgba(255,255,255,.1)', boxShadow: '0 16px 34px -12px rgba(0,0,0,.7)' }}
        >
          {items.map((it, i) => (
            <div
              key={i}
              onClick={() => { setOpen(false); it.onClick && it.onClick(); }}
              style={{ display: 'flex', alignItems: 'center', gap: 9, padding: '9px 11px', borderRadius: 9, cursor: 'pointer', whiteSpace: 'nowrap', color: it.danger ? 'var(--danger-text)' : 'var(--ink-700)' }}
            >
              {it.icon}
              <span style={{ fontSize: 15, fontWeight: 600 }}>{it.label}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}