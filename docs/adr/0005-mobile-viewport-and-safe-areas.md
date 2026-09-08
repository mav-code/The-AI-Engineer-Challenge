# ADR-0005: Dynamic viewport units and safe-area insets for the app shell

- **Status:** Accepted
- **Decided:** 2026-09-07 (`a0801e7`)
- **Recorded:** 2026-09-08
- **Applies to:** `frontend/app/globals.css`, `frontend/app/layout.tsx`, the shell element in `ChatInterface.tsx`

## Context

The app is a full-height shell: header, scrolling transcript, footer pinned to
the bottom. A user reported the send button being off-screen on mobile, but
could not reproduce it on demand — which is the signature of a bug that depends
on transient viewport state rather than screen width.

## Decision

**Never use `h-screen` (`100vh`) for the app shell.** On mobile `100vh` is the
*layout* viewport: it ignores the on-screen keyboard and the collapsing URL bar,
so a bottom-anchored footer is pushed below the visible area the moment the
keyboard opens. The shell uses the `.app-viewport` utility, which declares
`height: 100vh` and then `height: 100dvh` — the `vh` line surviving as the
fallback for browsers older than `dvh` (pre-Safari 15.4 / Chrome 108).

**`pb-safe` and `viewport-fit=cover` are coupled.** The footer's bottom padding
is `max(1rem, env(safe-area-inset-bottom))` so it clears the iPhone home
indicator. `env(safe-area-inset-*)` resolves to `0px` unless the viewport meta
carries `viewport-fit=cover`, which is set via the `viewport` export in
`app/layout.tsx`. Removing either one silently disables the other.

## Consequences

- Any future full-height container must use `.app-viewport`, not `h-screen`. A
  stray `h-screen` reintroduces the original bug on mobile only.
- The `viewport` export in `layout.tsx` exists primarily for `viewport-fit`; it
  otherwise restates the Next.js defaults.
- **`min-w-0` on the composer textarea is defensive only.** It was *not* the
  cause of the off-screen send button. Verified with Playwright across
  240–414px, with and without the class: results identical, `scrollWidth` never
  exceeding the viewport. Do not cite it as the fix.
- The keyboard scenario itself remains unverified on real hardware — it cannot be
  reproduced in a desktop browser. The `dvh` change is the standard remedy for
  the reported symptom, not a confirmed diagnosis.
