/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    // In development, proxy /api/* to the local FastAPI backend on :8000.
    // On Vercel (production), same-origin requests hit the Python serverless
    // function directly via vercel.json routing — no rewrite needed.
    if (process.env.NODE_ENV !== 'development') return []
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/api/:path*',
      },
    ]
  },
}

export default nextConfig
