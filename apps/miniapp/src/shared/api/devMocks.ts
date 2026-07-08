/**
 * Dev-only mock data. Used by the API client as a fallback when the backend
 * is unavailable in development (import.meta.env.DEV). Lets the UI be reviewed
 * with realistic content. NEVER active in production builds.
 */
import type { Order, ProductDetail, ProductListItem } from '../types'

const cover = 'https://picsum.photos/seed/midnight-desires/600/338'

export const mockProduct: ProductDetail = {
  id: 1,
  slug: 'midnight-desires',
  title: 'Midnight Desires',
  cover_url: cover,
  category: { id: 1, slug: 'romance', title: 'Romance' },
  tags: [
    { id: 1, slug: 'romance', title: 'Romance' },
    { id: 2, slug: '18plus', title: '18+' },
  ],
  display_views: 2400,
  display_purchases: 2400,
  is_premium: true,
  price_stars: 350,
  approx_usd: 4.9,
  description:
    'A sensual journey through the night. Passion, intimacy, and unforgettable moments.',
  preview_video_url: 'https://www.w3schools.com/html/mov_bbb.mp4',
}

export const mockProducts: ProductListItem[] = [mockProduct]

export const mockOrders: Order[] = [
  {
    id: 1,
    status: 'paid',
    total_stars: 350,
    base_discount_percent: 0,
    promo_discount_percent: 0,
    final_discount_percent: 0,
    paid_stars: 350,
    approx_usd: 4.9,
    created_at: new Date().toISOString(),
    items: [
      {
        id: 1,
        product_id: 1,
        title: 'Midnight Desires',
        quantity: 1,
        price_stars: 350,
        google_drive_link: 'https://drive.google.com/',
      },
    ],
  },
]

export const mockProfile = {
  first_name: 'Veri',
  last_name: 'User',
  username: 'veri_user',
  telegram_id: 1,
  is_premium: true,
}

export const mockSupportTickets = [
  {
    id: 1,
    topic: 'Payment issue',
    status: 'answered',
    created_at: new Date(Date.now() - 3600_000).toISOString(),
    messages: [
      { id: 1, sender_type: 'user', text: 'My payment did not go through.', created_at: new Date(Date.now() - 3600_000).toISOString() },
      { id: 2, sender_type: 'admin', text: 'Thanks for reaching out — could you share the order number?', created_at: new Date(Date.now() - 1800_000).toISOString() },
    ],
  },
]

/** Resolve a mock payload for a given GET path, or undefined if unmocked. */
export function resolveMock(url: string): unknown {
  const path = url.split('?')[0].replace(/\/+$/, '')
  if (path === '/products' || path.endsWith('/products')) return mockProducts
  if (path.includes('/products/')) return mockProduct
  if (path.endsWith('/orders')) return mockOrders
  if (path.endsWith('/profile')) return mockProfile
  if (path.endsWith('/support/tickets')) return mockSupportTickets
  return undefined
}
