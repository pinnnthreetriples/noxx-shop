import * as React from 'react'
import * as RR from 'react-router-dom'
import * as I18N from 'react-i18next'
import { startDomTranslator, setDomLang } from '../shared/i18n/domI18n'

import * as Store from '../shared/lib/store'
import BottomNav from '../shared/noxx/BottomNav'
import ErrorBoundary from '../shared/noxx/ErrorBoundary'
import * as Motion from '../shared/noxx/motion'
import AgeConfirmPage from '../pages/AgeConfirmPage'
import HomePage from '../pages/HomePage'
import CatalogPage from '../pages/CatalogPage'
import ProductPage from '../pages/ProductPage'
import CartPage from '../pages/CartPage'
import CheckoutPage from '../pages/CheckoutPage'
import PaymentPage from '../pages/PaymentPage'
import SuccessPage from '../pages/SuccessPage'
import PaymentFailPage from '../pages/PaymentFailPage'
import PurchasesPage from '../pages/PurchasesPage'
import FavoritesPage from '../pages/FavoritesPage'
import RecentlyViewedPage from '../pages/RecentlyViewedPage'
import ProfilePage from '../pages/ProfilePage'
import SubscriptionPage from '../pages/SubscriptionPage'
import PaymentHistoryPage from '../pages/PaymentHistoryPage'
import SupportPage from '../pages/SupportPage'
import TermsPage from '../pages/TermsPage'
import WelcomePage from '../pages/WelcomePage'
import LanguageSelectPage from '../pages/LanguageSelectPage'

// screens that show the bottom tab bar (design: showMainNav)
const NAV_PATHS = ['/', '/catalog', '/favorites', '/purchases', '/profile']

function showNavFor(pathname: string): boolean {
  // Detail / sub views are pushed screens without the tab bar (design parity)
  return NAV_PATHS.includes(pathname)
}

function FrameContent() {
  const loc = RR.useLocation()
  const frameRef = React.useRef<HTMLDivElement>(null)

  React.useLayoutEffect(() => {
    Motion.enterScreen(frameRef.current)
  }, [loc.pathname])

  const cartCount = Store.useAppStore((s) => s.cartItems.reduce((n: number, i: { quantity: number }) => n + i.quantity, 0))
  const prevCart = React.useRef(cartCount)
  React.useEffect(() => {
    if (cartCount !== prevCart.current) {
      if (cartCount > prevCart.current) {
        document.querySelectorAll('[data-cart-badge]').forEach((el) => Motion.pop(el))
      }
      document.querySelectorAll('[data-total]').forEach((el) => Motion.pulse(el))
      prevCart.current = cartCount
    }
  }, [cartCount])

  return (
    <>
      <ErrorBoundary>
      <div ref={frameRef} style={{ display: 'contents' }}>
      <RR.Routes>
        <RR.Route path="/" element={<HomePage />} />
        <RR.Route path="/catalog" element={<CatalogPage />} />
        <RR.Route path="/product/:slug" element={<ProductPage />} />
        <RR.Route path="/cart" element={<CartPage />} />
        <RR.Route path="/checkout" element={<CheckoutPage />} />
        <RR.Route path="/pay/:orderId" element={<PaymentPage />} />
        <RR.Route path="/success" element={<SuccessPage />} />
        <RR.Route path="/fail" element={<PaymentFailPage />} />
        <RR.Route path="/purchases" element={<PurchasesPage />} />
        <RR.Route path="/favorites" element={<FavoritesPage />} />
        <RR.Route path="/recently-viewed" element={<RecentlyViewedPage />} />
        <RR.Route path="/profile" element={<ProfilePage />} />
        <RR.Route path="/subscription" element={<SubscriptionPage />} />
        <RR.Route path="/payment-history" element={<PaymentHistoryPage />} />
        <RR.Route path="/support" element={<SupportPage />} />
        <RR.Route path="/terms" element={<TermsPage />} />
        <RR.Route path="/welcome" element={<WelcomePage />} />
        <RR.Route path="/age-confirm" element={<AgeConfirmPage />} />
      </RR.Routes>
      </div>
      </ErrorBoundary>
      {showNavFor(loc.pathname) && <BottomNav />}
    </>
  )
}

function App() {
  const { i18n } = I18N.useTranslation()
  const language = Store.useAppStore((s) => s.language)
  const langChosen = Store.useAppStore((s) => s.langChosen)
  const ageConfirmed = Store.useAppStore((s) => s.ageConfirmed)

  React.useEffect(() => {
    i18n.changeLanguage(language)
    setDomLang(language)
  }, [language, i18n])

  React.useEffect(() => Motion.bindPress(), [])

  React.useEffect(() => { startDomTranslator(language) }, [])

  if (!langChosen) {
    return (
      <div className="noxx-frame">
        <LanguageSelectPage />
      </div>
    )
  }

  if (!ageConfirmed) {
    return (
      <div className="noxx-frame">
        <AgeConfirmPage />
      </div>
    )
  }

  return (
    <div className="noxx-frame">
      <FrameContent />
    </div>
  )
}

export default App