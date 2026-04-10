'use client'
import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Sidebar from '@/components/layout/Sidebar'
import { useAuthStore } from '@/lib/store'
import api from '@/lib/api'

export default function MainLayout({ children }: { children: React.ReactNode }) {
  const { user, setUser } = useAuthStore()
  const router = useRouter()

  useEffect(() => {
    // アクセストークンがなければログインへ
    const token = localStorage.getItem('access_token')
    if (!token) {
      router.replace('/login')
      return
    }
    // Zustand にユーザーがいなければ（ページリロード後など） /me で復元
    if (!user) {
      api.get('/api/v1/auth/me/').then(({ data }) => {
        setUser({
          id:         data.id,
          email:      data.email,
          role:       data.role,
          full_name:  data.full_name ?? data.email,
          department: data.department,
        })
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
