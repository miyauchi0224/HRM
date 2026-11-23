'use client'
import { toast } from '@/lib/toast'
import { useState } from 'react'
import Link from 'next/link'
import { useParams, useRouter, useSearchParams } from 'next/navigation'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'
import { ArrowLeft, Lock } from 'lucide-react'
import type { PulseSurvey } from '../page'

interface QuestionResult {
  id: string
  text: string
  kind: 'scale5' | 'enps' | 'text'
  answer_count: number
  average?: number | null
  enps?: number | null
  promoters?: number
  passives?: number
  detractors?: number
  distribution?: Record<string, number>
  comments?: string[]
}

interface Results {
  response_count: number
  min_group_size: number
  insufficient: boolean
  questions: QuestionResult[]
  departments: { department: string; insufficient?: boolean; response_count?: number; averages?: Record<string, number | null> }[]
}

/** パルスサーベイの回答（全社員）と集計（人事。?view=results） */
export default function PulseSurveyPage() {
  const { id } = useParams<{ id: string }>()
  const view   = useSearchParams().get('view')
  const { data: survey, isLoading } = useQuery<PulseSurvey>({
    queryKey: ['pulse-survey', id],
    queryFn: () => api.get(`/api/v1/pulse/surveys/${id}/`).then((r) => r.data),
  })

  if (isLoading || !survey) return <p className="text-gray-400 text-sm">読み込み中...</p>

  return (
    <div className="max-w-2xl">
      <Link href="/pulse" className="text-sm text-gray-500 flex items-center gap-1 mb-4">
        <ArrowLeft size={14} /> 一覧へ
      </Link>
      <h1 className="text-2xl font-bold text-gray-800">{survey.title}</h1>
      <p className="text-sm text-gray-500 mt-1 mb-6 flex items-center gap-1">
        {survey.is_anonymous && <Lock size={13} />}
        {survey.start_date} 〜 {survey.end_date}・{survey.is_anonymous ? '匿名（回答者は記録されません）' : '記名'}
      </p>
      {view === 'results' ? <ResultsView id={id} survey={survey} /> : <AnswerForm survey={survey} />}
    </div>
  )
}

