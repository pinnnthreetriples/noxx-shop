import { useQuery } from '@tanstack/react-query'
import api from '@/shared/api/client'

export interface Profile {
  id?: number
  first_name?: string
  username?: string
  photo_url?: string
  stars_balance?: number
  total_orders?: number
  is_premium?: boolean
  premium_until?: string
  [key: string]: unknown
}

/** Current user profile / balance summary. */
export function useProfile() {
  return useQuery({
    queryKey: ['profile'],
    queryFn: async () => {
      const res = await api.get<Profile>('/profile')
      return res.data
    },
  })
}
