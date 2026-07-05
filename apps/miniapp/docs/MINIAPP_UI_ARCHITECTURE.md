# Mini App UI Architecture

_Scope: `apps/miniapp`. This document defines the **UI architecture** of the
Telegram Mini App: the FSD layers, what belongs in each, how to add components
and features, and how to use tokens, themes and Telegram CSS variables._

> Goal: a **stable architecture** so future work is additive, not a refactor.
> Build the **foundation first, then screens**. Never ship a quick visual patch.

---

## 1. Feature-Sliced Design (FSD) layers

The app is organised top-down. **Imports may only point downward** in this list
(a layer may import from layers below it, never above, never sideways at the
same layer except through a slice's public `index.ts`).

```
app        →  composition root: providers, router, global styles, i18n
pages      →  one component per route; thin; compose widgets/features
widgets    →  self-contained UI blocks that compose features + entities
features   →  a single user scenario (add to cart, apply promo, switch theme)
entities   →  business nouns (product, order, user, promo): types + presentational UI
shared     →  framework-agnostic building blocks: ui, lib, tokens, api, types
```

Dependency rule:

```
app → pages → widgets → features → entities → shared
```

### What each layer MAY contain

| Layer | Allowed | Forbidden |
|---|---|---|
| **app** | router, providers (Theme, Query), `index.css`, i18n bootstrap | business logic, screen markup |
| **pages** | route component, layout of widgets/features, data fetching wiring | one-off styles, complex calculations, duplicated UI |
| **widgets** | compose entities + features + `shared/ui`; may read the store | raw API calls, low-level styling primitives |
| **features** | one scenario's logic + its UI; may read/write the store and call API | unrelated scenarios, generic UI primitives |
| **entities** | domain `model/types.ts` + **presentational** `ui/*` for that noun | API calls, store access, cross-entity imports |
| **shared** | `ui/` (Tma*), `lib/` (cn, telegram), `tokens/`, `api/`, `types/` | anything about products, cart, payments, Stars |

### What is forbidden everywhere

- ❌ Copying Figma-generated code (see §7).
- ❌ Importing from a slice's internals — always go through its `index.ts`.
- ❌ Sideways imports between two entities or two features.
- ❌ Business logic (products, cart, payments, Stars) inside `shared/ui`.
- ❌ API requests inside `shared/ui` or inside `entities`.
- ❌ Heavy computation inside `pages`.

---

## 2. How to add a new UI component (`shared/ui`)

`shared/ui` holds the **design-system primitives** — the `Tma*` components. They
are generic, themeable and know **nothing** about the domain.

1. Create the folder:
   ```
   src/shared/ui/TmaThing/
   ├── TmaThing.tsx        # implementation
   ├── TmaThing.types.ts   # Props + variant/size unions
   └── index.ts            # public re-exports
   ```
2. Rules for the component:
   - **Typed**, no `any`.
   - Accept `className` and spread the rest of the native props.
   - Use `variant` / `size` unions where it has visual variations.
   - Interactive elements use a **44px touch target** (`min-h-touch` / `h-touch`).
   - Style with **token-backed Tailwind classes / CSS variables** only
     (`bg-surface`, `text-text`, `rounded-2xl`, `z-sheet`…), never hard-coded hex.
   - **No business logic, no API, no store.**
3. Re-export it from `src/shared/ui/index.ts` (the barrel).
4. Run typecheck + build (see §10 in AGENTS.md).

Before writing anything new: **search `shared/ui` first** — reuse or extend an
existing primitive instead of duplicating it.

---

## 3. How to add a new feature

A feature is **one user scenario** (e.g. "apply promo code", "switch language").

```
src/features/<feature-name>/
├── model/      # hooks, store slices, scenario logic
├── ui/         # the feature's own components (compose shared/ui + entities)
└── index.ts    # public API
```

Rules:
- A feature may read/write the store and call the API client.
- A feature composes `shared/ui` primitives and `entities` — it does **not**
  re-implement primitives.
- Keep scenarios isolated: don't import one feature from another.
- Expose only what's needed via `index.ts`.

To assemble a screen: `pages → widgets → features → entities → shared/ui`.

---

## 4. Using design tokens

Tokens are the single source of truth, split by concern under `src/shared/tokens/`:

```
src/shared/tokens/
├── colors.ts       # semantic color → CSS variable map
├── typography.ts   # fontSize (tuples) + fontWeight
├── spacing.ts      # spacing scale + touchTarget
├── radius.ts       # border-radius scale
├── shadows.ts      # elevation shadows
├── zIndex.ts       # layering contract (nav/overlay/sheet/toast)
├── motion.ts       # durations + easing (framer-motion)
└── index.ts        # public API: re-exports + aggregate `tokens` object
```

- In components, you normally consume tokens **through Tailwind utilities**
  (`p-4`, `rounded-2xl`, `text-sm`, `z-sheet`) — Tailwind's theme is derived from
  these exact values, so they always agree.
- For JS-side needs (e.g. framer-motion timings) import from `shared/tokens`:
  ```ts
  transition={{ duration: motionTokens.base, ease: motionTokens.ease }}
  ```
- `src/shared/config/tokens.ts` is kept as a **backward-compatible re-export**
  (`export * from '../tokens'`). New code should import from `shared/tokens`.
- Never hard-code colors, radii or spacing in components.

---

## 5. Using themes

- `ThemeProvider` (`src/shared/theme`) syncs the app with the Telegram theme and
  toggles the `dark` class on the document root (Tailwind `darkMode: 'class'`).
- Components stay **theme-agnostic**: they use **semantic** classes
  (`bg-surface`, `text-text`, `text-hint`, `border-border`) that automatically
  resolve to the right value in light/dark.
- Never branch on the theme inside a component to pick a color — pick a semantic
  token and let the theme layer resolve it.

---

## 6. Using Telegram CSS variables

Telegram injects `--tg-theme-*` variables at runtime. We **do not** consume them
directly in components. Instead:

```
--tg-theme-*   (Telegram, runtime)
     ↓  bridged in src/app/index.css
--ds-*         (our semantic design-system variables, with dark fallbacks)
     ↓  mapped in tailwind.config.js
bg-surface / text-text / …   (semantic Tailwind utilities used in components)
```

- The bridge lives in `src/app/index.css` (`--ds-bg: var(--tg-theme-bg-color, …)`).
- Add a new semantic color by: defining `--ds-x` in `index.css`, mapping it in
  `tailwind.config.js`, and documenting it in `tokens/colors.ts`.
- Components reference only the semantic Tailwind name — never `var(--tg-theme-*)`
  and never a raw hex.

---

## 7. Why you must NOT copy Figma-generated code

Figma "Dev Mode" / plugin output produces **absolute-positioned, pixel-hard
markup** with inline hex colors, magic numbers and no semantics. Pasting it:

- breaks **theming** (hard-coded colors ignore light/dark and Telegram themes),
- breaks **responsiveness** (absolute coordinates instead of flow layout),
- breaks **reuse** (no variants, no props, duplicated everywhere),
- breaks **a11y / touch targets**, and
- rots instantly when the design changes.

Use Figma as a **visual reference** only. Implement with `Tma*` components,
tokens and semantic classes. The kit is a spec, not a source file.

---

## 8. Why pages must be thin

A page is a **composition + wiring** unit, not a place for UI or logic:

- it picks which widgets/features to show and passes data/handlers,
- it does **not** contain bespoke markup, one-off styles or calculations,
- heavy logic lives in features/entities/lib; derived data is computed there.

Thin pages mean a screen can be restructured by moving widgets around, with zero
risk to business logic. If a page grows its own styled blocks → extract a widget.

---

## 9. Why `shared/ui` must not know about business logic

`shared/ui` is the **reusable, domain-free** layer. If a primitive knew about
products, the cart, payments or Stars:

- it couldn't be reused across unrelated screens,
- it would couple the design system to today's business rules,
- every domain change would ripple into low-level UI,
- testing and theming would become entangled with data.

So: `TmaButton` knows "primary/secondary/size/loading" — never "buy", "Stars" or
"cart". Domain meaning is added one layer up, in `entities` (e.g. `ProductPrice`,
`ProductCard`) and `features`/`widgets`.

---

## 10. Current inventory

**shared/ui (Tma\*):** Button, IconButton, Card, Input, Badge, Avatar, ListItem,
PriceTag, Section, Segmented, Sheet, Skeleton, Spinner, EmptyState, **Banner,
Chip, Select, Modal, Snackbar, Tabs, VideoPlayer**.

**entities:**
- `product`: ProductCard, ProductListItem, ProductHeroCard, ProductStats,
  ProductPrice, ProductTags, ProductPreviewPlayer (+ `lib/format`).
- `order`: types (Order/OrderItem/OrderStatus) + `PurchaseItem`.
- `user`: `TelegramUser` + `ProfileCell`.
- `promo`: `PromoCode`/`AppliedDiscount` + `DiscountBlock`.

**widgets:** BottomNav, product-list, floating-cart, checkout-sheet,
profile-menu, home-banners.

**pages:** Home, Catalog, Product, Cart, Success, Purchases, Favorites, Profile,
Support, Terms, AgeConfirm — all on the design system.

---

## 11. Checklist before committing UI changes

1. New UI? → looked in `shared/ui` first.
2. No one-off styles in `pages`; no business logic in `shared/ui`/`entities`.
3. No API calls in `shared/ui` / `entities`.
4. No Figma-generated code pasted.
5. Tokens/semantic classes only — no hard-coded hex/spacing.
6. `npm run typecheck` (or `npx tsc --noEmit`) — 0 errors.
7. `npm run build` — succeeds.
8. `npm run lint` / `aislop ci` if configured — clean.
