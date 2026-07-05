# Prompt for next session — bring telegram-bot0Video (NoxX) to full working state

Paste everything below into a fresh Claude Code session started in
`C:\Users\user\Documents\telegram-bot0Video`.

---

You are taking over a Telegram mini-app e-commerce project ("NoxX" — an 18+ video shop).
Backend + admin already run locally; the mini-app frontend is a static design prototype not
yet wired to the API. Your mission: **wire the frontend to the real backend, match the design
reference, fix all bugs (including UI/UX across every language), verify the admin panel,
create and connect a real Telegram bot, and get the whole thing to a launch-ready working
state — implementing AND verifying each step yourself.**

## Environment — read first (do not fight this)

- OS: Windows 11. Project lives on the **Windows** filesystem: `C:\Users\user\Documents\telegram-bot0Video`.
- **Docker Desktop WSL integration is BROKEN on this machine** (the `/mnt/wsl/docker-desktop`
  mount flickers, `/var/run/docker.sock` never persists in WSL). DO NOT try to run docker from
  inside WSL. Drive Docker from Windows only:
  `& "C:\Program Files\Docker\Docker\resources\bin\docker.exe" -c desktop-linux <args>`
- Helper script for the stack: **`.\run.ps1 up|down|ps|seed|logs|backend-shell`** (project root).
  It targets compose project `infra` and brings up postgres/redis/backend/admin/media-server
  (NOT bot/cloudflared). `make` and `docker-compose` are NOT installed on Windows.
- Compose file: `infra/docker-compose.yml`. Env: root `.env`. Always pass `--env-file` + a fixed
  project name `-p infra` when calling compose directly. Example:
  `& $docker -c desktop-linux compose -p infra -f infra\docker-compose.yml --env-file .env --project-directory infra <cmd>`
- After ANY backend code change you must rebuild+recreate the backend image (code is baked in,
  not mounted): `.\run.ps1 up` (or `compose up -d --build backend`).

## What already works (verified — don't redo)

- Stack up: admin http://localhost:3000, backend http://localhost:8000/docs, media http://localhost:9000,
  postgres:5432, redis:6379. If `localhost` is slow in a client, use `127.0.0.1`.
- **Admin login: `admin@example.com` / `admin12345`** (email/password checked against
  `ADMIN_DEFAULT_EMAIL/PASSWORD` env; the admin model itself is Telegram-id based). Works, returns JWT.
- **4 real published products exist** (Midnight Desires, Velvet Secrets, Private Moments, Forbidden Play)
  with en+ru translations, categories, prices, picsum cover URLs.
- Categories/tags seeded (`new`, `popular`, `premium`; tags `promo`, `hd`).

## Fixes already applied (keep them; understand them)

