import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface FavoritesState {
  /** Favourited product ids (client-side source of truth). */
  ids: number[]
  toggle: (id: number) => void
  add: (id: number) => void
  remove: (id: number) => void
  isFavorite: (id: number) => boolean
  clear: () => void
}

/** Persisted favourites store. Owned by the favorites feature. */
export const useFavoritesStore = create<FavoritesState>()(
  persist(
    (set, get) => ({
      ids: [],
      toggle: (id) =>
        set((s) => ({
          ids: s.ids.includes(id) ? s.ids.filter((x) => x !== id) : [...s.ids, id],
        })),
      add: (id) => set((s) => (s.ids.includes(id) ? s : { ids: [...s.ids, id] })),
      remove: (id) => set((s) => ({ ids: s.ids.filter((x) => x !== id) })),
      isFavorite: (id) => get().ids.includes(id),
      clear: () => set({ ids: [] }),
    }),
    { name: 'tma-favorites' },
  ),
)
