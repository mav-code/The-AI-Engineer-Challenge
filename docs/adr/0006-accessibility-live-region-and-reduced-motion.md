# ADR-0006: Announce completed replies only; honour reduced motion in JS as well as CSS

- **Status:** Accepted
- **Decided:** 2026-09-08 (`0e50f79`)
- **Recorded:** 2026-09-08
- **Applies to:** `frontend/components/ChatInterface.tsx`, `frontend/app/globals.css`

## Context

The app is 100% streamed text revealed by a typewriter effect, which is the
worst case for a screen reader and for anyone sensitive to motion. Before this
decision the component carried three `aria-label`s and nothing else: replies
were never announced, and the typewriter, the bouncing typing indicator and the
pulsing status dot all ran regardless of the OS reduce-motion setting.

## Decision

**The transcript must not be a live region.** The typewriter mutates the last
bubble roughly 40 times per second. Putting `aria-live` on `<main>` — or
`role="log"`, whose *implicit* live region is the same trap — makes a screen
reader read partial words continuously. Instead, a separate `sr-only`
`aria-live="polite"` `aria-atomic="true"` region carries exactly one thing at a
time: the welcome line on load, `"The Analyst is considering."` while a reply is
in flight, and the reply's full text once it has finished revealing. `<main>` is
labelled `Session transcript` and stays ordinarily navigable.

Decorative elements are hidden from the accessibility tree: the typing indicator
(the live region says it in words) and the status dot (the adjacent text says
it).

**Reduced motion is handled in two places because one is not enough.** A blanket
`@media (prefers-reduced-motion: reduce)` block in `globals.css` collapses
animations and transitions to 0.01ms — near-zero rather than `none`, so
`animationend`/`transitionend` still fire. The typewriter is a JS timer that no
media query can reach, so `usePrefersReducedMotion()` supplies the same signal
to React. It starts `false` and reads the real value in an effect, because the
server has no `matchMedia` and guessing would desync hydration.

The reduced-motion path stays routed **through the same timer**, jumping
`typedUpTo` to the full length rather than bypassing the effect, so the
completion branch — and the closing line it queues at the end of a session —
behaves identically either way.

## Consequences

- Anything that announces to a screen reader goes through the single live region.
  Adding a second one, or promoting the transcript to a live region, reintroduces
  the partial-word problem.
- The typewriter's reduced-motion branch must not short-circuit the effect;
  bypassing the timer would drop the queued closing line.
- Verified end-to-end with Playwright against a mocked `/api/chat`: the live
  region is empty mid-typewriter and holds the full text afterwards; reveal takes
  ~3ms under `reduce` versus ~850ms normally; `animate-bounce` collapses to
  0.01ms. Re-run that check after touching either mechanism.
