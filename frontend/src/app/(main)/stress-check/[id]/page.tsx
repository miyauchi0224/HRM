'use client'
import { useState, useEffect } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import api from '@/lib/api'
import { useParams, useRouter } from 'next/navigation'
import { HeartPulse, CheckCircle2, Save, ChevronRight } from 'lucide-react'

// ===== 型定義 =====
interface Question {
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
  questions: Question[]
}

// セクション情報
const SECTION_LABELS: Record<string, { label: string; description: string; color: string }> = {
  A: { label: 'A. 仕事のストレス要因', description: '現在の仕事の状況についてお答えください', color: 'blue' },
  B: { label: 'B. ストレス反応',       description: '最近1ヶ月の状態についてお答えください',   color: 'rose' },
  C: { label: 'C. 周囲のサポート',     description: '周囲のサポートについてお答えください',     color: 'green' },
  D: { label: 'D. 満足度',             description: '全体的な満足度についてお答えください',     color: 'purple' },
}

const CHOICES = [
  { value: 1, label: 'そうだ' },
  { value: 2, label: 'まあそうだ' },
  { value: 3, label: 'ややちがう' },
  { value: 4, label: 'ちがう' },
]

const SECTION_COLOR_MAP: Record<string, string> = {
  blue:   'bg-blue-50 border-blue-200 text-blue-700',
  rose:   'bg-rose-50 border-rose-200 text-rose-700',
  green:  'bg-green-50 border-green-200 text-green-700',
  purple: 'bg-purple-50 border-purple-200 text-purple-700',
}

const RADIO_COLOR_MAP: Record<string, string> = {
  blue:   'checked:accent-blue-600',
  rose:   'checked:accent-rose-600',
  green:  'checked:accent-green-600',
  purple: 'checked:accent-purple-600',
}

