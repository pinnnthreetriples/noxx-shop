/** Format a Telegram Stars price, optionally with an approximate USD value. */
export function formatStars(stars: number): string {
  return new Intl.NumberFormat().format(stars)
}

export function formatApproxUsd(usd?: number): string | undefined {
  if (usd == null) return undefined
  try {
    return new Intl.NumberFormat(undefined, { style: 'currency', currency: 'USD' }).format(usd)
  } catch {
    return `$${usd}`
  }
}
