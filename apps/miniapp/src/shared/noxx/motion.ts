import * as React from 'react'
import gsap from 'gsap'

// NoxX motion layer — GSAP-driven, mirroring the reference design's motion:
// pressFx, animateScreen, popIn, heroIn, pop, pulse, heartPop, indicator slides,
// plus the gate/success entrance timelines.

export const reduce = (): boolean => {
  try {
    return typeof window !== 'undefined' &&
      !!window.matchMedia &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches
  } catch {
    return false
  }
}

// Shared easing tokens (GSAP ease strings).
export const E = {
  out2: 'power2.out',
  out3: 'power3.out',
  back15: 'back.out(1.5)',
  back16: 'back.out(1.6)',
  back24: 'back.out(2.4)',
  back3: 'back.out(3)',
  back32: 'back.out(3.2)',
  back35: 'back.out(3.5)',
} as const

type El = Element | null | undefined

function fromTo(el: El, from: gsap.TweenVars, to: gsap.TweenVars): void {
  if (!el || reduce()) return
  gsap.fromTo(el, from, { overwrite: 'auto', clearProps: 'opacity,transform', ...to })
}

/* ---- micro-interactions ---- */

export function pop(el?: El) {
  fromTo(el, { scale: 0.3 }, { scale: 1, duration: 0.5, ease: E.back32 })
}

export function pulse(el?: El) {
  fromTo(el, { scale: 1.16 }, { scale: 1, duration: 0.45, ease: E.out3 })
}

export function heartPop(el?: El) {
  fromTo(el, { scale: 0.5 }, { scale: 1, duration: 0.55, ease: E.back35 })
}

export function heroIn(el?: El) {
  fromTo(el, { scale: 1.08 }, { scale: 1, duration: 0.7, ease: E.out2 })
}

export function planDotPop(el?: El) {
  fromTo(el, { scale: 0 }, { scale: 1, duration: 0.42, ease: E.back3 })
}

export function popIn(el?: El, origin = 'center') {
  if (!el || reduce()) return
  const dy = /top/.test(origin) ? -6 : 6
  ;(el as HTMLElement).style.transformOrigin = origin
  fromTo(el, { opacity: 0, scale: 0.92, y: dy }, { opacity: 1, scale: 1, y: 0, duration: 0.2, ease: E.out2 })
}

/** Soft pulse for "Loading…" placeholders (self-expiring so detached nodes don't tween forever). */
export function loadingPulse(el?: El) {
  if (!el || reduce()) return
  gsap.fromTo(el, { opacity: 1 }, { opacity: 0.35, duration: 0.7, ease: 'sine.inOut', yoyo: true, repeat: 20, overwrite: 'auto' })
}

/* Stable ref-callbacks for the transpiled views (identity must not change
   between renders, otherwise React re-runs the ref on every render). */
export const loadingPulseRef = (el: Element | null) => { if (el) loadingPulse(el) }
export const popInRef = (el: Element | null) => { if (el) popIn(el, 'bottom right') }
export const planDotPopRef = (el: Element | null) => { if (el) planDotPop(el) }

/* ---- screen entrance (animateScreen) ---- */

// Guards against StrictMode's double layout-effect on the same screen node.
let _lastEnter: { el: HTMLElement | null; t: number } = { el: null, t: 0 }

export function enterScreen(rootEl?: El) {
  if (reduce()) return
  // Resolve the real screen element. App.tsx passes a display:contents wrapper
  // whose only child is the position:absolute screen, so descend to (or fall back
  // to) the single router-mounted [data-screen-label] element.
  let screen = (rootEl as HTMLElement | null) ?? null
  if (!screen || !screen.matches?.('[data-screen-label]')) {
    screen =
      (screen?.querySelector?.('[data-screen-label]') as HTMLElement | null) ??
      (document.querySelector('[data-screen-label]') as HTMLElement | null)
  }
  if (!screen) return
  // Screens with their own entrance timeline (gate/success) opt out.
  if (screen.hasAttribute('data-self-anim') || screen.querySelector('[data-self-anim]')) return

  // StrictMode double-invokes layout effects; a second run mid-flight would kill
  // the first tween and can strand blocks at opacity 0. Debounce repeat calls on
  // the same screen node within one frame-window.
  const now = (typeof performance !== 'undefined' ? performance.now() : 0)
  if (_lastEnter.el === screen && now - _lastEnter.t < 150) return
  _lastEnter = { el: screen, t: now }

  // Clear any stranded inline state left by a previous (gsap-era) entrance.
  screen.style.opacity = ''
  screen.style.transform = ''

  // Prefer explicit [data-anim] blocks (reference parity); else stagger the
  // content region's children (descend into a lone list so rows cascade).
  let items = Array.from(screen.querySelectorAll('[data-anim]')) as HTMLElement[]
  if (!items.length) {
    const container = findContent(screen)
    items = container ? flowChildren(container) : []
    if (items.length === 1 && items[0].children.length >= 2) {
      items = flowChildren(items[0])
    }
  }
  // CSS-animation driven (compositor, not gsap/rAF) so the tab transition plays
  // reliably in Telegram WebViews. `backwards` fill hides each item only during
  // its stagger delay, then reverts to the element's own styles — nothing is left
  // stranded, so no safety sweep is needed.
  if (items.length) {
    const spread = Math.min(0.4, items.length * 0.06)
    items.forEach((el, i) => {
      const delay = items.length > 1 ? (i / (items.length - 1)) * spread : 0
      el.style.animation = `noxxItemIn .42s cubic-bezier(.22,.61,.36,1) ${delay.toFixed(3)}s backwards`
    })
  } else {
    screen.style.animation = 'noxxScreenIn .26s ease-out backwards'
  }
}

