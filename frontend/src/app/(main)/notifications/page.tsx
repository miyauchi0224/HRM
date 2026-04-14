'use client'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'
import { Bell, CheckCheck } from 'lucide-react'

interface Notification {
  id: string
  title: string
  message: string
  type: string
  is_read: boolean
  related_url: string | null
  created_at: string
}

const TYPE_COLOR: Record<string, string> = {
  overtime_alert: 'bg-red-100 text-red-600',
  attendance_mod: 'bg-blue-100 text-blue-600',
  leave_request:  'bg-green-100 text-green-600',
  mbo_feedback:   'bg-purple-100 text-purple-600',
  expense_request:'bg-yellow-100 text-yellow-700',
  skill_expiry:   'bg-orange-100 text-orange-600',
}

function timeAgo(dateStr: string): string {
  const diff = Math.floor((Date.now() - new Date(dateStr).getTime()) / 1000)
  if (diff < 60)    return `${diff}秒前`
  if (diff < 3600)  return `${Math.floor(diff / 60)}分前`
  if (diff < 86400) return `${Math.floor(diff / 3600)}時間前`
  return `${Math.floor(diff / 86400)}日前`
}

export default function NotificationsPage() {
  const qc = useQueryClient()

  const { data, isLoading } = useQuery<{ unread_count: number; results: Notification[] }>({
    queryKey: ['notifications-all'],
    queryFn: () => api.get('/api/v1/notifications/').then((r) => r.data),
  })

  const readOneMut = useMutation({
    mutationFn: (id: string) => api.patch(`/api/v1/notifications/${id}/read/`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['notifications-all'] }),
  })

  const readAllMut = useMutation({
    mutationFn: () => api.patch('/api/v1/notifications/read-all/'),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['notifications-all'] }),
  })

  const notifications = data?.results ?? []
  const unread        = data?.unread_count ?? 0

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
          <Bell size={22} />
          通知
          {unread > 0 && (
            <span className="bg-red-500 text-white text-xs font-bold px-2 py-0.5 rounded-full">
              {unread}
            </span>
          )}
        </h1>
        {unread > 0 && (
          <button
            onClick={() => readAllMut.mutate()}
            disabled={readAllMut.isPending}
            className="flex items-center gap-2 text-sm text-gray-500 hover:text-blue-600 transition-colors"
          >
            <CheckCheck size={16} /> すべて既読にする
          </button>
        )}
      </div>

      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        {isLoading ? (
          <p className="text-center text-gray-400 text-sm py-10">読み込み中...</p>
        ) : notifications.length === 0 ? (
          <div className="text-center py-12">
            <Bell size={28} className="mx-auto text-gray-300 mb-3" />
            <p className="text-gray-400 text-sm">通知がありません</p>
          </div>
        ) : (
          <ul>
            {notifications.map((n) => (
              <li
                key={n.id}
                onClick={() => {
                  if (!n.is_read) readOneMut.mutate(n.id)
                  if (n.related_url) window.location.href = n.related_url
                }}
                className={`flex gap-4 px-5 py-4 border-b border-gray-50 cursor-pointer hover:bg-gray-50 transition-colors ${
                  !n.is_read ? 'bg-blue-50' : ''
                }`}
              >
                {/* 未読インジケーター */}
                <div className="pt-1.5 shrink-0">
                  <div className={`w-2 h-2 rounded-full ${!n.is_read ? 'bg-blue-500' : 'bg-transparent'}`} />
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${TYPE_COLOR[n.type] ?? 'bg-gray-100 text-gray-600'}`}>
                      {n.type.replace(/_/g, ' ')}
                    </span>
                    <span className="text-xs text-gray-400">{timeAgo(n.created_at)}</span>
                  </div>
                  <p className={`text-sm font-medium ${!n.is_read ? 'text-gray-900' : 'text-gray-700'}`}>
                    {n.title}
                  </p>
                  <p className="text-xs text-gray-500 mt-0.5">{n.message}</p>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}
