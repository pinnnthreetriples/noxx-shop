# Mini App Design System — Final Report

_apps/miniapp · закрытие UI-migration debt + favorites slice_

## 1. Резюме

Полностью закрыт технический долг по миграции UI Telegram Mini App на дизайн-систему
(FSD: `shared/tokens` → `shared/theme` → `shared/ui` → `entities` → `features` → `widgets`).
Из `src/pages` устранены все legacy `tg-*` классы и одноразовые inline-стили,
реализован полноценный favorites-слайс, добавлены недостающие примитивы дизайн-системы.

| Критерий готовности | Статус |
|---|---|
| `tg-*` legacy-классов в `pages` | ✅ нет (0) |
| favorites slice непустой и работает | ✅ да |
| TSC_ERRORS | ✅ 0 |
| ESLINT_PROBLEMS | ✅ 0 |
| BUILD | ✅ OK (498.02 kB / gzip 160.90 kB) |

## 2. Убранные legacy `tg-*` классы

| Класс | Где встречался | Чем заменён |
|---|---|---|
| `tg-safe-top` | Home, Catalog, Favorites, Product (×2), Cart, Profile, Purchases, Support, RecentlyViewed | safe-area инкапсулирован в `TmaScreen` (canonical `.safe-top`) |
| `tg-safe-bottom` | Product (нижний action-bar) | `.safe-bottom` внутри виджета `ProductActionBar` |

Дополнительно введены **канонические** safe-area утилиты `.safe-top` / `.safe-bottom`
в `app/index.css`; старые `.tg-safe-*` оставлены как deprecated-алиасы (без использования в коде).

> `tg-theme-*` — это CSS-переменные темы Telegram (мост темы в `shared/theme`),
> они **не** являются legacy-классами и сохранены намеренно.

### Исправленный баг
- В `SupportPage` textarea использовала класс `border-separator` — **несуществующий**
  цвет в Tailwind-конфиге (рамка не отрисовывалась). Устранён переходом на компонент
  `TmaTextarea` (`border-border`).

## 3. Обновлённые экраны (12 / 12)

| Экран | Ключевые изменения |
|---|---|
| HomePage | `TmaScreen`, секции через `TmaSection` |
| CatalogPage | `TmaScreen`, поиск/раскладка, подключён favorites-слайс |
| FavoritesPage | `TmaScreen`, источник правды — favorites-слайс (фильтр каталога по id) |
| ProductPage | `TmaScreen`-паттерн, виджет `ProductActionBar`, `FavoriteButton`, общий `formatStars/formatApproxUsd` |
| CartPage | `TmaScreen`, удалён дубль `formatUsd` → общий `formatApproxUsd` |
| ProfilePage | `TmaScreen`, feature `LanguageSwitcher`, `TmaSwitch` вместо самописного тоггла |
| PurchasesPage | `TmaScreen`, entity `OrderCard` вместо inline-разметки заказа |
| SupportPage | `TmaScreen`, `TmaTextarea` (фикс `border-separator`), `TmaSegmented` |
| SuccessPage | `TmaScreen centered` |
| AgeConfirmPage | `TmaScreen centered` |
| TermsPage | `TmaScreen` с заголовком/назад |
| RecentlyViewedPage | `TmaScreen`, виджет `ProductList`, подключён favorites |

Все i18n-ключи, API-эндпоинты и бизнес-логика сохранены без изменений.

## 4. Favorites slice (FSD)

`src/features/favorites/`
- `model/store.ts` — `useFavoritesStore` (zustand + `persist`, ключ `tma-favorites`):
  `ids`, `toggle`, `add`, `remove`, `isFavorite`, `clear`.
- `model/hooks.ts` — `useFavoriteIds`, `useIsFavorite`, `useToggleFavorite` (с haptic).
- `ui/FavoriteButton.tsx` — переиспользуемая кнопка-сердце поверх `TmaIconButton`.
- `index.ts` — публичный API слайса.

**Подключение (без дублей логики):**
- ProductPage — `FavoriteButton` (overlay поверх обложки).
- CatalogPage / FavoritesPage / RecentlyViewedPage — `favoriteIds` + `onToggleFavorite`
  пробрасываются в виджет `ProductList` → `ProductCard`.
- FavoritesPage берёт источник правды из слайса (клиентский, persisted).

## 5. Добавленные компоненты / виджеты

**shared/ui**
- `TmaScreen` — layout-примитив (safe-area + контейнер + header + анимация входа).
- `TmaTextarea` — многострочное поле в стиле `TmaInput`.
- `TmaSwitch` — доступный on/off-тоггл (role="switch").

**features**
- `favorites` (store + hooks + FavoriteButton).
- `language-switcher` (`model/languages.ts` + `LanguageSwitcher` — сетка чипов, i18n + store).

**entities**
- `order/ui/OrderCard` — карточка заказа (header + `PurchaseItem`-список + download).

**widgets**
- `product-action-bar` — фиксированный нижний бар товара (в корзину + купить, safe-bottom).

## 6. Пройденные проверки

| Проверка | Команда | Результат |
|---|---|---|
| TypeScript | `tsc --noEmit` (= `npm run build` step) | ✅ 0 ошибок |
| ESLint | `npm run lint` (`--max-warnings 0`) | ✅ 0 проблем |
| Production build | `vite build` | ✅ built in ~5.9s, 498.02 kB / gzip 160.90 kB |
| `tg-*` в pages | `grep -rn 'tg-' src/pages` | ✅ NONE |

> `npm run typecheck` как отдельного скрипта в `package.json` нет — типизация
> покрывается шагом `tsc` в `npm run build`; запускалась также напрямую `tsc --noEmit`.
> `aislop ci`: бинарь `aislop` в окружении не установлен (присутствует только
> конфиг `.aislop/config.yml`), поэтому шаг пропущен.

## 7. Остаточный техдолг

- `.tg-safe-*` оставлены как deprecated-алиасы в CSS (в коде не используются) — можно
  удалить в отдельном чистящем PR после проверки внешних потребителей.
- Бэкенд-эндпоинт `/favorites` больше не источник правды для экрана (слайс клиентский);
  при необходимости серверной синхронизации — добавить `features/favorites/api` и
  гидратацию стора (структура слайса к этому готова).
