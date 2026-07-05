/**
 * Order domain types. Re-exported from the shared type registry so the entity
 * owns its public contract while keeping a single source of truth.
 */
export type { Order, OrderItem } from '../../../shared/types'

/** Known order lifecycle states (string-open for forward-compat). */
export type OrderStatus = 'pending' | 'paid' | 'delivered' | 'refunded' | (string & Record<never, never>)
