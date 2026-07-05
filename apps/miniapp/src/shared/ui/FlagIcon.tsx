import * as React from 'react'

export type FlagCode = 'en' | 'ru' | 'es' | 'de' | 'el' | 'tr' | 'bg' | 'sr' | 'ro' | 'mo';

export interface FlagIconProps {
  /** Language/country code. */
  code: FlagCode;
  /** Width in px (height is 2/3 of this). Default 23. */
  size?: number;
  style?: React.CSSProperties;
}

/**
 * Inline-SVG country flags for the NoxX language picker. Emoji flags fall back to
 * bare letter-pairs ("GB", "DE") on Telegram desktop and many platforms, so the
 * brand uses these instead. 3:2 ratio, soft corners, faint hairline ring.
 */
const FLAGS = {
  ru: (<React.Fragment>
    <rect width="24" height="16" fill="#fff" />
    <rect y="5.33" width="24" height="5.33" fill="#0039A6" />
    <rect y="10.66" width="24" height="5.34" fill="#D52B1E" />
  </React.Fragment>),
  es: (<React.Fragment>
    <rect width="24" height="16" fill="#AA151B" />
    <rect y="4" width="24" height="8" fill="#F1BF00" />
    <circle cx="9" cy="8" r="1.5" fill="#AA151B" opacity="0.35" />
  </React.Fragment>),
  en: (<React.Fragment>
    <rect width="24" height="16" fill="#012169" />
    <path d="M0 0L24 16M24 0L0 16" stroke="#fff" strokeWidth="3.5" />
    <path d="M0 0L24 16M24 0L0 16" stroke="#C8102E" strokeWidth="1.4" />
    <rect x="9" width="6" height="16" fill="#fff" /><rect y="5" width="24" height="6" fill="#fff" />
    <rect x="10" width="4" height="16" fill="#C8102E" /><rect y="6" width="24" height="4" fill="#C8102E" />
  </React.Fragment>),
  de: (<React.Fragment>
    <rect width="24" height="5.34" fill="#0a0a0a" /><rect y="5.33" width="24" height="5.34" fill="#DD0000" /><rect y="10.66" width="24" height="5.34" fill="#FFCE00" />
  </React.Fragment>),
  el: (<React.Fragment>
    <rect width="24" height="16" fill="#fff" />
    <rect y="0" width="24" height="1.78" fill="#0D5EAF" /><rect y="3.56" width="24" height="1.78" fill="#0D5EAF" /><rect y="7.11" width="24" height="1.78" fill="#0D5EAF" /><rect y="10.67" width="24" height="1.78" fill="#0D5EAF" /><rect y="14.22" width="24" height="1.78" fill="#0D5EAF" />
    <rect width="8.9" height="8.9" fill="#0D5EAF" />
    <rect x="3.45" width="2" height="8.9" fill="#fff" /><rect y="3.45" width="8.9" height="2" fill="#fff" />
  </React.Fragment>),
  tr: (<React.Fragment>
    <rect width="24" height="16" fill="#E30A17" />
    <circle cx="9.6" cy="8" r="4" fill="#fff" /><circle cx="11" cy="8" r="3.2" fill="#E30A17" />
    <path d="M14.1 5.9l.66 1.5 1.62.16-1.23 1.07.38 1.59-1.43-.86-1.43.86.38-1.59-1.23-1.07 1.62-.16z" fill="#fff" />
  </React.Fragment>),
  bg: (<React.Fragment>
    <rect width="24" height="5.34" fill="#fff" /><rect y="5.33" width="24" height="5.34" fill="#00966E" /><rect y="10.66" width="24" height="5.34" fill="#D62612" />
  </React.Fragment>),
  sr: (<React.Fragment>
    <rect width="24" height="5.34" fill="#C6363C" /><rect y="5.33" width="24" height="5.34" fill="#0C4076" /><rect y="10.66" width="24" height="5.34" fill="#fff" />
  </React.Fragment>),
  ro: (<React.Fragment>
    <rect width="8" height="16" fill="#002B7F" /><rect x="8" width="8" height="16" fill="#FCD116" /><rect x="16" width="8" height="16" fill="#CE1126" />
  </React.Fragment>),
  mo: (<React.Fragment>
    <rect width="8" height="16" fill="#0046AE" /><rect x="8" width="8" height="16" fill="#FFD200" /><rect x="16" width="8" height="16" fill="#CC092F" />
    <circle cx="12" cy="8" r="2.2" fill="none" stroke="#A07A2E" strokeWidth="1" />
  </React.Fragment>),
};

export function FlagIcon({ code, size = 23, style = {} }: FlagIconProps) {
  const flag = FLAGS[code];
  if (!flag) return null;
  return (
    <span style={{ display: 'block', width: size, height: size * 2 / 3, borderRadius: 3, overflow: 'hidden', flex: 'none', boxShadow: '0 0 0 1px rgba(255,255,255,.14)', ...style }}>
      <svg width="100%" height="100%" viewBox="0 0 24 16" style={{ display: 'block' }}>{flag}</svg>
    </span>
  );
}

/** Language codes with a flag, in picker order. */
export const FLAG_CODES = Object.keys(FLAGS);

/** Returns just the flag <svg> (fills its container) for embedding in an
 *  existing chip wrapper. Returns null for unknown codes. */
// eslint-disable-next-line react-refresh/only-export-components -- helper export alongside the vendored component; HMR hint only
export function flagSvg(code: FlagCode | string): React.ReactElement | null {
  const flag = (FLAGS as Partial<Record<string, React.ReactElement>>)[code]
  if (!flag) return null
  return (
    <svg width="100%" height="100%" viewBox="0 0 24 16" style={{ display: 'block' }}>{flag}</svg>
  )
}
