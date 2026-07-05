import { useQuery } from '@tanstack/react-query'
import api from '@/shared/api/client'
import type { Order } from '@/shared/types'

/** Purchase history for the current user. */
export function useOrders() {
  return useQuery({
    queryKey: ['orders'],
    queryFn: async () => {
      const res = await api.get<Order[]>('/orders')
      return res.data
    },
  })
}
