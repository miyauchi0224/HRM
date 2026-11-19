import type { MetadataRoute } from 'next'

// ホーム画面に追加したときの設定（詳細設計書 7.9）
export default function manifest(): MetadataRoute.Manifest {
  return {
    name:             'HRM 人事管理システム',
    short_name:       'HRM',
    description:      '勤怠・休暇・申請を管理する社内システム',
    start_url:        '/',
    display:          'standalone',
    background_color: '#111827',
    theme_color:      '#111827',
    lang:             'ja',
    icons: [
      { src: '/icons/icon-192.png', sizes: '192x192', type: 'image/png' },
      { src: '/icons/icon-512.png', sizes: '512x512', type: 'image/png' },
      { src: '/icons/icon-512.png', sizes: '512x512', type: 'image/png', purpose: 'maskable' },
    ],
    shortcuts: [
      { name: '打刻', short_name: '打刻', url: '/clock', icons: [{ src: '/icons/icon-192.png', sizes: '192x192' }] },
    ],
  }
}
