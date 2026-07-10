# Cloudflare security response headers — noxx-shop

Manual, click-by-click configuration for the `noxxshop.com` zone in the Cloudflare
dashboard. Nothing here is code — apply it directly in Cloudflare.

## Hosts in this zone (confirmed from the repo)

| Host | Service | Notes |
|---|---|---|
| `app.noxxshop.com` | miniapp (nginx static + `/api`, `/media` same-origin proxy) | Must render inside the Telegram in-app webview iframe |
| `api.noxxshop.com` | backend (FastAPI) | Already sets `X-Content-Type-Options` + `Referrer-Policy` itself (`apps/backend/app/main.py`) |
| `admin.noxxshop.com` | admin (react-admin SPA), calls `api.noxxshop.com` cross-origin | Not embedded anywhere — can be locked down hard |
| `media.noxxshop.com` | Cloudflare R2 custom domain (video/image CDN) | Binary media only, no HTML |

`admin.noxxshop.com` was not in `.env.example`/config (only the `ADMIN_PUBLIC_URL` variable name is
there) — it comes from project memory (`telegram-bot0video-production-domain`) which records the
actual tunnel routing: `app.noxxshop.com→miniapp:80`, `api.noxxshop.com→backend:8000`,
`admin.noxxshop.com→admin:3000`. If the operator has since renamed it, swap the hostname below.

The admin SPA is built with `VITE_API_BASE_URL=https://api.noxxshop.com` baked in at build time
(`.github/workflows/build-images.yml`), so it calls the API **cross-origin**, not through a
same-origin proxy like the miniapp does. That changes its CSP `connect-src`.

## Where to configure this

**Rules → Transform Rules → Response Header Transform Rules** (called "Modify Response Header" in
the UI). Available on the Free plan. Create one rule per host below, each scoped with a `Custom
filter expression` on `http.host`.

For HSTS specifically, use **SSL/TLS → Edge Certificates → HTTP Strict Transport Security (HSTS)**
instead of a Transform Rule — it's zone-wide, one toggle, and Cloudflare recommends it over a
manually-set `Strict-Transport-Security` header. Since all four hosts should get HSTS, set it once
at the zone level rather than duplicating it in every Transform Rule.

### HSTS (zone-level, SSL/TLS → Edge Certificates → HSTS)

1. Dashboard → zone `noxxshop.com` → **SSL/TLS** → **Edge Certificates**.
2. Scroll to **HTTP Strict Transport Security (HSTS)** → **Enable HSTS** → confirm the warning dialog.
3. Set:
   - **Max Age Header (max-age)**: `12 months` (`31536000` seconds)
   - **Apply HSTS policy to subdomains (includeSubDomains)**: ON
   - **Preload**: **OFF**
   - **No-Sniff header (`X-Content-Type-Options: nosniff`)**: leave **OFF** here — the backend
     already sends this itself, and Cloudflare's HSTS panel applies its no-sniff toggle
     zone-wide, which would double up on `api.noxxshop.com` responses.
4. Save.

**Preload tradeoff:** `preload` submits the zone to the browser-vendor HSTS preload list, baked
into Chrome/Firefox/Safari — it protects the very first visit (no trust-on-first-use window) but
is effectively **irreversible on any practical timescale** (removal takes months and only works if
you submitted removal before most browser releases shipped your entry). Don't enable it until
HTTPS has been solid across all four hosts for a while and there's no plan to ever run any
`*.noxxshop.com` subdomain over plain HTTP. Revisit in a few months, not now.

## Rule 1: `admin.noxxshop.com`

**Filter expression:** `http.host eq "admin.noxxshop.com"`

Set these response headers:

| Header | Value |
|---|---|
| `Content-Security-Policy-Report-Only` | see policy below |
| `X-Frame-Options` | `DENY` |
| `Permissions-Policy` | `camera=(), microphone=(), geolocation=()` |
| `Referrer-Policy` | `strict-origin-when-cross-origin` |

Do **not** set `X-Content-Type-Options` here from Cloudflare if you later decide to front the admin
static bundle through the backend — for now the admin container is a plain static SPA host with no
origin-set security headers, so it's safe to set `Referrer-Policy` at Cloudflare for this host.

