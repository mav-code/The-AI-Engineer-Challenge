import type { Metadata, Viewport } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Mental Coach – Your AI Support Partner',
  description: 'A warm, supportive AI mental coach to help you navigate life\'s challenges with confidence.',
}

// Next.js supplies `width=device-width, initial-scale=1` by default; we
// restate it here only to add `viewport-fit=cover`, which is what makes the
// `env(safe-area-inset-*)` values non-zero on notched iPhones.
export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  viewportFit: 'cover',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={inter.className}>{children}</body>
    </html>
  )
}
