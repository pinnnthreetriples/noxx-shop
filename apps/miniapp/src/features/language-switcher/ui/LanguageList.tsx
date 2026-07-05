import type { FlagCode } from '@/shared/ui'
import { useTranslation } from 'react-i18next'
import { LANGUAGES } from '@/features/language-switcher'
import { FlagIcon } from '@/shared/ui'
const CheckIcon = (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--pink-500)" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round">
    <path d="M5 12.5l4.5 4.5L19 7" />
  </svg>
)

/** Selectable list of supported interface languages. */
export function LanguageList() {
  const { i18n } = useTranslation()
  const current = i18n.language?.split('-')[0]

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      {LANGUAGES.map((lang) => {
        const active = lang.code === current
        return (
          <div
            key={lang.code}
            role="button"
            onClick={() => i18n.changeLanguage(lang.code)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 12,
              padding: '13px 14px',
              borderRadius: 14,
              cursor: 'pointer',
              background: active ? 'var(--surface-pink)' : 'var(--surface-1)',
              border: active ? '1px solid var(--border-pink-bright)' : '1px solid var(--hairline-strong)',
            }}
          >
            <FlagIcon code={lang.code as FlagCode} size={26} />
            <span style={{ flex: 1, fontSize: 15, fontWeight: 600, color: active ? '#fff' : 'var(--ink-200)' }}>{lang.label}</span>
            {active && CheckIcon}
          </div>
        )
      })}
    </div>
  )
}