// NoxX view-model. Supplies every binding the transpiled screen views
// reference, sourced from the local store + the real backend API.
import * as React from 'react'
import * as RR from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import * as Store from '../lib/store'
import * as Model from './model'
import * as FlagIcon from '../ui/FlagIcon'
import api from '../api/client'
import { useProducts, useProduct } from '@/entities/product/api/queries'
import { useOrders } from '@/entities/order/api/queries'
import { useProfile } from '@/entities/user/api/queries'
import type { ProductListItem } from '../types'

const PINK = '#ff3d8b'
const DIM = '#6b6470'
const STAR_USD = 0.02 // fallback rate; the effective rate comes from GET /settings
const fmtNum = (n: number) => (n >= 1000 ? (n / 1000).toFixed(1).replace(/\.0$/, '') + 'K' : String(n))
const fmtUsd = (n: number) => '$' + n.toFixed(2)

const MEDIA_BASE = ((import.meta.env.VITE_MEDIA_BASE_URL as string) || '').replace(/\/+$/, '')

// Design-baseline gradients: shown under covers while they load and as
// fallback when a product has no cover image.
const FALLBACK_BGS = [
  'radial-gradient(72% 70% at 30% 35%,#e3ab92 0%,rgba(227,171,146,0) 60%),radial-gradient(70% 80% at 73% 68%,#8e4350 0%,rgba(142,67,80,0) 62%),linear-gradient(140deg,#3a2126,#5b3138)',
  'radial-gradient(70% 70% at 68% 32%,#cf90a6 0%,rgba(207,144,166,0) 60%),radial-gradient(72% 80% at 28% 74%,#5e3148 0%,rgba(94,49,72,0) 62%),linear-gradient(140deg,#2d1b27,#4b2c3b)',
  'radial-gradient(72% 72% at 36% 40%,#ddae8c 0%,rgba(221,174,140,0) 60%),radial-gradient(70% 80% at 78% 72%,#6f4636 0%,rgba(111,70,54,0) 62%),linear-gradient(140deg,#3a2820,#574036)',
  'radial-gradient(72% 70% at 58% 34%,#cd8081 0%,rgba(205,128,129,0) 60%),radial-gradient(70% 80% at 26% 72%,#5c2d36 0%,rgba(92,45,54,0) 62%),linear-gradient(140deg,#331d22,#52303b)',
]

function coverBg(id: number, coverUrl?: string | null): string {
  const grad = FALLBACK_BGS[id % FALLBACK_BGS.length]
  if (!coverUrl) return grad
  const url = /^https?:\/\//.test(coverUrl) ? coverUrl : MEDIA_BASE + (coverUrl.startsWith('/') ? '' : '/') + coverUrl
  return `url("${url}") center / cover no-repeat, ${grad}`
}

interface Rec {
  id: number
  slug: string
  title: string
  tagline: string
  duration: string
  catSlug: string
  purchasesStat: string
  viewsStat: string
  viewsFull: string
  stars: number
  usd: string
  discount: number
  premium: boolean
  badge: string
  sold: number
  desc: string
  status: 'downloaded' | 'available'
  bg: string
}

function toRec(p: ProductListItem & { description?: string }, rate: number): Rec {
  const tags = p.tags || []
  // Match New/Popular/Premium by slug OR localized title, across category and tags:
  // admins may rename a category (slug stays behind) or attach these as tags, so a
  // slug-only check silently misses them and the chip falls back to flat grey text.
  const norm = (s?: string) => (s || '').trim().toLowerCase()
  const hasKind = (kind: string) =>
    norm(p.category?.slug) === kind || norm(p.category?.title) === kind ||
    tags.some((t) => norm(t.slug) === kind || norm(t.title) === kind)
  return {
    id: p.id,
    slug: p.slug,
    title: p.title,
    tagline: p.category?.title || tags.map((t) => t.title).join(' · '),
    duration: '', // backend has no duration; views hide the chip when empty
    catSlug: p.category?.slug || '',
    purchasesStat: fmtNum(p.display_purchases),
    viewsStat: fmtNum(p.display_views),
    viewsFull: fmtNum(p.display_views),
    stars: p.price_stars,
    usd: fmtUsd(p.approx_usd ?? p.price_stars * rate),
    discount: 0,
    premium: p.is_premium,
    badge: p.is_premium || hasKind('premium') ? 'Premium'
      : hasKind('new') ? 'New'
      : hasKind('popular') ? 'Popular' : '',
    sold: p.display_purchases,
    desc: p.description ?? '',
    status: 'available',
    bg: coverBg(p.id, p.cover_url),
  }
}

function fallbackRec(productId: number, title: string, priceStars: number, rate: number): Rec {
  return {
    id: productId, slug: '', title, tagline: '', duration: '', catSlug: '',
    purchasesStat: '', viewsStat: '', viewsFull: '', stars: priceStars,
    usd: fmtUsd(priceStars * rate), discount: 0, premium: false, badge: '',
    sold: 0, desc: '', status: 'available', bg: coverBg(productId, null),
  }
}

// Support conversation shapes — mirror the backend SupportTicketDetail /
// SupportMessageOut (apps/backend/app/modules/support/schemas.py).
export interface SupportMsg {
  id: number
  sender_type: string
  text?: string | null
  file_url?: string | null
  file_type?: string | null
  created_at: string
}
export interface SupportTicket {
  id: number
  topic: string
  status: string
  created_at: string
  messages: SupportMsg[]
}

