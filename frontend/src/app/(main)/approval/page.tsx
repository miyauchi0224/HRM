'use client'
import { useState, useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'
import { useAuthStore } from '@/lib/store'
import { FileText, Plus, CheckCircle, XCircle, Clock, ChevronRight, Paperclip, Download, X, File } from 'lucide-react'

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

interface FileAttachment {
  id: string
  file: string
  file_name: string
  file_size: number
  content_type: string
  uploaded_at: string
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
  file_attachments: FileAttachment[]
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes}B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)}KB`
  return `${(bytes / 1024 / 1024).toFixed(1)}MB`
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
  const [attachUploading, setAttachUploading] = useState<string | null>(null)
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const [pendingFiles, setPendingFiles] = useState<File[]>([])
  const attachRefs = useRef<Record<string, HTMLInputElement | null>>({})
  const newAttachRef = useRef<HTMLInputElement>(null)

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
    onSuccess: async (res) => {
      const reqId = res.data.id
      // 起案時に選択されたファイルを順番にアップロード
      for (const file of pendingFiles) {
        const fd = new FormData()
        fd.append('file', file)
        try { await api.post(`/api/v1/approval/requests/${reqId}/attachments/`, fd) }
        catch { /* silent */ }
      }
      setPendingFiles([])
      qc.invalidateQueries({ queryKey: ['approval-requests'] })
      setShowNew(false)
      setDefaultSteps([])
    },
  })

  const submitMut = useMutation({
    mutationFn: (id: string) => api.post(`/api/v1/approval/requests/${id}/submit/`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['approval-requests'] }),
  })

  const decideMut = useMutation({
    mutationFn: ({ id, decision, comment }: any) =>
      api.patch(`/api/v1/approval/requests/${id}/decide/`, { decision, comment }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['approval-requests'] }); setSelected(null) },
    onError: (err: any) => {
      const msg = err?.response?.data?.error ?? err?.response?.data?.detail ?? '処理に失敗しました'
      alert(msg)
    },
  })

  const withdrawMut = useMutation({
    mutationFn: (id: string) => api.post(`/api/v1/approval/requests/${id}/withdraw/`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['approval-requests'] }),
  })

  const deleteAttachMut = useMutation({
    mutationFn: ({ reqId, attachId }: { reqId: string; attachId: string }) =>
      api.delete(`/api/v1/approval/requests/${reqId}/attachments/${attachId}/`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['approval-requests'] }),
  })

  const uploadAttachment = async (reqId: string, e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    setAttachUploading(reqId)
    try {
      const form = new FormData()
      form.append('file', file)
      await api.post(`/api/v1/approval/requests/${reqId}/attachments/`, form)
      qc.invalidateQueries({ queryKey: ['approval-requests'] })
    } catch {
      alert('ファイルのアップロードに失敗しました')
    } finally {
      setAttachUploading(null)
      const ref = attachRefs.current[reqId]
      if (ref) ref.value = ''
    }
  }

  const downloadAttachment = async (reqId: string, attachId: string, fileName: string) => {
    const res = await api.get(
      `/api/v1/approval/requests/${reqId}/attachments/${attachId}/download/`,
      { responseType: 'blob' }
    )
    const a = document.createElement('a')
    a.href = window.URL.createObjectURL(new Blob([res.data]))
    a.download = fileName
    a.click()
  }

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
              const isExpanded = expandedId === req.id
              return (
                <div key={req.id}>
                  <div className="p-4 hover:bg-gray-50">
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

                        {/* 添付ファイル件数 */}
                        {req.file_attachments?.length > 0 && (
                          <button
                            onClick={() => setExpandedId(isExpanded ? null : req.id)}
                            className="mt-2 flex items-center gap-1 text-xs text-indigo-600 hover:text-indigo-800"
                          >
                            <Paperclip size={12} />
                            添付ファイル {req.file_attachments.length}件 {isExpanded ? '▲' : '▼'}
                          </button>
                        )}
                      </div>
                      <div className="flex items-center gap-2 shrink-0">
                        {/* ファイル添付ボタン */}
                        <label className={`flex items-center gap-1 text-xs px-2 py-1.5 rounded border cursor-pointer transition-colors ${
                          attachUploading === req.id
                            ? 'border-gray-200 text-gray-400 cursor-not-allowed'
                            : 'border-indigo-200 text-indigo-600 hover:bg-indigo-50'
                        }`}>
                          <Paperclip size={12} />
                          {attachUploading === req.id ? '...' : '添付'}
                          <input
                            type="file"
                            className="hidden"
                            disabled={attachUploading === req.id}
                            ref={(el) => { attachRefs.current[req.id] = el }}
                            onChange={(e) => uploadAttachment(req.id, e)}
                          />
                        </label>
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

                  {/* 添付ファイル展開エリア */}
                  {isExpanded && req.file_attachments?.length > 0 && (
                    <div className="bg-indigo-50 px-8 py-3 border-t border-indigo-100">
                      <p className="text-xs font-medium text-indigo-600 mb-2">添付ファイル</p>
                      <div className="flex flex-wrap gap-3">
                        {req.file_attachments.map((att) => (
                          <div key={att.id}
                            className="flex items-center gap-2 bg-white border border-indigo-100 rounded-lg px-3 py-2 text-xs">
                            <File size={14} className="text-indigo-400 shrink-0" />
                            <span className="text-gray-700 max-w-[160px] truncate">{att.file_name}</span>
                            <span className="text-gray-400">{formatFileSize(att.file_size)}</span>
                            <button
                              onClick={() => downloadAttachment(req.id, att.id, att.file_name)}
                              className="text-indigo-500 hover:text-indigo-700 ml-1"
                              title="ダウンロード"
                            >
                              <Download size={13} />
                            </button>
                            <button
                              onClick={() => confirm('削除しますか？') && deleteAttachMut.mutate({ reqId: req.id, attachId: att.id })}
                              className="text-gray-300 hover:text-red-400 ml-1"
                              title="削除"
                            >
                              <X size={12} />
                            </button>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
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

              {/* 添付ファイル（見積書など） */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">添付ファイル（見積書・資料など）</label>
                <div
                  className="border-2 border-dashed border-gray-300 rounded-lg p-3 cursor-pointer hover:border-indigo-400 transition-colors"
                  onClick={() => newAttachRef.current?.click()}
                  onDragOver={(e) => e.preventDefault()}
                  onDrop={(e) => {
                    e.preventDefault()
                    const newFiles = Array.from(e.dataTransfer.files)
                    setPendingFiles((prev) => [...prev, ...newFiles])
                  }}
                >
                  <p className="text-xs text-gray-500 text-center">クリックまたはドラッグでファイルを追加</p>
                  <input
                    ref={newAttachRef}
                    type="file"
                    multiple
                    className="hidden"
                    onChange={(e) => {
                      const newFiles = Array.from(e.target.files ?? [])
                      setPendingFiles((prev) => [...prev, ...newFiles])
                      e.target.value = ''
                    }}
                  />
                </div>
                {pendingFiles.length > 0 && (
                  <ul className="mt-2 space-y-1">
                    {pendingFiles.map((f, i) => (
                      <li key={i} className="flex items-center justify-between text-xs bg-gray-50 rounded px-2 py-1">
                        <span className="truncate text-gray-700">{f.name} <span className="text-gray-400">({(f.size / 1024).toFixed(0)} KB)</span></span>
                        <button onClick={() => setPendingFiles((prev) => prev.filter((_, j) => j !== i))} className="ml-2 text-gray-400 hover:text-red-500">×</button>
                      </li>
                    ))}
                  </ul>
                )}
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
          isPending={decideMut.isPending}
        />
      )}
    </div>
  )
}

function DecideModal({ req, onClose, onDecide, isPending }: {
  req: ApprovalRequest
  onClose: () => void
  onDecide: (decision: string, comment: string) => void
  isPending?: boolean
}) {
  const [comment, setComment] = useState('')

  const handleDecide = (decision: string) => {
    if (!comment.trim()) {
      alert('承認・却下には理由（コメント）を入力してください')
      return
    }
    onDecide(decision, comment)
  }

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
          <label className="block text-sm font-medium text-gray-700 mb-1">
            理由・コメント <span className="text-red-500">*</span>
          </label>
          <textarea
            className="w-full border rounded-lg px-3 py-2 text-sm h-20 resize-none"
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            placeholder="承認・却下の理由を入力してください（必須）"
          />
          {!comment.trim() && <p className="text-xs text-red-500 mt-1">理由は必須です</p>}
        </div>
        <div className="flex gap-3 mt-4">
          <button onClick={onClose} disabled={isPending} className="flex-1 border border-gray-300 text-gray-700 py-2 rounded-lg text-sm disabled:opacity-50">キャンセル</button>
          <button
            onClick={() => handleDecide('rejected')}
            disabled={isPending || !comment.trim()}
            className="flex-1 bg-red-500 text-white py-2 rounded-lg text-sm hover:bg-red-600 disabled:opacity-50"
          >{isPending ? '処理中...' : '却下'}</button>
          <button
            onClick={() => handleDecide('approved')}
            disabled={isPending || !comment.trim()}
            className="flex-1 bg-green-600 text-white py-2 rounded-lg text-sm hover:bg-green-700 disabled:opacity-50"
          >{isPending ? '処理中...' : '承認'}</button>
        </div>
      </div>
    </div>
  )
}
