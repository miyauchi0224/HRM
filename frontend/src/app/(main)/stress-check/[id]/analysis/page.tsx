'use client'
import { useParams } from 'next/navigation'
import { useQuery } from '@tanstack/react-query'
import api from '@/lib/api'
import { useAuthStore } from '@/lib/store'
import Link from 'next/link'
import { BarChart2, HeartPulse, ArrowLeft, Users, AlertTriangle } from 'lucide-react'

// ===== 型定義 =====
interface StressCheckPeriod {
  id: string
  title: string
  start_date: string
  end_date: string
  is_published: boolean
}

interface DepartmentSummary {
  department: string
  count: number
  high_stress_count: number
  avg_score: number
}

interface GroupAnalysis {
  period_id: string
  period_title: string
  total_responses: number
  high_stress_count: number
  high_stress_rate: number
  avg_score: number
  department_summary: DepartmentSummary[]
}

export default function StressCheckAnalysisPage() {
  const { id: periodId } = useParams<{ id: string }>()
  const { user } = useAuthStore()
  const isHR = ['hr', 'admin'].includes(user?.role ?? '')

  // ===== 期間情報取得 =====
  const { data: period, isLoading: periodLoading } = useQuery<StressCheckPeriod>({
    queryKey: ['stress-check-period', periodId],
    queryFn: () =>
      api.get(`/api/v1/stress-check/periods/${periodId}/`).then((r) => r.data),
    enabled: !!periodId && isHR,
  })

  // ===== 集団分析データ取得 =====
  const { data: analysis, isLoading: analysisLoading } = useQuery<GroupAnalysis>({
    queryKey: ['stress-check-group-analysis', periodId],
    queryFn: () =>
      api.get(`/api/v1/stress-check/periods/${periodId}/group-analysis/`).then((r) => r.data),
    enabled: !!periodId && isHR,
  })

  // ===== 権限チェック =====
  if (!isHR) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] p-6">
        <div className="bg-white rounded-2xl shadow-lg p-10 text-center max-w-md w-full">
          <AlertTriangle className="w-14 h-14 text-amber-400 mx-auto mb-4" />
          <h2 className="text-xl font-bold text-gray-900 mb-2">権限がありません</h2>
          <p className="text-gray-500 mb-6 text-sm">
            集団分析はHR・管理者のみ閲覧できます。
          </p>
          <Link
            href="/stress-check"
            className="inline-flex items-center gap-2 px-5 py-2.5 bg-rose-500 hover:bg-rose-600 text-white rounded-lg text-sm font-medium transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            ストレスチェック一覧に戻る
          </Link>
        </div>
      </div>
    )
  }

  // ===== ローディング =====
  if (periodLoading || analysisLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-rose-500" />
      </div>
    )
  }

  return (
    <div className="p-6 max-w-5xl mx-auto">
      {/* 戻るリンク */}
      <Link
        href="/stress-check"
        className="inline-flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-800 mb-5 transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        ストレスチェック一覧に戻る
      </Link>

      {/* ページタイトル */}
      <div className="flex items-center gap-3 mb-6">
        <BarChart2 className="w-7 h-7 text-rose-500" />
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            {period?.title ?? analysis?.period_title ?? '集団分析'}
          </h1>
          <p className="text-sm text-gray-500">集団分析レポート</p>
        </div>
      </div>

      {/* サマリーカード */}
      {analysis && (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
            {/* 総回答数 */}
            <div className="bg-white border rounded-xl p-5 shadow-sm">
              <div className="flex items-center gap-2 mb-2 text-blue-600">
                <Users className="w-5 h-5" />
                <span className="text-xs font-medium uppercase tracking-wide">総回答数</span>
              </div>
              <p className="text-3xl font-bold text-gray-900">
                {analysis.total_responses}
                <span className="text-base font-normal text-gray-500 ml-1">名</span>
              </p>
            </div>

            {/* 高ストレス者数 */}
            <div className="bg-white border rounded-xl p-5 shadow-sm">
              <div className="flex items-center gap-2 mb-2 text-red-500">
                <AlertTriangle className="w-5 h-5" />
                <span className="text-xs font-medium uppercase tracking-wide">高ストレス者数</span>
              </div>
              <p className="text-3xl font-bold text-gray-900">
                {analysis.high_stress_count}
                <span className="text-base font-normal text-gray-500 ml-1">名</span>
              </p>
            </div>

            {/* 高ストレス率 */}
            <div className="bg-white border rounded-xl p-5 shadow-sm">
              <div className="flex items-center gap-2 mb-2 text-rose-500">
                <HeartPulse className="w-5 h-5" />
                <span className="text-xs font-medium uppercase tracking-wide">高ストレス率</span>
              </div>
              <p className="text-3xl font-bold text-gray-900">
                {analysis.high_stress_rate.toFixed(1)}
                <span className="text-base font-normal text-gray-500 ml-1">%</span>
              </p>
            </div>

            {/* 平均スコア */}
            <div className="bg-white border rounded-xl p-5 shadow-sm">
              <div className="flex items-center gap-2 mb-2 text-green-600">
                <BarChart2 className="w-5 h-5" />
                <span className="text-xs font-medium uppercase tracking-wide">平均スコア</span>
              </div>
              <p className="text-3xl font-bold text-gray-900">
                {analysis.avg_score.toFixed(1)}
                <span className="text-base font-normal text-gray-500 ml-1">点</span>
              </p>
            </div>
          </div>

          {/* 部署別テーブル */}
          <div className="bg-white border rounded-xl shadow-sm overflow-hidden">
            <div className="px-6 py-4 border-b bg-gray-50">
              <h2 className="text-base font-semibold text-gray-800">部署別集計</h2>
            </div>
            {analysis.department_summary.length === 0 ? (
              <div className="text-center py-12 text-gray-400 text-sm">
                部署別データがありません
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-xs text-gray-500 uppercase tracking-wide border-b">
                      <th className="px-6 py-3 font-medium">部署名</th>
                      <th className="px-6 py-3 font-medium text-right">回答数</th>
                      <th className="px-6 py-3 font-medium text-right">高ストレス者数</th>
                      <th className="px-6 py-3 font-medium text-right">平均スコア</th>
                      <th className="px-6 py-3 font-medium">高ストレス率</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {analysis.department_summary.map((dept) => {
                      const rate =
                        dept.count > 0
                          ? Math.round((dept.high_stress_count / dept.count) * 100)
                          : 0
                      return (
                        <tr key={dept.department} className="hover:bg-gray-50 transition-colors">
                          <td className="px-6 py-4 font-medium text-gray-900">
                            {dept.department}
                          </td>
                          <td className="px-6 py-4 text-right text-gray-700">
                            {dept.count} 名
                          </td>
                          <td className="px-6 py-4 text-right">
                            <span
                              className={`font-medium ${
                                dept.high_stress_count > 0 ? 'text-red-600' : 'text-gray-600'
                              }`}
                            >
                              {dept.high_stress_count} 名
                            </span>
                          </td>
                          <td className="px-6 py-4 text-right text-gray-700">
                            {dept.avg_score.toFixed(1)} 点
                          </td>
                          <td className="px-6 py-4 w-48">
                            <div className="flex items-center gap-2">
                              <div className="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
                                <div
                                  className="h-full bg-red-500 rounded-full transition-all duration-500"
                                  style={{ width: `${Math.min(rate, 100)}%` }}
                                />
                              </div>
                              <span className="text-xs text-gray-500 w-10 text-right shrink-0">
                                {rate}%
                              </span>
                            </div>
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </>
      )}

      {/* analysis がない場合 */}
      {!analysisLoading && !analysis && (
        <div className="text-center py-16 text-gray-400">
          <BarChart2 className="w-12 h-12 mx-auto mb-3 opacity-40" />
          <p>集団分析データがありません</p>
        </div>
      )}
    </div>
  )
}
