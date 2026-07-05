export interface TelegramUser {
  id: number
  first_name?: string
  last_name?: string
  username?: string
  language_code?: string
  is_premium?: boolean
}

export interface InitDataParsed {
  user?: string
  auth_date: string
  hash: string
  query_id?: string
}

export const SUPPORTED_LANGUAGES = ['en', 'ru', 'de', 'el', 'ro', 'bg', 'mo', 'sr', 'tr'] as const
export type SupportedLanguage = (typeof SUPPORTED_LANGUAGES)[number]

export const LANGUAGE_NAMES: Record<SupportedLanguage, string> = {
  en: 'English',
  ru: 'Russian',
  de: 'German',
  el: 'Greek',
  ro: 'Romanian',
  bg: 'Bulgarian',
  mo: 'Moldavian',
  sr: 'Serbian',
  tr: 'Turkish',
}

export interface SeedCategoryInput {
  slug: string
  translations: Record<string, string>
}

export interface SeedTagInput {
  slug: string
  translations: Record<string, string>
}
