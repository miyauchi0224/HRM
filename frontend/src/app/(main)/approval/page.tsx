'use client'
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'
import { useAuthStore } from '@/lib/store'
import { FileText, Plus, CheckCircle, XCircle, Clock, ChevronRight } from 'lucide-react'

interface ApprovalStep {
  id: string
  approver: string
  approver_name: string
  step_role: string
  step_role_label: string
  order: number
  decision: string
  comment: string
  decided_at: string | null
}

interface ApprovalRequest {
  id: string
  title: string
  category: string
  amount: number | null
  content: string
  status: string
  applicant_name: string
  submitted_at: string | null
  created_at: string
  steps: ApprovalStep[]
}

interface DefaultStep {
  employee_id: string
  name: string
  step_role: string
  order: number
}

const CATEGORY_LABELS: Record<string, string> = {
  purchase: '購買申請', travel: '出張申請', contract: '契約申請',
  budget: '予算申請', hr: '人事申請', other: 'その他',
}
const STATUS_CONFIG: Record<string, { label: string; color: string }> = {
  draft: { label: '下書き', color: 'bg-gray-100 text-gray-600' },
  pending: { label: '審査中', color: 'bg-yellow-100 text-yellow-700' },
  approved: { label: '承認済', color: 'bg-green-100 text-green-700' },
  rejected: { label: '却下', color: 'bg-red-100 text-red-600' },
  withdrawn: { label: '取り下げ', color: 'bg-gray-100 text-gray-500' },
}
const STEP_ROLE_ICON: Record<string, string> = {
  supervisor: '上司', manager: '部門長', accounting: '財務', custom: 'カスタム'
}
const DECISION_CONFIG: Record<string, { icon: typeof CheckCircle; color: string }> = {
  approved: { icon: CheckCircle, color: 'text-green-500' },
  rejected: { icon: XCircle, color: 'text-red-500' },
  pending: { icon: Clock, color: 'text-gray-400' },
}

