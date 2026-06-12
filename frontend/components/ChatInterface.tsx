'use client'

import { useState, useRef, useEffect, KeyboardEvent, ReactNode } from 'react'
import { SESSION_LIMIT, isLockedOut, nextMidnight, userTurnCount } from '../lib/session'

// localStorage key for the overnight lockout (ms timestamp of next midnight).
const LOCKOUT_KEY = 'analyst.lockedUntil'

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

const WELCOME: Message = {
  role: 'assistant',
  content:
    "Ah. You haff come.\n\nZis vas not a coincidence, you know. Ze mind does not make accidents. Sit down und tell me everyzing. I am listening.",
}

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
  const [status, setStatus] = useState<'checking' | 'online' | 'offline'>('checking')
  const bottomRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // Sending is blocked while a reply is in flight OR still being "spoken".
  const busy = loading || typedUpTo !== null

  useEffect(() => {
    fetch('/api/health')
      .then(r => setStatus(r.ok ? 'online' : 'offline'))
      .catch(() => setStatus('offline'))
  }, [])

  // The office keeps hours: a concluded session locks the couch until the
  // next local midnight. Trivially circumventable via devtools — by design.
  useEffect(() => {
    const stored = localStorage.getItem(LOCKOUT_KEY)
    if (isLockedOut(stored ? Number(stored) : null, new Date())) setEnded(true)
  }, [])

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
            <p className="text-gray-900 text-xs mt-0.5 opacity-60">Your problems are worse than you think.</p>
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
            This is not a real attempt at mental health care, let alone a replacement for professional health care.
          </p>
        </footer>

      </div>
    </div>
  )
}
