'use client'
import { useEffect, useState } from 'react'
import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import { Clock, Menu } from 'lucide-react'
import { useQueryClient } from '@tanstack/react-query'
import Sidebar from '@/components/layout/Sidebar'
import { useAuthStore } from '@/lib/store'
import api from '@/lib/api'

export default function MainLayout({ children }: { children: React.ReactNode }) {
  const { user, setUser } = useAuthStore()
  const router      = useRouter()
  const pathname    = usePathname()
  const queryClient = useQueryClient()
  const [menuOpen, setMenuOpen] = useState(false)

  // 画面を移動したらスマホ用メニューを閉じる
  useEffect(() => { setMenuOpen(false) }, [pathname])

  useEffect(() => {
    const token = localStorage.getItem('access_token')
    if (!token) {
      router.replace('/login')
      return
    }

    // ユーザー情報の復元
    if (!user) {
      api.get('/api/v1/auth/me/').then(({ data }) => {
        setUser({
          id:         data.id,
          email:      data.email,
          role:       data.role,
          full_name:  data.full_name ?? data.email,
          department: data.department,
        })

        // ユーザー情報取得後、よく使う共通データをバックグラウンドでプリフェッチ
        // → 各ページに遷移した時点でキャッシュが温まっており即座に表示される
        const role = data.role
        queryClient.prefetchQuery({
          queryKey: ['notifications'],
          queryFn:  () => api.get('/api/v1/notifications/').then((r) => r.data),
          staleTime: 5 * 60 * 1000,
        })
        // 顧客以外は勤怠・プロジェクトもプリフェッチ
        if (role !== 'customer') {
          const ym = new Date().toISOString().slice(0, 7)
          queryClient.prefetchQuery({
            queryKey: ['attendance', ym],
            queryFn:  () => api.get(`/api/v1/attendance/?year_month=${ym}`).then((r) => r.data.results ?? r.data),
            staleTime: 5 * 60 * 1000,
          })
          queryClient.prefetchQuery({
            queryKey: ['projects'],
            queryFn:  () => api.get('/api/v1/attendance/projects/').then((r) => r.data.results ?? r.data),
            staleTime: 5 * 60 * 1000,
          })
        }
      }).catch(() => {
        // トークン無効 → api.ts の interceptor がログインへリダイレクト
      })
    }
  }, [])

  return (
    <div className="flex min-h-screen bg-gray-50">
      {/* PC: 常に表示 */}
      <div className="hidden md:flex">
        <Sidebar />
      </div>

      {/* スマホ: メニューボタンで開くドロワー */}
      {menuOpen && (
        <div className="fixed inset-0 z-40 flex md:hidden">
          <div className="absolute inset-0 bg-black/40" onClick={() => setMenuOpen(false)} />
          <div className="relative z-10 overflow-y-auto">
            <Sidebar />
          </div>
        </div>
      )}

      <div className="flex-1 min-w-0 flex flex-col">
        <header className="md:hidden sticky top-0 z-30 flex items-center gap-3 bg-gray-900 text-white px-4 py-3">
          <button onClick={() => setMenuOpen(true)} aria-label="メニューを開く">
            <Menu size={22} />
          </button>
          <span className="font-bold">HRM</span>
          <Link href="/clock" className="ml-auto flex items-center gap-1 text-sm bg-blue-600 px-3 py-1.5 rounded-lg">
            <Clock size={14} /> 打刻
          </Link>
        </header>
        <main className="flex-1 p-4 md:p-6 overflow-auto">
          {children}
        </main>
      </div>
    </div>
  )
}