export function useNoxx() {
  const nav = RR.useNavigate()
  const loc = RR.useLocation()
  const params = RR.useParams()
  const qc = useQueryClient()
  const cartItems = Store.useAppStore((s) => s.cartItems)
  const addToCart = Store.useAppStore((s) => s.addToCart)
  const removeFromCart = Store.useAppStore((s) => s.removeFromCart)
  const clearCart = Store.useAppStore((s) => s.clearCart)
  const language = Store.useAppStore((s) => s.language)
  const { t } = useTranslation()
  const setLanguage = Store.useAppStore((s) => s.setLanguage)
  const setAgeConfirmed = Store.useAppStore((s) => s.setAgeConfirmed)
  const payMethod = Store.useAppStore((s) => s.payMethod)
  const setPayMethod = Store.useAppStore((s) => s.setPayMethod)
  const payCrypto = payMethod === 'crypto'

  const [menuOpenId, setMenuOpenId] = React.useState<number | null>(null)
  const [langOpen, setLangOpen] = React.useState(false)
  const [activeFilter, setActiveFilter] = React.useState('all')
  const [activeTab, setActiveTab] = React.useState('all')
  const [selectedPlan, setSelectedPlan] = React.useState('year')
  const [promoVisible, setPromoVisible] = React.useState(true)
  const [gateChecked, setGateChecked] = React.useState(false)

  // Stars→USD rate: admin "manual" rate wins; "auto" = the design-baseline 0.02
  // (mirrors the backend default in core/config.py).
  const settingsQ = useQuery({
    queryKey: ['settings'],
    queryFn: async () => (await api.get<{
      stars_to_usd_mode?: string
      manual_stars_to_usd_rate?: number | null
      subscription_coming_soon_enabled?: boolean
      subscription_coming_soon_text?: string | null
      terms_text_en?: string | null
      refund_policy_text_en?: string | null
      discount_first_purchase_percent?: number
      discount_bulk_percent?: number
      discount_bulk_min_items?: number
      discount_loyalty_percent?: number
      sub_price_week_stars?: number
      sub_price_month_stars?: number
      sub_price_year_stars?: number
      // per-language legal texts: terms_text_${lang} / refund_policy_text_${lang}
      [key: string]: unknown
    }>('/settings')).data,
    staleTime: 5 * 60_000,
  })
  const starRate = settingsQ.data?.stars_to_usd_mode === 'manual' && settingsQ.data?.manual_stars_to_usd_rate
    ? Number(settingsQ.data.manual_stars_to_usd_rate) : STAR_USD

  const productsQ = useProducts()
  const products = React.useMemo(() => productsQ.data ?? [], [productsQ.data])
  const recs = React.useMemo(() => products.map((p) => toRec(p, starRate)), [products, starRate])

  const detailQ = useProduct(params.slug)
  const ordersQ = useOrders()
  const profileQ = useProfile()
  const orders = React.useMemo(() => ordersQ.data ?? [], [ordersQ.data])

  const favQ = useQuery({
    queryKey: ['favorites'],
    queryFn: async () => (await api.get<ProductListItem[]>('/favorites')).data,
  })
  const favList = React.useMemo(() => favQ.data ?? [], [favQ.data])
  const favSet = React.useMemo(() => new Set(favList.map((p) => p.id)), [favList])

  const favMut = useMutation({
    mutationFn: async (id: number) => {
      if (favSet.has(id)) await api.delete(`/favorites/${id}`)
      else await api.post(`/favorites/${id}`)
    },
    onMutate: async (id: number) => {
      await qc.cancelQueries({ queryKey: ['favorites'] })
      const prev = qc.getQueryData<ProductListItem[]>(['favorites']) ?? []
      const next = prev.some((p) => p.id === id)
        ? prev.filter((p) => p.id !== id)
        : [...prev, ...products.filter((p) => p.id === id)]
      qc.setQueryData(['favorites'], next)
      return { prev }
    },
    onError: (_e, _id, ctx) => { if (ctx) qc.setQueryData(['favorites'], ctx.prev) },
    onSettled: () => qc.invalidateQueries({ queryKey: ['favorites'] }),
  })
  const toggleFavorite = (id: number) => favMut.mutate(id)

  const checkoutMut = useMutation({
    mutationFn: async () =>
      (await api.post<{ order_id: number; invoice_url: string; provider?: string }>('/checkout/create', {
        product_ids: cartRecs.map((r) => r.id),
        promo_code: promoApplied || undefined,
        provider: payCrypto ? 'orbchain' : 'telegram',
      })).data,
    onSuccess: (data) => {
      // In-app crypto checkout: our own payment screen (coin picker + address),
      // no redirect out of the mini-app. The order is created; free the cart.
      if (data.provider === 'orbchain') {
        clearCart()
        nav('/pay/' + data.order_id)
        return
      }
      // Telegram Stars fallback — native invoice sheet.
      const url = data.invoice_url || ''
      const tg = window.Telegram?.WebApp
      const finish = () => {
        clearCart()
        qc.invalidateQueries({ queryKey: ['orders'] })
        nav('/success')
      }
      if (tg?.initData && tg.openInvoice && url.startsWith('https://t.me/$')) {
        // 'cancelled' = user closed the sheet themselves — stay on checkout, no error.
        tg.openInvoice(url, (status) => {
          if (status === 'paid') finish()
          else if (status === 'failed') nav('/fail')
        })
        return
      }
      // No native invoice sheet (browser dev / bot deep link): open the link and
      // stay here — we can't observe the payment, so never claim success.
      if (url.startsWith('http')) { if (tg?.openLink) tg.openLink(url); else window.open(url, '_blank') }
    },
    onError: () => nav('/fail'),
  })

  // Support ticket: lands in the admin panel; the bot pings admins about it.
  const supportMut = useMutation({
    mutationFn: async (p: { topic: string; message: string }) =>
      (await api.post<{ id: number }>('/support/tickets', p)).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['support-tickets'] }),
  })

  // Two-way support: the user's tickets with their full message thread (user +
  // admin). Polled so the owner's replies appear while the screen is open.
  // Also fetched on the profile screen to power the unread-reply badge.
  const onSupport = loc.pathname === '/support'
  const onProfile = loc.pathname === '/profile'
  const supportTicketsQ = useQuery({
    queryKey: ['support-tickets'],
    queryFn: async () => (await api.get<SupportTicket[]>('/support/tickets')).data,
    enabled: onSupport || onProfile,
    refetchInterval: onSupport ? 15_000 : false,
  })

  // Unread badge: is there an admin reply newer than the last one the user saw
  // on /support? Tracked client-side per device — no backend read-state.
  const latestAdminReplyAt = Math.max(0, ...(supportTicketsQ.data || []).flatMap(
    (tk) => tk.messages.filter((m) => m.sender_type === 'admin').map((m) => Date.parse(m.created_at) || 0),
  ))
  const supportUnread = latestAdminReplyAt > Number(localStorage.getItem('noxx_support_seen_at') || 0)
  React.useEffect(() => {
    if (onSupport && latestAdminReplyAt) localStorage.setItem('noxx_support_seen_at', String(latestAdminReplyAt))
  }, [onSupport, latestAdminReplyAt])
  const supportReplyMut = useMutation({
    mutationFn: async (p: { ticketId: number; text: string }) =>
      (await api.post(`/support/tickets/${p.ticketId}/messages`, { text: p.text })).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['support-tickets'] }),
  })

  // Premium subscription checkout — same invoice flow as products, minus the cart.
  const subscribeMut = useMutation({
    mutationFn: async (plan: string) =>
      (await api.post<{ order_id: number; invoice_url: string; provider?: string }>('/subscription/checkout', {
        plan,
        provider: payCrypto ? 'orbchain' : 'telegram',
      })).data,
    onSuccess: (data) => {
      if (data.provider === 'orbchain') { nav('/pay/' + data.order_id); return }
      const url = data.invoice_url || ''
      const tg = window.Telegram?.WebApp
      if (tg?.initData && tg.openInvoice && url.startsWith('https://t.me/$')) {
        tg.openInvoice(url, (status) => {
          if (status === 'paid') {
            qc.invalidateQueries({ queryKey: ['profile'] })
            qc.invalidateQueries({ queryKey: ['orders'] })
            nav('/success', { state: { sub: true } })
          } else if (status === 'failed') nav('/fail')
        })
        return
      }
      if (url.startsWith('http')) { if (tg?.openLink) tg.openLink(url); else window.open(url, '_blank') }
    },
    onError: () => nav('/fail'),
  })

  const cartIds = new Set(cartItems.map((c) => c.productId))

  const statusDown: React.CSSProperties = { padding: '3px 9px', borderRadius: '999px', background: 'rgba(86,222,160,.14)', color: '#56dea0', fontSize: '11.5px', fontWeight: 700 }
  const statusAvail: React.CSSProperties = { padding: '3px 9px', borderRadius: '999px', background: 'rgba(255,255,255,.08)', color: '#b7adb5', fontSize: '11.5px', fontWeight: 700 }
  // category chips always carry a colour — Premium pink / Popular amber / New mint, others a neutral accent; never flat grey
  const tagStyleFor = (label: string): React.CSSProperties => {
    const base: React.CSSProperties = { padding: '5px 11px', borderRadius: '999px', fontSize: '12.5px', fontWeight: 600 }
    switch (label.toLowerCase()) {
      case 'premium': return { ...base, background: 'rgba(255,120,180,.13)', border: '1px solid rgba(255,120,180,.32)', color: '#ff9ecb' }
      case 'popular': return { ...base, background: 'rgba(255,170,80,.13)', border: '1px solid rgba(255,170,80,.32)', color: '#ffc36e' }
      case 'new': return { ...base, background: 'rgba(90,220,170,.13)', border: '1px solid rgba(90,220,170,.32)', color: '#8fe8cc' }
      default: return { ...base, background: 'rgba(150,130,220,.13)', border: '1px solid rgba(150,130,220,.30)', color: '#c4b8e8' }
    }
  }

  const vmVideo = (rec: Rec) => {
    const inCart = cartIds.has(rec.id)
    const fav = favSet.has(rec.id)
    const addStyle: React.CSSProperties = { display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px', padding: '8px 14px', borderRadius: '12px', border: 'none', fontSize: '13px', fontWeight: 700, cursor: 'pointer', background: inCart ? 'rgba(255,255,255,.1)' : 'linear-gradient(135deg,#ff5aa0,#ff2e93)', color: '#fff' }
    return {
      id: rec.id, slug: rec.slug, title: rec.title, tagline: rec.tagline, duration: rec.duration,
      bg: { position: 'absolute', inset: 0, background: rec.bg } as React.CSSProperties,
      purchases: rec.purchasesStat, views: rec.viewsStat, viewsFull: rec.viewsFull,
      stars: rec.stars, priceFmt: String(rec.stars), usd: rec.usd, soldFmt: fmtNum(rec.sold),
      premium: rec.premium, discount: rec.discount > 0 ? ('−' + rec.discount + '%') : '', hasBadge: !!rec.badge, badge: rec.badge, badgeStyle: { display: 'inline-block', color: rec.badge === 'Premium' ? '#ff9ecb' : rec.badge === 'Popular' ? '#ffc36e' : '#8fe8cc', fontSize: '11px', fontWeight: 700 },
      // card subtitle: hide the category when the colored badge already says the same
      cardSub: rec.badge && rec.tagline.trim().toLowerCase() === rec.badge.toLowerCase() ? '' : rec.tagline,
      inCart, notInCart: !inCart,
      onOpen: () => { if (rec.slug) nav('/product/' + rec.slug) },
      // Buttons live inside the card, whose own onClick opens the product —
      // stop propagation so taps on them don't also navigate.
      onAdd: (e?: React.MouseEvent) => { e?.stopPropagation(); if (!inCart) addToCart(rec.id) },
      onRemove: (e?: React.MouseEvent) => { e?.stopPropagation(); removeFromCart(rec.id) },
      onMenu: (e?: React.MouseEvent) => { e?.stopPropagation(); setMenuOpenId(menuOpenId === rec.id ? null : rec.id) },
      menuOpen: menuOpenId === rec.id,
      status: rec.status === 'downloaded' ? 'Downloaded' : 'Available',
      statusStyle: rec.status === 'downloaded' ? statusDown : statusAvail,
      downloaded: rec.status === 'downloaded', available: rec.status !== 'downloaded',
      onFav: (e?: React.MouseEvent) => { e?.stopPropagation(); toggleFavorite(rec.id) },
      heartFill: fav ? PINK : 'none', heartStroke: fav ? PINK : '#9a8f99',
      addStyle, addLabel: inCart ? 'In cart' : 'Add',
    }
  }

  const cartRecs = cartItems.map((c) => recs.find((r) => r.id === c.productId)).filter(Boolean) as Rec[]

  // A deleted product must not haunt the persisted cart: its stored id renders
  // nothing yet kept Checkout and the fab badge alive. Purge once the catalog is in.
  React.useEffect(() => {
    if (!productsQ.isSuccess) return
    cartItems.filter((c) => !recs.some((r) => r.id === c.productId)).forEach((c) => removeFromCart(c.productId))
  }, [productsQ.isSuccess, recs, cartItems, removeFromCart])
  const favRecs = recs.filter((r) => favSet.has(r.id))

  // purchases: one library row per bought product; "Downloaded" once a delivery link exists
  const purchaseRecs = React.useMemo(() => {
    const byProduct = new Map<number, Rec>()
    for (const o of orders) {
      if (o.status !== 'paid') continue // pending/failed checkouts are not purchases
      for (const it of o.items || []) {
        const base = recs.find((r) => r.id === it.product_id) ?? fallbackRec(it.product_id, it.title, it.price_stars, starRate)
        const status: Rec['status'] = (it.google_drive_link || it.tg_delivered) ? 'downloaded' : 'available'
        const existing = byProduct.get(it.product_id)
        if (!existing || status === 'downloaded') byProduct.set(it.product_id, { ...base, status })
      }
    }
    return [...byProduct.values()]
  }, [orders, recs, starRate])
  const purchaseFiltered = purchaseRecs.filter((v) => activeTab === 'all' ? true : activeTab === 'downloaded' ? v.status === 'downloaded' : v.status !== 'downloaded')

  const cartTotalStars = cartRecs.reduce((s, v) => s + v.stars, 0)
  const cartTotalUsdN = cartRecs.reduce((s, v) => s + parseFloat(v.usd.replace('$', '')), 0)

  // Server-side discount math (auto tiers + promo) — the backend is the source
  // of truth, the invoice charges exactly to_pay_stars.
  interface EstimateOut { total_stars: number; base_discount_percent: number; promo_discount_percent: number; final_discount_percent: number; to_pay_stars: number }
  const [promoInput, setPromoInput] = React.useState('')
  const [promoApplied, setPromoApplied] = React.useState<string | null>(null)
  const cartIdsArr = cartItems.map((c) => c.productId)
  const estimateQ = useQuery({
    queryKey: ['estimate', cartIdsArr, promoApplied],
    queryFn: async () => (await api.post<EstimateOut>('/cart/estimate', { product_ids: cartIdsArr, promo_code: promoApplied || undefined })).data,
    enabled: cartIdsArr.length > 0,
  })
  const est = estimateQ.data
  const coToPayStars = est?.to_pay_stars ?? cartTotalStars
  // Row labels keyed by the admin-configured tier percents
  const sset = settingsQ.data
  const DISCOUNT_LABELS: Record<number, string> = {
    [sset?.discount_first_purchase_percent ?? 10]: 'First purchase',
    [sset?.discount_bulk_percent ?? 15]: `${sset?.discount_bulk_min_items ?? 20}+ videos`,
    [sset?.discount_loyalty_percent ?? 30]: 'Loyalty',
  }

  // One row per applied discount; the amounts always add up to subtotal − total,
  // so the promo row absorbs the max_discount cap when it kicks in.
  const basePct = est?.base_discount_percent ?? 0
  const promoPct = est?.promo_discount_percent ?? 0
  const totalSave = cartTotalStars - coToPayStars
  const baseSave = promoPct > 0 ? Math.min(Math.floor(cartTotalStars * basePct / 100), totalSave) : totalSave
  const coDiscountRows = [
    ...(basePct > 0 ? [{ label: DISCOUNT_LABELS[basePct] ?? 'Discount', pct: basePct, stars: '−' + baseSave, usd: '−' + fmtUsd(baseSave * starRate) }] : []),
    ...(promoPct > 0 ? [{ label: 'Promo' + (promoApplied ? ' · ' + promoApplied.toUpperCase() : ''), pct: promoPct, stars: '−' + (totalSave - baseSave), usd: '−' + fmtUsd((totalSave - baseSave) * starRate) }] : []),
  ]

  const favIdsArr = favList.map((p) => p.id)
  const favEstQ = useQuery({
    queryKey: ['estimate', favIdsArr],
    queryFn: async () => (await api.post<EstimateOut>('/cart/estimate', { product_ids: favIdsArr })).data,
    enabled: favIdsArr.length > 0,
  })

  // payment history: real orders grouped by month (backend returns newest-first)
  const payHistory = React.useMemo(() => {
    const STATUS: Record<string, { label: string; color: string }> = {
      paid: { label: 'Completed', color: '#7ee0c0' },
      pending: { label: 'Pending', color: '#f7b23b' },
      failed: { label: 'Failed', color: '#ff5a6e' },
      cancelled: { label: 'Cancelled', color: '#9aa0b3' },
      refunded_manual: { label: 'Refunded', color: '#9aa0b3' },
    }
    const groups: { label: string; items: { id: number; title: string; date: string; statusLabel: string; statusColor: string; stars: string; usd: string }[] }[] = []
    for (const o of orders) {
      const d = new Date(o.created_at)
      const label = d.toLocaleString('en-US', { month: 'long', year: 'numeric' }).toUpperCase()
      if (!groups.length || groups[groups.length - 1].label !== label) groups.push({ label, items: [] })
      const st = STATUS[o.status] ?? { label: o.status, color: '#9aa0b3' }
      const first = o.items?.[0]?.title
      const subTitle = o.subscription_plan
        ? 'Premium · ' + ({ week: 'Weekly', month: 'Monthly', year: 'Yearly' }[o.subscription_plan] ?? o.subscription_plan)
        : null
      groups[groups.length - 1].items.push({
        id: o.id,
        title: subTitle ?? (first ? (o.items.length > 1 ? `${first} +${o.items.length - 1} more` : first) : `Order #${o.id}`),
        date: d.toLocaleString('en-US', { month: 'short', day: '2-digit' }),
        statusLabel: st.label, statusColor: st.color,
        stars: o.paid_stars.toLocaleString('en-US'),
        usd: fmtUsd(o.approx_usd ?? o.paid_stars * starRate),
      })
    }
    return groups
  }, [orders, starRate])
  const paidOrders = orders.filter((o) => o.status === 'paid')
  const payTotalStars = paidOrders.reduce((s, o) => s + o.paid_stars, 0)
  const payTotalUsd = fmtUsd(paidOrders.reduce((s, o) => s + (o.approx_usd ?? o.paid_stars * starRate), 0))

  // detail (product page) — resolved from :slug; list item renders instantly,
  // detail query adds the description
  const listMatch = params.slug ? recs.find((r) => r.slug === params.slug) : undefined
  const dRec: Rec = detailQ.data ? toRec(detailQ.data, starRate) : listMatch ?? fallbackRec(0, '', 0, starRate)

  // record a real view once per opened product
  const viewedRef = React.useRef<number | null>(null)
  const detailId = params.slug ? dRec.id : 0
  React.useEffect(() => {
    if (detailId && viewedRef.current !== detailId) {
      viewedRef.current = detailId
      api.post(`/products/${detailId}/view`).catch(() => {})
    }
  }, [detailId])

  const detailTags = detailQ.data?.tags?.map((t) => t.title) ?? []
  const dupCat = dRec.badge && dRec.catSlug === dRec.badge.toLowerCase()
  // premium gets its chip; non-premium gets nothing — a "Standard" label is noise
  const tagLabels = [...new Set([dupCat ? '' : dRec.tagline, ...detailTags, dRec.premium ? 'Premium' : ''].filter(Boolean))]
  // Premium perk: active subscriber gets premium videos for free (claim)
  const detailOwned = purchaseRecs.some((r) => r.id === dRec.id)
  const claimMut = useMutation({
    mutationFn: async (id: number) =>
      (await api.post<{ ok: boolean; order_id: number }>('/subscription/claim', { product_id: id })).data,
    onSuccess: () => {
      window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred?.('success')
      qc.invalidateQueries({ queryKey: ['orders'] })
      nav('/purchases')
    },
  })
  const rawPreview = detailQ.data?.preview_video_url || ''
  const detail = {
    id: dRec.id, bg: { position: 'absolute', inset: 0, background: dRec.bg } as React.CSSProperties,
    title: dRec.title, desc: dRec.desc, viewsFull: dRec.viewsFull, purchases: dRec.purchasesStat, stars: dRec.stars,
    tagObjs: tagLabels.map((label) => ({ label, style: tagStyleFor(label) })),
    previewUrl: rawPreview ? (/^https?:\/\//.test(rawPreview) ? rawPreview : MEDIA_BASE + (rawPreview.startsWith('/') ? '' : '/') + rawPreview) : '',
    inCart: cartIds.has(dRec.id),
    owned: detailOwned,
    canClaim: !!profileQ.data?.is_premium && dRec.premium && !detailOwned,
    onClaim: () => { if (!claimMut.isPending) claimMut.mutate(dRec.id) },
    claimBusy: claimMut.isPending,
    onAdd: () => {
      if (cartIds.has(dRec.id)) return
      addToCart(dRec.id)
      window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred?.('success')
    },
    onBuy: () => { if (!cartIds.has(dRec.id)) addToCart(dRec.id); nav('/checkout') },
    onFav: () => toggleFavorite(dRec.id),
    heartFill: favSet.has(dRec.id) ? PINK : 'none', heartStroke: favSet.has(dRec.id) ? PINK : '#fff',
  }

  // bottom-nav active styling
  const path = loc.pathname
  const navColor = (active: boolean) => (active ? '#fff' : DIM)
  const navFill = (active: boolean) => (active ? PINK : 'none')
  const isHome = path === '/', isFav = path === '/favorites', isPurch = path === '/purchases', isProf = path === '/profile'

  // Plan prices come from admin Settings (fallbacks mirror the backend defaults);
  // the yearly badge shows the real saving vs 12 months.
  const weekStars = settingsQ.data?.sub_price_week_stars ?? 99
  const monthStars = settingsQ.data?.sub_price_month_stars ?? 299
  const yearStars = settingsQ.data?.sub_price_year_stars ?? 2499
  const yearSavePct = Math.round((1 - yearStars / (monthStars * 12)) * 100)
  // Prepaid periods, no auto-renewal — the copy must not promise recurring billing.
  const subPlans = [
    { code: 'week', name: 'Weekly', sub: '7 days access', stars: weekStars, tag: '' },
    { code: 'month', name: 'Monthly', sub: '30 days access', stars: monthStars, tag: '' },
    { code: 'year', name: 'Yearly', sub: '365 days access', stars: yearStars, tag: yearSavePct > 0 ? `BEST VALUE · ${yearSavePct}%` : '' },
  ].map((pp) => {
    const p = { ...pp, priceFmt: String(pp.stars), usdFmt: fmtUsd(pp.stars * starRate) }
    const selected = selectedPlan === p.code
    return {
      ...p, selected,
      onSelect: () => setSelectedPlan(p.code),
      cardStyle: { position: 'relative', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '14px', padding: '16px 18px', borderRadius: '18px', cursor: 'pointer', background: selected ? 'rgba(255,90,160,.1)' : 'rgba(255,255,255,.04)', border: '1px solid ' + (selected ? 'rgba(255,90,160,.55)' : 'rgba(255,255,255,.08)') } as React.CSSProperties,
      dotStyle: { width: '20px', height: '20px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', border: '2px solid ' + (selected ? '#ff5aa0' : 'rgba(255,255,255,.25)') } as React.CSSProperties,
    }
  })
  const curPlan = subPlans.find((p) => p.selected) || subPlans[0]

  const pillStyle = (active: boolean): React.CSSProperties => ({ padding: '8px 15px', borderRadius: '999px', whiteSpace: 'nowrap', cursor: 'pointer', fontSize: '13px', fontWeight: 600, position: 'relative', zIndex: 1, background: 'transparent', color: active ? '#fff' : '#b7adb5', border: '1px solid transparent', transition: 'color .25s ease' })
  const catFilters = [ { key: 'all', label: 'All' }, { key: 'new', label: 'New' }, { key: 'trending', label: 'Popular' }, { key: 'premium', label: 'Premium' } ].map((f) => ({ label: f.label, active: activeFilter === f.key, style: pillStyle(activeFilter === f.key), onClick: () => setActiveFilter(f.key) }))
  // purchases tabs stretch across the whole pill container (equal columns)
  const pTabs = [ { key: 'all', label: 'All' }, { key: 'downloaded', label: 'Downloaded' }, { key: 'available', label: 'Available' } ].map((tb) => ({ label: tb.label, active: activeTab === tb.key, style: { ...pillStyle(activeTab === tb.key), flex: 1, textAlign: 'center', padding: '8px 6px', overflow: 'hidden', textOverflow: 'ellipsis' } as React.CSSProperties, onClick: () => setActiveTab(tb.key) }))

  const catalogRecs = recs.filter((r) =>
    activeFilter === 'all' ? true :
    activeFilter === 'new' ? r.catSlug === 'new' || r.badge === 'New' :
    activeFilter === 'trending' ? r.catSlug === 'popular' :
    r.premium)

  const gateBtnStyle: React.CSSProperties = { width: '100%', padding: '16px', borderRadius: '16px', border: 'none', cursor: 'pointer', fontSize: '15px', fontWeight: 700, color: '#fff', background: 'linear-gradient(135deg,#ff5aa0,#ff2e93)', boxShadow: '0 12px 30px rgba(255,46,147,.35)' }

  const productsLoading = productsQ.isLoading
  const productsError = productsQ.isError && !productsLoading

  const setLangEverywhere = (code: string) => {
    setLanguage(code)
    setLangOpen(false)
    // persist on the backend so product titles come back in this language
    api.post('/profile/language', { language: code })
      .then(() => {
        qc.invalidateQueries({ queryKey: ['products'] })
        qc.invalidateQueries({ queryKey: ['product'] })
        qc.invalidateQueries({ queryKey: ['favorites'] })
        qc.invalidateQueries({ queryKey: ['orders'] })
      })
      .catch(() => {})
  }

  return {
    // screen flags
    showHome: true, showCatalog: true, showDetail: true, showCart: true, showCheckout: true,
    showSuccess: true, showPurchases: true, showFavorites: true, showProfile: true,
    showSubscription: true, showPayments: true, showSupport: true, showTerms: true,
    showGate: true, showWelcome: true, showMainNav: true,
    glowOn: true,
    // data states
    productsLoading, productsError, retryProducts: () => productsQ.refetch(),
    homeEmpty: !productsLoading && !productsError && recs.length === 0,
    catalogEmpty: !productsLoading && !productsError && catalogRecs.length === 0,
    purchasesEmpty: !ordersQ.isLoading && purchaseFiltered.length === 0,
    // navigation
    goHome: () => nav('/'), backHome: () => nav('/'), explore: () => nav('/catalog'), seeAll: () => nav('/catalog'),
    search: () => nav('/catalog'), goCart: () => nav('/cart'), cartClose: () => nav(-1),
    goSubscription: () => nav('/subscription'), goFav: () => nav('/favorites'), goPurch: () => nav('/purchases'),
    goSuccessPurch: () => nav('/purchases'), goPurchases: () => nav('/purchases'), goProfile: () => nav('/profile'), backProfile: () => nav('/profile'),
    goCheckout: () => nav('/checkout'), checkoutBack: () => nav('/cart'), continueShop: () => nav('/catalog'),
    goSupport: () => nav('/support'), goTerms: () => nav('/terms'), goPayments: () => nav('/payment-history'),
    supportUnread,
    goGate: () => nav('/age-confirm'),
    // Deep-linked opens (the bot's "View" button lands straight on /product/:slug)
    // have no history entry, so nav(-1) is a no-op that traps the user in the card —
    // fall back to Home when there's nothing to go back to.
    detailBack: () => (loc.key === 'default' ? nav('/') : nav(-1)),
    enter: () => {
      if (gateChecked) {
        setAgeConfirmed(true)
        api.post('/profile/confirm-age', { confirmed: true }).catch(() => {})
        nav('/welcome')
      }
    },
    // home
    offerCountdown: '11:59:47', homeVideos: recs.slice(0, 4).map(vmVideo),
    dismissPromo: () => setPromoVisible(false), promoVisible,
    // catalog
    catFilters, catalogVideos: catalogRecs.map(vmVideo),
    // detail
    detail, detailUsd: dRec.usd,
    // cart
    // counts follow cartRecs (renderable items), not the raw store: a stored id
    // whose product was deleted must not keep Checkout alive on an empty-looking cart
    cartItems: cartRecs.map(vmVideo), cartCount: cartRecs.length, hasCart: cartRecs.length > 0,
    cartEmpty: cartRecs.length === 0, cartTotalFmt: String(cartTotalStars), cartTotalUsd: '$' + cartTotalUsdN.toFixed(2),
    // checkout — totals come from the backend estimate so the UI always matches the invoice
    coItems: cartRecs.map(vmVideo),
    coTotalFmt: String(coToPayStars), coTotalUsd: fmtUsd(coToPayStars * starRate),
    coDiscountRows, coHasDiscount: coDiscountRows.length > 0,
    coSubtotalFmt: String(cartTotalStars), coSubtotalUsd: fmtUsd(cartTotalUsdN),
    // promo code entry — validated by the same /cart/estimate call
    promoValue: promoInput,
    promoOnChange: (e: React.ChangeEvent<HTMLInputElement>) => setPromoInput(e.target.value),
    promoApply: () => { const c = promoInput.trim(); if (c) setPromoApplied(c) },
    promoAppliedCode: promoPct > 0 && promoApplied ? promoApplied.toUpperCase() : null,
    promoInvalid: !!promoApplied && !!est && !estimateQ.isFetching && promoPct === 0,
    promoRemove: () => { setPromoApplied(null); setPromoInput('') },
    promoBusy: !!promoApplied && estimateQ.isFetching,
    coInsufficient: false, // real balance lives in Telegram; the invoice flow enforces it
    // payment method (stars | crypto) — drives the currency shown across the app
    payCrypto, payStars: !payCrypto,
    payMethods: (['stars', 'crypto'] as const).map((code) => {
      const selected = payMethod === code
      return {
        code, crypto: code === 'crypto', selected,
        name: code === 'crypto' ? 'Crypto' : 'Telegram Stars',
        sub: code === 'crypto' ? 'BTC · ETH · USDT · SOL & more' : 'Pay with your Stars balance',
        onSelect: () => setPayMethod(code),
        cardStyle: {
          display: 'flex', alignItems: 'center', gap: '14px', padding: '16px', borderRadius: '16px', cursor: 'pointer', marginBottom: '10px',
          border: '1px solid ' + (selected ? 'rgba(255,90,160,.45)' : 'rgba(255,255,255,.08)'),
          background: selected ? 'rgba(255,90,160,.04)' : 'rgba(255,255,255,.02)',
        } as React.CSSProperties,
      }
    }),
    paySecureNote: payCrypto ? 'Secure crypto payment' : 'Secure payment via Telegram',
    doPay: () => { if (cartRecs.length > 0 && !checkoutMut.isPending) checkoutMut.mutate() },
    // favorites
    favoriteItems: favRecs.map(vmVideo), favCount: favRecs.length, favEmpty: !favQ.isLoading && favRecs.length === 0,
    favBundleCount: favRecs.length, favHasItems: favRecs.length > 0,
    favSavePct: favEstQ.data?.final_discount_percent ?? 0,
    addAllFavs: () => { favRecs.forEach((v) => { if (!cartIds.has(v.id)) addToCart(v.id) }); nav('/cart') },
    // purchases
    purchaseItems: purchaseFiltered.map(vmVideo), pTabs,
    // payment history
    payHistory,
    payTotalStars: payTotalStars.toLocaleString('en-US'),
    payTotalUsd,
    paymentsLoading: ordersQ.isLoading,
    paymentsEmpty: !ordersQ.isLoading && orders.length === 0,
    // profile
    balanceFmt: '',
    premiumActive: !!profileQ.data?.is_premium,
    premiumUntilFmt: profileQ.data?.premium_until
      ? new Date(profileQ.data.premium_until).toLocaleString('en-US', { month: 'short', day: '2-digit', year: 'numeric' })
      : '',
    profileName: [profileQ.data?.first_name, (profileQ.data as Record<string, unknown> | undefined)?.last_name].filter(Boolean).join(' ') || profileQ.data?.username || 'NoxX User',
    toggleLang: () => setLangOpen((o) => !o), langOpen,
    langItems: Model.LANGUAGES.map((l) => ({ flagEl: FlagIcon.flagSvg(l.code), name: l.name, selected: language === l.code, onClick: () => setLangEverywhere(l.code) })),
    // subscription — prepaid premium periods; the admin "coming soon" toggle
    // can take the CTA offline without a redeploy.
    subPlans, subscribePrice: curPlan.priceFmt, subscribeUsd: curPlan.usdFmt,
    subscribeNow: () => { if (!subscribeMut.isPending) subscribeMut.mutate(selectedPlan) },
    subscribeBusy: subscribeMut.isPending,
    subComingSoon: settingsQ.data?.subscription_coming_soon_enabled ?? true,
    subComingSoonText: settingsQ.data?.subscription_coming_soon_text || 'Subscriptions are coming soon.',
    // support / terms — admin-edited texts win, design defaults as fallback
    termsSections: (() => {
      const s = settingsQ.data
      const pick = (base: string) =>
        (s?.[`${base}_${language}`] as string | undefined)?.trim() ||
        (s?.[`${base}_en`] as string | undefined)?.trim()
      const termsTxt = pick('terms_text')
      const refundTxt = pick('refund_policy_text')
      if (!termsTxt && !refundTxt) return Model.PLAN_TERMS
      return [
        ...(termsTxt ? [{ head: t('termsServiceHead'), body: termsTxt }] : []),
        ...(refundTxt ? [{ head: t('termsRefundsHead'), body: refundTxt }] : []),
      ]
    })(),
    supportTopics: Model.SUPPORT_TOPICS,
    sendSupport: (topic: string, message: string) => supportMut.mutateAsync({ topic, message }),
    supportBusy: supportMut.isPending,
    // two-way support conversations
    supportTickets: supportTicketsQ.data ?? [],
    supportLoading: supportTicketsQ.isLoading,
    supportError: supportTicketsQ.isError && !supportTicketsQ.isLoading,
    replySupport: (ticketId: number, text: string) => supportReplyMut.mutateAsync({ ticketId, text }),
    replyBusy: supportReplyMut.isPending,
    // gate
    gateBtnStyle, toggleGate: () => setGateChecked((c) => !c), gateOk: gateChecked, gateNo: !gateChecked,
    // bottom-nav active state
    navHomeFill: navFill(isHome), navHomeColor: navColor(isHome), navHomeLabel: navColor(isHome),
    navFavFill: navFill(isFav), navFavColor: navColor(isFav), navFavLabel: navColor(isFav),
    navPurchFill: navFill(isPurch), navPurchColor: navColor(isPurch), navPurchLabel: navColor(isPurch),
    navProfFill: navFill(isProf), navProfColor: navColor(isProf), navProfLabel: navColor(isProf),
  }
}
