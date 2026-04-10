'use client'
import { useQuery } from '@tanstack/react-query'
import api from '@/lib/api'
import { useAuthStore } from '@/lib/store'
import { Clock, Calendar, Target, Bell } from 'lucide-react'

export default function DashboardPage() {
  const user = useAuthStore((s) => s.user)

  const { data: summary } = useQuery({
    queryKey: ['attendance-summary'],
    queryFn: () => api.get('/api/v1/attendance/summary/').then((r) => r.data),
  })

  const { data: notifications } = useQuery({
    queryKey: ['notifications'],
    queryFn: () => api.get('/api/v1/notifications/').then((r) => r.data),
  })

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-800 mb-1">ダッシュボード</h1>
      <p className="text-gray-500 text-sm mb-6">
        おはようございます、{user?.full_name ?? 'ゲスト'}さん
      </p>

      {/* KPIカード */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <KpiCard
          icon={<Clock className="text-blue-500" size={20} />}
          label="今月の労働時間"
          value={summary ? `${Math.floor(summary.total_work_minutes / 60)}h` : '—'}
          sub={summary ? `残業 ${Math.floor(summary.total_overtime_minutes / 60)}h` : ''}
          alert={summary?.overtime_alert}
        />
        <KpiCard
          icon={<Calendar className="text-green-500" size={20} />}
          label="出勤日数"
          value={summary ? `${summary.total_work_days}日` : '—'}
        />
        <KpiCard
          icon={<Bell className="text-yellow-500" size={20} />}
          label="未読通知"
          value={notifications ? `${notifications.unread_count}件` : '—'}
        />
        <KpiCard
          icon={<Target className="text-purple-500" size={20} />}
          label="MBO"
          value="確認する"
          href="/mbo"
        />
      </div>

      {/* 通知一覧（直近5件） */}
      <div className="bg-white rounded-xl border border-gray-200 p-5">
        <h2 className="text-base font-semibold text-gray-700 mb-4 flex items-center gap-2">
          <Bell size={16} /> 最新通知
        </h2>
        {notifications?.results?.length > 0 ? (
          <ul className="space-y-2">
            {notifications.results.slice(0, 5).map((n: any) => (
              <li key={n.id} className={`p-3 rounded-lg text-sm ${n.is_read ? 'bg-gray-50' : 'bg-blue-50'}`}>
                <p className="font-medium text-gray-800">{n.title}</p>
                <p className="text-gray-500 text-xs mt-0.5">{n.message}</p>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-gray-400 text-sm">通知はありません</p>
        )}
      </div>
    </div>
  )
}

function KpiCard({ icon, label, value, sub, alert, href }: {
  icon: React.ReactNode; label: string; value: string; sub?: string
  alert?: boolean; href?: string
}) {
  const content = (
    <div className={`bg-white rounded-xl border p-4 ${alert ? 'border-red-300 bg-red-50' : 'border-gray-200'}`}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs text-gray-500">{label}</span>
        {icon}
      </div>
      <p className={`text-2xl font-bold ${alert ? 'text-red-600' : 'text-gray-800'}`}>{value}</p>
      {sub && <p className="text-xs text-gray-400 mt-0.5">{sub}</p>}
    </div>
  )
  if (href) return <a href={href} className="block hover:opacity-80 transition-opacity">{content}</a>
  return content
}
