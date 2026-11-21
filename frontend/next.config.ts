import type { NextConfig } from 'next'

/**
 * 全画面にセキュリティヘッダーを付ける（詳細設計書 9.7）
 * script-src の 'unsafe-inline' は Next.js のインラインスクリプトのため（nonce 方式は今後の課題）
 */
const isDev = process.env.NODE_ENV !== 'production'
const apiOrigin = (() => {
  try {
    return new URL(process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000').origin
  } catch {
    return 'http://localhost:8000'
  }
})()

const csp = [
  "default-src 'self'",
  `script-src 'self' 'unsafe-inline'${isDev ? " 'unsafe-eval'" : ''}`,
  "style-src 'self' 'unsafe-inline'",
  `img-src 'self' data: blob: https: ${apiOrigin}`,
  "font-src 'self' data:",
  `connect-src 'self' ${apiOrigin}${isDev ? ' ws: wss:' : ''}`,
  `media-src 'self' blob: ${apiOrigin}`,
  `frame-src 'self' blob: ${apiOrigin}`,
  "worker-src 'self'",
  "manifest-src 'self'",
  "object-src 'none'",
  "base-uri 'self'",
  "form-action 'self'",
  "frame-ancestors 'none'",
].join('; ')

const securityHeaders = [
  { key: 'Content-Security-Policy', value: csp },
  { key: 'X-Frame-Options', value: 'DENY' },
  { key: 'X-Content-Type-Options', value: 'nosniff' },
  { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
  { key: 'Permissions-Policy', value: 'geolocation=(self), camera=(), microphone=(), payment=()' },
]

const nextConfig: NextConfig = {
  poweredByHeader: false,
  async headers() {
    return [{ source: '/:path*', headers: securityHeaders }]
  },
}

export default nextConfig
