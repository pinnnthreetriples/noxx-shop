import polyglotI18nProvider from 'ra-i18n-polyglot'
import russianMessages from './ru'

export const i18nProvider = polyglotI18nProvider(() => russianMessages, 'ru')
