# Telegram Mini App — UI Kit / Design System Migration Report

_Scope: `apps/miniapp` only. Admin, backend and bot were not touched._

## 1. What was wrong (audit)

- **The app did not compile.** A previous FSD move left files in `src/shared/*`
  while every page still imported old paths (`../store`, `../api/client`,
  `../types`). Baseline: **35 TypeScript errors** (13× `TS2307` broken modules,
  22× `TS7006` implicit `any`).
- **No design system.** 13 screens with ad-hoc Tailwind classes, no reusable
  components, duplicated markup (product cards, buttons, empty states).
- **No design tokens.** Colors/spacing/radii hard-coded per screen.
- **Duplicate entry point** (`src/main.tsx` + `src/app/main.tsx`).
- **Untyped Telegram integration** (raw `window.Telegram`, `any`), header color
  hard-coded, no theme sync, no haptics.
- **No ESLint config** despite ESLint being installed (lint could not run).

## 2. Architecture created (Feature-Sliced Design)

`pages → widgets → entities → shared`, with a single composition root.

```
src/
  app/        providers/ (Query+Theme+Router), App.tsx, index.css
  shared/     config/(tokens) lib/(cn, telegram, store) theme/ ui/ api/ types/
  entities/   product/ (ProductCard, price format)
  widgets/    BottomNav/
  pages/      screens
```

Each component is a folder with `Component.tsx` + `Component.types.ts` + `index.ts`.

## 3. Design tokens

`src/shared/config/tokens.ts` is the single source of truth: spacing, radius,
typography, font weight, shadow, motion, z-index, 44px touch target. Tailwind
extends its theme from these values.

Colors are **runtime-themeable**: semantic `--ds-*` CSS variables
(`src/app/index.css`) resolve to Telegram `--tg-theme-*` with dark fallbacks and
auto-sync on Telegram's `themeChanged`. Components use only semantic Tailwind
names (`bg-bg`, `text-text`, `bg-accent`, `border-border`, …).

## 4. Components created

**Base UI (`shared/ui`):** TmaButton (6 variants: primary, secondary, outline,
ghost, danger, overlay), TmaIconButton, TmaCard, TmaInput, TmaBadge, TmaSpinner,
TmaSkeleton, TmaSection, TmaEmptyState, TmaSheet (bottom sheet/modal),
TmaSegmented, TmaPriceTag, TmaListItem, TmaAvatar.

All are fully typed (no `any`), support `className`, `disabled`, `loading`/`size`/
`variant` where relevant, a11y attributes and a 44px touch target.

**Entity:** ProductCard (grid + list layouts, Stars pricing, premium badge,
optional favourite toggle).

**Infra:** `cn()` util, typed Telegram wrapper (`haptic`, `hapticNotify`,
`initTelegram`, `applyTelegramTheme`), `ThemeProvider`, `AppProviders`.

## 5. Screens migrated

| Screen | Status |
|---|---|
| HomePage | ✅ migrated (sections, ProductCard grid, skeletons) |
| CatalogPage | ✅ migrated (search, grid/list toggle, skeletons, empty state) |
| ProductPage | ✅ migrated (overlay back/preview, Buy now/Add to cart, skeleton) |
| CartPage | ✅ migrated (list items, promo, typed estimate, checkout) |
| FavoritesPage | ✅ migrated (list + empty state) |
| ProfilePage | ✅ migrated (avatar, language grid, notifications switch, links) |
| BottomNav (widget) | ✅ migrated (tokens, cart badge, haptics, safe-area) |
| AgeConfirmPage | ✅ migrated (TmaButton, gate icon, entry animation, haptics) |
| SuccessPage | ✅ migrated (TmaButton ×2, spring check icon) |
| TermsPage | ✅ migrated (TmaCard + TmaIconButton back) |
| RecentlyViewedPage | ✅ migrated (ProductCard grid, skeletons, empty state) |
| PurchasesPage | ✅ migrated (TmaCard, Stars TmaBadge, download TmaButton, skeletons/empty) |
| SupportPage | ✅ migrated (TmaSegmented topic, TmaButton, ticket TmaCard/TmaBadge, hapticNotify) |

Button usage follows the spec: Buy now → primary, Add to cart → secondary,
Preview → overlay, Report problem → ghost.

## 6. Still to migrate (next iteration)

**None — all screens are now on the design system.** ✅

The remaining 6 secondary screens (SuccessPage, PurchasesPage,
RecentlyViewedPage, SupportPage, TermsPage, AgeConfirmPage) were migrated off the
legacy `tg-*` markup onto `Tma*` components and `entities/product`. The entire
active user path now lives on the design system; there are no longer two markup
"dialects" in the codebase.

Highlights of this pass:
- Logic preserved — endpoints (`/orders`, `/recently-viewed`, `/support/tickets`),
  i18n keys and behaviour unchanged.
- Type-safety — Support gained a `Topic` union and a status→badge-variant map; no `any`.
- UX — loading skeletons, empty states, and haptics (`hapticNotify` success/error
  on ticket submit; `disabled`/`loading` on the submit button).

## 7. Checks run (Step 9)

| Check | Before | After |
|---|---|---|
| `tsc --noEmit` | 35 errors | **0 errors** |
| `eslint` (no-explicit-any: error) | could not run (no config) | **0 errors** |
| `vite build` | n/a | **success** (~3s, JS 159 kB gzip, CSS 4.3 kB gzip) |

## 8. Errors fixed

- 13 broken module imports → repointed to `src/shared/*`.
- 22 implicit-`any` errors → resolved automatically once types flowed through.
- 1 remaining `any` in ProfilePage → typed `Profile` interface.
- Removed duplicate entry point and legacy `BottomNav.tsx`.
- Added missing ESLint config so lint is enforceable in CI.

## 9. How the foundation prevents future refactors

- Tokens + semantic colors mean a theme change is one place, not 13 screens.
- The component contract (folder + types + index) keeps the API stable.
- FSD dependency direction prevents tangled imports.
- New screens compose existing `Tma*` components instead of re-styling markup.

## 10. Remaining UI debt

- ✅ ~~6 legacy screens still to migrate~~ — **done** (see §6). All screens migrated.
- `ProductCard` favourite toggle needs a store action + `/favorites` POST/DELETE
  (favourites are currently read-only; store has no favourites slice).
- `TmaSegmented` is now adopted (SupportPage topic selector); `TmaSheet` built
  but not yet adopted by a screen (ready for filters / sort).
- Telegram `MainButton` integration not yet wired to checkout (optional UX win).
- Bundle > 500 kB pre-gzip — consider route-level code splitting.
- No component tests/Storybook yet.
```