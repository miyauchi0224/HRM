'use client'
import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useQueryClient } from '@tanstack/react-query'
import Sidebar from '@/components/layout/Sidebar'
import { useAuthStore } from '@/lib/store'
import api from '@/lib/api'

export default function MainLayout({ children }: { children: React.ReactNode }) {
  const { user, setUser } = useAuthStore()
  const router      = useRouter()
  const queryClient = useQueryClient()

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
      <Sidebar />
      <main className="flex-1 p-6 overflow-auto">
        {children}
      </main>
    </div>
  )
}
