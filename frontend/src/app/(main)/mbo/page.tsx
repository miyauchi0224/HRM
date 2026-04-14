'use client'
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'
import { useAuthStore } from '@/lib/store'
import { Target, Plus, ChevronDown, ChevronRight, Send, Star, CheckCircle, Pencil } from 'lucide-react'

// ===== 型定義 =====
interface MBOGoal {
  id: string
  year: number
  period: 'first_half' | 'second_half'
  title: string
  target_level: string
  weight: number
  self_score: string | null
  manager_score: string | null
  status: 'draft' | 'submitted' | 'approved' | 'evaluated'
  employee_name: string
  reports: MBOReport[]
}

interface MBOReport {
  id: string
  goal: string
  month: string
  action_content: string
  result: string
  manager_comment: string
  ai_suggestion: string
  status: 'draft' | 'submitted' | 'commented'
}

const STATUS_LABEL: Record<string, { label: string; color: string }> = {
  draft:     { label: '下書き', color: 'bg-gray-100 text-gray-600' },
  submitted: { label: '提出済（承認待ち）', color: 'bg-yellow-100 text-yellow-700' },
  approved:  { label: '承認済', color: 'bg-green-100 text-green-700' },
  evaluated: { label: '評価済', color: 'bg-purple-100 text-purple-700' },
}

const PERIOD_LABEL: Record<string, string> = {
  first_half: '上期',
  second_half: '下期',
}

export default function MboPage() {
  const currentYear = new Date().getFullYear()
  const [year, setYear]     = useState(currentYear)
  const [period, setPeriod] = useState<'first_half' | 'second_half'>(
    new Date().getMonth() < 9 ? 'first_half' : 'second_half'
  )
  const [showNewGoal, setShowNewGoal] = useState(false)
  const qc   = useQueryClient()
  const user = useAuthStore((s) => s.user)
  const isManager = user?.role !== 'employee'

  const { data: goals = [], isLoading } = useQuery<MBOGoal[]>({
    queryKey: ['mbo-goals', year, period],
    queryFn: () =>
      api.get(`/api/v1/mbo/goals/?year=${year}&period=${period}`).then((r) => r.data.results ?? r.data),
  })

  const totalWeight = goals.reduce((sum, g) => sum + g.weight, 0)

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
          <Target size={22} /> MBO 目標管理
        </h1>
        <button
          onClick={() => setShowNewGoal(true)}
          className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
        >
          <Plus size={16} /> 目標を追加
        </button>
      </div>

      {/* フィルター */}
      <div className="flex gap-3 mb-6">
        <select
          value={year}
          onChange={(e) => setYear(Number(e.target.value))}
          className="px-3 py-2 border border-gray-300 rounded-lg text-sm"
        >
          {[currentYear - 1, currentYear, currentYear + 1].map((y) => (
            <option key={y} value={y}>{y}年度</option>
          ))}
        </select>
        <div className="flex rounded-lg border border-gray-300 overflow-hidden">
          {(['first_half', 'second_half'] as const).map((p) => (
            <button
              key={p}
              onClick={() => setPeriod(p)}
              className={`px-4 py-2 text-sm font-medium transition-colors ${
                period === p ? 'bg-blue-600 text-white' : 'bg-white text-gray-600 hover:bg-gray-50'
              }`}
            >
              {PERIOD_LABEL[p]}
            </button>
          ))}
        </div>
      </div>

      {/* ウェイト合計 */}
      <div className="mb-4 space-y-1">
        <div className="flex items-center gap-3">
          <div className="flex-1 bg-gray-200 rounded-full h-2">
            <div
              className={`h-2 rounded-full transition-all ${
                totalWeight > 100 ? 'bg-red-500' : totalWeight === 100 ? 'bg-green-500' : 'bg-blue-500'
              }`}
              style={{ width: `${Math.min(totalWeight, 100)}%` }}
            />
          </div>
          <span className={`text-sm font-medium shrink-0 ${
            totalWeight > 100 ? 'text-red-600' : totalWeight === 100 ? 'text-green-600' : 'text-gray-600'
          }`}>
            ウェイト合計 {totalWeight}%
          </span>
        </div>
        {totalWeight < 100 && goals.length > 0 && !isLoading && (
          <p className="text-xs text-yellow-600 bg-yellow-50 border border-yellow-200 rounded-lg px-3 py-1.5">
            ⚠ ウェイト合計が 100% になるまで申請できません（残り {100 - totalWeight}%）
          </p>
        )}
      </div>

      {/* 目標一覧 */}
      {isLoading ? (
        <p className="text-gray-400 text-sm">読み込み中...</p>
      ) : goals.length === 0 ? (
        <div className="bg-white rounded-xl border border-dashed border-gray-300 p-12 text-center">
          <Target size={32} className="mx-auto text-gray-300 mb-3" />
          <p className="text-gray-400 text-sm">この期の目標はまだ設定されていません</p>
          <button
            onClick={() => setShowNewGoal(true)}
            className="mt-4 text-blue-600 hover:underline text-sm"
          >
            ＋ 最初の目標を追加する
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {goals.map((goal) => (
            <GoalCard
              key={goal.id}
              goal={goal}
              isManager={isManager}
              totalWeight={totalWeight}
              onUpdate={() => qc.invalidateQueries({ queryKey: ['mbo-goals'] })}
            />
          ))}
        </div>
      )}

      {/* 新規目標モーダル */}
      {showNewGoal && (
        <NewGoalModal
          year={year}
          period={period}
          onClose={() => setShowNewGoal(false)}
          onSaved={() => {
            setShowNewGoal(false)
            qc.invalidateQueries({ queryKey: ['mbo-goals'] })
          }}
        />
      )}
    </div>
  )
}

