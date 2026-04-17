/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',

  // 静的アセット（JS・CSS・画像）に長期キャッシュを設定
  // → 2回目以降のアクセスでブラウザキャッシュから即座に読み込む
  async headers() {
    return [
      {
        source: '/_next/static/:path*',
        headers: [
          { key: 'Cache-Control', value: 'public, max-age=31536000, immutable' },
        ],
      },
      {
        source: '/favicon.ico',
        headers: [
          { key: 'Cache-Control', value: 'public, max-age=86400' },
        ],
      },
    ]
  },

  // 画像最適化（アバターなど）
  images: {
    remotePatterns: [
      { protocol: 'http',  hostname: 'localhost' },
      { protocol: 'https', hostname: '*.amazonaws.com' },
    ],
  },

  // 実験的機能：CSS の最適化
  experimental: {
    optimizeCss: false, // Critters が未インストールの場合は false
  },
}

export default nextConfig