export default function ApprovalPage() {
  const user = useAuthStore((s) => s.user)
  const qc = useQueryClient()
  const [showNew, setShowNew] = useState(false)
  const [selected, setSelected] = useState<ApprovalRequest | null>(null)
  const [form, setForm] = useState({ title: '', category: 'purchase', amount: '', content: '' })
  const [defaultSteps, setDefaultSteps] = useState<DefaultStep[]>([])

  const { data: requests = [], isLoading } = useQuery<ApprovalRequest[]>({
    queryKey: ['approval-requests'],
    queryFn: () => api.get('/api/v1/approval/requests/').then((r) => r.data.results ?? r.data),
  })

  const buildStepsMut = useMutation({
    mutationFn: () => api.post('/api/v1/approval/requests/build-default-steps/'),
    onSuccess: (res) => setDefaultSteps(res.data.steps ?? []),
  })

  const createMut = useMutation({
    mutationFn: (data: any) => api.post('/api/v1/approval/requests/', data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['approval-requests'] }); setShowNew(false); setDefaultSteps([]) },
  })

  const submitMut = useMutation({
    mutationFn: (id: string) => api.post(`/api/v1/approval/requests/${id}/submit/`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['approval-requests'] }),
  })

  const decideMut = useMutation({
    mutationFn: ({ id, decision, comment }: any) =>
      api.patch(`/api/v1/approval/requests/${id}/decide/`, { decision, comment }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['approval-requests'] }); setSelected(null) },
  })

  const withdrawMut = useMutation({
    mutationFn: (id: string) => api.post(`/api/v1/approval/requests/${id}/withdraw/`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['approval-requests'] }),
  })

  const pendingCount = requests.filter((r) => r.status === 'pending').length

  const openNew = () => {
    setShowNew(true)
    buildStepsMut.mutate()
  }

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <FileText className="text-indigo-600" size={28} />
          <div>
            <h1 className="text-2xl font-bold text-gray-800">電子稟議</h1>
            <p className="text-sm text-gray-500">起案者 → 上司 → 部門長 → 財務 の承認フロー</p>
          </div>
        </div>
        <button
          onClick={openNew}
          className="flex items-center gap-2 bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700"
        >
          <Plus size={18} /> 新規起案
        </button>
      </div>

      {/* KPI */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        {[
          { label: '全申請', value: requests.length, color: 'text-gray-800' },
          { label: '審査中', value: pendingCount, color: 'text-yellow-600' },
          { label: '承認済', value: requests.filter((r) => r.status === 'approved').length, color: 'text-green-600' },
        ].map((item) => (
          <div key={item.label} className="bg-white rounded-xl shadow-sm border p-4 text-center">
            <p className={`text-3xl font-bold ${item.color}`}>{item.value}</p>
            <p className="text-sm text-gray-500 mt-1">{item.label}</p>
          </div>
        ))}
      </div>

      {/* 申請一覧 */}
      <div className="bg-white rounded-xl shadow-sm border overflow-hidden">
        {isLoading ? (
          <div className="p-8 text-center text-gray-400">読み込み中...</div>
        ) : requests.length === 0 ? (
          <div className="p-8 text-center text-gray-400">申請がありません</div>
        ) : (
          <div className="divide-y">
            {requests.map((req) => {
              const cfg = STATUS_CONFIG[req.status] ?? { label: req.status, color: 'bg-gray-100 text-gray-600' }
              return (
                <div key={req.id} className="p-4 hover:bg-gray-50">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-1">
                        <span className="font-semibold text-gray-800">{req.title}</span>
                        <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${cfg.color}`}>{cfg.label}</span>
                        <span className="text-xs text-gray-500">{CATEGORY_LABELS[req.category]}</span>
                        {req.amount != null && (
                          <span className="text-xs font-medium text-gray-700">¥{req.amount.toLocaleString()}</span>
                        )}
                      </div>
                      <p className="text-sm text-gray-500 mb-2">起案者: {req.applicant_name}</p>

                      {/* 承認フロー表示 */}
                      {req.steps.length > 0 && (
                        <div className="flex items-center gap-1 flex-wrap">
                          <span className="text-xs text-gray-400 mr-1">承認ルート:</span>
                          {req.steps.map((step, i) => {
                            const dcfg = DECISION_CONFIG[step.decision] ?? DECISION_CONFIG.pending
                            const Icon = dcfg.icon
                            return (
                              <div key={step.id} className="flex items-center gap-1">
                                {i > 0 && <ChevronRight size={12} className="text-gray-300" />}
                                <div className={`flex items-center gap-1 text-xs px-2 py-0.5 rounded-full border ${
                                  step.decision === 'approved' ? 'bg-green-50 border-green-200 text-green-700' :
                                  step.decision === 'rejected' ? 'bg-red-50 border-red-200 text-red-600' :
                                  'bg-gray-50 border-gray-200 text-gray-500'
                                }`}>
                                  <Icon size={11} className={dcfg.color} />
                                  <span>{STEP_ROLE_ICON[step.step_role]}</span>
                                  <span className="font-medium">{step.approver_name}</span>
                                </div>
                              </div>
                            )
                          })}
                        </div>
                      )}
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      {req.status === 'draft' && (
                        <button
                          onClick={() => submitMut.mutate(req.id)}
                          className="text-xs bg-indigo-100 text-indigo-700 px-3 py-1.5 rounded-lg hover:bg-indigo-200"
                        >申請</button>
                      )}
                      {req.status === 'pending' && (
                        <button
                          onClick={() => setSelected(req)}
                          className="text-xs bg-green-100 text-green-700 px-3 py-1.5 rounded-lg hover:bg-green-200"
                        >承認/却下</button>
                      )}
                      {['draft', 'pending'].includes(req.status) && req.applicant_name === user?.full_name && (
                        <button
                          onClick={() => withdrawMut.mutate(req.id)}
                          className="text-xs bg-gray-100 text-gray-600 px-3 py-1.5 rounded-lg hover:bg-gray-200"
                        >取り下げ</button>
                      )}
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>

      {/* 新規起案モーダル */}
      {showNew && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg p-6">
            <h2 className="text-lg font-bold text-gray-800 mb-4">新規稟議起案</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">件名 *</label>
                <input
                  className="w-full border rounded-lg px-3 py-2 text-sm"
                  value={form.title}
                  onChange={(e) => setForm({ ...form, title: e.target.value })}
                  placeholder="例：プリンター購入申請"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">カテゴリ</label>
                  <select
                    className="w-full border rounded-lg px-3 py-2 text-sm"
                    value={form.category}
                    onChange={(e) => setForm({ ...form, category: e.target.value })}
                  >
                    {Object.entries(CATEGORY_LABELS).map(([k, v]) => (
                      <option key={k} value={k}>{v}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">金額（円）</label>
                  <input
                    type="number"
                    className="w-full border rounded-lg px-3 py-2 text-sm"
                    value={form.amount}
                    onChange={(e) => setForm({ ...form, amount: e.target.value })}
                    placeholder="0"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">申請内容 *</label>
                <textarea
                  className="w-full border rounded-lg px-3 py-2 text-sm h-28 resize-none"
                  value={form.content}
                  onChange={(e) => setForm({ ...form, content: e.target.value })}
                  placeholder="申請の目的・理由・詳細を記載してください"
                />
              </div>

              {/* 自動生成された承認ルート */}
              {defaultSteps.length > 0 && (
                <div className="bg-indigo-50 rounded-lg p-3">
                  <p className="text-xs font-medium text-indigo-700 mb-2">承認ルート（自動設定）</p>
                  <div className="flex items-center gap-1 flex-wrap">
                    <span className="text-xs bg-white border border-indigo-200 text-indigo-700 px-2 py-1 rounded-full">
                      {user?.full_name}（起案者）
                    </span>
                    {defaultSteps.map((step) => (
                      <div key={step.employee_id} className="flex items-center gap-1">
                        <ChevronRight size={14} className="text-indigo-300" />
                        <span className="text-xs bg-white border border-indigo-200 text-indigo-700 px-2 py-1 rounded-full">
                          {STEP_ROLE_ICON[step.step_role]}: {step.name}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              {buildStepsMut.isPending && (
                <p className="text-xs text-gray-400">承認者を自動取得中...</p>
              )}
            </div>
            <div className="flex gap-3 mt-6">
              <button
                onClick={() => { setShowNew(false); setDefaultSteps([]) }}
                className="flex-1 border border-gray-300 text-gray-700 py-2 rounded-lg text-sm hover:bg-gray-50"
              >キャンセル</button>
              <button
                onClick={() => createMut.mutate({
                  title: form.title,
                  category: form.category,
                  amount: form.amount || null,
                  content: form.content,
                  approver_ids: defaultSteps.map((s) => s.employee_id),
                })}
                disabled={!form.title || !form.content}
                className="flex-1 bg-indigo-600 text-white py-2 rounded-lg text-sm hover:bg-indigo-700 disabled:opacity-50"
              >下書き保存</button>
            </div>
          </div>
        </div>
      )}

      {/* 承認/却下モーダル */}
      {selected && (
        <DecideModal
          req={selected}
          onClose={() => setSelected(null)}
          onDecide={(decision, comment) => decideMut.mutate({ id: selected.id, decision, comment })}
        />
      )}
    </div>
  )
}

function DecideModal({ req, onClose, onDecide }: {
  req: ApprovalRequest
  onClose: () => void
  onDecide: (decision: string, comment: string) => void
}) {
  const [comment, setComment] = useState('')

  const currentStep = req.steps.find((s) => s.decision === 'pending')

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-md p-6">
        <h2 className="text-lg font-bold text-gray-800 mb-1">{req.title}</h2>
        <p className="text-sm text-gray-500 mb-4">申請者: {req.applicant_name}</p>
        <p className="text-sm text-gray-700 bg-gray-50 rounded-lg p-3 mb-4">{req.content}</p>

        {/* 承認フロー全体表示 */}
        <div className="mb-4">
          <p className="text-xs font-medium text-gray-500 mb-2">承認ルート</p>
          <div className="flex items-center gap-1 flex-wrap">
            {req.steps.map((step, i) => {
              const dcfg = DECISION_CONFIG[step.decision] ?? DECISION_CONFIG.pending
              const Icon = dcfg.icon
              const isCurrent = step.id === currentStep?.id
              return (
                <div key={step.id} className="flex items-center gap-1">
                  {i > 0 && <ChevronRight size={12} className="text-gray-300" />}
                  <div className={`flex items-center gap-1 text-xs px-2 py-1 rounded-full border ${
                    isCurrent ? 'bg-yellow-50 border-yellow-300 text-yellow-700 font-bold' :
                    step.decision === 'approved' ? 'bg-green-50 border-green-200 text-green-700' :
                    'bg-gray-50 border-gray-200 text-gray-400'
                  }`}>
                    <Icon size={11} className={dcfg.color} />
                    <span>{STEP_ROLE_ICON[step.step_role]}: {step.approver_name}</span>
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {currentStep && (
          <p className="text-xs text-yellow-700 bg-yellow-50 rounded px-3 py-2 mb-4">
            あなたの承認番が来ています（{STEP_ROLE_ICON[currentStep.step_role]}）
          </p>
        )}

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">コメント</label>
          <textarea
            className="w-full border rounded-lg px-3 py-2 text-sm h-20 resize-none"
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            placeholder="コメントを入力（任意）"
          />
        </div>
        <div className="flex gap-3 mt-4">
          <button onClick={onClose} className="flex-1 border border-gray-300 text-gray-700 py-2 rounded-lg text-sm">キャンセル</button>
          <button
            onClick={() => onDecide('rejected', comment)}
            className="flex-1 bg-red-500 text-white py-2 rounded-lg text-sm hover:bg-red-600"
          >却下</button>
          <button
            onClick={() => onDecide('approved', comment)}
            className="flex-1 bg-green-600 text-white py-2 rounded-lg text-sm hover:bg-green-700"
          >承認</button>
        </div>
      </div>
    </div>
  )
}
