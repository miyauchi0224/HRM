'use client'
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'
import { useAuthStore } from '@/lib/store'
import { HeartPulse, Plus, CheckCircle2, Clock, BarChart2, X } from 'lucide-react'
import Link from 'next/link'

// ===== 型定義 =====
interface StressCheckPeriod {
  id: string
  title: string
  start_date: string
  end_date: string
  is_published: boolean
  response_count: number
  high_stress_count: number
  created_at: string
}

interface StressCheckResponse {
  id: string
  period: string
  is_submitted: boolean
  submitted_at: string | null
  high_stress: boolean
  total_score: number
}

// ===== 新規作成フォーム =====
interface NewPeriodForm {
  title: string
  start_date: string
  end_date: string
}

export default function StressCheckPage() {
  const { user } = useAuthStore()
  const isHR = ['hr', 'admin'].includes(user?.role ?? '')
  const qc = useQueryClient()
  const [showNew, setShowNew] = useState(false)
  const [form, setForm] = useState<NewPeriodForm>({ title: '', start_date: '', end_date: '' })
  const [error, setError] = useState('')

  // ===== データ取得 =====
  const { data: periods = [], isLoading: periodsLoading } = useQuery<StressCheckPeriod[]>({
    queryKey: ['stress-check-periods'],
    queryFn: () => api.get('/api/v1/stress-check/periods/').then((r) => r.data.results ?? r.data),
  })

  // 一般社員: 自分の回答一覧
  const { data: myResponses = [] } = useQuery<StressCheckResponse[]>({
    queryKey: ['stress-check-my-responses'],
    queryFn: () => api.get('/api/v1/stress-check/responses/').then((r) => r.data.results ?? r.data),
    enabled: !isHR,
  })

  // ===== ミューテーション =====
  const createMutation = useMutation({
    mutationFn: (data: NewPeriodForm) => api.post('/api/v1/stress-check/periods/', data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['stress-check-periods'] })
      setShowNew(false)
      setForm({ title: '', start_date: '', end_date: '' })
      setError('')
    },
    onError: (e: any) => {
      setError(e.response?.data?.detail ?? '作成に失敗しました')
    },
  })

  const publishMutation = useMutation({
    mutationFn: (id: string) => api.post(`/api/v1/stress-check/periods/${id}/publish/`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['stress-check-periods'] })
    },
  })

  const handleCreate = () => {
    if (!form.title || !form.start_date || !form.end_date) {
      setError('すべての項目を入力してください')
      return
    }
    createMutation.mutate(form)
  }

  // 一般社員向け: 期間とマイレスポンスを紐付け
  const getMyResponse = (periodId: string) =>
    myResponses.find((r) => r.period === periodId)

  if (periodsLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    )
  }

  return (
    <div className="p-6 max-w-5xl mx-auto">
      {/* ヘッダー */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <HeartPulse className="w-7 h-7 text-rose-500" />
          <div>
            <h1 className="text-2xl font-bold text-gray-900">ストレスチェック</h1>
            <p className="text-sm text-gray-500">
              {isHR ? '実施期間の管理・集団分析' : '回答状況の確認'}
            </p>
          </div>
        </div>
        {isHR && (
          <button
            onClick={() => setShowNew(true)}
            className="flex items-center gap-2 bg-rose-500 hover:bg-rose-600 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
          >
            <Plus className="w-4 h-4" />
            新規作成
          </button>
        )}
      </div>

      {/* 新規作成モーダル（HR専用） */}
      {showNew && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl p-6 w-full max-w-md mx-4">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold text-gray-900">実施期間を新規作成</h2>
              <button onClick={() => { setShowNew(false); setError('') }}>
                <X className="w-5 h-5 text-gray-400 hover:text-gray-600" />
              </button>
            </div>
            {error && (
              <div className="mb-4 p-3 bg-red-50 text-red-600 rounded-lg text-sm">{error}</div>
            )}
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">タイトル</label>
                <input
                  type="text"
                  value={form.title}
                  onChange={(e) => setForm({ ...form, title: e.target.value })}
                  placeholder="例: 2026年度 第1回ストレスチェック"
                  className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-rose-400 focus:outline-none"
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">回答開始日</label>
                  <input
                    type="date"
                    value={form.start_date}
                    onChange={(e) => setForm({ ...form, start_date: e.target.value })}
                    className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-rose-400 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">回答終了日</label>
                  <input
                    type="date"
                    value={form.end_date}
                    onChange={(e) => setForm({ ...form, end_date: e.target.value })}
                    className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-rose-400 focus:outline-none"
                  />
                </div>
              </div>
            </div>
            <div className="flex justify-end gap-3 mt-6">
              <button
                onClick={() => { setShowNew(false); setError('') }}
                className="px-4 py-2 text-sm text-gray-600 border rounded-lg hover:bg-gray-50"
              >
                キャンセル
              </button>
              <button
                onClick={handleCreate}
                disabled={createMutation.isPending}
                className="px-4 py-2 text-sm bg-rose-500 hover:bg-rose-600 text-white rounded-lg disabled:opacity-50"
              >
                {createMutation.isPending ? '作成中...' : '作成する'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* HR: 実施期間一覧 */}
      {isHR && (
        <div className="space-y-4">
          {periods.length === 0 ? (
            <div className="text-center py-16 text-gray-400">
              <HeartPulse className="w-12 h-12 mx-auto mb-3 opacity-40" />
              <p>実施期間がまだありません</p>
              <p className="text-sm mt-1">「新規作成」から追加してください</p>
            </div>
          ) : (
            periods.map((period) => (
              <div key={period.id} className="bg-white border rounded-xl p-5 shadow-sm">
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="font-semibold text-gray-900">{period.title}</h3>
                    <p className="text-sm text-gray-500 mt-1">
                      {period.start_date} 〜 {period.end_date}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    {period.is_published ? (
                      <span className="px-2 py-1 text-xs bg-green-100 text-green-700 rounded-full font-medium">
                        公開中
                      </span>
                    ) : (
                      <button
                        onClick={() => publishMutation.mutate(period.id)}
                        disabled={publishMutation.isPending}
                        className="px-3 py-1 text-xs bg-rose-500 hover:bg-rose-600 text-white rounded-full font-medium disabled:opacity-50"
                      >
                        公開する
                      </button>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-6 mt-4 pt-4 border-t">
                  <div className="flex items-center gap-2 text-sm text-gray-600">
                    <CheckCircle2 className="w-4 h-4 text-green-500" />
                    <span>回答済み: <strong>{period.response_count}</strong> 名</span>
                  </div>
                  <div className="flex items-center gap-2 text-sm text-gray-600">
                    <HeartPulse className="w-4 h-4 text-red-500" />
                    <span>高ストレス: <strong>{period.high_stress_count}</strong> 名</span>
                  </div>
                  {period.is_published && (
                    <Link
                      href={`/stress-check/${period.id}/analysis`}
                      className="ml-auto flex items-center gap-1 text-sm text-blue-600 hover:text-blue-800 font-medium"
                    >
                      <BarChart2 className="w-4 h-4" />
                      集団分析
                    </Link>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* 一般社員: 回答状況一覧 */}
      {!isHR && (
        <div className="space-y-4">
          {periods.length === 0 ? (
            <div className="text-center py-16 text-gray-400">
              <HeartPulse className="w-12 h-12 mx-auto mb-3 opacity-40" />
              <p>現在実施中のストレスチェックはありません</p>
            </div>
          ) : (
            periods.map((period) => {
              const myResp = getMyResponse(period.id)
              return (
                <div key={period.id} className="bg-white border rounded-xl p-5 shadow-sm">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="font-semibold text-gray-900">{period.title}</h3>
                      <p className="text-sm text-gray-500 mt-1">
                        回答期間: {period.start_date} 〜 {period.end_date}
                      </p>
                    </div>
                    <div className="flex items-center gap-3">
                      {myResp?.is_submitted ? (
                        <div className="flex items-center gap-2 text-green-600">
                          <CheckCircle2 className="w-5 h-5" />
                          <span className="text-sm font-medium">回答済み</span>
                        </div>
                      ) : (
                        <div className="flex items-center gap-2 text-amber-600">
                          <Clock className="w-5 h-5" />
                          <span className="text-sm font-medium">未回答</span>
                        </div>
                      )}
                      {!myResp?.is_submitted && (
                        <Link
                          href={`/stress-check/${period.id}`}
                          className="px-4 py-2 text-sm bg-rose-500 hover:bg-rose-600 text-white rounded-lg font-medium"
                        >
                          回答する
                        </Link>
                      )}
                    </div>
                  </div>
                  {myResp?.is_submitted && myResp.submitted_at && (
                    <p className="text-xs text-gray-400 mt-3 pt-3 border-t">
                      提出日時: {new Date(myResp.submitted_at).toLocaleString('ja-JP')}
                    </p>
                  )}
                </div>
              )
            })
          )}
        </div>
      )}
    </div>
  )
}
