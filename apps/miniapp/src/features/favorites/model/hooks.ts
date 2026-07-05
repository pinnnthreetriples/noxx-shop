import { useCallback } from 'react'
import { haptic } from '../../../shared/lib/telegram'
import { useFavoritesStore } from './store'

/** Reactive list of favourited product ids. */
export function useFavoriteIds(): number[] {
  return useFavoritesStore((s) => s.ids)
}

/** Reactive boolean for a single product. */
export function useIsFavorite(id: number): boolean {
  return useFavoritesStore((s) => s.ids.includes(id))
}

/** Returns a stable toggle callback with haptic feedback. */
export function useToggleFavorite(): (id: number) => void {
  const toggle = useFavoritesStore((s) => s.toggle)
  return useCallback(
    (id: number) => {
      haptic('light')
      toggle(id)
    },
    [toggle],
  )
}
