import type { Order } from '../model/types'

const STATUS_LABEL: Record<string, string> = {
  paid: 'Paid',
  pending: 'Pending',
  completed: 'Completed',
  cancelled: 'Cancelled',
  failed: 'Failed',
}

function statusColor(status: string): { bg: string; fg: string } {
  if (status === 'paid' || status === 'completed') return { bg: 'rgba(76,217,140,.14)', fg: 'var(--ok-text)' }
  if (status === 'cancelled' || status === 'failed') return { bg: 'rgba(255,90,120,.14)', fg: '#ff8aa0' }
  return { bg: 'var(--surface-3)', fg: 'var(--ink-350)' }
}

interface OrderCardProps {
  order: Order
}

/** A single purchase summary card for the order history list. */
export function OrderCard({ order }: OrderCardProps) {
  const sc = statusColor(order.status)
  const date = new Date(order.created_at).toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' })
  const itemCount = order.items?.length ?? 0

  return (
    <div
      style={{
        background: 'var(--surface-1)',
        border: '1px solid var(--hairline-strong)',
        borderRadius: 18,
        padding: 16,
        marginBottom: 12,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12 }}>
        <div style={{ fontSize: 15, fontWeight: 700, color: '#fff' }}>Order #{order.id}</div>
        <span style={{ fontSize: 12, fontWeight: 600, padding: '4px 10px', borderRadius: 999, background: sc.bg, color: sc.fg }}>
          {STATUS_LABEL[order.status] ?? order.status}
        </span>
      </div>
      <div style={{ fontSize: 13, color: 'var(--ink-350)', marginTop: 6 }}>
        {date} · {itemCount} item{itemCount === 1 ? '' : 's'}
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 5, marginTop: 12, fontSize: 16, fontWeight: 700, color: 'var(--gold-ink)' }}>
        <svg width="16" height="16" viewBox="0 0 24 24" fill="#f7b23b">
          <path d="M12 2l2.95 5.98 6.6.96-4.78 4.66 1.13 6.57L12 17.98 6.1 20.16l1.13-6.57L2.45 8.94l6.6-.96z" />
        </svg>
        {order.paid_stars}
      </div>
    </div>
  )
}
