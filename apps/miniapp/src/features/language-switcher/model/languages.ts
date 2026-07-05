export interface LanguageOption {
  code: string
  label: string
}

/** Supported UI languages for the Mini App. */
export const LANGUAGES: ReadonlyArray<LanguageOption> = [
  { code: 'en', label: 'English' },
  { code: 'ru', label: 'Русский' },
  { code: 'de', label: 'Deutsch' },
  { code: 'el', label: 'Ελληνικά' },
  { code: 'ro', label: 'Română' },
  { code: 'bg', label: 'Български' },
  { code: 'mo', label: 'Moldovenească' },
  { code: 'sr', label: 'Српски' },
  { code: 'tr', label: 'Türkçe' },
]