1. `apps/backend/requirements.txt`: `asyncpg 0.29→0.30` (0.29 won't compile on python:3.13).
2. `apps/admin/Dockerfile`: `npm install`→`npm ci` (npm install hangs on the react-admin tree in Docker).
3. `apps/admin/.dockerignore`: added (excludes node_modules/dist).
4. `infra/docker-compose.yml`: backend got `ADMIN_DEFAULT_EMAIL/PASSWORD/TELEGRAM_ID` passthrough.
5. `apps/backend/app/modules/catalog/service.py`: added `selectinload` eager-loading in
   `list_products` and `get_product_by_slug` — they crashed with `MissingGreenlet` on any real product.
6. `apps/backend/app/main.py`: CORS now allows Vite dev origins (localhost:5173/5174) when `app_env==development`.
7. `apps/miniapp/src/shared/api/client.ts`: dev-only fallback to `VITE_DEV_INIT_DATA` for auth outside Telegram.
8. `apps/miniapp/.env.development`: `VITE_API_BASE_URL=http://localhost:8000`, `VITE_MEDIA_BASE_URL=http://localhost:9000`,
   and a locally-forged `VITE_DEV_INIT_DATA` (Telegram initData signed with the empty BOT_TOKEN; expires ~24h — regenerate if 401 "initData expired", see below).

## The core problem to solve

**The mini-app frontend is a static design prototype, disconnected from the backend.**
- Pages (`apps/miniapp/src/pages/HomePage.tsx`, `CatalogPage.tsx`, `ProductPage.tsx`, etc.) render from
  `useNoxx()` → `apps/miniapp/src/shared/noxx/useNoxx.tsx` → `apps/miniapp/src/shared/noxx/model.ts`,
  which is a **hardcoded** view-model (fake titles, durations, view counts).
- The real API hooks exist but are **unused**: `apps/miniapp/src/entities/{product,order,user}/api/queries.ts`
  (`useProducts`, `useProduct`, etc.). `useNoxx.tsx` imports no API at all.

## Tasks (implement AND verify each)

1. **Wire the frontend to the backend.** Replace the hardcoded data in `useNoxx`/`model.ts` with real
   data from `useProducts()` / `useProduct(slug)` and the other query hooks. Map backend
   `ProductListItem`/`ProductDetail` fields (id, slug, title, cover_url, price_stars, display_views,
   display_purchases, category, tags, is_premium) into the NoxX card shape (`VideoRec`). Cover images:
   backend returns absolute cover_url (use directly) or media paths (prefix with `VITE_MEDIA_BASE_URL`).
   Cover Home, Catalog, Product detail, Favorites, Purchases, Cart/Checkout as far as endpoints allow.
   Handle loading/empty/error states. Keep the NoxX visual design intact.
2. **Match the design reference.** Confirm with the user where the reference lives (Figma/screenshots).
   The current NoxX styling (`apps/miniapp/src/app/*.css`, inline styles) IS the reference baseline — keep
   its look while feeding real data.
3. **Fix all bugs + UI/UX across every language.** The app supports 10 languages (en, ru, es, de, el,
   tr, bg, sr, ro, mo) — see `apps/miniapp/src/app/i18n.ts` and `src/shared/i18n/`. Switch through EACH
   language and fix overflow/truncation/layout/RTL/missing-translation bugs. Verify age-gate, bottom nav,
   product cards, cart, checkout, profile, subscription in every language.
4. **Verify the admin panel end-to-end.** Log in, and exercise CRUD for products, categories, tags,
   orders, promo codes, users, settings. Confirm the mini-app reflects admin changes (create a product in
   admin → it appears in the mini-app catalog). Note: admin product create/update expects **flat
   translation keys** `title_<lang>` / `description_<lang>` in the payload (NOT a `translations` array —
   the `ProductCreate` schema is misleading; the service reads `title_en`, etc.).
5. **Create and connect a real Telegram bot.** Use the browser (Telegram Web) to talk to @BotFather:
   create a bot, get the token and username, set a Mini App / menu button URL. Then:
   - Put the token in `.env` (`BOT_TOKEN`, `BOT_USERNAME`), and set `TELEGRAM_WEBAPP_URL` to the public
     mini-app URL.
   - The mini-app must be reachable over HTTPS for Telegram: use the `cloudflared` service
     (`infra/docker-compose.yml`) with a tunnel, or `cloudflared tunnel --url` quick tunnel; wire the
     public URL into BotFather and `TELEGRAM_WEBAPP_URL`/`VITE_API_BASE_URL` as needed.
   - Bring up the `bot` and `cloudflared` compose services (currently excluded). Rebuild as needed.
   - Once a REAL bot token exists, real Telegram initData works — the forged `VITE_DEV_INIT_DATA` dev
     hack is only for browser-without-Telegram testing.
   - **HUMAN-IN-THE-LOOP:** creating the bot requires logging into the user's Telegram account (phone +
     login code) in the browser. You cannot do this alone — stop and get the user to authenticate when
     BotFather/Telegram Web needs it. Do not invent tokens.
6. **Definition of done:** open the mini-app inside Telegram (via the bot) and browse a real catalog;
   admin changes reflect live; all 10 languages render cleanly; bot responds; no console/network errors.
   Report exactly what you verified and how.

## Useful technical notes

- **Mini-app auth flow:** `apps/miniapp/src/shared/api/client.ts` sends header `x-telegram-init-data`
  = `window.Telegram.WebApp.initData`. Backend validates it in `apps/backend/app/core/security.py`
  (`validate_init_data`) and `app/auth.py` (`get_current_user`), using `BOT_TOKEN` as the HMAC secret.
- **Regenerate the dev forged initData** (needed only while there's no real bot; expires ~24h). Run this
  inside the backend container and paste the output into `apps/miniapp/.env.development` as
  `VITE_DEV_INIT_DATA="..."`, then restart the vite dev server:
  ```python
  # docker.exe -c desktop-linux exec -i infra-backend-1 python <<'PY'
  import hmac,hashlib,json,urllib.parse,time
  from app.core.config import settings
  bt=settings.bot_token or ""
  u=json.dumps({"id":123456789,"first_name":"Dev","username":"devuser","language_code":"en"},separators=(",",":"))
  ad=str(int(time.time())); p={"auth_date":ad,"user":u}
  dcs="\n".join(f"{k}={v}" for k,v in sorted(p.items()))
  sec=hmac.new(b"WebAppData",bt.encode(),hashlib.sha256).digest()
  h=hmac.new(sec,dcs.encode(),hashlib.sha256).hexdigest()
  print("&".join([f"auth_date={ad}","user="+urllib.parse.quote(u),"hash="+h]))
  PY
  ```
- **Run the mini-app dev server:** it's a Vite app in `apps/miniapp`. `npm ci` then `npm run dev`
  (native Windows works fine; port 5173 is taken by another project `telebuba`, so use another port,
  e.g. `npm run dev -- --port 5174 --strictPort`). Node is on PATH.
- **Backend catalog endpoints the mini-app needs:** `GET /products`, `GET /products/{slug}`,
  `POST /products/{id}/view`, plus favorites/orders/users modules (see `apps/backend/app/modules/`).
  All require the initData header.
- **Explore with Serena/Semble** (symbol search) rather than reading whole files.

## Cautions

- Don't reintroduce `npm install` in the admin Dockerfile (it hangs) — keep `npm ci`.
- Don't rely on WSL for docker. Don't delete the WSL backup copy at `/home/userpnj/telegram-bot0Video`.
- Product create/update: flat `title_<lang>` keys, not a translations array.
- Rebuild the backend image after backend code edits.
- Bot creation / Telegram login needs the user — pause for them.
