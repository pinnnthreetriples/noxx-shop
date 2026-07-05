/**
 * Dev-only mock data for the admin panel. Used as a fallback when the backend
 * (localhost:8000) is unreachable, so the UI can be explored without it.
 * Tree-shaken out of production builds via import.meta.env.DEV guards.
 * Resource keys MUST match the <Resource name="..."> values in App.tsx.
 */

type Row = Record<string, unknown>

const products: Row[] = [
  { id: 1, slug: 'midnight-desires', title: 'Midnight Desires', price_stars: 350, manual_usd: 4.99, trend_score: 92, is_premium: true, is_published: true, category_id: 1, views: 2400, created_at: '2026-06-01T10:00:00Z' },
  { id: 2, slug: 'velvet-secrets', title: 'Velvet Secrets', price_stars: 420, manual_usd: 5.99, trend_score: 78, is_premium: true, is_published: true, category_id: 1, views: 1890, created_at: '2026-06-03T12:30:00Z' },
  { id: 3, slug: 'private-moments', title: 'Private Moments', price_stars: 250, manual_usd: 3.49, trend_score: 85, is_premium: false, is_published: true, category_id: 2, views: 3120, created_at: '2026-06-05T09:15:00Z' },
  { id: 4, slug: 'gentle-touch', title: 'Gentle Touch', price_stars: 300, manual_usd: 3.99, trend_score: 60, is_premium: false, is_published: false, category_id: 2, views: 760, created_at: '2026-06-08T18:45:00Z' },
  { id: 5, slug: 'after-hours', title: 'After Hours', price_stars: 500, manual_usd: 6.99, trend_score: 88, is_premium: true, is_published: true, category_id: 3, views: 980, created_at: '2026-06-10T22:05:00Z' },
]

const categories: Row[] = [
  { id: 1, name: 'Romance', slug: 'romance', sort_order: 1, product_count: 2 },
  { id: 2, name: 'Soft', slug: 'soft', sort_order: 2, product_count: 2 },
  { id: 3, name: 'Premium', slug: 'premium', sort_order: 3, product_count: 1 },
]

const tags: Row[] = [
  { id: 1, name: '18+', slug: '18plus', product_count: 5 },
  { id: 2, name: 'New', slug: 'new', product_count: 3 },
  { id: 3, name: 'Popular', slug: 'popular', product_count: 2 },
  { id: 4, name: 'HD', slug: 'hd', product_count: 4 },
]

const users: Row[] = [
  { id: 101, telegram_id: 588213441, username: 'alex_n', first_name: 'Alex', is_premium: true, is_blocked: false, age_confirmed: true, notifications_enabled: true, balance_stars: 120, orders_count: 3, created_at: '2026-05-20T08:00:00Z' },
  { id: 102, telegram_id: 730112984, username: 'maria_k', first_name: 'Maria', is_premium: false, is_blocked: false, age_confirmed: true, notifications_enabled: false, balance_stars: 0, orders_count: 1, created_at: '2026-05-25T14:20:00Z' },
  { id: 103, telegram_id: 419002731, username: 'dmitry', first_name: 'Dmitry', is_premium: true, is_blocked: false, age_confirmed: true, notifications_enabled: true, balance_stars: 540, orders_count: 7, created_at: '2026-06-02T19:10:00Z' },
  { id: 104, telegram_id: 905417220, username: 'sveta', first_name: 'Sveta', is_premium: false, is_blocked: true, age_confirmed: false, notifications_enabled: true, balance_stars: 30, orders_count: 2, created_at: '2026-06-09T11:35:00Z' },
]

const orders: Row[] = [
  { id: 9001, user_id: 101, product_id: 1, total_stars: 350, paid_stars: 350, final_discount: 0, status: 'paid', created_at: '2026-06-12T10:11:00Z' },
  { id: 9002, user_id: 103, product_id: 5, total_stars: 500, paid_stars: 500, final_discount: 0, status: 'paid', created_at: '2026-06-14T16:42:00Z' },
  { id: 9003, user_id: 102, product_id: 3, total_stars: 250, paid_stars: 0, final_discount: 0, status: 'pending', created_at: '2026-06-15T09:03:00Z' },
  { id: 9004, user_id: 104, product_id: 2, total_stars: 420, paid_stars: 420, final_discount: 63, status: 'refunded', created_at: '2026-06-16T20:27:00Z' },
]

const promo_codes: Row[] = [
  { id: 1, code: 'WELCOME10', discount_type: 'percent', discount_value: 10, active: true, usage_limit: 100, used_count: 23, starts_at: '2026-06-01T00:00:00Z', expires_at: '2026-12-31T23:59:00Z' },
  { id: 2, code: 'PREMIUM25', discount_type: 'percent', discount_value: 25, active: false, usage_limit: 50, used_count: 50, starts_at: '2026-05-01T00:00:00Z', expires_at: '2026-07-01T00:00:00Z' },
  { id: 3, code: 'SUMMER15', discount_type: 'percent', discount_value: 15, active: true, usage_limit: 200, used_count: 87, starts_at: '2026-06-01T00:00:00Z', expires_at: '2026-09-01T00:00:00Z' },
  { id: 4, code: 'STARS50', discount_type: 'fixed', discount_value: 50, active: true, usage_limit: 30, used_count: 4, starts_at: '2026-06-20T00:00:00Z', expires_at: '2026-08-01T00:00:00Z' },
]

