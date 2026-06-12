'use client'

import { useState, useRef, useEffect, KeyboardEvent, ReactNode } from 'react'
import {
  SESSION_LIMIT,
  greeting,
  isLockedOut,
  nextMidnight,
  parseDossier,
  userTurnCount,
} from '../lib/session'

// localStorage keys: the overnight lockout (ms timestamp of next midnight)
// and the dossier (conversation, session number, case notes).
const LOCKOUT_KEY = 'analyst.lockedUntil'
const DOSSIER_KEY = 'analyst.dossier'

// Converts *word* spans to <em> — the only markdown the model is instructed to emit.
function renderContent(text: string): ReactNode[] {
  return text.split(/(\*[^*\n]+\*)/g).map((part, i) =>
    part.startsWith('*') && part.endsWith('*')
      ? <em key={i}>{part.slice(1, -1)}</em>
      : part
  )
}

interface Message {
  role: 'user' | 'assistant'
  content: string
}

// The opening line is owned by lib/session.ts (greeting(1)) so first-visit
// and returning-patient greetings live side by side.
const WELCOME: Message = { role: 'assistant', content: greeting(1) }

/*
 * Four-step palette — every touching pair of surfaces is exactly ±1 step.
 *
 *   Step 1  #D45F2A  deep burnt orange  page background (card sides on wide screens)
 *   Step 2  #EDA551  warm amber         header, user bubbles, all avatars
 *   Step 3  #F9D074  warm yellow        message area, send button
 *   Step 4  #F8F0E4  warm cream         AI bubbles, input footer, textarea
 *   Accent  #E2C3DA  dusty mauve        decorative borders and focus rings
 *
 * Contact graph (all ±1):
 *   page bg (1) ↔ header (2) ↔ message area (3) ↔ AI bubbles (4)
 *                                               ↔ user bubbles (2)
 *                                               ↔ footer (4) ↔ textarea (4)
 *                                                             ↔ send btn (3)
 */

// Twemoji SVGs give consistent geometry on every platform (no system-font variation).
// Codepoints: 🧐 U+1F9D0, 😰 U+1F630.
const ANALYST_SVG = 'https://cdn.jsdelivr.net/gh/twitter/twemoji@14.0.2/assets/svg/1f9d0.svg'
const USER_SVG    = 'https://cdn.jsdelivr.net/gh/twitter/twemoji@14.0.2/assets/svg/1f630.svg'

// Twemoji face circles span ~33 of the 36-unit viewBox (ratio ≈ 0.917).
// Sizing the image to 1/0.917 ≈ 109% of the container makes the face
// fill the circle exactly; the monocle chain and sweat bead escape via overflow-visible.
const EMOJI_SCALE = '109%'

// The Analyst does not rush. Each reply sits behind a deliberate pause, then
// is "spoken" character by character. This is a pure client-side effect —
// the API response is already complete, so it costs no extra tokens.
const PAUSE_MIN_MS = 800        // shortest pre-reply silence
const PAUSE_RANGE_MS = 2200     // random extra silence on top (0–2.2s)
const TYPE_TICK_MS = 24         // ms between typewriter ticks
const TYPE_CHARS_PER_TICK = 3   // ≈125 chars/sec reveal speed

function Avatar({ src, alt, className }: { src: string; alt: string; className: string }) {
  return (
    <div className={className}>
      <img
        src={src}
        alt={alt}
        draggable={false}
        className="absolute pointer-events-none"
        style={{ width: EMOJI_SCALE, height: EMOJI_SCALE, top: '50%', left: '50%', transform: 'translate(-50%, -50%)' }}
      />
    </div>
  )
}

