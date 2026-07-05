import { useQuery } from '@tanstack/react-query'
import api from '@/shared/api/client'
import type { ProductListItem, ProductDetail } from '@/shared/types'

export interface ProductQuery {
  category?: string
  tag?: string
  search?: string
  premium?: boolean
}

/** Catalog list. The dev mock returns the seeded catalog regardless of params. */
export function useProducts(params?: ProductQuery) {
  return useQuery({
    queryKey: ['products', params ?? {}],
    queryFn: async () => {
      const res = await api.get<ProductListItem[]>('/products', { params })
      return res.data
    },
  })
}

/** Single product detail by slug. */
export function useProduct(slug?: string) {
  return useQuery({
    queryKey: ['product', slug],
    enabled: Boolean(slug),
    queryFn: async () => {
      const res = await api.get<ProductDetail>(`/products/${slug}`)
      return res.data
    },
  })
}
