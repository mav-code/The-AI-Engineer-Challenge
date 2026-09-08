# ADR-0002: Avatars are Twemoji SVGs, not system emoji glyphs

- **Status:** Accepted
- **Decided:** 2026-06-02 (`555bb87`)
- **Recorded:** 2026-09-08 — written retroactively from CLAUDE.md
- **Applies to:** the `Avatar` component and its constants in `frontend/components/ChatInterface.tsx`

## Context

The Analyst and the patient are represented by emoji. Rendered as text glyphs,
emoji are drawn by the platform's own font — Apple, Windows and Android each
draw 🧐 and 😰 differently, in different proportions and with different padding
inside the em box. A layout tuned on one platform is wrong on the others, and
the character *is* the product here.

## Decision

Load avatars as `<img>` elements pointing at the Twemoji SVG CDN (jsDelivr,
v14.0.2) so every platform renders identical artwork.

- Analyst: 🧐 `U+1F9D0` → `1f9d0.svg`
- Patient: 😰 `U+1F630` → `1f630.svg`
- `EMOJI_SCALE = '109%'` — a **geometric** constant: `1 / (33/36)`, where 33/36
  is the Twemoji face-to-viewBox ratio. It is derived, not tuned. Do not replace
  it with a per-platform magic number.
- The avatar `<div>` uses `overflow-visible` + `rounded-full`, so the face fills
  the circular border and small extrusions (the monocle chain, the sweat bead)
  escape the circle naturally rather than being clipped.

All three constants live at the top of `ChatInterface.tsx` and are consumed
through the shared `Avatar` component. Sizes and positions are never inlined at
call sites.

## Consequences

- Avatars depend on a third-party CDN at runtime. Accepted: they are decorative,
  and `alt` text carries the meaning.
- Because these are `<img>` tags rather than `next/image`, the
  `@next/next/no-img-element` rule is suppressed at the call site with a stated
  reason — `next/image` passes SVGs through unoptimised and would only add a
  `remotePatterns` config. See `frontend/.eslintrc.js`.
- **The favicon deliberately does not reuse this artwork.** A full emoji face is
  illegible at 16px, and vendoring Twemoji into the repo would bring its CC-BY
  attribution requirement with it. `frontend/app/icon.svg` is instead an original
  monocle mark drawn in the [ADR-0001](0001-four-step-colour-palette.md) palette.