// ===== 目標カード =====
function GoalCard({ goal, isManager, totalWeight, onUpdate }: { goal: MBOGoal; isManager: boolean; totalWeight: number; onUpdate: () => void }) {
  const [open, setOpen]             = useState(false)
  const [selfScore, setSelfScore]   = useState(goal.self_score ?? '')
  const [submitting, setSubmitting] = useState(false)
  const [approving, setApproving]   = useState(false)
  // インライン編集
  const [editingGoal, setEditingGoal] = useState(false)
  const [editTitle, setEditTitle]     = useState(goal.title)
  const [editTarget, setEditTarget]   = useState(goal.target_level)
  const [editWeight, setEditWeight]   = useState(goal.weight)
  const [savingGoal, setSavingGoal]   = useState(false)
  const qc = useQueryClient()

  const saveGoalEdit = async () => {
    setSavingGoal(true)
    try {
      await api.patch(`/api/v1/mbo/goals/${goal.id}/`, {
        title: editTitle, target_level: editTarget, weight: editWeight,
      })
      setEditingGoal(false)
      onUpdate()
    } catch (e: any) {
      alert(e.response?.data?.error ?? '更新に失敗しました')
    } finally { setSavingGoal(false) }
  }

  const submitGoal = async () => {
    setSubmitting(true)
    try {
      await api.patch(`/api/v1/mbo/goals/${goal.id}/submit/`)
      onUpdate()
    } finally {
      setSubmitting(false)
    }
  }

  const approveGoal = async () => {
    setApproving(true)
    try {
      await api.patch(`/api/v1/mbo/goals/${goal.id}/approve/`)
      onUpdate()
    } finally {
      setApproving(false)
    }
  }

  const saveSelfScore = async () => {
    await api.patch(`/api/v1/mbo/goals/${goal.id}/`, { self_score: selfScore })
    onUpdate()
  }

  const st = STATUS_LABEL[goal.status]

  return (
    <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
      {/* ヘッダー */}
      <div
        className="flex items-center gap-3 p-5 cursor-pointer hover:bg-gray-50"
        onClick={() => setOpen(!open)}
      >
        <button className="text-gray-400">
          {open ? <ChevronDown size={18} /> : <ChevronRight size={18} />}
        </button>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${st.color}`}>
              {st.label}
            </span>
            <span className="text-xs text-gray-400">ウェイト {goal.weight}%</span>
          </div>
          <p className="font-medium text-gray-800 truncate">{goal.title}</p>
        </div>
        <div className="text-right shrink-0">
          <p className="text-xs text-gray-400">自己評価</p>
          <p className="font-semibold text-gray-700">{goal.self_score ?? '—'}</p>
          {goal.manager_score && (
            <>
              <p className="text-xs text-gray-400 mt-1">上司評価</p>
              <p className="font-semibold text-purple-600">{goal.manager_score}</p>
            </>
          )}
        </div>
      </div>

      {/* 展開エリア */}
      {open && (
        <div className="border-t border-gray-100 p-5 space-y-5">
          {/* 目標詳細 */}
          {goal.target_level && (
            <div>
              <p className="text-xs font-medium text-gray-500 mb-1">達成水準</p>
              <p className="text-sm text-gray-700 whitespace-pre-wrap">{goal.target_level}</p>
            </div>
          )}

          {/* 下書き：インライン編集 */}
          {goal.status === 'draft' && !isManager && (
            <div className="bg-gray-50 rounded-lg p-4">
              {editingGoal ? (
                <div className="space-y-3">
                  <div>
                    <label className="text-xs text-gray-500 block mb-1">目標タイトル</label>
                    <input value={editTitle} onChange={(e) => setEditTitle(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm" />
                  </div>
                  <div>
                    <label className="text-xs text-gray-500 block mb-1">
                      達成水準 <span className="text-blue-500">（定量的に記述：例「売上を前期比120%にする」「資格を3つ取得する」）</span>
                    </label>
                    <textarea value={editTarget} onChange={(e) => setEditTarget(e.target.value)}
                      rows={3} className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm resize-none" />
                  </div>
                  <div>
                    <label className="text-xs text-gray-500 block mb-1">ウェイト（%）</label>
                    <input type="number" min={1} max={100} value={editWeight}
                      onChange={(e) => setEditWeight(Number(e.target.value))}
                      className="w-32 px-3 py-2 border border-gray-300 rounded-lg text-sm" />
                  </div>
                  <div className="flex gap-2">
                    <button onClick={saveGoalEdit} disabled={savingGoal || !editTitle.trim()}
                      className="px-3 py-1.5 bg-blue-600 text-white text-xs rounded-lg font-medium disabled:opacity-40">
                      {savingGoal ? '保存中...' : '保存'}
                    </button>
                    <button onClick={() => setEditingGoal(false)}
                      className="px-3 py-1.5 bg-gray-200 text-gray-600 text-xs rounded-lg">キャンセル</button>
                  </div>
                </div>
              ) : (
                <div className="flex items-center justify-between">
                  <p className="text-xs text-gray-500">下書き中 — 申請前に内容を編集できます</p>
                  <button onClick={() => setEditingGoal(true)}
                    className="text-xs text-blue-600 hover:underline flex items-center gap-1">
                    <Pencil size={11} /> 編集
                  </button>
                </div>
              )}
            </div>
          )}

          {/* 管理職：承認ボタン */}
          {isManager && goal.status === 'submitted' && (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-yellow-800">承認待ちの目標があります</p>
                <p className="text-xs text-yellow-600 mt-0.5">{goal.employee_name}さんが目標を提出しました</p>
              </div>
              <button
                onClick={approveGoal}
                disabled={approving}
                className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-green-300 text-white text-sm rounded-lg font-medium"
              >
                <CheckCircle size={15} /> {approving ? '処理中...' : '承認する'}
              </button>
            </div>
          )}

          {/* 自己評価 + 提出 */}
          {goal.status === 'draft' && totalWeight !== 100 && (
            <p className="text-xs text-yellow-600 bg-yellow-50 border border-yellow-200 rounded-lg px-3 py-2">
              ウェイト合計を 100% にしてから申請してください（現在 {totalWeight}%）
            </p>
          )}
          {goal.status === 'draft' && (
            <div className="flex gap-3 items-end">
              <div className="flex-1">
                <label className="text-xs font-medium text-gray-500 block mb-1">
                  自己評価スコア（0〜5）
                </label>
                <input
                  type="number"
                  min={0} max={5} step={0.1}
                  value={selfScore}
                  onChange={(e) => setSelfScore(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                  placeholder="例: 4.0"
                />
              </div>
              <button
                onClick={saveSelfScore}
                className="px-4 py-2 text-sm bg-gray-100 hover:bg-gray-200 rounded-lg font-medium transition-colors"
              >
                保存
              </button>
              <button
                onClick={submitGoal}
                disabled={submitting || totalWeight !== 100}
                className="flex items-center gap-2 px-4 py-2 text-sm bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white rounded-lg font-medium transition-colors"
                title={totalWeight !== 100 ? `ウェイト合計が${totalWeight}%です。100%にしてから提出してください` : ''}
              >
                <Send size={14} /> {submitting ? '送信中...' : '提出'}
              </button>
            </div>
          )}

          {/* 月間報告一覧 */}
          <div>
            <p className="text-xs font-medium text-gray-500 mb-3">月間報告</p>
            {goal.reports.length === 0 ? (
              <p className="text-xs text-gray-400">月間報告がありません</p>
            ) : (
              <div className="space-y-3">
                {goal.reports.map((r) => (
                  <ReportCard key={r.id} report={r} onUpdate={onUpdate} />
                ))}
              </div>
            )}
            {/* 承認済みまたは評価済みの場合のみ月報追加可能 */}
            {(goal.status === 'approved' || goal.status === 'evaluated') ? (
              <NewReportForm goalId={goal.id} onSaved={onUpdate} />
            ) : (
              goal.status !== 'draft' && (
                <p className="mt-3 text-xs text-gray-400">
                  ※ 目標が承認されると月間報告を追加できます
                </p>
              )
            )}
          </div>
        </div>
      )}
    </div>
  )
}

// ===== 月間報告カード =====
function ReportCard({ report, onUpdate }: { report: MBOReport; onUpdate: () => void }) {
  const [editing, setEditing]     = useState(false)
  const [action, setAction]       = useState(report.action_content)
  const [result, setResult]       = useState(report.result)
  const [saving, setSaving]       = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [aiLoading, setAiLoading] = useState(false)
  const [aiText, setAiText]       = useState(report.ai_suggestion)

  const submitReport = async () => {
    setSubmitting(true)
    try {
      await api.patch(`/api/v1/mbo/reports/${report.id}/submit/`)
      onUpdate()
    } catch {
      alert('申請に失敗しました')
    } finally {
      setSubmitting(false)
    }
  }

  const save = async () => {
    setSaving(true)
    try {
      await api.patch(`/api/v1/mbo/reports/${report.id}/`, { action_content: action, result })
      setEditing(false)
      onUpdate()
    } finally {
      setSaving(false)
    }
  }

  const requestAI = async () => {
    setAiLoading(true)
    try {
      const res = await api.post(`/api/v1/mbo/reports/${report.id}/ai-suggest/`)
      setAiText(res.data.ai_suggestion)
    } catch {
      alert('AI提案の取得に失敗しました')
    } finally {
      setAiLoading(false)
    }
  }

  return (
    <div className="bg-gray-50 rounded-lg p-4 text-sm">
      <div className="flex items-center justify-between mb-3">
        <span className="font-medium text-gray-700">
          {new Date(report.month).toLocaleDateString('ja-JP', { year: 'numeric', month: 'long' })}
        </span>
        {report.status === 'draft' && !editing && (
          <button
            onClick={() => setEditing(true)}
            className="text-xs text-blue-600 hover:underline"
          >
            編集
          </button>
        )}
      </div>

      {editing ? (
        <div className="space-y-3">
          <div>
            <label className="text-xs text-gray-500 block mb-1">行動内容</label>
            <textarea
              value={action}
              onChange={(e) => setAction(e.target.value)}
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm resize-none"
            />
          </div>
          <div>
            <label className="text-xs text-gray-500 block mb-1">結果・考察</label>
            <textarea
              value={result}
              onChange={(e) => setResult(e.target.value)}
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm resize-none"
            />
          </div>
          <div className="flex gap-2">
            <button
              onClick={save}
              disabled={saving}
              className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs rounded-lg font-medium"
            >
              {saving ? '保存中...' : '保存'}
            </button>
            <button
              onClick={() => setEditing(false)}
              className="px-3 py-1.5 bg-gray-200 hover:bg-gray-300 text-gray-700 text-xs rounded-lg"
            >
              キャンセル
            </button>
          </div>
        </div>
      ) : (
        <div className="space-y-2">
          {report.action_content && (
            <div>
              <p className="text-xs text-gray-400">行動内容</p>
              <p className="text-gray-700 whitespace-pre-wrap">{report.action_content}</p>
            </div>
          )}
          {report.result && (
            <div>
              <p className="text-xs text-gray-400">結果・考察</p>
              <p className="text-gray-700 whitespace-pre-wrap">{report.result}</p>
            </div>
          )}

          {/* AI提案 */}
          {aiText ? (
            <div className="bg-purple-50 border border-purple-200 rounded-lg p-3 mt-2">
              <p className="text-xs font-medium text-purple-600 mb-1">✦ AI フィードバック</p>
              <p className="text-xs text-gray-700 whitespace-pre-wrap">{aiText}</p>
            </div>
          ) : (
            <button
              onClick={requestAI}
              disabled={aiLoading || !report.action_content}
              className="mt-2 text-xs text-purple-600 hover:underline disabled:text-gray-400 disabled:no-underline"
            >
              {aiLoading ? 'AI分析中...' : '✦ AI フィードバックを取得'}
            </button>
          )}

          {/* 月報申請ボタン（下書き時のみ） */}
          {report.status === 'draft' && (
            <button
              onClick={submitReport}
              disabled={submitting || !report.action_content}
              className="mt-2 flex items-center gap-1 text-xs px-3 py-1.5 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white rounded-lg font-medium"
            >
              <Send size={12} /> {submitting ? '申請中...' : '上司に申請'}
            </button>
          )}
          {report.status === 'submitted' && (
            <p className="mt-2 text-xs text-yellow-600 font-medium">✓ 申請済み（承認待ち）</p>
          )}
          {report.status === 'commented' && (
            <p className="mt-2 text-xs text-green-600 font-medium">✓ コメント済み</p>
          )}

          {/* 上司コメント */}
          {report.manager_comment && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-3 mt-2">
              <p className="text-xs font-medium text-green-600 mb-1">上司コメント</p>
              <p className="text-xs text-gray-700 whitespace-pre-wrap">{report.manager_comment}</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// ===== 月間報告 新規フォーム =====
function NewReportForm({ goalId, onSaved }: { goalId: string; onSaved: () => void }) {
  const [open, setOpen]       = useState(false)
  const [month, setMonth]     = useState(new Date().toISOString().slice(0, 7))
  const [action, setAction]   = useState('')
  const [result, setResult]   = useState('')
  const [saving, setSaving]   = useState(false)

  const save = async () => {
    setSaving(true)
    try {
      await api.post('/api/v1/mbo/reports/', {
        goal: goalId,
        month: `${month}-01`,
        action_content: action,
        result,
      })
      setOpen(false)
      setAction('')
      setResult('')
      onSaved()
    } catch (e: any) {
      alert(e.response?.data?.non_field_errors?.[0] ?? '登録に失敗しました')
    } finally {
      setSaving(false)
    }
  }

  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        className="mt-3 text-xs text-blue-600 hover:underline"
      >
        ＋ 月間報告を追加
      </button>
    )
  }

  return (
    <div className="mt-3 bg-blue-50 border border-blue-200 rounded-lg p-4 space-y-3">
      <p className="text-xs font-medium text-blue-700">月間報告を追加</p>
      <div>
        <label className="text-xs text-gray-500 block mb-1">対象月</label>
        <input
          type="month"
          value={month}
          onChange={(e) => setMonth(e.target.value)}
          className="px-3 py-2 border border-gray-300 rounded-lg text-sm"
        />
      </div>
      <div>
        <label className="text-xs text-gray-500 block mb-1">行動内容</label>
        <textarea
          value={action}
          onChange={(e) => setAction(e.target.value)}
          rows={3}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm resize-none"
          placeholder="今月取り組んだ行動を記入してください"
        />
      </div>
      <div>
        <label className="text-xs text-gray-500 block mb-1">結果・考察</label>
        <textarea
          value={result}
          onChange={(e) => setResult(e.target.value)}
          rows={3}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm resize-none"
          placeholder="結果と振り返りを記入してください"
        />
      </div>
      <div className="flex gap-2">
        <button
          onClick={save}
          disabled={saving}
          className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs rounded-lg font-medium"
        >
          {saving ? '登録中...' : '登録'}
        </button>
        <button
          onClick={() => setOpen(false)}
          className="px-3 py-1.5 bg-white hover:bg-gray-100 border border-gray-300 text-gray-700 text-xs rounded-lg"
        >
          キャンセル
        </button>
      </div>
    </div>
  )
}

// ===== 新規目標モーダル =====
function NewGoalModal({
  year, period, onClose, onSaved,
}: {
  year: number
  period: 'first_half' | 'second_half'
  onClose: () => void
  onSaved: () => void
}) {
  const [title, setTitle]           = useState('')
  const [targetLevel, setTarget]    = useState('')
  const [weight, setWeight]         = useState(100)
  const [saving, setSaving]         = useState(false)

  const save = async () => {
    if (!title.trim()) return
    setSaving(true)
    try {
      await api.post('/api/v1/mbo/goals/', { year, period, title, target_level: targetLevel, weight })
      onSaved()
    } catch (e: any) {
      const msg = e.response?.data?.error ?? e.response?.data?.weight?.[0] ?? '登録に失敗しました'
      alert(msg)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg">
        <div className="flex items-center justify-between p-6 border-b border-gray-100">
          <h2 className="font-bold text-gray-800">新しい目標を追加</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl leading-none">×</button>
        </div>

        <div className="p-6 space-y-4">
          <div>
            <label className="text-sm font-medium text-gray-700 block mb-1">
              目標タイトル <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
              placeholder="例: 顧客満足度スコアを90%以上に向上させる"
            />
          </div>

          <div>
            <label className="text-sm font-medium text-gray-700 block mb-1">達成水準</label>
            <textarea
              value={targetLevel}
              onChange={(e) => setTarget(e.target.value)}
              rows={4}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm resize-none"
              placeholder="目標の具体的な達成基準を記入してください"
            />
          </div>

          <div>
            <label className="text-sm font-medium text-gray-700 block mb-1">
              ウェイト（%）
            </label>
            <input
              type="number"
              min={1} max={100}
              value={weight}
              onChange={(e) => setWeight(Number(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
            />
            <p className="text-xs text-gray-400 mt-1">全目標のウェイト合計が 100% になるよう設定</p>
          </div>

          <div className="flex gap-2 text-sm text-gray-500 bg-gray-50 rounded-lg px-4 py-3">
            <span>{year}年度</span>
            <span>·</span>
            <span>{PERIOD_LABEL[period]}</span>
          </div>
        </div>

        <div className="flex gap-3 px-6 pb-6">
          <button
            onClick={onClose}
            className="flex-1 py-2.5 border border-gray-300 rounded-lg text-sm text-gray-600 hover:bg-gray-50 font-medium"
          >
            キャンセル
          </button>
          <button
            onClick={save}
            disabled={!title.trim() || saving}
            className="flex-1 py-2.5 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white rounded-lg text-sm font-medium transition-colors"
          >
            {saving ? '登録中...' : '目標を登録'}
          </button>
        </div>
      </div>
    </div>
  )
}
