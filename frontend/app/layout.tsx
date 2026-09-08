import type { Metadata, Viewport } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

// Absolute URLs are required for social-card images. Vercel injects VERCEL_URL
// per deployment; NEXT_PUBLIC_SITE_URL overrides it once there's a real domain.
const siteUrl =
  process.env.NEXT_PUBLIC_SITE_URL ??
  (process.env.VERCEL_URL ? `https://${process.env.VERCEL_URL}` : 'http://localhost:3000')

const DESCRIPTION =
  'A stern, sinister continental psychoanalyst who has actually read Freud. ' +
  'Every reply is grounded in public-domain psychoanalytic texts.'

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl),
  title: 'The Analyst',
  description: DESCRIPTION,
  // app/icon.svg, app/apple-icon.png and app/opengraph-image.png are picked up
  // by Next.js file conventions — no manual <link>/<meta> needed for those.
  openGraph: {
    title: 'The Analyst',
    description: DESCRIPTION,
    siteName: 'The Analyst',
    type: 'website',
    url: siteUrl,
  },
  twitter: {
    card: 'summary_large_image',
    title: 'The Analyst',
    description: DESCRIPTION,
  },
}

// Next.js supplies `width=device-width, initial-scale=1` by default; we
// restate it here only to add `viewport-fit=cover`, which is what makes the
// `env(safe-area-inset-*)` values non-zero on notched iPhones.
export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  viewportFit: 'cover',
  // Tints mobile browser chrome to the page background (palette step 1).
  themeColor: '#D45F2A',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      {/* Background is repeated on <body> so rubber-band overscroll on iOS
          reveals the page colour rather than a white gap. */}
      <body className={`${inter.className} bg-[#D45F2A]`}>{children}</body>
    </html>
  )
}
