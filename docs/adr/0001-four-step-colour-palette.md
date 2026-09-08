# ADR-0001: Four-step colour palette with ±1 adjacency

- **Status:** Accepted
- **Decided:** 2026-06-01 (`2d3c5f1`)
- **Recorded:** 2026-09-08 — written retroactively from CLAUDE.md
- **Applies to:** `frontend/components/ChatInterface.tsx`, `frontend/app/globals.css`, any new surface or generated asset

## Context

The UI is a stack of surfaces that touch each other: page background → header →
message area → bubbles → footer → controls. Picking colours per-component
produces muddy or low-contrast adjacencies, and the project's frontend rules
already forbid poor contrast outright. A rule was needed that makes the
*relationship* between surfaces decidable rather than a matter of taste.

## Decision

A single warm ramp of four discrete steps, plus one accent that is never used as
a surface fill. **Every pair of touching surfaces must be exactly ±1 step
apart.**

| Step | Hex | Role |
|---|---|---|
| 1 | `#D45F2A` | Page background (burnt orange) |
| 2 | `#EDA551` | Header, user bubbles, user avatar (warm amber) |
| 3 | `#F9D074` | Message area, send button (warm yellow) |
| 4 | `#F8F0E4` | AI bubbles, input footer, textarea (warm cream) |
| Accent | `#E2C3DA` | Focus rings, decorative borders (dusty mauve) |

Contact graph — consult before adding a surface:

```
page bg (1) ↔ header (2) ↔ message area (3) ↔ AI bubbles (4)
                                            ↔ user bubbles (2)
                                            ↔ footer (4) ↔ textarea (4)
                                                          ↔ send btn (3)
```

## Consequences

- A new surface must be placed on the contact graph before its colour is chosen;
  the graph, not preference, determines the answer.
- Arbitrary colours cannot be introduced. A design that needs a fifth value is a
  reason to revisit this ADR, not to break it locally.
- The rule extends to generated assets. The favicon and social card
  (`frontend/app/icon.svg`, `opengraph-image.png`) use steps 1 and 2 against each
  other for exactly this reason — see [ADR-0002](0002-twemoji-avatars.md).
- Text colour is not a surface and is not bound by the ±1 rule; body copy is
  near-black for real contrast.
