import type { Metadata, Viewport } from 'next'
import './globals.css'
import { Providers } from './providers'
import ServiceWorkerRegister from '@/components/ServiceWorkerRegister'

export const metadata: Metadata = {
  title: 'HRM - 人事管理システム',
  description: '人事管理システム',
  appleWebApp: { capable: true, title: 'HRM', statusBarStyle: 'black-translucent' },
  icons: { apple: '/icons/icon-192.png' },
}

export const viewport: Viewport = {
  themeColor: '#111827',
  width: 'device-width',
  initialScale: 1,
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ja">
      <body>
        <Providers>{children}</Providers>
        <ServiceWorkerRegister />
      </body>
    </html>
  )
}
