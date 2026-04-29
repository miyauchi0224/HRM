'use client'
import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'
import { useParams, useRouter } from 'next/navigation'
import { ArrowLeft, Save, Check, AlertCircle } from 'lucide-react'
import Link from 'next/link'

interface StressCheckQuestion {
  order: number
  section: string
  text: string
  reverse: boolean
}

interface StressCheckResponse {
  id: string
  period: string
  employee: string
  employee_name: string
  answers: Record<string, number>
  submitted_at: string | null
  is_submitted: boolean
  high_stress: boolean
  total_score: number
  questions: StressCheckQuestion[]
}

interface StressCheckPeriod {
  id: string
  title: string
  start_date: string
  end_date: string
  is_published: boolean
}

export default function StressCheckResponsePage() {
  const params = useParams()
  const router = useRouter()
  const periodId = params.periodId as string
  const qc = useQueryClient()

  const [answers, setAnswers] = useState<Record<string, number>>({})
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null)

  const { data: period } = useQuery<StressCheckPeriod>({
    queryKey: ['stress-check-period', periodId],
    queryFn: () => api.get(`/api/v1/stress-check/periods/${periodId}/`).then((r) => r.data),
  })

  const { data: response } = useQuery<StressCheckResponse>({
    queryKey: ['stress-check-response', periodId],
    queryFn: async () => {
      const res = await api.post('/api/v1/stress-check/responses/start/', { period_id: periodId })
      return res.data
    },
  })

  useEffect(() => {
    if (response) {
      setAnswers(response.answers || {})
    }
  }, [response])

  const saveMut = useMutation({
    mutationFn: async () => {
      if (!response) return
      return api.patch(`/api/v1/stress-check/responses/${response.id}/save/`, { answers })
    },
    onSuccess: () => {
      setMessage({ type: 'success', text: '保存しました' })
      setTimeout(() => setMessage(null), 3000)
      qc.invalidateQueries({ queryKey: ['stress-check-response', periodId] })
    },
    onError: (err: any) => {
      setMessage({ type: 'error', text: err.response?.data?.error ?? '保存に失敗しました' })
    },
  })

  const submitMut = useMutation({
    mutationFn: async () => {
      if (!response) return
      return api.post(`/api/v1/stress-check/responses/${response.id}/submit/`, { answers })
    },
    onSuccess: () => {
      setMessage({ type: 'success', text: '提出しました' })
      setTimeout(() => router.push('/stress-check'), 2000)
    },
    onError: (err: any) => {
      setMessage({ type: 'error', text: err.response?.data?.error ?? '提出に失敗しました' })
    },
  })

  if (!response || !period) {
    return (
      <div className="flex items-center justify-center py-12">
        <p className="text-gray-500">読み込み中...</p>
      </div>
    )
  }

  if (response.is_submitted) {
    return (
      <div className="max-w-2xl mx-auto">
        <Link href="/stress-check" className="flex items-center gap-1 text-blue-600 hover:underline mb-6">
          <ArrowLeft size={16} /> 一覧へ戻る
        </Link>
        <div className="bg-green-50 border border-green-200 rounded-xl p-8 text-center">
          <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <Check size={32} className="text-green-600" />
          </div>
          <h2 className="text-xl font-bold text-gray-800 mb-2">提出済み</h2>
          <p className="text-gray-600 mb-4">ストレスチェックの回答をありがとうございました。</p>
          <div className="bg-white rounded-lg p-4 mb-4 inline-block">
            <p className="text-sm text-gray-600">合計スコア</p>
            <p className="text-3xl font-bold text-gray-800">{response.total_score}</p>
            {response.high_stress && (
              <p className="text-red-600 text-sm mt-2 flex items-center justify-center gap-1">
                <AlertCircle size={14} /> 高ストレス状態です
              </p>
            )}
          </div>
          <Link
            href="/stress-check"
            className="inline-block mt-4 px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium"
          >
            一覧へ戻る
          </Link>
        </div>
      </div>
    )
  }

  const questions = response.questions || []
  const sections = ['A', 'B', 'C', 'D']
  const sectionTitles: Record<string, string> = {
    A: '仕事のストレス要因',
    B: 'ストレス反応',
    C: '周囲のサポート',
    D: '満足度',
  }

  const answeredCount = Object.values(answers).filter((a) => a > 0).length
  const allAnswered = answeredCount === questions.length

  return (
    <div className="max-w-3xl mx-auto">
      <Link href="/stress-check" className="flex items-center gap-1 text-blue-600 hover:underline mb-6">
        <ArrowLeft size={16} /> 一覧へ戻る
      </Link>

      <div className="bg-white rounded-xl border border-gray-200 p-6 mb-6">
        <h1 className="text-2xl font-bold text-gray-800 mb-2">{period.title}</h1>
        <p className="text-sm text-gray-600 mb-4">
          {period.start_date} 〜 {period.end_date}
        </p>
        <div className="bg-blue-50 rounded-lg p-3">
          <p className="text-sm text-blue-800">
            全 {questions.length} 問中 <strong>{answeredCount}</strong> 問に回答済み
          </p>
          <div className="w-full bg-blue-200 rounded-full h-2 mt-2">
            <div
              className="bg-blue-600 h-2 rounded-full transition-all"
              style={{ width: `${(answeredCount / questions.length) * 100}%` }}
            />
          </div>
        </div>
      </div>

      {message && (
        <div
          className={`rounded-lg p-4 mb-6 flex items-center gap-2 ${
            message.type === 'success' ? 'bg-green-50 text-green-700 border border-green-200' : 'bg-red-50 text-red-700 border border-red-200'
          }`}
        >
          {message.type === 'success' ? <Check size={16} /> : <AlertCircle size={16} />}
          {message.text}
        </div>
      )}

      <div className="space-y-8">
        {sections.map((section) => {
          const sectionQuestions = questions.filter((q) => q.section === section)
          if (sectionQuestions.length === 0) return null

          return (
            <section key={section}>
              <h2 className="text-lg font-bold text-gray-800 mb-4">
                セクション {section}: {sectionTitles[section]}
              </h2>
              <div className="space-y-4">
                {sectionQuestions.map((q) => {
                  const answer = answers[String(q.order)] || 0
                  const labels = ['', 'あてはまらない', 'ややあてはまらない', 'ややあてはまる', 'あてはまる']
                  return (
                    <div key={q.order} className="bg-white rounded-lg border border-gray-200 p-4">
                      <p className="text-sm text-gray-800 font-medium mb-3">
                        <span className="text-gray-500">問{q.order}. </span>
                        {q.text}
                      </p>
                      <div className="flex gap-2">
                        {[1, 2, 3, 4].map((score) => (
                          <button
                            key={score}
                            onClick={() => setAnswers((prev) => ({ ...prev, [String(q.order)]: score }))}
                            className={`flex-1 py-2 px-3 rounded-lg font-medium text-sm transition-colors ${
                              answer === score
                                ? 'bg-blue-600 text-white'
                                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                            }`}
                          >
                            {score}
                          </button>
                        ))}
                      </div>
                      <p className="text-xs text-gray-500 mt-2">
                        {answer > 0 ? labels[answer] : '未回答'}
                      </p>
                    </div>
                  )
                })}
              </div>
            </section>
          )
        })}
      </div>

      <div className="flex gap-3 mt-8 sticky bottom-0 bg-white py-4 border-t border-gray-200">
        <button
          onClick={() => saveMut.mutate()}
          disabled={saveMut.isPending}
          className="flex-1 flex items-center justify-center gap-2 py-3 bg-gray-200 hover:bg-gray-300 disabled:bg-gray-100 text-gray-700 rounded-lg font-medium transition-colors"
        >
          <Save size={18} />
          {saveMut.isPending ? '保存中...' : '途中保存'}
        </button>
        <button
          onClick={() => {
            if (!allAnswered) {
              setMessage({ type: 'error', text: 'すべての質問に回答してください' })
              return
            }
            submitMut.mutate()
          }}
          disabled={!allAnswered || submitMut.isPending}
          className="flex-1 flex items-center justify-center gap-2 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white rounded-lg font-medium transition-colors"
        >
          <Check size={18} />
          {submitMut.isPending ? '提出中...' : '提出する'}
        </button>
      </div>
    </div>
  )
}
