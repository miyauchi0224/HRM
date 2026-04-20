'use client'
import { useQuery } from '@tanstack/react-query'
import api from '@/lib/api'
import { useAuthStore } from '@/lib/store'
import { BarChart2, Users, TrendingUp, DollarSign } from 'lucide-react'

interface HeadcountData {
  total: number
  by_role: Array<{ role: string; count: number }>
}
interface AttendanceTrendRow {
  month: string; avg_attendance_days: number; total_records: number; employee_count: number
}
interface ExpenseRow {
  month: string; expense_type: string; total: number; count: number
}

const ROLE_LABELS: Record<string, string> = {
  employee: '社員', supervisor: '上司', manager: '管理職',
  hr: '人事', accounting: '経理', customer: '顧客', admin: '管理者'
}

const BAR_COLORS = ['bg-indigo-500', 'bg-blue-500', 'bg-green-500', 'bg-yellow-500', 'bg-red-500', 'bg-purple-500', 'bg-pink-500']

export default function AnalyticsPage() {
  const user = useAuthStore((s) => s.user)
  const isHR = ['hr', 'admin'].includes(user?.role ?? '')

  const { data: headcount } = useQuery<HeadcountData>({
    queryKey: ['analytics-headcount'],
    queryFn: () => api.get('/api/v1/analytics/headcount/').then((r) => r.data),
    enabled: isHR,
  })

  const { data: trend = [] } = useQuery<AttendanceTrendRow[]>({
    queryKey: ['analytics-attendance-trend'],
    queryFn: () => api.get('/api/v1/analytics/attendance-trend/').then((r) => r.data),
    enabled: isHR,
  })

  const { data: expenses = [] } = useQuery<ExpenseRow[]>({
    queryKey: ['analytics-expense-summary'],
    queryFn: () => api.get('/api/v1/analytics/expense-summary/').then((r) => r.data),
    enabled: isHR,
  })

  const { data: leaveUsage = [] } = useQuery<any[]>({
    queryKey: ['analytics-leave-usage'],
    queryFn: () => api.get('/api/v1/analytics/leave-usage/').then((r) => r.data),
    enabled: isHR,
  })

  if (!isHR) {
    return (
      <div className="p-6 flex items-center justify-center min-h-96">
        <div className="text-center text-gray-400">
          <BarChart2 size={48} className="mx-auto mb-3 opacity-30" />
          <p>分析ダッシュボードは人事担当者以上が利用できます</p>
        </div>
      </div>
    )
  }

  const maxTrend = Math.max(...trend.map((t) => t.avg_attendance_days), 1)
  const expenseByMonth = expenses.reduce<Record<string, number>>((acc, row) => {
    acc[row.month] = (acc[row.month] ?? 0) + row.total
    return acc
  }, {})
  const maxExpense = Math.max(...Object.values(expenseByMonth), 1)
  const avgLeaveUsage = leaveUsage.length > 0
    ? Math.round(leaveUsage.reduce((s, l) => s + l.usage_pct, 0) / leaveUsage.length)
    : 0

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="flex items-center gap-3 mb-6">
        <BarChart2 className="text-indigo-600" size={28} />
        <div>
          <h1 className="text-2xl font-bold text-gray-800">分析ダッシュボード</h1>
          <p className="text-sm text-gray-500">勤怠・人員・経費のKPI分析</p>
        </div>
      </div>

      {/* KPI カード */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <div className="bg-white rounded-xl border shadow-sm p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-indigo-50 rounded-lg"><Users className="text-indigo-600" size={20} /></div>
            <div>
              <p className="text-2xl font-bold text-gray-800">{headcount?.total ?? '-'}</p>
              <p className="text-xs text-gray-500">総社員数</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl border shadow-sm p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-green-50 rounded-lg"><TrendingUp className="text-green-600" size={20} /></div>
            <div>
              <p className="text-2xl font-bold text-gray-800">{avgLeaveUsage}%</p>
              <p className="text-xs text-gray-500">平均有給消化率</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl border shadow-sm p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-yellow-50 rounded-lg"><DollarSign className="text-yellow-600" size={20} /></div>
            <div>
              <p className="text-2xl font-bold text-gray-800">
                ¥{(Object.values(expenseByMonth).reduce((s, v) => s + v, 0) / 10000).toFixed(0)}万
              </p>
              <p className="text-xs text-gray-500">直近6か月経費合計</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl border shadow-sm p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-purple-50 rounded-lg"><BarChart2 className="text-purple-600" size={20} /></div>
            <div>
              <p className="text-2xl font-bold text-gray-800">{trend.length > 0 ? trend[trend.length - 1].total_records : '-'}</p>
              <p className="text-xs text-gray-500">先月の出勤記録数</p>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-6 mb-6">
        {/* ロール別人員 */}
        <div className="bg-white rounded-xl border shadow-sm p-5">
          <h2 className="font-semibold text-gray-700 mb-4">ロール別人員数</h2>
          <div className="space-y-3">
            {(headcount?.by_role ?? []).map((item, i) => {
              const pct = headcount?.total ? Math.round(item.count / headcount.total * 100) : 0
              return (
                <div key={item.role}>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-gray-600">{ROLE_LABELS[item.role] ?? item.role}</span>
                    <span className="font-medium text-gray-800">{item.count}名 ({pct}%)</span>
                  </div>
                  <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                    <div
                      className={`h-full ${BAR_COLORS[i % BAR_COLORS.length]} rounded-full transition-all`}
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* 月別出勤トレンド */}
        <div className="bg-white rounded-xl border shadow-sm p-5">
          <h2 className="font-semibold text-gray-700 mb-4">月別出勤記録数トレンド</h2>
          <div className="flex items-end gap-2 h-40">
            {trend.map((row, i) => {
              const pct = (row.total_records / Math.max(...trend.map((t) => t.total_records), 1)) * 100
              return (
                <div key={row.month} className="flex-1 flex flex-col items-center gap-1">
                  <span className="text-xs text-gray-500">{row.total_records}</span>
                  <div className="w-full bg-indigo-200 rounded-t" style={{ height: `${pct}%`, minHeight: '4px' }} />
                  <span className="text-xs text-gray-400">{row.month?.slice(5)}</span>
                </div>
              )
            })}
          </div>
        </div>
      </div>

      {/* 月別経費グラフ */}
      <div className="bg-white rounded-xl border shadow-sm p-5 mb-6">
        <h2 className="font-semibold text-gray-700 mb-4">月別承認経費合計</h2>
        <div className="flex items-end gap-3 h-40">
          {Object.entries(expenseByMonth).map(([month, total]) => {
            const pct = (total / maxExpense) * 100
            return (
              <div key={month} className="flex-1 flex flex-col items-center gap-1">
                <span className="text-xs text-gray-500">¥{(total / 10000).toFixed(0)}万</span>
                <div className="w-full bg-green-300 rounded-t" style={{ height: `${pct}%`, minHeight: '4px' }} />
                <span className="text-xs text-gray-400">{month?.slice(5)}</span>
              </div>
            )
          })}
        </div>
      </div>

      {/* 有給消化率ランキング */}
      <div className="bg-white rounded-xl border shadow-sm overflow-hidden">
        <div className="px-5 py-3 border-b bg-gray-50">
          <h2 className="font-semibold text-gray-700 text-sm">有給消化率（{new Date().getFullYear()}年度）</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="text-xs text-gray-500 bg-gray-50 uppercase">
              <tr>
                <th className="px-4 py-3 text-left">社員名</th>
                <th className="px-4 py-3 text-right">付与日数</th>
                <th className="px-4 py-3 text-right">使用日数</th>
                <th className="px-4 py-3 text-right">残日数</th>
                <th className="px-4 py-3 text-right">消化率</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {leaveUsage.slice(0, 10).map((item: any) => (
                <tr key={item.employee_id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium text-gray-800">{item.employee_name}</td>
                  <td className="px-4 py-3 text-right text-gray-600">{item.granted}日</td>
                  <td className="px-4 py-3 text-right text-gray-600">{item.used}日</td>
                  <td className="px-4 py-3 text-right text-gray-600">{item.remaining}日</td>
                  <td className="px-4 py-3 text-right">
                    <span className={`font-medium ${item.usage_pct >= 80 ? 'text-green-600' : item.usage_pct >= 50 ? 'text-yellow-600' : 'text-red-500'}`}>
                      {item.usage_pct}%
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
