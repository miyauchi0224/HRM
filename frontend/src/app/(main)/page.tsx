'use client'
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'
import { useAuthStore } from '@/lib/store'
import { Clock, Calendar, Target, Bell, CheckSquare, Newspaper, Pin, Play, Square, GanttChartSquare } from 'lucide-react'
import Link from 'next/link'
import CalendarPanel from './components/CalendarPanel'
import ComplianceChecklist from './components/ComplianceChecklist'

export default function DashboardPage() {
  const user       = useAuthStore((s) => s.user)
  const isCustomer = user?.role === 'customer'
  const qc   = useQueryClient()
  const [clockError, setClockError] = useState<string | null>(null)

  const today = new Date().toISOString().slice(0, 10)

  const { data: summary } = useQuery({
    queryKey: ['attendance-summary'],
    queryFn: () => api.get('/api/v1/attendance/summary/').then((r) => r.data),
  })

  const { data: todayRecords = [] } = useQuery<any[]>({
    queryKey: ['attendance', today],
    queryFn: () => api.get(`/api/v1/attendance/?year_month=${today.slice(0, 7)}`).then((r) => r.data.results ?? r.data),
  })

  const todayRecord = todayRecords.find((r: any) => r.date === today)
  const isWorking   = todayRecord && !todayRecord.clock_out
  const isDone      = todayRecord?.clock_out

  const clockInMut = useMutation({
    mutationFn: () => api.post('/api/v1/attendance/clock-in/', {}),
    onSuccess: () => {
      setClockError(null)
      qc.invalidateQueries({ queryKey: ['attendance'] })
      qc.invalidateQueries({ queryKey: ['attendance-summary'] })
    },
    onError: (err: any) => {
      const status = err?.response?.status
      const data   = err?.response?.data
      const msg    = data?.error ?? data?.detail ?? (typeof data === 'string' ? data.slice(0, 200) : null)
                     ?? `出勤打刻に失敗しました（HTTP ${status ?? 'network error'}）`
      setClockError(msg)
    },
  })
  const clockOutMut = useMutation({
    mutationFn: () => api.post('/api/v1/attendance/clock-out/', { break_minutes: 60 }),
    onSuccess: () => {
      setClockError(null)
      qc.invalidateQueries({ queryKey: ['attendance'] })
      qc.invalidateQueries({ queryKey: ['attendance-summary'] })
    },
    onError: (err: any) => {
      const status = err?.response?.status
      const data   = err?.response?.data
      const msg    = data?.error ?? data?.detail ?? (typeof data === 'string' ? data.slice(0, 200) : null)
                     ?? `退勤打刻に失敗しました（HTTP ${status ?? 'network error'}）`
      setClockError(msg)
    },
  })

  const { data: notifications } = useQuery({
    queryKey: ['notifications'],
    queryFn: () => api.get('/api/v1/notifications/').then((r) => r.data),
  })

  const { data: todos = [] } = useQuery<any[]>({
    queryKey: ['todos'],
    queryFn: () => api.get('/api/v1/todo/items/').then((r) => r.data.results ?? r.data),
  })

  const { data: recentArticles = [] } = useQuery<any[]>({
    queryKey: ['intra-recent'],
    queryFn: () => api.get('/api/v1/intra/articles/recent/').then((r) => r.data),
  })

  const { data: myTasks = [] } = useQuery<any[]>({
    queryKey: ['my-project-tasks'],
    queryFn: () => api.get('/api/v1/attendance/project-tasks/?status=todo,in_progress,review').then((r) => r.data.results ?? r.data),
    enabled: !isCustomer,
  })

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-800 mb-1">ダッシュボード</h1>
      <p className="text-gray-500 text-sm mb-6">
        おはようございます、{user?.full_name ?? 'ゲスト'}さん
      </p>

      {/* 打刻ボタン（顧客には非表示）*/}
      {!isCustomer && <div className="bg-white rounded-xl border border-gray-200 p-4 mb-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-700">
              {isDone ? '本日の勤務完了' : isWorking ? '勤務中' : '本日はまだ出勤していません'}
            </p>
            {todayRecord?.clock_in && (
              <p className="text-xs text-gray-400 mt-0.5">
                出勤: {todayRecord.clock_in}
                {todayRecord.clock_out && `　退勤: ${todayRecord.clock_out}`}
              </p>
            )}
          </div>
          <div className="flex gap-2">
            {!isWorking && !isDone && (
              <button
                onClick={() => clockInMut.mutate()}
                disabled={clockInMut.isPending}
                className="flex items-center gap-2 px-5 py-2.5 bg-green-600 hover:bg-green-700 disabled:bg-green-300 text-white text-sm font-semibold rounded-lg transition-colors"
              >
                <Play size={15} /> {clockInMut.isPending ? '打刻中...' : '出勤'}
              </button>
            )}
            {isWorking && (
              <button
                onClick={() => clockOutMut.mutate()}
                disabled={clockOutMut.isPending}
                className="flex items-center gap-2 px-5 py-2.5 bg-red-600 hover:bg-red-700 disabled:bg-red-300 text-white text-sm font-semibold rounded-lg transition-colors"
              >
                <Square size={15} /> {clockOutMut.isPending ? '打刻中...' : '退勤'}
              </button>
            )}
            {isDone && (
              <span className="text-xs text-gray-400 bg-gray-100 rounded-lg px-4 py-2.5">勤務終了</span>
            )}
          </div>
        </div>
        {clockError && (
          <p className="mt-2 text-xs text-red-600 bg-red-50 rounded-lg px-3 py-2">
            {clockError}
          </p>
        )}
      </div>}

      {/* KPIカード（顧客には通知のみ表示）*/}
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
          href="/notifications"
        />
        <KpiCard
          icon={<Target className="text-purple-500" size={20} />}
          label="MBO"
          value="確認する"
          href="/mbo"
        />
      </div>

      {/* カレンダー */}
      {!isCustomer && <CalendarPanel />}

      {/* コンプライアンスチェックリスト */}
      {!isCustomer && <ComplianceChecklist />}

      {/* プロジェクトタスク（自分のガントチャート） */}
      {!isCustomer && myTasks.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-5 mb-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-base font-semibold text-gray-700 flex items-center gap-2">
              <GanttChartSquare size={16} className="text-blue-500" /> 自分のプロジェクトタスク
            </h2>
            <Link href="/project" className="text-xs text-blue-600 hover:underline">プロジェクト管理へ</Link>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="text-gray-400 border-b border-gray-100">
                  <th className="text-left pb-2 font-medium w-48">タスク名</th>
                  <th className="text-left pb-2 font-medium w-24">プロジェクト</th>
                  <th className="text-left pb-2 font-medium w-20">ステータス</th>
                  <th className="text-right pb-2 font-medium w-12">進捗</th>
                  <th className="pb-2 min-w-[200px]">期間</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {myTasks.slice(0, 8).map((task: any) => {
                  const STATUS_COLOR: Record<string, string> = { todo: 'bg-gray-300', in_progress: 'bg-blue-400', review: 'bg-yellow-400', done: 'bg-green-400' }
                  const STATUS_TEXT: Record<string, string> = { todo: '未着手', in_progress: '進行中', review: 'レビュー中', done: '完了' }
                  return (
                    <tr key={task.id} className="hover:bg-gray-50">
                      <td className="py-2 font-medium text-gray-800 truncate pr-2">{task.title}</td>
                      <td className="py-2 text-gray-500 truncate pr-2">{task.project_code}</td>
                      <td className="py-2">
                        <span className={`px-1.5 py-0.5 rounded text-white text-xs ${STATUS_COLOR[task.status]}`}>{STATUS_TEXT[task.status]}</span>
                      </td>
                      <td className="py-2 text-right text-gray-500">{task.progress}%</td>
                      <td className="py-2 px-2">
                        {task.start_date ? (
                          <div className="flex items-center gap-1">
                            <span className="text-gray-400 whitespace-nowrap">{task.start_date.slice(5)} 〜 {task.end_date?.slice(5) ?? '?'}</span>
                          </div>
                        ) : <span className="text-gray-300">—</span>}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* TODOリスト */}
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-base font-semibold text-gray-700 flex items-center gap-2">
              <CheckSquare size={16} /> TODOリスト
            </h2>
            <Link href="/todo" className="text-xs text-blue-600 hover:underline">すべて見る</Link>
          </div>
          {todos.filter((t) => t.status !== 'done').length === 0 ? (
            <p className="text-gray-400 text-sm">未完了のTODOはありません</p>
          ) : (
            <ul className="space-y-2">
              {todos.filter((t) => t.status !== 'done').slice(0, 5).map((t: any) => (
                <li key={t.id} className="flex items-start gap-2 p-2 rounded-lg bg-gray-50 text-sm">
                  <span className={`mt-0.5 inline-block w-2 h-2 rounded-full shrink-0 ${
                    t.status === 'in_progress' ? 'bg-blue-500' : 'bg-gray-300'
                  }`} />
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-gray-800 truncate">{t.title}</p>
                    {t.due_date && (
                      <p className="text-xs text-gray-400 mt-0.5">
                        期限: {new Date(t.due_date).toLocaleDateString('ja-JP')}
                      </p>
                    )}
                  </div>
                  <span className={`text-xs px-2 py-0.5 rounded-full shrink-0 ${
                    t.status === 'in_progress'
                      ? 'bg-blue-100 text-blue-700'
                      : 'bg-gray-100 text-gray-600'
                  }`}>
                    {t.status === 'in_progress' ? '作業中' : '未着手'}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* イントラ最新記事 */}
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-base font-semibold text-gray-700 flex items-center gap-2">
              <Newspaper size={16} /> 最新記事
            </h2>
            <Link href="/intra" className="text-xs text-blue-600 hover:underline">すべて見る</Link>
          </div>
          {recentArticles.length === 0 ? (
            <p className="text-gray-400 text-sm">公開中の記事はありません</p>
          ) : (
            <ul className="space-y-2">
              {recentArticles.map((a: any) => (
                <li key={a.id}>
                  <Link
                    href={`/intra/${a.id}`}
                    className="flex items-start gap-2 p-2 rounded-lg hover:bg-gray-50 transition-colors"
                  >
                    {a.is_pinned && <Pin size={12} className="text-yellow-500 mt-0.5 shrink-0" />}
                    <div className="flex-1 min-w-0">
                      <p className={`text-sm font-medium truncate ${a.is_read ? 'text-gray-600' : 'text-gray-900'}`}>
                        {!a.is_read && (
                          <span className="inline-block w-1.5 h-1.5 bg-blue-500 rounded-full mr-1.5 align-middle" />
                        )}
                        {a.title}
                      </p>
                      <p className="text-xs text-gray-400 mt-0.5">
                        {a.author_name} · {a.published_at ? new Date(a.published_at).toLocaleDateString('ja-JP') : ''}
                      </p>
                    </div>
                  </Link>
                </li>
              ))}
            </ul>
          )}
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