/** In-flow (non absolute/fixed) element children. */
function flowChildren(el: Element): HTMLElement[] {
  return (Array.from(el.children) as HTMLElement[]).filter((c) => {
    const pos = getComputedStyle(c).position
    return pos !== 'absolute' && pos !== 'fixed'
  })
}

function findContent(screen: Element): HTMLElement | null {
  const kids = flowChildren(screen)
  // Every screen is a flex column with one flex:1 content region — that's the
  // block set to stagger. Prefer flex-grow (reliable) over overflow, since a
  // horizontally-scrolling row (e.g. Catalog's category pills) also computes
  // overflow-y:auto and would otherwise win.
  const region =
    kids.find((el) => parseFloat(getComputedStyle(el).flexGrow) >= 1) ??
    kids.find((el) => {
      const oy = getComputedStyle(el).overflowY
      return oy === 'auto' || oy === 'scroll'
    })
  if (region) return region
  // Fallback: the child with the most children.
  let best: HTMLElement | null = null
  let bestKids = 1
  for (const el of kids) {
    if (el.children.length > bestKids) {
      bestKids = el.children.length
      best = el
    }
  }
  return best
}

/* ---- entrance timelines for standalone screens ---- */

/** Age gate: badge springs in, then copy/checkbox/button rise in sequence.
 *  Returns the timeline — callers must kill() it in their effect cleanup so a
 *  StrictMode double-mount cannot strand elements at opacity 0. */
export function gateIn(rootEl?: El): gsap.core.Timeline | undefined {
  if (!rootEl || reduce()) return
  const root = rootEl as HTMLElement
  const kids = Array.from(root.children).filter((el) => {
    const pos = getComputedStyle(el).position
    return pos !== 'absolute' && pos !== 'fixed'
  })
  if (!kids.length) return
  const [badge, ...rest] = kids
  gsap.killTweensOf(kids)
  gsap.set(kids, { clearProps: 'opacity,transform' })
  const tl = gsap.timeline()
  tl.fromTo(badge, { opacity: 0, scale: 0.55 }, { opacity: 1, scale: 1, duration: 0.65, ease: E.back24, clearProps: 'opacity,transform' })
  if (rest.length) {
    tl.fromTo(
      rest,
      { opacity: 0, y: 14 },
      { opacity: 1, y: 0, duration: 0.45, ease: E.out2, stagger: 0.09, clearProps: 'opacity,transform' },
      '-=0.35',
    )
  }
  return tl
}

/** Payment success: check bursts in, tick draws itself, copy/buttons rise.
 *  Returns the timeline — kill() it in the effect cleanup (StrictMode). */
export function successIn(rootEl?: El): gsap.core.Timeline | undefined {
  if (!rootEl || reduce()) return
  const root = rootEl as HTMLElement
  const check = root.querySelector('[data-success-check]') as HTMLElement | null
  const tickPath = check?.querySelector('svg path') as SVGPathElement | null
  const kids = (Array.from(root.children) as HTMLElement[]).filter((el) => {
    const pos = getComputedStyle(el).position
    return pos !== 'absolute' && pos !== 'fixed'
  })
  const rest = kids.slice(1)
  gsap.killTweensOf(kids)
  gsap.set(kids, { clearProps: 'opacity,transform' })
  const tl = gsap.timeline()
  if (kids[0]) tl.fromTo(kids[0], { opacity: 0, scale: 0.4 }, { opacity: 1, scale: 1, duration: 0.6, ease: E.back24, clearProps: 'opacity,transform' })
  if (tickPath) {
    try {
      const len = tickPath.getTotalLength()
      tl.fromTo(
        tickPath,
        { strokeDasharray: len, strokeDashoffset: len },
        { strokeDashoffset: 0, duration: 0.45, ease: E.out2, clearProps: 'strokeDasharray,strokeDashoffset' },
        '-=0.25',
      )
    } catch { /* non-rendered svg */ }
  }
  if (rest.length) {
    tl.fromTo(
      rest,
      { opacity: 0, y: 14 },
      { opacity: 1, y: 0, duration: 0.45, ease: E.out2, stagger: 0.09, clearProps: 'opacity,transform' },
      '-=0.2',
    )
  }
  return tl
}

