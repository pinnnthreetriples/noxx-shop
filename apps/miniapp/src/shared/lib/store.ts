import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface CartItem {
  productId: number
  quantity: number
}

interface AppState {
  cartItems: CartItem[]
  addToCart: (productId: number) => void
  removeFromCart: (productId: number) => void
  setQuantity: (productId: number, quantity: number) => void
  clearCart: () => void
  language: string
  setLanguage: (lang: string) => void
  langChosen: boolean
  setLangChosen: (v: boolean) => void
  ageConfirmed: boolean
  setAgeConfirmed: (v: boolean) => void
  payMethod: 'stars' | 'crypto'
  setPayMethod: (m: 'stars' | 'crypto') => void
}

export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      cartItems: [],
      addToCart: (productId) =>
        set((state) => {
          const existing = state.cartItems.find((i) => i.productId === productId)
          if (existing) {
            return {
              cartItems: state.cartItems.map((i) =>
                i.productId === productId ? { ...i, quantity: i.quantity + 1 } : i
              ),
            }
          }
          return { cartItems: [...state.cartItems, { productId, quantity: 1 }] }
        }),
      removeFromCart: (productId) =>
        set((state) => ({
          cartItems: state.cartItems.filter((i) => i.productId !== productId),
        })),
      setQuantity: (productId, quantity) =>
        set((state) => ({
          cartItems:
            quantity <= 0
              ? state.cartItems.filter((i) => i.productId !== productId)
              : state.cartItems.map((i) => (i.productId === productId ? { ...i, quantity } : i)),
        })),
      clearCart: () => set({ cartItems: [] }),
      language: 'en',
      setLanguage: (lang) => set({ language: lang }),
      langChosen: false,
      setLangChosen: (v) => set({ langChosen: v }),
      ageConfirmed: false,
      setAgeConfirmed: (v) => set({ ageConfirmed: v }),
      payMethod: 'stars',
      setPayMethod: (m) => set({ payMethod: m }),
    }),
    {
      name: 'noxx-store-v3',
      partialize: (state) => ({ language: state.language, langChosen: state.langChosen, ageConfirmed: state.ageConfirmed, cartItems: state.cartItems, payMethod: state.payMethod }),
    }
  )
)