import { IconButton } from '@/shared/ui'
import { useIsFavorite, useToggleFavorite } from '@/features/favorites'
import type { MouseEvent } from 'react'
interface FavoriteButtonProps {
  productId: number
}

/** Heart toggle wired to the favorites store. */
export function FavoriteButton({ productId }: FavoriteButtonProps) {
  const isFav = useIsFavorite(productId)
  const toggle = useToggleFavorite()

  const onClick = (e: MouseEvent) => {
    e.stopPropagation()
    toggle(productId)
  }

  return (
    <IconButton aria-label={isFav ? 'Remove from favorites' : 'Add to favorites'} onClick={onClick}>
      <svg width="20" height="20" viewBox="0 0 24 24" fill={isFav ? 'var(--pink-500)' : 'none'} stroke={isFav ? 'var(--pink-500)' : '#e9e2e8'} strokeWidth="1.8">
        <path d="M12 20.5C7 17 3.5 13.8 3.5 9.6 3.5 6.9 5.6 5 8 5c1.6 0 3 .9 4 2.3C13 5.9 14.4 5 16 5c2.4 0 4.5 1.9 4.5 4.6 0 4.2-3.5 7.4-8.5 10.9z" />
      </svg>
    </IconButton>
  )
}
