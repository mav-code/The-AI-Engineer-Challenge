// Session bookkeeping for The Analyst: turn limits and the overnight lockout.
// Pure functions only — localStorage access stays in the component, so all of
// this is unit-testable without a browser.

// A session ends after this many USER turns (the Analyst bills by the turn).
export const SESSION_LIMIT = 12

export function userTurnCount(messages: { role: string }[]): number {
  return messages.filter((m) => m.role === 'user').length
}

// The lockout lasts until the next local midnight — "come back tomorrow"
// in the patient's own timezone. At exactly midnight you still get the
// full following day, never a zero-length lockout.
export function nextMidnight(now: Date): number {
  const midnight = new Date(now.getFullYear(), now.getMonth(), now.getDate() + 1)
  return midnight.getTime()
}

export function isLockedOut(lockedUntil: number | null, now: Date): boolean {
  return lockedUntil !== null && now.getTime() < lockedUntil
}

// ── The dossier: everything the Analyst keeps on a patient ──────────────────
// Stored in localStorage only — the "file" never leaves the patient's browser.

export interface DossierMessage {
  role: string
  content: string
}

export interface Dossier {
  messages: DossierMessage[]
  ended: boolean
  notes: string | null // this session's case notes, if fetched
  sessionCount: number // 1-based number of the CURRENT session
}

const FRESH_DOSSIER: Dossier = { messages: [], ended: false, notes: null, sessionCount: 1 }

export function parseDossier(raw: string | null): Dossier {
  if (!raw) return { ...FRESH_DOSSIER }
  try {
    const parsed = JSON.parse(raw)
    if (typeof parsed !== 'object' || parsed === null || !Array.isArray(parsed.messages)) {
      return { ...FRESH_DOSSIER }
    }
    return {
      messages: parsed.messages,
      ended: Boolean(parsed.ended),
      notes: typeof parsed.notes === 'string' ? parsed.notes : null,
      sessionCount: typeof parsed.sessionCount === 'number' ? parsed.sessionCount : 1,
    }
  } catch {
    return { ...FRESH_DOSSIER }
  }
}

// Greetings. Session 1 is the canonical welcome; returning patients get a
// recognition chosen deterministically by session number (so tests — and
// reloads — see the same line).
const FIRST_VISIT_GREETING =
  'Ah. You haff come.\n\nZis vas not a coincidence, you know. Ze mind does not make accidents. Sit down und tell me everyzing. I am listening.'

const RETURNING_GREETINGS = [
  'Ah. You return. Session %N%. Ze couch remembers your shape. Sit.',
  'So. Session %N%. You could not stay avay — zis itself is diagnostic. Sit down.',
  'Punctual, for vunce. Session %N%. Let us see vat has festered since last time.',
]

export function greeting(sessionCount: number): string {
  if (sessionCount <= 1) return FIRST_VISIT_GREETING
  const variant = RETURNING_GREETINGS[(sessionCount - 2) % RETURNING_GREETINGS.length]
  return variant.replace('%N%', String(sessionCount))
}

// Canned ritual delivered after the final exchange's reply — the model's own
// closing varies, but the session always ends on this fixed, clock-watching
// dismissal so the cutoff never feels abrupt.
export const CLOSING_LINE =
  '*glances at ze clock* Our time is up. Go home. Sleep. Und if you dream — write it down. Ze office reopens tomorrow.'