**CSP policy for the react-admin + Material UI SPA** (now **enforcing** — see status note below):

```
Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https://media.noxxshop.com; media-src 'self' https://media.noxxshop.com; font-src 'self' data:; connect-src 'self' https://api.noxxshop.com https://*.ingest.de.sentry.io; frame-ancestors 'none'; base-uri 'self'; form-action 'self'; object-src 'none'
```

Notes on the directives:
- `style-src 'unsafe-inline'` is needed because Material UI's emotion CSS-in-JS injects `<style>`
  tags at runtime; Cloudflare Transform Rules can't hand out a per-request nonce, so a strict
  `style-src` isn't achievable here without changing the app itself.
- `connect-src` includes `https://api.noxxshop.com` (cross-origin API calls) and
  `https://*.ingest.de.sentry.io` (Sentry error reporting — org `viniji` is on the `de` region;
  only wired up if `VITE_SENTRY_DSN` is set for the build).
- `img-src` includes `https://media.noxxshop.com` because product cover images are served as full
  R2 CDN URLs (`apps/backend/app/core/r2.py`), not proxied through the admin origin.
- `media-src 'self' https://media.noxxshop.com` is **required** too: the product editor previews the
  existing `preview_video_url` (`<video src="https://media.noxxshop.com/...mp4">`). Without it,
  `media-src` falls back to `default-src 'self'` and the video preview is silently blocked (image
  still shows, since that's covered by `img-src`). This was missed in the first enforcing flip and
  added after the admin video preview broke — keep it.
- `frame-ancestors 'none'` is intentionally stricter than `X-Frame-Options: DENY` needs to be —
  keep both; older browsers only understand `X-Frame-Options`.

**Status:** the admin rule is now **enforcing** (`Content-Security-Policy`, not Report-Only) as of
2026-07-10, verified in-browser against the dashboard, product list, and product editor (image +
video preview + live API calls all load clean). The miniapp rule (`app.noxxshop.com`, below) is
still `Content-Security-Policy-Report-Only` — it can only be safely flipped after testing inside the
real Telegram client, since it can't be exercised in a plain browser.

**How the flip was done (for reference / re-doing on another host):** edit the existing Transform
Rule and rename its header from `Content-Security-Policy-Report-Only` to `Content-Security-Policy`
(value unchanged). Watch for a new inline script/style pattern from a Vite build or MUI bump that a
short observation window wouldn't have surfaced — re-verify in-browser after any admin redeploy.

## Rule 2: `app.noxxshop.com` (miniapp — must stay embeddable)

**Filter expression:** `http.host eq "app.noxxshop.com"`

This is the Telegram Mini App, opened inside Telegram's in-app webview `<iframe>`. **Do not** set
`X-Frame-Options` or a restrictive `frame-ancestors` here — either one breaks the app inside
Telegram entirely (blank screen, no fallback).

Set only:

| Header | Value |
|---|---|
| `Content-Security-Policy-Report-Only` | see policy below |

**CSP (Report-Only)**, built from what `apps/miniapp/index.html` actually loads (the Telegram
Web App script) plus the same-origin `/api` and `/media` nginx proxies (`apps/miniapp/nginx.conf`)
and the CDN host media is actually served from:

```
Content-Security-Policy-Report-Only: default-src 'self'; script-src 'self' https://telegram.org; style-src 'self' 'unsafe-inline'; img-src 'self' data: https://media.noxxshop.com; media-src 'self' https://media.noxxshop.com; font-src 'self' data:; connect-src 'self' https://media.noxxshop.com https://*.ingest.de.sentry.io; frame-ancestors *; base-uri 'self'; form-action 'self'; object-src 'none'
```

Notes:
- `script-src` allows `https://telegram.org` for `<script src="https://telegram.org/js/telegram-web-app.js">`.
- `img-src`/`media-src` allow `https://media.noxxshop.com` directly — product `cover_url` /
  `preview_video_url` values returned by the API are full R2 CDN URLs, not paths behind the `/media`
  nginx proxy.
- `connect-src 'self'` covers the same-origin `/api` and `/media` proxy paths; the miniapp itself
  never calls `api.noxxshop.com` cross-origin (unlike admin).
- `frame-ancestors *` is explicit (equivalent to omitting the directive) so it's obvious in the
  policy text that embedding is intentionally unrestricted — don't ever tighten this without
  re-testing inside the actual Telegram client (both mobile and desktop webviews).
- Since this is Report-Only for now, an over-permissive `frame-ancestors *` costs nothing extra;
  revisit only if you ever need clickjacking protection on a *non-Telegram* entry point to this host.

## Rule 3: `api.noxxshop.com` — do NOT duplicate origin headers

**No Transform Rule needed for security headers on this host.**

`apps/backend/app/main.py` already sets, on every response, via `response.headers.setdefault(...)`:
- `X-Content-Type-Options: nosniff`
- `Referrer-Policy: strict-origin-when-cross-origin`

Setting the same headers again at Cloudflare is redundant at best; if a future Cloudflare rule
used a "Set static" action (rather than one that respects existing headers) it would silently
overwrite the origin's Content-Type-Options/Referrer-Policy semantics with no benefit — and one
more place to keep in sync when the backend changes them. Leave `api.noxxshop.com` alone here.
CSP/`X-Frame-Options` don't apply to a JSON API and are deliberately not set by the backend either
(see the comment above `_security_headers` in `main.py`).

Zone-level HSTS (above) already covers this host.

## Rule 4: `media.noxxshop.com` — minimal

**Filter expression:** `http.host eq "media.noxxshop.com"`

No Transform Rule needed beyond zone-level HSTS. This host serves binary video/image bytes from an
R2 bucket, not HTML — CSP, `X-Frame-Options`, and `Permissions-Policy` have no meaningful effect on
byte responses and risk breaking a future use case (e.g. if this host ever serves an HTML preview
page) for no gain.

**R2 bucket listing:** this isn't a Cloudflare response-header setting — it's a bucket
configuration. Confirm in **R2 → (bucket) → Settings → Public Access** that only the connected
custom domain (`media.noxxshop.com`) serves objects, and that the bucket's own `r2.dev` public URL
is **disabled**. Neither exposes S3 `ListObjects` by default, but don't attach a Worker or any
custom route that would. Full detail in `docs/server-hardening-runbook.md`.

## Verification checklist

Run after applying all rules (allow a minute or two for Cloudflare's edge to propagate):

```bash
# admin: CSP-Report-Only, X-Frame-Options DENY, Permissions-Policy, HSTS
curl -sI https://admin.noxxshop.com/ | grep -Ei 'content-security-policy-report-only|x-frame-options|permissions-policy|strict-transport-security|referrer-policy'

# miniapp: CSP-Report-Only present, NO x-frame-options, HSTS present
curl -sI https://app.noxxshop.com/ | grep -Ei 'content-security-policy-report-only|x-frame-options|strict-transport-security'
# ^ the x-frame-options grep should return NOTHING

# api: origin headers still present, no duplicated CSP/frame headers from Cloudflare, HSTS present
curl -sI https://api.noxxshop.com/health | grep -Ei 'x-content-type-options|referrer-policy|strict-transport-security|content-security-policy|x-frame-options'
# ^ x-content-type-options and referrer-policy should appear exactly once each

# media: HSTS present, nothing else unexpected; confirm no directory listing
curl -sI https://media.noxxshop.com/
curl -s https://media.noxxshop.com/ | head -c 500   # should not look like an XML bucket listing
```

Expected results:
- `admin.noxxshop.com`: `content-security-policy-report-only`, `x-frame-options: DENY`,
  `permissions-policy`, `referrer-policy`, `strict-transport-security` all present.
- `app.noxxshop.com`: `content-security-policy-report-only` present; `x-frame-options` **absent**;
  `strict-transport-security` present (transport security doesn't affect framing).
- `api.noxxshop.com`: `x-content-type-options: nosniff` and `referrer-policy` present exactly once
  (from the backend, not doubled by Cloudflare); `strict-transport-security` present; no CSP or
  `x-frame-options` (never set for the API).
- `media.noxxshop.com`: `strict-transport-security` present; response body is the media file or a
  404, never an XML/JSON bucket listing.

Also check **Cloudflare dashboard → Security → Events** after a day of admin traffic for CSP
Report-Only violations surfaced via the browser (visible in each browser's own DevTools console —
no report collector is configured), before flipping the admin policy to enforcing.
