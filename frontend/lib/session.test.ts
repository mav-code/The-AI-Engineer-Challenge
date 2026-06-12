import { describe, expect, it } from 'vitest'
import { SESSION_LIMIT, isLockedOut, nextMidnight, userTurnCount } from './session'

describe('userTurnCount', () => {
  it('counts only user messages', () => {
    expect(
      userTurnCount([
        { role: 'assistant' }, // WELCOME
        { role: 'user' },
        { role: 'assistant' },
        { role: 'user' },
      ])
    ).toBe(2)
  })

  it('is zero for a fresh session', () => {
    expect(userTurnCount([{ role: 'assistant' }])).toBe(0)
  })
})

describe('nextMidnight', () => {
  it('returns the upcoming local midnight', () => {
    const now = new Date(2026, 5, 11, 15, 30, 0) // June 11, 3:30pm local
    expect(new Date(nextMidnight(now)).getTime()).toBe(new Date(2026, 5, 12, 0, 0, 0).getTime())
  })

  it('at exactly midnight, locks until the NEXT midnight (a full day)', () => {
    const now = new Date(2026, 5, 11, 0, 0, 0)
    expect(new Date(nextMidnight(now)).getTime()).toBe(new Date(2026, 5, 12, 0, 0, 0).getTime())
  })

  it('handles month boundaries', () => {
    const now = new Date(2026, 5, 30, 23, 59, 0) // June 30, 11:59pm
    expect(new Date(nextMidnight(now)).getTime()).toBe(new Date(2026, 6, 1, 0, 0, 0).getTime())
  })
})

describe('isLockedOut', () => {
  const now = new Date(2026, 5, 11, 9, 0, 0)

  it('is false with no stored lockout', () => {
    expect(isLockedOut(null, now)).toBe(false)
  })

  it('is true before the lockout expires', () => {
    expect(isLockedOut(now.getTime() + 60_000, now)).toBe(true)
  })

  it('is false after the lockout expires', () => {
    expect(isLockedOut(now.getTime() - 60_000, now)).toBe(false)
  })
})

describe('SESSION_LIMIT', () => {
  it('is twelve user turns', () => {
    expect(SESSION_LIMIT).toBe(12)
  })
})

import { greeting, parseDossier } from './session'

describe('greeting', () => {
  it('session 1 gets the standard welcome', () => {
    expect(greeting(1)).toMatch(/You haff come/)
  })

  it('returning sessions mention the session number', () => {
    expect(greeting(2)).toContain('Session 2')
    expect(greeting(5)).toContain('Session 5')
  })

  it('returning greetings vary but are deterministic', () => {
    expect(greeting(3)).toBe(greeting(3))
    expect(greeting(2)).not.toBe(greeting(3))
  })
})

describe('parseDossier', () => {
  it('returns a fresh dossier when nothing is stored', () => {
    const d = parseDossier(null)
    expect(d.sessionCount).toBe(1)
    expect(d.messages).toEqual([])
    expect(d.ended).toBe(false)
    expect(d.notes).toBeNull()
  })

  it('returns a fresh dossier on corrupted storage', () => {
    expect(parseDossier('{not json').sessionCount).toBe(1)
    expect(parseDossier('"a string"').messages).toEqual([])
  })

  it('round-trips a real dossier', () => {
    const original = {
      messages: [{ role: 'user', content: 'hello' }],
      ended: true,
      notes: 'Case notes — hm.',
      sessionCount: 4,
    }
    const d = parseDossier(JSON.stringify(original))
    expect(d).toEqual(original)
  })
})
