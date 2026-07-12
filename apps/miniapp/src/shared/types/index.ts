export interface ProductListItem {
  id: number
  slug: string
  title: string
  cover_url?: string
  category?: { id: number; slug: string; title: string }
  tags: { id: number; slug: string; title: string }[]
  display_views: number
  display_purchases: number
  is_premium: boolean
  price_stars: number
  approx_usd?: number
}

export interface ProductDetail extends ProductListItem {
  description?: string
  preview_video_url?: string
}

export interface OrderItem {
  id: number
  product_id: number
  title: string
  quantity: number
  price_stars: number
  google_drive_link?: string
  tg_delivered?: boolean
}

export interface Order {
  id: number
  status: string
  total_stars: number
  base_discount_percent: number
  promo_discount_percent: number
  final_discount_percent: number
  paid_stars: number
  approx_usd?: number
  subscription_plan?: string
  created_at: string
  items: OrderItem[]
}
