'use client'
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'
import { useAuthStore } from '@/lib/store'
import { Star, Plus, Send } from 'lucide-react'

interface EvalPeriod { id: string; fiscal_year: number; period_type: string }
interface EvalQuestion { id: string; category: string; text: string }
interface Evaluation {
  id: string; period: string; subject_name: string; evaluator_name: string
  evaluator_type: string; is_submitted: boolean; scores: Array<{ question: string; question_text: string; score: number; comment: string }>
}

const EVAL_TYPE: Record<string, string> = {
  self: '自己評価', supervisor: '上司評価', peer: '同僚評価', subordinate: '部下評価'
}
const CATEGORY: Record<string, string> = {
  performance: '業績評価', competency: 'コンピテンシー', attitude: '行動・姿勢'
}

export default function EvaluationPage() {
  const user = useAuthStore((s) => s.user)
  const qc = useQueryClient()
  const [showNew, setShowNew] = useState(false)
  const [selectedEval, setSelectedEval] = useState<Evaluation | null>(null)
  const [scores, setScores] = useState<Record<string, { score: number; comment: string }>>({})

  const { data: periods = [] } = useQuery<EvalPeriod[]>({
    queryKey: ['eval-periods'],
    queryFn: () => api.get('/api/v1/evaluation/periods/').then((r) => r.data.results ?? r.data),
  })

  const { data: questions = [] } = useQuery<EvalQuestion[]>({
    queryKey: ['eval-questions'],
    queryFn: () => api.get('/api/v1/evaluation/questions/').then((r) => r.data.results ?? r.data),
  })

  const { data: evaluations = [], isLoading } = useQuery<Evaluation[]>({
    queryKey: ['evaluations'],
    queryFn: () => api.get('/api/v1/evaluation/evaluations/').then((r) => r.data.results ?? r.data),
  })

  const submitMut = useMutation({
    mutationFn: (id: string) => api.post(`/api/v1/evaluation/evaluations/${id}/submit/`),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['evaluations'] }); setSelectedEval(null) },
  })

  const saveMut = useMutation({
    mutationFn: ({ id, scores: s }: any) =>
      api.patch(`/api/v1/evaluation/evaluations/${id}/`, {
        scores: Object.entries(s).map(([qid, data]: any) => ({
          question: qid, score: data.score, comment: data.comment
        }))
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['evaluations'] }),
  })

  const pending = evaluations.filter((e) => !e.is_submitted)
  const submitted = evaluations.filter((e) => e.is_submitted)

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <Star className="text-indigo-600" size={28} />
          <div>
            <h1 className="text-2xl font-bold text-gray-800">360度評価</h1>
            <p className="text-sm text-gray-500">上司・同僚・部下からの多面評価</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-4 mb-6">
        {[
          { label: '全評価数', value: evaluations.length },
          { label: '未提出', value: pending.length },
          { label: '提出済', value: submitted.length },
        ].map((item) => (
          <div key={item.label} className="bg-white rounded-xl border shadow-sm p-4 text-center">
            <p className="text-3xl font-bold text-gray-800">{item.value}</p>
            <p className="text-sm text-gray-500 mt-1">{item.label}</p>
          </div>
        ))}
      </div>

      {/* 未提出の評価 */}
      {pending.length > 0 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-4 mb-6">
          <h2 className="font-semibold text-yellow-800 mb-3 text-sm">未提出の評価 ({pending.length}件)</h2>
          <div className="space-y-2">
            {pending.map((ev) => (
              <div key={ev.id} className="bg-white rounded-lg border border-yellow-100 p-3 flex items-center justify-between">
                <div>
                  <p className="font-medium text-gray-800 text-sm">評価対象: {ev.subject_name}</p>
                  <p className="text-xs text-gray-500">{EVAL_TYPE[ev.evaluator_type]}</p>
                </div>
                <button
                  onClick={() => {
                    setSelectedEval(ev)
                    const init: Record<string, { score: number; comment: string }> = {}
                    ev.scores.forEach((s) => { init[s.question] = { score: s.score, comment: s.comment } })
                    questions.forEach((q) => { if (!init[q.id]) init[q.id] = { score: 3, comment: '' } })
                    setScores(init)
                  }}
                  className="text-xs bg-indigo-600 text-white px-3 py-1.5 rounded-lg hover:bg-indigo-700"
                >
                  評価入力
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 提出済 */}
      <div className="bg-white rounded-xl border shadow-sm overflow-hidden">
        <div className="px-5 py-3 border-b bg-gray-50">
          <h2 className="font-semibold text-gray-700 text-sm">提出済評価一覧</h2>
        </div>
        {isLoading ? (
          <div className="p-6 text-center text-gray-400">読み込み中...</div>
        ) : submitted.length === 0 ? (
          <div className="p-8 text-center text-gray-400 text-sm">提出済の評価はありません</div>
        ) : (
          <table className="w-full text-sm">
            <thead className="text-xs text-gray-500 bg-gray-50 uppercase">
              <tr>
                <th className="px-4 py-3 text-left">評価対象者</th>
                <th className="px-4 py-3 text-left">評価種別</th>
                <th className="px-4 py-3 text-left">評価者</th>
                <th className="px-4 py-3 text-center">平均スコア</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {submitted.map((ev) => {
                const avg = ev.scores.length > 0
                  ? (ev.scores.reduce((s, sc) => s + sc.score, 0) / ev.scores.length).toFixed(1)
                  : '-'
                return (
                  <tr key={ev.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 font-medium text-gray-800">{ev.subject_name}</td>
                    <td className="px-4 py-3 text-gray-600">{EVAL_TYPE[ev.evaluator_type]}</td>
                    <td className="px-4 py-3 text-gray-600">{ev.evaluator_name}</td>
                    <td className="px-4 py-3 text-center">
                      <div className="flex items-center justify-center gap-1">
                        <Star size={14} className="text-yellow-400 fill-yellow-400" />
                        <span className="font-bold text-gray-800">{avg}</span>
                        <span className="text-gray-400 text-xs">/5</span>
                      </div>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        )}
      </div>

      {/* 評価入力モーダル */}
      {selectedEval && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-2xl p-6 max-h-[90vh] overflow-y-auto">
            <h2 className="text-lg font-bold text-gray-800 mb-1">
              {selectedEval.subject_name} への {EVAL_TYPE[selectedEval.evaluator_type]}
            </h2>
            <p className="text-sm text-gray-500 mb-4">各項目を1〜5で評価してください</p>
            <div className="space-y-4">
              {questions.map((q) => (
                <div key={q.id} className="bg-gray-50 rounded-lg p-4">
                  <p className="text-sm font-medium text-gray-700 mb-2">
                    <span className="text-xs bg-indigo-100 text-indigo-600 px-1.5 py-0.5 rounded mr-2">
                      {CATEGORY[q.category]}
                    </span>
                    {q.text}
                  </p>
                  <div className="flex gap-2 mb-2">
                    {[1, 2, 3, 4, 5].map((n) => (
                      <button
                        key={n}
                        onClick={() => setScores((prev) => ({ ...prev, [q.id]: { ...prev[q.id], score: n } }))}
                        className={`w-9 h-9 rounded-lg text-sm font-bold transition-colors ${
                          scores[q.id]?.score === n
                            ? 'bg-indigo-600 text-white'
                            : 'bg-white border text-gray-600 hover:bg-indigo-50'
                        }`}
                      >{n}</button>
                    ))}
                  </div>
                  <input
                    className="w-full border rounded px-2 py-1 text-xs"
                    placeholder="コメント（任意）"
                    value={scores[q.id]?.comment ?? ''}
                    onChange={(e) => setScores((prev) => ({ ...prev, [q.id]: { ...prev[q.id], comment: e.target.value } }))}
                  />
                </div>
              ))}
            </div>
            <div className="flex gap-3 mt-6">
              <button onClick={() => setSelectedEval(null)} className="flex-1 border text-gray-700 py-2 rounded-lg text-sm">閉じる</button>
              <button
                onClick={() => saveMut.mutate({ id: selectedEval.id, scores })}
                className="flex-1 border border-indigo-600 text-indigo-600 py-2 rounded-lg text-sm hover:bg-indigo-50"
              >保存</button>
              <button
                onClick={() => { saveMut.mutate({ id: selectedEval.id, scores }); submitMut.mutate(selectedEval.id) }}
                className="flex-1 bg-indigo-600 text-white py-2 rounded-lg text-sm hover:bg-indigo-700 flex items-center justify-center gap-2"
              ><Send size={14} /> 提出</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
