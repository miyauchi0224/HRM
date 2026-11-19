'use client'
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import api from '@/lib/api'
import { CalendarCheck } from 'lucide-react'

interface ObligationRow {
  employee_id: string
  full_name: string
  department: string
  grant_date: string
  deadline: string
  granted_days: number
  taken_days: number
  remaining_required: number
  days_until_deadline: number
  status: 'ok' | 'warning' | 'overdue'
}

const STATUS: Record<string, { label: string; color: string }> = {
  overdue: { label: '期限超過', color: 'bg-red-100 text-red-700' },
  warning: { label: '要注意',   color: 'bg-amber-100 text-amber-700' },
  ok:      { label: '問題なし', color: 'bg-green-100 text-green-700' },
}

/** 有給 年5日取得状況の一覧（上司は部下のみ、労務・人事は全社員。詳細設計書 7.2） */
export default function LeaveObligationPage() {
  const [onlyPending, setOnlyPending] = useState(true)
  const { data: rows = [], isLoading, error } = useQuery<ObligationRow[]>({
    queryKey: ['leave-obligation-summary'],
    queryFn: () => api.get('/api/v1/leave/grants/obligation-summary/').then((r) => r.data),
  })

  const visible = onlyPending ? rows.filter((r) => r.remaining_required > 0) : rows
  const counts  = {
    overdue: rows.filter((r) => r.status === 'overdue').length,
    warning: rows.filter((r) => r.status === 'warning').length,
    done:    rows.filter((r) => r.remaining_required === 0).length,
  }

  return (
    <div>
      <div className="flex items-center gap-2 mb-2">
        <CalendarCheck size={22} className="text-blue-600" />
        <h1 className="text-2xl font-bold text-gray-800">有給 年5日取得状況</h1>
      </div>
      <p className="text-sm text-gray-500 mb-6">
        年10日以上付与された社員は、付与日から1年以内に5日以上の取得が必要です（労働基準法 第39条第7項）。
      </p>

      <div className="grid grid-cols-3 gap-4 mb-6">
        {[
          { label: '期限超過',  value: counts.overdue, color: 'text-red-600' },
          { label: '要注意（残り90日以内）', value: counts.warning, color: 'text-amber-600' },
          { label: '取得完了',  value: counts.done,    color: 'text-green-600' },
        ].map((c) => (
          <div key={c.label} className="bg-white rounded-xl border border-gray-200 p-4 text-center">
            <p className="text-xs text-gray-400 mb-1">{c.label}</p>
            <p className={`text-2xl font-bold ${c.color}`}>{c.value}<span className="text-sm font-normal ml-1">人</span></p>
          </div>
        ))}
      </div>

      <div className="bg-white rounded-xl border border-gray-200 overflow-x-auto">
        <div className="px-5 py-3 border-b border-gray-100 flex items-center justify-between">
          <h2 className="font-semibold text-gray-700">社員ごとの状況</h2>
          <label className="text-sm text-gray-600 flex items-center gap-2">
            <input type="checkbox" checked={onlyPending} onChange={(e) => setOnlyPending(e.target.checked)} />
            未達の社員のみ
          </label>
        </div>
        {isLoading ? (
          <p className="text-center text-gray-400 text-sm py-10">読み込み中...</p>
        ) : error ? (
          <p className="text-center text-red-500 text-sm py-10">表示する権限がありません</p>
        ) : visible.length === 0 ? (
          <p className="text-center text-gray-400 text-sm py-10">対象の社員はいません</p>
        ) : (
          <table className="w-full text-sm min-w-[640px]">
            <thead>
              <tr className="text-gray-400 text-xs border-b border-gray-100">
                <th className="text-left px-5 py-3 font-medium">氏名</th>
                <th className="text-left px-5 py-3 font-medium">部署</th>
                <th className="text-left px-5 py-3 font-medium">対象期間</th>
                <th className="text-left px-5 py-3 font-medium">取得 / 必要</th>
                <th className="text-left px-5 py-3 font-medium">期限まで</th>
                <th className="text-left px-5 py-3 font-medium">状態</th>
              </tr>
            </thead>
            <tbody>
              {visible.map((r) => {
                const done = r.remaining_required === 0
                const st = done ? { label: '取得完了', color: 'bg-green-100 text-green-700' } : STATUS[r.status]
                return (
                  <tr key={r.employee_id} className="border-b border-gray-50">
                    <td className="px-5 py-3 font-medium text-gray-700">{r.full_name}</td>
                    <td className="px-5 py-3 text-gray-500">{r.department}</td>
                    <td className="px-5 py-3 text-gray-500 whitespace-nowrap">{r.grant_date} 〜 {r.deadline}</td>
                    <td className="px-5 py-3 text-gray-700">{r.taken_days} / 5 日</td>
                    <td className="px-5 py-3 text-gray-500">
                      {r.days_until_deadline >= 0 ? `${r.days_until_deadline}日` : `${-r.days_until_deadline}日超過`}
                    </td>
                    <td className="px-5 py-3">
                      <span className={`text-xs px-2.5 py-1 rounded-full font-medium ${st.color}`}>{st.label}</span>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
