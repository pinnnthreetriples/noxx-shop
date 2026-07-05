// @ts-nocheck — vendored NoxX design-system component (inline styles)
import * as React from 'react'

export interface VideoRowProps {
  title: string;
  tagline?: string;
  /** CSS background for the thumbnail (layered radial gradients — see THUMBS in the app). */
  thumb?: string;
  duration?: string;       // "12:45"
  views?: string;          // "2.4K"
  purchases?: string;      // "990"
  /** Price / rating in Stars. */
  stars?: number;
  /** Corner badge: "Premium" (pink) or "New" (green). */
  badge?: 'Premium' | 'New';
  /** Discount chip, e.g. "−15%". */
  discount?: string;
  onOpen?: () => void;
  style?: React.CSSProperties;
}

import { StarPrice } from './StarPrice';
import { Badge } from './Badge';

const Stat = ({ icon, children }) => (
  <span style={{ display: 'inline-flex', alignItems: 'center', gap: 5, color: 'var(--ink-400)', fontSize: 12.5 }}>
    {icon}{children}
  </span>
);
const eyeIcon = <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--ink-400)" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round"><path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7Z" /><circle cx="12" cy="12" r="3" /></svg>;
const bagIcon = <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--ink-400)" strokeWidth="1.7" strokeLinejoin="round"><path d="M5 8h14l-1 11.2a2 2 0 0 1-2 1.8H8a2 2 0 0 1-2-1.8Z" /><path d="M8.5 8V6.5a3.5 3.5 0 0 1 7 0V8" /></svg>;

/**
 * Catalog / list video row: gradient thumbnail with a glass play button,
 * duration chip, and a discount chip (top-right of the thumbnail); then
 * title, tagline, an optional Premium/New label, two stats, and a star rating.
 */
export function VideoRow({ title, tagline, thumb, duration, views, purchases, stars, badge, discount, onOpen, style = {} }: VideoRowProps) {
  return (
    <div onClick={onOpen} style={{
      position: 'relative', display: 'flex', gap: 14, alignItems: 'stretch', padding: 10,
      borderRadius: 18, cursor: 'pointer', overflow: 'hidden', fontFamily: 'var(--font-sans)',
      background: 'var(--surface-1)', border: '1px solid var(--hairline)', ...style,
    }}>
      <div style={{ position: 'relative', width: 130, height: 92, borderRadius: 13, overflow: 'hidden', flex: 'none' }}>
        <div style={{ position: 'absolute', inset: 0, background: thumb || 'linear-gradient(140deg,#3a2126,#5b3138)' }} />
        <div style={{ position: 'absolute', inset: 0, background: 'linear-gradient(180deg,transparent 42%,rgba(0,0,0,.55))' }} />
        {discount && <div style={{ position: 'absolute', right: 7, top: 7, zIndex: 3 }}><Badge variant="discount">{discount}</Badge></div>}
        <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <div style={{ width: 38, height: 38, borderRadius: '50%', background: 'rgba(18,9,14,.5)', backdropFilter: 'blur(4px)', border: '1px solid rgba(255,255,255,.18)', display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 0 18px var(--glow-pink)' }}>
            <svg width="13" height="13" viewBox="0 0 24 24" fill="#fff"><path d="M8 5v14l11-7z" /></svg>
          </div>
        </div>
        {duration && (
          <div style={{ position: 'absolute', left: 7, bottom: 7, display: 'flex', alignItems: 'center', gap: 3, padding: '2px 6px', borderRadius: 7, background: 'rgba(0,0,0,.62)', backdropFilter: 'blur(3px)', color: '#fff', fontSize: 11, fontWeight: 600 }}>
            <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="9" /><path d="M12 7.5V12l3 2" /></svg>{duration}
          </div>
        )}
      </div>
      <div style={{ flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column', justifyContent: 'center', padding: '1px 0' }}>
        <div style={{ fontSize: 17, fontWeight: 600, color: 'var(--ink-900)', letterSpacing: '-.2px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{title}</div>
        {tagline && <div style={{ fontSize: 13, color: 'var(--ink-350)', marginTop: 4, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{tagline}</div>}
        {badge && <div style={{ marginTop: 9 }}><Badge variant={badge === 'New' ? 'new' : 'premium'}>{badge}</Badge></div>}
        <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginTop: 11 }}>
          {views != null && <Stat icon={eyeIcon}>{views}</Stat>}
          {purchases != null && <Stat icon={bagIcon}>{purchases}</Stat>}
          {stars != null && <span style={{ marginLeft: 'auto' }}><StarPrice amount={stars} size="sm" /></span>}
        </div>
      </div>
    </div>
  );
}
