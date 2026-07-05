/** Telegram user as exposed by the Mini App SDK (initDataUnsafe.user). */
export interface TelegramUser {
  id: number
  first_name: string
  last_name?: string
  username?: string
  photo_url?: string
  language_code?: string
  is_premium?: boolean
}

/** Convenience: display name derived from a Telegram user. */
export function getUserDisplayName(user: Pick<TelegramUser, 'first_name' | 'last_name' | 'username'>): string {
  const full = [user.first_name, user.last_name].filter(Boolean).join(' ').trim()
  return full || user.username || 'User'
}
