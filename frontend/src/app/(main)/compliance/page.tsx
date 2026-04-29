'use client'
import { useAuthStore } from '@/lib/store'
import ComplianceChecklist from '../components/ComplianceChecklist'
import { AlertCircle } from 'lucide-react'

export default function CompliancePage() {
  const user = useAuthStore((s) => s.user)
  const isHR = user?.role === 'hr' || user?.role === 'admin'

  if (!isHR) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <AlertCircle size={48} className="mx-auto mb-3 text-red-500" />
          <h2 className="text-lg font-bold text-gray-800 mb-2">アクセス権がありません</h2>
          <p className="text-gray-600">このページは労務部スタッフのみアクセス可能です。</p>
        </div>
      </div>
    )
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-800 mb-6">コンプライアンスチェックリスト</h1>
      <ComplianceChecklist />
    </div>
  )
}
