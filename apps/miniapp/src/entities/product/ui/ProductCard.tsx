import { useNavigate } from 'react-router-dom'
import { formatStars } from '../lib/format'
import type { ProductListItem } from '@/shared/types'
function compact(n: number): string {
  return new Intl.NumberFormat('en', { notation: 'compact', maximumFractionDigits: 1 }).format(n ?? 0)
}

const FALLBACK_BG =
  'radial-gradient(72% 70% at 30% 35%,#e3ab92 0,rgba(227,171,146,0) 60%),' +
  'radial-gradient(70% 80% at 73% 68%,#8e4350 0,rgba(142,67,80,0) 62%),' +
  'linear-gradient(140deg,#3a2126,#5b3138)'

const PlayIcon = (
  <svg width="11" height="11" viewBox="0 0 24 24" fill="#fff"><path d="M8 5v14l11-7z" /></svg>
)
const BagIcon = (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--ink-350)" strokeWidth="1.7" strokeLinejoin="round">
    <path d="M5 8h14l-1 11.2a2 2 0 0 1-2 1.8H8a2 2 0 0 1-2-1.8Z" />
    <path d="M8.5 8V6.5a3.5 3.5 0 0 1 7 0V8" />
  </svg>
)
const EyeIcon = (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--ink-350)" strokeWidth="1.7">
    <path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7Z" />
    <circle cx="12" cy="12" r="3" />
  </svg>
)
const StarIcon = (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="#f7b23b">
    <path d="M12 2l2.95 5.98 6.6.96-4.78 4.66 1.13 6.57L12 17.98 6.1 20.16l1.13-6.57L2.45 8.94l6.6-.96z" />
  </svg>
)

interface ProductCardProps {
  product: ProductListItem
}

/** Catalog/listing row for a single product (the NoxX "video row"). */
export function ProductCard({ product }: ProductCardProps) {
  const navigate = useNavigate()
  const tag = product.category?.title ?? product.tags?.[0]?.title ?? ''
  const thumbStyle = product.cover_url
    ? { background: `url(${product.cover_url}) center / cover no-repeat` }
    : { background: FALLBACK_BG }

  return (
    <div className="row" role="button" onClick={() => navigate(`/product/${product.slug}`)}>
      <div className="thumb" style={thumbStyle}>
        <div className="play"><div>{PlayIcon}</div></div>
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div className="ttl">{product.title}</div>
        {tag && <div className="tag">{tag}</div>}
        <div className="stats">
          <div className="stat">{BagIcon}<span>{compact(product.display_purchases)}</span></div>
          <div className="stat">{EyeIcon}<span>{compact(product.display_views)}</span></div>
          <div className="rate">{StarIcon}<span>{formatStars(product.price_stars)}</span></div>
        </div>
      </div>
    </div>
  )
}
