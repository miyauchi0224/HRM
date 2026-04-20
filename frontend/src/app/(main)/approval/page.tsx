'use client'
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'
import { useAuthStore } from '@/lib/store'
import { FileText, Plus, ChevronRight, CheckCircle, XCircle, Clock } from 'lucide-react'

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
  steps: Array<{ id: string; approver_name: string; order: number; decision: string; comment: string }>
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

export default function ApprovalPage() {
  const user = useAuthStore((s) => s.user)
  const qc = useQueryClient()
  const [showNew, setShowNew] = useState(false)
  const [selected, setSelected] = useState<ApprovalRequest | null>(null)
  const [form, setForm] = useState({ title: '', category: 'purchase', amount: '', content: '' })

  const { data: requests = [], isLoading } = useQuery<ApprovalRequest[]>({
    queryKey: ['approval-requests'],
    queryFn: () => api.get('/api/v1/approval/requests/').then((r) => r.data.results ?? r.data),
  })

  const createMut = useMutation({
    mutationFn: (data: any) => api.post('/api/v1/approval/requests/', data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['approval-requests'] }); setShowNew(false) },
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

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <FileText className="text-indigo-600" size={28} />
          <div>
            <h1 className="text-2xl font-bold text-gray-800">電子稟議</h1>
            <p className="text-sm text-gray-500">購買・出張・契約などの承認申請</p>
          </div>
        </div>
        <button
          onClick={() => setShowNew(true)}
          className="flex items-center gap-2 bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700"
        >
          <Plus size={18} /> 新規申請
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
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-gray-500 text-xs uppercase">
              <tr>
                <th className="px-4 py-3 text-left">件名</th>
                <th className="px-4 py-3 text-left">カテゴリ</th>
                <th className="px-4 py-3 text-left">申請者</th>
                <th className="px-4 py-3 text-right">金額</th>
                <th className="px-4 py-3 text-center">ステータス</th>
                <th className="px-4 py-3 text-center">操作</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {requests.map((req) => {
                const cfg = STATUS_CONFIG[req.status] ?? { label: req.status, color: 'bg-gray-100 text-gray-600' }
                return (
                  <tr key={req.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 font-medium text-gray-800">{req.title}</td>
                    <td className="px-4 py-3 text-gray-600">{CATEGORY_LABELS[req.category] ?? req.category}</td>
                    <td className="px-4 py-3 text-gray-600">{req.applicant_name}</td>
                    <td className="px-4 py-3 text-right text-gray-800">
                      {req.amount != null ? `¥${req.amount.toLocaleString()}` : '-'}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${cfg.color}`}>
                        {cfg.label}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <div className="flex items-center justify-center gap-2">
                        {req.status === 'draft' && (
                          <button
                            onClick={() => submitMut.mutate(req.id)}
                            className="text-xs bg-indigo-100 text-indigo-700 px-2 py-1 rounded hover:bg-indigo-200"
                          >申請</button>
                        )}
                        {req.status === 'pending' && (
                          <button
                            onClick={() => setSelected(req)}
                            className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded hover:bg-green-200"
                          >承認/却下</button>
                        )}
                        {['draft', 'pending'].includes(req.status) && req.applicant_name === user?.full_name && (
                          <button
                            onClick={() => withdrawMut.mutate(req.id)}
                            className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded hover:bg-gray-200"
                          >取り下げ</button>
                        )}
                      </div>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        )}
      </div>

      {/* 新規申請モーダル */}
      {showNew && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg p-6">
            <h2 className="text-lg font-bold text-gray-800 mb-4">新規稟議申請</h2>
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
            </div>
            <div className="flex gap-3 mt-6">
              <button
                onClick={() => setShowNew(false)}
                className="flex-1 border border-gray-300 text-gray-700 py-2 rounded-lg text-sm hover:bg-gray-50"
              >キャンセル</button>
              <button
                onClick={() => createMut.mutate({
                  title: form.title,
                  category: form.category,
                  amount: form.amount || null,
                  content: form.content,
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
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-md p-6">
        <h2 className="text-lg font-bold text-gray-800 mb-1">{req.title}</h2>
        <p className="text-sm text-gray-500 mb-4">申請者: {req.applicant_name}</p>
        <p className="text-sm text-gray-700 bg-gray-50 rounded-lg p-3 mb-4">{req.content}</p>
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
