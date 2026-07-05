# veri — Brand Redesign Report

_Scope: `apps/miniapp`. Visual redesign onto the new "veri" Figma design. No business logic, endpoints, i18n keys or FSD structure changed._

## Approach
Foundation-first: the redesign was driven through the design-system layers, **not** by rewriting screens from scratch. Tokens + shared/ui + entity card carried most of the new look; pages only changed where layout/composition changed.

## 1. Tokens & theme (`src/app/index.css`, `tailwind.config.js`)
- Switched to a **fixed dark brand palette** (deep black canvas), decoupled from Telegram light/dark theme.
- Signature gradient `--ds-gradient-primary` (pink #e0218a → coral #f7b29a), soft gradient, and pink **glow** shadows.
- New utilities: `.bg-gradient-brand`, `.bg-gradient-soft`, `.text-gradient-brand`, `.shadow-glow(-sm)`, `.aura-pink`.
- Tailwind extends: `star`, `accent2` colors; `gradient-brand`/`gradient-soft` bg images; `glow` shadows; `3xl` radius.

## 2. Shared UI
- `TmaButton` — `primary` now brand-gradient + glow; new `softGradient` variant; pill radius.
- `TmaCard` — subtle borders + new `glow` variant.
- `TmaSegmented` — gradient active pill (rounded-full).
- `TmaBadge` — added `premium` + `info` variants.
- **New:** `TmaStepper` (− value +), `TmaFab` (floating gradient action button with count badge).

## 3. Entity
- `ProductCard` rebuilt as a **video card**: landscape preview, glowing play overlay, premium badge, gold star pricing, heart toggle. `list` + `grid` layouts.

## 4. Screens (all on the design system)
| Screen | New design |
|---|---|
| Home | veri header, −10% promo banner, "New videos" list, Premium banner, floating cart FAB |
| Catalog | back/title/filter, All/New/Popular/Premium pills, video list, floating cart |
| Product | player (preview, progress, time, Preview badge), tag pills, stats, price card, Add to cart / Buy now |
| Cart | "Your cart"/Close, item rows + steppers, total card, gradient Checkout, Continue shopping, secure footer |
| Purchases | back/title/filter, All/Videos/Bundles tabs, status (Downloaded/Available), 3-dot menu, promo banner |
| Favorites | veri header, big title + saved-count badge, heart video cards |
| Profile | avatar with pink aura glow, name + Premium member, icon menu card |
| BottomNav | Home/Favorites/Purchases/Profile, gradient active indicator |

## 5. State
- `store`: added `setQuantity(productId, quantity)` for cart steppers (removes item at 0).

## 6. Validation
- TypeScript: 0 errors
- Production build: ✓ success
- Verified in browser (Home, Profile, Cart render correctly; empty states shown without backend).

## Notes
- Lists are empty until the backend (`apps/backend`) is running; chrome/empty-states verified.
- Settings menu item links to `/settings` (route not yet defined — placeholder for future).
