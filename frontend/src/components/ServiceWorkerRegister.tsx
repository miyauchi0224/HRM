'use client'
import { useEffect } from 'react'

/** PWA 用の Service Worker を登録する（本番ビルドのみ。開発中はキャッシュの混乱を避ける） */
export default function ServiceWorkerRegister() {
  useEffect(() => {
    if (process.env.NODE_ENV !== 'production' || !('serviceWorker' in navigator)) return
    navigator.serviceWorker.register('/sw.js').catch(() => {
      // 登録できなくてもアプリは通常どおり動く
    })
  }, [])
  return null
}
