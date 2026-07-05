# Telegram Mini App — Design System

A Figma-derived, token-based design system for `apps/miniapp`, organised with
Feature-Sliced Design (FSD). The goal is a stable foundation so screens can be
built and changed without large refactors.

## Architecture (Feature-Sliced Design)

```
src/
  app/            # composition root: providers, routing, global styles
    providers/    # AppProviders (Query + Theme + Router)
    App.tsx
    index.css     # design-system CSS variable layer
  shared/         # reusable, domain-agnostic foundation
    config/       # design tokens (single source of truth)
    lib/          # cn(), telegram wrapper, zustand store
    theme/        # ThemeProvider + useTheme
    ui/           # base components (Tma*)
    api/          # axios client
    types/        # shared TS types
  entities/       # domain models + their UI
    product/      # ProductCard, price formatting
  widgets/        # composite blocks (BottomNav)
  pages/          # screens
```

**Dependency rule:** `pages → widgets → entities → shared`. Lower layers never
import from higher ones.

## Design tokens

Tokens live in `src/shared/config/tokens.ts` (spacing, radius, typography,
shadow, motion, z-index, touch target). Tailwind extends its theme from these
exact values, so utility classes always mean the same thing.

**Colors** are runtime-themeable. The CSS layer in `src/app/index.css` defines
semantic `--ds-*` variables that resolve to Telegram theme variables
(`--tg-theme-*`) with dark-mode fallbacks. Components reference only semantic
Tailwind colors — never raw hex or Telegram variables:

| Semantic | Tailwind | Source |
|---|---|---|
| Background | `bg-bg`, `bg-bg-secondary`, `bg-section` | Telegram bg / secondary / section |
| Surface | `bg-surface`, `bg-surface-elevated` | derived |
| Text | `text-text`, `text-hint`, `text-subtitle` | Telegram text / hint |
| Accent | `bg-accent`, `text-accent-text` | Telegram button color |
| Danger | `text-danger` / `bg-danger` | Telegram destructive |
| Border | `border-border` | derived from text |

The theme auto-syncs to Telegram's `themeChanged` event via `ThemeProvider`.

## Component contract

Every component lives in its own folder:

```
TmaButton/
  TmaButton.tsx        # implementation
  TmaButton.types.ts   # typed props (no `any`)
  index.ts             # public exports
```

All components support `className`, are fully typed, expose `variant` / `size`
where relevant, include accessibility attributes, and respect a 44px minimum
touch target on mobile.

### Base UI (`shared/ui`)

| Component | Purpose | Key props |
|---|---|---|
| `TmaButton` | Primary control | `variant` (primary/secondary/outline/ghost/danger/overlay), `size`, `loading`, `fullWidth`, `iconLeft/Right` |
| `TmaIconButton` | Icon-only action | `variant`, `size`, `active`, required `aria-label` |
| `TmaCard` | Container | `variant`, `padding`, `interactive` |
| `TmaInput` | Text field | `label`, `error`, `hint`, `iconLeft/Right` |
| `TmaBadge` | Status pill | `variant`, `size` |
| `TmaSpinner` | Loading indicator | `size` |
| `TmaSkeleton` | Loading placeholder | `width`, `height`, `rounded` |
| `TmaSection` | Titled block | `title`, `action` |
| `TmaEmptyState` | Empty/zero data | `icon`, `title`, `description`, `action` |
| `TmaSheet` | Bottom sheet / modal | `open`, `onClose`, `title`, `footer` |
| `TmaSegmented` | Tabs / switch | `options`, `value`, `onChange` |
| `TmaPriceTag` | Currency price | `price`, `oldPrice`, `currency`, `size` |
| `TmaListItem` | Row | `leading`, `title`, `subtitle`, `trailing` |
| `TmaAvatar` | User avatar | `src`, `name`, `size` |

### Entities

- `ProductCard` (`entities/product`) — storefront card, `layout: 'grid' | 'list'`,
  optional favourite toggle, Telegram Stars pricing.

## Button variant usage (from the spec)

| Action | Variant |
|---|---|
| Buy now | `primary` |
| Add to cart | `secondary` |
| Preview | `overlay` |
| Download | `primary` |
| Report problem | `ghost` |

## Example

```tsx
import { TmaButton, TmaCard, TmaSection } from '@/shared/ui'
import { ProductCard } from '@/entities/product'

<TmaSection title="Featured">
  <div className="grid grid-cols-2 gap-3">
    {products.map((p) => (
      <ProductCard key={p.id} product={p} layout="grid" />
    ))}
  </div>
  <TmaButton variant="primary" fullWidth>Buy now</TmaButton>
</TmaSection>
```

## Telegram integration

`shared/lib/telegram.ts` is a typed, defensive wrapper (safe outside Telegram):

- `initTelegram()` — ready + expand + theme sync (called by `ThemeProvider`)
- `applyTelegramTheme()` — maps `themeParams` to CSS variables
- `haptic()` / `hapticNotify()` — haptic feedback, no-op outside Telegram
```
