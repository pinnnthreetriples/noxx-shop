/** A promo code and the discount it grants. */
export interface PromoCode {
  code: string
  discount_percent: number
}

/** Resolved discount breakdown applied to an order/cart. */
export interface AppliedDiscount {
  /** Base (e.g. loyalty) discount percent. */
  base_percent: number
  /** Additional promo-code discount percent. */
  promo_percent: number
  /** Effective combined discount percent. */
  final_percent: number
}