function AnswerForm({ survey }: { survey: PulseSurvey }) {
  const router = useRouter()
  const qc     = useQueryClient()
  const [answers, setAnswers] = useState<Record<string, number | string>>({})
  const [saving, setSaving]   = useState(false)

  if (survey.has_answered) {
    return <p className="bg-green-50 text-green-700 rounded-xl p-5">回答ありがとうございました。</p>
  }

  const missing = survey.questions.filter((q) => q.is_required && (answers[q.id] === undefined || answers[q.id] === ''))
  const submit = async () => {
    setSaving(true)
    try {
      await api.post(`/api/v1/pulse/surveys/${survey.id}/answer/`, { answers })
      qc.invalidateQueries({ queryKey: ['pulse-surveys'] })
      qc.invalidateQueries({ queryKey: ['pulse-survey', survey.id] })
      router.push('/pulse')
    } catch (e: any) {
      toast.error(e.response?.data?.error ?? '送信に失敗しました')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="space-y-4">
      {survey.questions.map((q, i) => (
        <div key={q.id} className="bg-white rounded-xl border border-gray-200 p-5">
          <p className="font-medium text-gray-800 mb-3">
            Q{i + 1}. {q.text}{q.is_required && <span className="text-red-500 ml-1">*</span>}
          </p>
          {q.kind === 'text' ? (
            <textarea rows={3} value={(answers[q.id] as string) ?? ''}
                      onChange={(e) => setAnswers({ ...answers, [q.id]: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm resize-none" />
          ) : (
            <>
              <div className="flex flex-wrap gap-1.5">
                {(q.kind === 'scale5' ? [1, 2, 3, 4, 5] : Array.from({ length: 11 }, (_, n) => n)).map((n) => (
                  <button key={n} onClick={() => setAnswers({ ...answers, [q.id]: n })}
                          className={`w-10 h-10 rounded-lg border text-sm font-medium ${
                            answers[q.id] === n ? 'bg-blue-600 text-white border-blue-600' : 'border-gray-300 text-gray-600 hover:bg-gray-50'
                          }`}>
                    {n}
                  </button>
                ))}
              </div>
              <div className="flex justify-between text-xs text-gray-400 mt-1">
                <span>{q.kind === 'scale5' ? 'そう思わない' : 'すすめない'}</span>
                <span>{q.kind === 'scale5' ? 'そう思う' : 'ぜひすすめたい'}</span>
              </div>
            </>
          )}
        </div>
      ))}
      <button onClick={submit} disabled={saving || missing.length > 0}
              className="w-full py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white rounded-xl font-medium">
        {saving ? '送信中...' : missing.length > 0 ? `未回答の必須質問があります（${missing.length}問）` : '回答を送信'}
      </button>
    </div>
  )
}

function ResultsView({ id, survey }: { id: string; survey: PulseSurvey }) {
  const { data, isLoading, error } = useQuery<Results>({
    queryKey: ['pulse-results', id],
    queryFn: () => api.get(`/api/v1/pulse/surveys/${id}/results/`).then((r) => r.data),
  })
  if (isLoading) return <p className="text-gray-400 text-sm">集計中...</p>
  if (error || !data) return <p className="text-red-500 text-sm">集計を表示する権限がありません</p>
  if (data.insufficient) {
    return (
      <p className="bg-gray-50 rounded-xl p-5 text-sm text-gray-600">
        回答が {data.response_count} 件のため集計を表示できません（回答者を特定されないよう、{data.min_group_size} 件以上で表示します）。
      </p>
    )
  }

  const numeric = data.questions.filter((q) => q.kind !== 'text')
  return (
    <div className="space-y-4">
      <p className="text-sm text-gray-600">回答数 {data.response_count} 件</p>
      {data.questions.map((q) => (
        <div key={q.id} className="bg-white rounded-xl border border-gray-200 p-5">
          <p className="font-medium text-gray-800 mb-3">{q.text}</p>
          {q.kind === 'text' ? (
            q.comments && q.comments.length > 0 ? (
              <ul className="space-y-2">
                {q.comments.map((c, i) => <li key={i} className="text-sm text-gray-700 bg-gray-50 rounded-lg px-3 py-2">{c}</li>)}
              </ul>
            ) : <p className="text-sm text-gray-400">回答なし</p>
          ) : (
            <>
              <p className="text-sm text-gray-600 mb-2">
                {q.kind === 'enps'
                  ? <>eNPS <span className="text-2xl font-bold text-gray-800 mx-1">{q.enps}</span>（推奨 {q.promoters}・中立 {q.passives}・批判 {q.detractors}）</>
                  : <>平均 <span className="text-2xl font-bold text-gray-800 mx-1">{q.average}</span> / 5</>}
              </p>
              <Distribution dist={q.distribution ?? {}} />
            </>
          )}
        </div>
      ))}

      {numeric.length > 0 && data.departments.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-5 overflow-x-auto">
          <p className="font-medium text-gray-800 mb-3">部署別の平均</p>
          <table className="w-full text-sm">
            <thead>
              <tr className="text-xs text-gray-400 border-b border-gray-100">
                <th className="text-left py-2 pr-3 font-medium">部署</th>
                {numeric.map((q, i) => <th key={q.id} className="text-right py-2 px-2 font-medium" title={q.text}>Q{i + 1}</th>)}
              </tr>
            </thead>
            <tbody>
              {data.departments.map((d) => (
                <tr key={d.department} className="border-b border-gray-50">
                  <td className="py-2 pr-3 text-gray-700">{d.department}</td>
                  {d.insufficient ? (
                    <td colSpan={numeric.length} className="py-2 px-2 text-right text-xs text-gray-400">
                      回答数が少ないため非表示
                    </td>
                  ) : numeric.map((q) => (
                    <td key={q.id} className="py-2 px-2 text-right text-gray-700">{d.averages?.[q.id] ?? '—'}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

function Distribution({ dist }: { dist: Record<string, number> }) {
  const max = Math.max(1, ...Object.values(dist))
  return (
    <div className="flex items-end gap-1 h-20">
      {Object.entries(dist).map(([k, v]) => (
        <div key={k} className="flex-1 flex flex-col items-center gap-1">
          <div className="w-full bg-blue-500 rounded-t" style={{ height: `${(v / max) * 60}px` }} title={`${k}: ${v}件`} />
          <span className="text-[10px] text-gray-400">{k}</span>
        </div>
      ))}
    </div>
  )
}