export default function StressCheckFormPage() {
  const { id: periodId } = useParams<{ id: string }>()
  const router = useRouter()
  const [responseId, setResponseId] = useState<string | null>(null)
  const [answers, setAnswers] = useState<Record<string, number>>({})
  const [saveMsg, setSaveMsg] = useState('')
  const [validationError, setValidationError] = useState('')
  const [submitted, setSubmitted] = useState(false)

  // ===== 回答開始: レコードの作成 or 取得 =====
  const startMutation = useMutation({
    mutationFn: () =>
      api.post('/api/v1/stress-check/responses/start/', { period_id: periodId }),
    onSuccess: (res) => {
      const data: StressCheckResponse = res.data
      setResponseId(data.id)
      setAnswers(data.answers ?? {})
      if (data.is_submitted) setSubmitted(true)
    },
  })

  useEffect(() => {
    if (periodId) startMutation.mutate()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [periodId])

  // ===== 質問一覧の取得（レスポンスから） =====
  const { data: responseData } = useQuery<StressCheckResponse>({
    queryKey: ['stress-check-response', responseId],
    queryFn: () =>
      api.get(`/api/v1/stress-check/responses/${responseId}/`).then((r) => r.data),
    enabled: !!responseId,
  })

  const questions: Question[] = responseData?.questions ?? []

  // セクション別にグループ化
  const sections = Object.keys(SECTION_LABELS)
  const questionsBySection = sections.reduce((acc, section) => {
    acc[section] = questions.filter((q) => q.section === section)
    return acc
  }, {} as Record<string, Question[]>)

  // ===== 途中保存 =====
  const saveMutation = useMutation({
    mutationFn: () =>
      api.patch(`/api/v1/stress-check/responses/${responseId}/save/`, { answers }),
    onSuccess: () => {
      setSaveMsg('保存しました')
      setTimeout(() => setSaveMsg(''), 2000)
    },
  })

  // ===== 最終提出 =====
  const submitMutation = useMutation({
    mutationFn: () =>
      api.post(`/api/v1/stress-check/responses/${responseId}/submit/`, { answers }),
    onSuccess: () => {
      setSubmitted(true)
    },
  })

  const handleAnswer = (questionOrder: number, value: number) => {
    setAnswers((prev) => ({ ...prev, [String(questionOrder)]: value }))
    setValidationError('')
  }

  const handleSubmit = () => {
    const answeredCount = Object.keys(answers).length
    if (answeredCount < questions.length) {
      setValidationError(
        `全57問に回答してください（未回答: ${questions.length - answeredCount}問）`
      )
      // 未回答の最初の問にスクロール
      const firstUnanswered = questions.find((q) => !answers[String(q.order)])
      if (firstUnanswered) {
        document.getElementById(`q-${firstUnanswered.order}`)?.scrollIntoView({
          behavior: 'smooth',
          block: 'center',
        })
      }
      return
    }
    submitMutation.mutate()
  }

  const answeredCount = Object.keys(answers).length
  const totalQuestions = questions.length
  const progress = totalQuestions > 0 ? Math.round((answeredCount / totalQuestions) * 100) : 0

  // ===== 提出完了画面 =====
  if (submitted) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] p-6">
        <div className="bg-white rounded-2xl shadow-lg p-10 text-center max-w-md w-full">
          <CheckCircle2 className="w-16 h-16 text-green-500 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-gray-900 mb-2">提出完了</h2>
          <p className="text-gray-500 mb-6">
            ストレスチェックへのご回答ありがとうございました。<br />
            結果は人事担当者が確認します。
          </p>
          <button
            onClick={() => router.push('/stress-check')}
            className="flex items-center gap-2 mx-auto px-6 py-3 bg-rose-500 hover:bg-rose-600 text-white rounded-lg font-medium"
          >
            一覧に戻る
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    )
  }

  // ===== ローディング =====
  if (startMutation.isPending || !responseId || questions.length === 0) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-rose-500" />
      </div>
    )
  }

  return (
    <div className="p-6 max-w-3xl mx-auto pb-32">
      {/* ヘッダー */}
      <div className="flex items-center gap-3 mb-2">
        <HeartPulse className="w-7 h-7 text-rose-500" />
        <h1 className="text-2xl font-bold text-gray-900">ストレスチェック</h1>
      </div>
      <p className="text-sm text-gray-500 mb-6">
        各質問について、最もあてはまるものを選んでください。全57問必須です。
      </p>

      {/* プログレスバー */}
      <div className="bg-white border rounded-xl p-4 mb-6 shadow-sm">
        <div className="flex justify-between text-sm text-gray-600 mb-2">
          <span>回答進捗</span>
          <span className="font-medium">{answeredCount} / {totalQuestions} 問</span>
        </div>
        <div className="h-2.5 bg-gray-100 rounded-full overflow-hidden">
          <div
            className="h-full bg-rose-500 rounded-full transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>
        <p className="text-right text-xs text-gray-400 mt-1">{progress}%</p>
      </div>

      {/* バリデーションエラー */}
      {validationError && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 text-red-600 rounded-xl text-sm">
          {validationError}
        </div>
      )}

      {/* セクション別質問 */}
      {sections.map((section) => {
        const sectionQuestions = questionsBySection[section] ?? []
        if (sectionQuestions.length === 0) return null
        const meta = SECTION_LABELS[section]
        const colorClass = SECTION_COLOR_MAP[meta.color]
        const radioColor = RADIO_COLOR_MAP[meta.color]

        return (
          <div key={section} className="mb-8">
            {/* セクションヘッダー */}
            <div className={`border rounded-xl px-5 py-3 mb-4 ${colorClass}`}>
              <h2 className="font-bold text-base">{meta.label}</h2>
              <p className="text-xs mt-0.5 opacity-80">{meta.description}</p>
            </div>

            {/* 問一覧 */}
            <div className="space-y-3">
              {sectionQuestions.map((q) => {
                const isAnswered = answers[String(q.order)] !== undefined
                return (
                  <div
                    key={q.order}
                    id={`q-${q.order}`}
                    className={`bg-white border rounded-xl p-5 shadow-sm transition-all ${
                      isAnswered ? 'border-gray-200' : 'border-amber-300'
                    }`}
                  >
                    <p className="text-sm font-medium text-gray-800 mb-4">
                      <span className="text-gray-400 mr-2">Q{q.order}.</span>
                      {q.text}
                    </p>
                    <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
                      {CHOICES.map((choice) => {
                        const selected = answers[String(q.order)] === choice.value
                        return (
                          <label
                            key={choice.value}
                            className={`flex items-center gap-2 p-3 rounded-lg border cursor-pointer text-sm transition-all ${
                              selected
                                ? 'border-rose-400 bg-rose-50 text-rose-700 font-medium'
                                : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50 text-gray-600'
                            }`}
                          >
                            <input
                              type="radio"
                              name={`q-${q.order}`}
                              value={choice.value}
                              checked={selected}
                              onChange={() => handleAnswer(q.order, choice.value)}
                              className={`shrink-0 ${radioColor}`}
                            />
                            {choice.label}
                          </label>
                        )
                      })}
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        )
      })}

      {/* 固定フッター: 途中保存・提出ボタン */}
      <div className="fixed bottom-0 left-0 right-0 bg-white border-t shadow-lg px-6 py-4 z-40">
        <div className="max-w-3xl mx-auto flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <button
              onClick={() => saveMutation.mutate()}
              disabled={saveMutation.isPending || answeredCount === 0}
              className="flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg text-sm text-gray-700 hover:bg-gray-50 disabled:opacity-40"
            >
              <Save className="w-4 h-4" />
              {saveMutation.isPending ? '保存中...' : '途中保存'}
            </button>
            {saveMsg && (
              <span className="text-sm text-green-600 font-medium">{saveMsg}</span>
            )}
          </div>
          <div className="flex items-center gap-3">
            <span className="text-sm text-gray-500">
              {answeredCount}/{totalQuestions}問 回答済み
            </span>
            <button
              onClick={handleSubmit}
              disabled={submitMutation.isPending}
              className="flex items-center gap-2 px-6 py-2 bg-rose-500 hover:bg-rose-600 text-white rounded-lg text-sm font-medium disabled:opacity-50"
            >
              <CheckCircle2 className="w-4 h-4" />
              {submitMutation.isPending ? '提出中...' : '最終提出'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