/* ---- press feedback (pressFx via global delegation) ---- */

let pressed: HTMLElement | null = null

export function bindPress(): () => void {
  const sel = 'button,[data-press]'
  const onDown = (e: Event) => {
    if (reduce()) return
    const t = e.target as HTMLElement | null
    const b = t && t.closest ? (t.closest(sel) as HTMLElement | null) : null
    if (b) {
      pressed = b
      gsap.to(b, { scale: 0.955, duration: 0.11, ease: E.out2, overwrite: 'auto' })
    }
  }
  const onUp = () => {
    if (pressed) {
      gsap.to(pressed, { scale: 1, duration: 0.34, ease: E.back24, overwrite: 'auto', clearProps: 'transform' })
      pressed = null
    }
  }
  document.addEventListener('pointerdown', onDown, true)
  window.addEventListener('pointerup', onUp, true)
  window.addEventListener('pointercancel', onUp, true)
  return () => {
    document.removeEventListener('pointerdown', onDown, true)
    window.removeEventListener('pointerup', onUp, true)
    window.removeEventListener('pointercancel', onUp, true)
  }
}

/* ---- sliding indicator (nav / catalog pills / purchases tabs) ----
   CSS-transition driven (transform/width), matching the reference's
   positionNavIndicator/positionPTab/positionCatPill. CSS transitions are
   compositor-based and play reliably in Telegram WebViews. The slide only works
   because useIndicator no longer lets a ResizeObserver/font-ready re-place snap
   it mid-animation (see below). */

const IND_EASE = 'cubic-bezier(.34,1.56,.64,1)' // easeOutBack — matches the reference's back.out overshoot

export function slideIndicator(
  ind: HTMLElement | null | undefined,
  item: HTMLElement | null | undefined,
  opts: { animate?: boolean; width?: boolean; vertical?: boolean; center?: boolean; ease?: string; duration?: number } = {},
) {
  if (!ind || !item) return
  const { animate = true, width = true, vertical = false, center = false, duration = 500 } = opts
  // `center`: keep a fixed-width indicator centered under the item (nav dashes).
  // Otherwise the indicator's left edge tracks the item (segmented pills).
  const x = center ? item.offsetLeft + item.offsetWidth / 2 - ind.offsetWidth / 2 : item.offsetLeft
  if (vertical) {
    ind.style.top = item.offsetTop + 'px'
    ind.style.height = item.offsetHeight + 'px'
  }
  const dur = duration / 1000
  ind.style.transition = animate && !reduce()
    ? `transform ${dur}s ${IND_EASE}, width ${dur}s ${IND_EASE}`
    : 'none'
  ind.style.transform = `translateX(${x}px)`
  if (width) ind.style.width = item.offsetWidth + 'px'
}

/* ---- React hook: keep a sliding indicator glued to the active item ---- */

export function useIndicator(
  wrapRef: React.RefObject<HTMLElement | null>,
  indSelector: string,
  activeSelector: string,
  dep: unknown,
  opts: { vertical?: boolean; center?: boolean; ease?: string; duration?: number; width?: boolean } = {},
) {
  const first = React.useRef(true)
  const place = (animate: boolean) => {
    const wrap = wrapRef.current
    if (!wrap) return
    const ind = wrap.querySelector(indSelector) as HTMLElement | null
    const active = wrap.querySelector(activeSelector) as HTMLElement | null
    slideIndicator(ind, active, { ...opts, animate })
  }

  // Animated re-place when the active item changes (slide). First run doesn't
  // animate (no slide-in on mount).
  React.useLayoutEffect(() => {
    place(!first.current)
    first.current = false
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [dep])

  // Reposition WITHOUT animating on real layout changes (font load, resize).
  // Mounted once — a ResizeObserver fires immediately on observe() and
  // document.fonts.ready is already resolved, so doing this in the [dep] effect
  // would snap the indicator right after every animated slide and kill it.
  React.useLayoutEffect(() => {
    const wrap = wrapRef.current
    if (!wrap) return
    let lastW = wrap.offsetWidth
    let ro: ResizeObserver | undefined
    if (typeof ResizeObserver !== 'undefined') {
      ro = new ResizeObserver(() => {
        const w = wrap.offsetWidth
        if (w !== lastW) { lastW = w; place(false) } // only on an actual size change
      })
      ro.observe(wrap)
    }
    try {
      const fonts = (document as { fonts?: { ready?: Promise<unknown> } }).fonts
      fonts?.ready?.then(() => place(false))
    } catch { /* document.fonts unsupported */ }
    return () => ro?.disconnect()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])
}