// Receipts for the disclaimer: documented dangers of AI "therapy" and the
// AI-psychosis spiral. Favicons come from Google's s2 service — the same
// external-CDN pattern as the Twemoji avatars.
const FURTHER_READING = [
  {
    title: 'Exploring the Dangers of AI in Mental Health Care',
    domain: 'hai.stanford.edu',
    url: 'https://hai.stanford.edu/news/exploring-the-dangers-of-ai-in-mental-health-care',
  },
  {
    title: 'Man Who Had Managed Mental Illness Effectively for Years Says ChatGPT Sent Him Into Hospitalization for Psychosis',
    domain: 'futurism.com',
    url: 'https://futurism.com/artificial-intelligence/mental-illness-chatgpt-psychosis-lawsuit',
  },
  {
    title: 'Generative AI Chatbots and Delusions: From Guesswork to Emerging Cases',
    domain: 'onlinelibrary.wiley.com',
    url: 'https://onlinelibrary.wiley.com/doi/10.1111/acps.70022',
  },
  {
    title: 'Chatbot psychosis',
    domain: 'en.wikipedia.org',
    url: 'https://en.wikipedia.org/wiki/Chatbot_psychosis',
  },
]

// The one place the app deliberately breaks character. The footer disclaimer
// opens this; it says, in plain earnest language, why none of this should be
// taken seriously — including the psychological risk of treating it as real.
function DisclaimerModal({ onClose }: { onClose: () => void }) {
  useEffect(() => {
    const onKey = (e: globalThis.KeyboardEvent) => e.key === 'Escape' && onClose()
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  return (
    // Dim scrim over the app; the panel itself is step 4 cream with the
    // standard black border, like every other surface in the card.
    <div
      className="fixed inset-0 z-50 bg-black/60 flex items-center justify-center p-4"
      onClick={onClose}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-label="What this app is, and is not"
        onClick={(e) => e.stopPropagation()}
        className="bg-[#F8F0E4] border-2 border-black rounded-2xl max-w-xl w-full max-h-[85vh] overflow-y-auto px-6 py-5 text-sm leading-relaxed text-gray-800"
      >
        <div className="flex items-start justify-between gap-4 mb-3">
          <h2 className="font-bold text-gray-900 text-base">
            It's just for fun folks
          </h2>
          <button
            onClick={onClose}
            aria-label="Close"
            className="flex-none w-7 h-7 rounded-full text-gray-900 font-bold leading-none"
          >
            ×
          </button>
        </div>

        <p className="mb-3">
          This is Claude with public-domain Freud and Jung 
          <a href="https://en.wikipedia.org/wiki/Retrieval-augmented_generation"> shoved down its throat</a>,
          told to speak in a funny Austrian accent and maybe be vaguely menacing, and shackled so as not to cost me too much money.
           I made this to learn about the Anthropic API, basically, and other AI fundamentals of the current moment.
        </p>

        <p className="mb-3">
          This is not therapy, or analysis, or anything. Do not use it to try and fix your life. You will drive yourself crazy. 
          Just because I told it not to be outwardly sycophantic doesn't mean it doesn't have all the same stuff going on under 
          the hood.
        </p>

        <p className="mb-3">
          I mean it's genre fiction basically. It's genre fiction you can get lost in and think you're doing therapy in. 
          That can be dangerous for your psyche. It's like a holodeck and a cult in one.
        </p>

        {/* Receipts, as link pills: step 3 on the cream panel (step 4),
            darkening to step 2 on hover like the send button. */}
        <ul className="flex flex-wrap gap-2 mb-3">
          {FURTHER_READING.map((link) => (
            <li key={link.url} className="max-w-full">
              <a
                href={link.url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 rounded-full border border-black bg-[#F9D074] hover:bg-[#EDA551] px-3 py-1.5 text-xs text-gray-900 transition-colors"
              >
                <img
                  src={`https://www.google.com/s2/favicons?domain=${link.domain}&sz=32`}
                  alt=""
                  className="w-4 h-4 flex-none"
                />
                <span>{link.title}</span>
              </a>
            </li>
          ))}
        </ul>

        <p className="mb-1">
          That's serious stuff! Don't do that!
        </p>
      </div>
    </div>
  )
}

function TypingIndicator() {
  return (
    <div className="flex items-end gap-2">
      <Avatar
        src={ANALYST_SVG}
        alt=""
        className="relative w-7 h-7 rounded-full bg-[#F8F0E4] border-2 border-black flex-shrink-0 overflow-visible"
      />
      <div className="bg-[#F8F0E4] border border-black rounded-2xl rounded-bl-sm px-4 py-3">
        <div className="flex gap-1 items-center h-4">
          {[0, 1, 2].map((i) => (
            <span
              key={i}
              className="w-2 h-2 bg-[#E2C3DA] rounded-full animate-bounce"
              style={{ animationDelay: `${i * 0.15}s` }}
            />
          ))}
        </div>
      </div>
    </div>
  )
}

export default function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([WELCOME])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  // Chars of the LAST message revealed so far; null = no animation running.
  const [typedUpTo, setTypedUpTo] = useState<number | null>(null)
  // The session is over (turn limit reached now, or lockout found on mount).
  const [ended, setEnded] = useState(false)
  // The case notes the Analyst "accidentally" leaves out after a session.
  const [notes, setNotes] = useState<string | null>(null)
  const [notesLoading, setNotesLoading] = useState(false)
  const [notesError, setNotesError] = useState(false)
  // 1-based number of the current session (grows when a concluded patient returns).
  const [sessionCount, setSessionCount] = useState(1)
  const [status, setStatus] = useState<'checking' | 'online' | 'offline'>('checking')
  const [showDisclaimer, setShowDisclaimer] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  // Blocks the persistence effect until hydration has read storage first.
  const hydrated = useRef(false)

  // Sending is blocked while a reply is in flight OR still being "spoken".
  const busy = loading || typedUpTo !== null

  useEffect(() => {
    fetch('/api/health')
      .then(r => setStatus(r.ok ? 'online' : 'offline'))
      .catch(() => setStatus('offline'))
  }, [])

  // Hydrate the dossier. Three cases:
  //  - mid-session transcript -> restore it as-is
  //  - concluded session, office still closed -> restore read-only (lockout)
  //  - concluded session, office reopened -> NEW session, returning greeting
  // The lockout is trivially circumventable via devtools — by design.
  useEffect(() => {
    const stored = localStorage.getItem(LOCKOUT_KEY)
    const locked = isLockedOut(stored ? Number(stored) : null, new Date())
    const dossier = parseDossier(localStorage.getItem(DOSSIER_KEY))

    if (dossier.messages.length > 0) {
      if (dossier.ended && !locked) {
        const nextSession = dossier.sessionCount + 1
        setSessionCount(nextSession)
        setMessages([{ role: 'assistant', content: greeting(nextSession) }])
      } else {
        setSessionCount(dossier.sessionCount)
        setMessages(dossier.messages as Message[])
        setEnded(dossier.ended || locked)
        setNotes(dossier.notes)
      }
    } else if (locked) {
      setEnded(true)
    }
    hydrated.current = true
  }, [])

  // Persist the dossier on every change (after hydration, so the stored
  // file is never clobbered by the initial render's default state).
  useEffect(() => {
    if (!hydrated.current) return
    localStorage.setItem(
      DOSSIER_KEY,
      JSON.stringify({ messages, ended, notes, sessionCount })
    )
  }, [messages, ended, notes, sessionCount])

  // The shredder. In-character data deletion: dossier, lockout, everything.
  function burnFile() {
    if (!window.confirm('Destroy ze file? Zere is no recovery.')) return
    localStorage.removeItem(DOSSIER_KEY)
    localStorage.removeItem(LOCKOUT_KEY)
    setMessages([WELCOME])
    setEnded(false)
    setNotes(null)
    setNotesError(false)
    setSessionCount(1)
    setTypedUpTo(null)
  }

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading, typedUpTo])

  // Typewriter: reveal the last message a few characters per tick.
  useEffect(() => {
    if (typedUpTo === null) return
    const full = messages[messages.length - 1]?.content ?? ''
    if (typedUpTo >= full.length) {
      setTypedUpTo(null)
      return
    }
    const timer = setTimeout(() => setTypedUpTo(typedUpTo + TYPE_CHARS_PER_TICK), TYPE_TICK_MS)
    return () => clearTimeout(timer)
  }, [typedUpTo, messages])

  function growTextarea() {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`
  }

  async function send() {
    const text = input.trim()
    if (!text || busy || ended) return

    // Is this exchange the session's last? (counting the message being sent)
    const final = userTurnCount(messages) + 1 >= SESSION_LIMIT

    setInput('')
    if (textareaRef.current) textareaRef.current.style.height = 'auto'
    setMessages((prev) => [...prev, { role: 'user', content: text }])
    setLoading(true)

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: [...messages, { role: 'user', content: text }],
          final,
        }),
      })

      if (!res.ok) {
        const body = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }))
        throw new Error(body.detail ?? `HTTP ${res.status}`)
      }

      const { reply } = await res.json()
      // A deliberate, slightly unsettling pause before the Analyst speaks
      // (the typing indicator stays visible throughout).
      await new Promise((r) => setTimeout(r, PAUSE_MIN_MS + Math.random() * PAUSE_RANGE_MS))
      setMessages((prev) => [...prev, { role: 'assistant', content: reply }])
      setTypedUpTo(0)
      if (final) {
        setEnded(true)
        localStorage.setItem(LOCKOUT_KEY, String(nextMidnight(new Date())))
      }
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: `⚠️ Couldn't reach the server. The dev has broken it either by mistake, or on purpose to frustrate users.\n\n(${err instanceof Error ? err.message : 'Network error'})`,
        },
      ])
    } finally {
      setLoading(false)
    }
  }

  async function fetchNotes() {
    if (notesLoading || notes) return
    setNotesLoading(true)
    setNotesError(false)
    try {
      const res = await fetch('/api/notes', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages }),
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const body = await res.json()
      setNotes(body.notes)
    } catch {
      setNotesError(true)
    } finally {
      setNotesLoading(false)
    }
  }

  function handleKey(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      send()
    }
  }

  return (
    // Step 1 — deep orange — visible on either side of the card on wide screens.
    <div className="h-screen bg-[#D45F2A] overflow-hidden flex justify-center">

      <div className="w-full max-w-4xl flex flex-col border-x border-black">

        {/* Step 2 — amber — one step from page bg (step 1) and message area (step 3). */}
        <header className="flex-none flex items-center gap-3 px-5 py-4 bg-[#EDA551] border-b border-black">
          <Avatar
            src={ANALYST_SVG}
            alt="The Analyst"
            className="relative w-10 h-10 rounded-full bg-[#F8F0E4] border-[3px] border-black flex-shrink-0 overflow-visible"
          />
          <div className="min-w-0">
            <h1 className="text-gray-900 font-bold text-lg leading-none">The Analyst</h1>
            <p className="text-gray-900 text-xs mt-0.5 opacity-60">Come in, my dear boy.</p>
          </div>
          <div className="ml-auto flex items-center gap-1.5 flex-shrink-0">
            <span className={`w-2 h-2 rounded-full ${
              status === 'online'   ? 'bg-green-600 animate-pulse' :
              status === 'offline'  ? 'bg-red-600' :
                                      'bg-gray-400 animate-pulse'
            }`} />
            <span className="text-gray-900 text-xs opacity-60">
              {status === 'online' ? 'Online' : status === 'offline' ? 'Offline' : 'Checking…'}
            </span>
          </div>
        </header>

        {/* Step 3 — warm yellow — message area. */}
        <main className="flex-1 overflow-y-auto px-4 py-5 space-y-4 bg-[#F9D074]">
          {messages.map((msg, i) => (
            <div
              key={i}
              className={`flex items-end gap-2 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}
            >
              <Avatar
                src={msg.role === 'assistant' ? ANALYST_SVG : USER_SVG}
                alt={msg.role === 'assistant' ? 'The Analyst' : 'You'}
                className={`relative w-7 h-7 rounded-full flex-shrink-0 border-2 border-black overflow-visible ${
                  msg.role === 'assistant' ? 'bg-[#F8F0E4]' : 'bg-[#EDA551]'
                }`}
              />

              {/* User bubble: amber (#EDA551), right-aligned.
                  AI bubble:   cream (#F8F0E4), left-aligned.
                  Sharp corner is on the outside-bottom to align with the avatar below. */}
              <div
                className={`max-w-[75%] px-4 py-2.5 text-sm leading-relaxed whitespace-pre-wrap border border-black ${
                  msg.role === 'user'
                    ? 'bg-[#EDA551] text-gray-900 rounded-2xl rounded-br-sm'
                    : 'bg-[#F8F0E4] text-gray-800 rounded-2xl rounded-bl-sm'
                }`}
                style={{ wordBreak: 'break-word' }}
              >
                {renderContent(
                  typedUpTo !== null && i === messages.length - 1
                    ? msg.content.slice(0, typedUpTo)
                    : msg.content
                )}
              </div>
            </div>
          ))}

          {loading && <TypingIndicator />}

          {/* After the session ends, the Analyst "accidentally" leaves his
              case notes within reach. Deliberately subtle — a reward for the
              curious, not a feature announcement. */}
          {ended && !busy && messages.length > 1 && !notes && (
            <button
              onClick={fetchNotes}
              disabled={notesLoading}
              className="block mx-auto text-xs italic text-gray-700 opacity-40 hover:opacity-90 transition-opacity duration-300 disabled:opacity-60"
            >
              {notesLoading
                ? '…deciphering ze handwriting…'
                : notesError
                  ? 'Ze notes are illegible. Squint again?'
                  : '…he has left his case notes on ze desk…'}
            </button>
          )}

          {/* The notes themselves: a loose page. Cream (step 4) on the message
              area (step 3) — ±1 adjacency holds; mauve is the decorative accent. */}
          {notes && (
            <div className="max-w-[85%] mx-auto bg-[#F8F0E4] border-2 border-[#E2C3DA] rounded-sm px-5 py-4 shadow-md -rotate-1">
              <p className="text-[10px] uppercase tracking-widest text-gray-500 mb-2">
                Private — not for ze patient
              </p>
              <div className="text-sm leading-relaxed text-gray-800 whitespace-pre-wrap font-serif">
                {renderContent(notes)}
              </div>
            </div>
          )}

          <div ref={bottomRef} />
        </main>

        {/* Step 4 — warm cream — one step forward from message area. */}
        <footer className="flex-none bg-[#F8F0E4] border-t border-black px-4 pt-3 pb-4">
          <div className="flex items-end gap-2">
            {/* Textarea: step 4 — same as footer, defined by its black border. */}
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => {
                setInput(e.target.value)
                growTextarea()
              }}
              onKeyDown={handleKey}
              placeholder={
                ended
                  ? 'Ze session is over. Ze office reopens tomorrow.'
                  : "Share what's on your mind… (Enter to send, Shift+Enter for a new line)"
              }
              rows={1}
              disabled={busy || ended}
              className="flex-1 resize-none rounded-xl border border-black bg-[#F8F0E4] text-gray-800 placeholder-gray-500 text-sm leading-relaxed px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-[#E2C3DA] focus:border-[#E2C3DA] disabled:opacity-50 disabled:cursor-not-allowed transition-shadow"
              style={{ maxHeight: 160 }}
            />
            {/* Send button: step 3 (#F9D074) — one step back from footer (step 4).
                Hover darkens to step 2 (#EDA551) — still adjacent. */}
            <button
              onClick={send}
              disabled={!input.trim() || busy || ended}
              aria-label="Send message"
              className="flex-none w-10 h-10 rounded-xl bg-[#F9D074] text-gray-900 border border-black hover:bg-[#EDA551] active:scale-95 disabled:opacity-40 disabled:cursor-not-allowed transition-all duration-150 flex items-center justify-center text-lg font-bold"
            >
              ↑
            </button>
          </div>
          {ended && (
            <p className="text-center text-gray-700 text-xs mt-2 font-medium">
              Session concluded. Ze office reopens tomorrow.
            </p>
          )}
          <p className="text-center text-gray-500 text-xs mt-2">
            <button
              onClick={() => setShowDisclaimer(true)}
              className="underline decoration-dotted hover:text-gray-800 transition-colors"
            >
              This is not a real attempt at mental health care, let alone a replacement
              for professional health care.
            </button>
            {(messages.length > 1 || sessionCount > 1) && (
              <>
                {' · '}
                <button
                  onClick={burnFile}
                  className="underline decoration-dotted hover:text-gray-800 transition-colors"
                >
                  burn my file 🔥
                </button>
              </>
            )}
          </p>
        </footer>

      </div>

      {showDisclaimer && <DisclaimerModal onClose={() => setShowDisclaimer(false)} />}
    </div>
  )
}