const support_tickets: Row[] = [
  { id: 1, user_id: 102, topic: 'Payment not credited', status: 'open', created_at: '2026-06-15T10:00:00Z' },
  { id: 2, user_id: 104, topic: 'Video will not play', status: 'pending', created_at: '2026-06-16T13:20:00Z' },
  { id: 3, user_id: 101, topic: 'Refund request', status: 'closed', created_at: '2026-06-13T08:45:00Z' },
  { id: 4, user_id: 103, topic: 'How to enable premium', status: 'open', created_at: '2026-06-18T07:30:00Z' },
]

const notifications: Row[] = [
  { id: 1, title: 'Summer sale -15%', body: 'Use code SUMMER15 on any video', product_id: 3, created_at: '2026-06-10T09:00:00Z' },
  { id: 2, title: 'New premium videos', body: 'Fresh premium content just dropped', product_id: 5, created_at: '2026-06-18T12:00:00Z' },
  { id: 3, title: 'Welcome bonus', body: 'Get 10% off your first purchase', product_id: 1, created_at: '2026-06-17T15:30:00Z' },
]

const admins: Row[] = [
  { id: 1, username: 'admin', role: 'superadmin', is_active: true, last_login: '2026-06-26T17:00:00Z' },
  { id: 2, username: 'moderator', role: 'moderator', is_active: true, last_login: '2026-06-25T11:20:00Z' },
]

const admin_logs: Row[] = [
  { id: 1, admin_id: 1, action: 'create', entity_type: 'product', entity_id: 1, created_at: '2026-06-01T10:00:00Z' },
  { id: 2, admin_id: 2, action: 'refund', entity_type: 'order', entity_id: 9004, created_at: '2026-06-16T20:30:00Z' },
  { id: 3, admin_id: 1, action: 'update', entity_type: 'promo_code', entity_id: 2, created_at: '2026-06-15T09:05:00Z' },
  { id: 4, admin_id: 2, action: 'block', entity_type: 'user', entity_id: 104, created_at: '2026-06-09T12:00:00Z' },
]

const link_delivery_logs: Row[] = [
  { id: 1, user_id: 101, order_id: 9001, product_id: 1, delivery_method: 'telegram', status: 'delivered', sent_at: '2026-06-12T10:12:00Z' },
  { id: 2, user_id: 103, order_id: 9002, product_id: 5, delivery_method: 'telegram', status: 'delivered', sent_at: '2026-06-14T16:43:00Z' },
  { id: 3, user_id: 102, order_id: 9003, product_id: 3, delivery_method: 'telegram', status: 'failed', sent_at: '2026-06-15T09:10:00Z' },
]


const settings: Row[] = [
  {
    id: 1,
    bot_name: 'Veri Bot',
    support_enabled: true,
    content_18_plus_enabled: true,
    default_language: 'ru',
    stars_to_usd_mode: 'manual',
    manual_stars_to_usd_rate: 0.013,
    max_discount_percent: 25,
    terms_text_en: 'By using this service you confirm you are 18+.',
    refund_policy_text_en: 'All sales are final. Refunds at our discretion.',
    notifications_enabled_by_default: true,
    subscription_coming_soon_enabled: false,
    subscription_coming_soon_text: 'Subscriptions are coming soon!',
  },
]

const DB: Record<string, Row[]> = {
  products, categories, tags, users, orders, promo_codes,
  support_tickets, notifications, admins, admin_logs, link_delivery_logs, settings,
}

function sortAndPage(rows: Row[], params: { pagination?: { page: number; perPage: number }; sort?: { field: string; order: string } }) {
  let data = [...rows]
  const sort = params.sort
  if (sort && sort.field) {
    data.sort((a, b) => {
      const av = a[sort.field] as never
      const bv = b[sort.field] as never
      if (av < bv) return sort.order === 'ASC' ? -1 : 1
      if (av > bv) return sort.order === 'ASC' ? 1 : -1
      return 0
    })
  }
  const total = data.length
  const pg = params.pagination
  if (pg) {
    const startIdx = (pg.page - 1) * pg.perPage
    data = data.slice(startIdx, startIdx + pg.perPage)
  }
  return { data, total }
}

export function mockGetList(resource: string, params: never) {
  const rows = DB[resource] || []
  return sortAndPage(rows, params)
}

export function mockGetOne(resource: string, id: string | number) {
  const rows = DB[resource] || []
  const row = rows.find((r) => String(r.id) === String(id))
  return row || { id }
}

export function mockGetMany(resource: string, ids: (string | number)[]) {
  const rows = DB[resource] || []
  return rows.filter((r) => ids.map(String).includes(String(r.id)))
}

export function hasMock(resource: string): boolean {
  return Boolean(DB[resource])
}
