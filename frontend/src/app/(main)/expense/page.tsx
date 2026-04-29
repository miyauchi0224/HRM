'use client'
import { useState, useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'
import { useAuthStore } from '@/lib/store'
import { Receipt, Plus, X, Upload, Download, Paperclip, Image as ImageIcon, File } from 'lucide-react'

interface AccountItem { id: string; code: string; name: string; category: string }

interface AttachmentItem {
  id: string
  file: string
  file_name: string
  file_size: number
  content_type: string
  uploaded_at: string
}

interface ExpenseRequest {
  id: string
  expense_date: string
  account_item: { id: string; name: string }
  amount: number
  description: string
  status: 'pending' | 'approved' | 'rejected' | 'cancelled'
  created_at: string
  attachments: AttachmentItem[]
}

const STATUS_CONFIG: Record<string, { label: string; color: string }> = {
  pending:   { label: '申請中', color: 'bg-yellow-100 text-yellow-700' },
  approved:  { label: '承認済', color: 'bg-green-100 text-green-700' },
  rejected:  { label: '却下',   color: 'bg-red-100 text-red-600' },
  cancelled: { label: '取消',   color: 'bg-gray-100 text-gray-500' },
}

const ACCOUNTING_ROLES = ['hr', 'accounting', 'admin']

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes}B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)}KB`
  return `${(bytes / 1024 / 1024).toFixed(1)}MB`
}

export default function ExpensePage() {
  const user         = useAuthStore((s) => s.user)
  const isAccounting = ACCOUNTING_ROLES.includes(user?.role ?? '')
  const [showNew, setShowNew]           = useState(false)
  const [uploading, setUploading]       = useState(false)
  const [uploadResult, setUploadResult] = useState<any>(null)
  const [expandedId, setExpandedId]     = useState<string | null>(null)
  const [attachUploading, setAttachUploading] = useState<string | null>(null)
  const fileRef    = useRef<HTMLInputElement>(null)
  const attachRefs = useRef<Record<string, HTMLInputElement | null>>({})
  const qc = useQueryClient()

  const { data: requests = [], isLoading } = useQuery<ExpenseRequest[]>({
    queryKey: ['expense-requests'],
    queryFn: () => api.get('/api/v1/expense/requests/').then((r) => r.data.results ?? r.data),
  })

  const cancelMut = useMutation({
    mutationFn: (id: string) => api.patch(`/api/v1/expense/requests/${id}/`, { status: 'cancelled' }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['expense-requests'] }),
  })

  const deleteAttachMut = useMutation({
    mutationFn: ({ reqId, attachId }: { reqId: string; attachId: string }) =>
      api.delete(`/api/v1/expense/requests/${reqId}/attachments/${attachId}/`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['expense-requests'] }),
  })

  const totalPending  = requests.filter((r) => r.status === 'pending').reduce((s, r) => s + r.amount, 0)
  const totalApproved = requests.filter((r) => r.status === 'approved').reduce((s, r) => s + r.amount, 0)

  const downloadTemplate = async () => {
    const res = await api.get('/api/v1/expense/requests/template-csv/', { responseType: 'blob' })
    const a = document.createElement('a')
    a.href = window.URL.createObjectURL(new Blob([res.data]))
    a.download = 'expense_upload_template.csv'
    a.click()
  }

  const uploadCsv = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    setUploading(true)
    setUploadResult(null)
    try {
      const form = new FormData()
      form.append('file', file)
      const res = await api.post('/api/v1/expense/requests/import-csv/', form)
      setUploadResult(res.data)
      qc.invalidateQueries({ queryKey: ['expense-requests'] })
    } catch {
      alert('アップロードに失敗しました')
    } finally {
      setUploading(false)
      if (fileRef.current) fileRef.current.value = ''
    }
  }

  const uploadAttachment = async (reqId: string, e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    setAttachUploading(reqId)
    try {
      const form = new FormData()
      form.append('file', file)
      await api.post(`/api/v1/expense/requests/${reqId}/attachments/`, form)
      qc.invalidateQueries({ queryKey: ['expense-requests'] })
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
      `/api/v1/expense/requests/${reqId}/attachments/${attachId}/download/`,
      { responseType: 'blob' }
    )
    const a = document.createElement('a')
    a.href = window.URL.createObjectURL(new Blob([res.data]))
    a.download = fileName
    a.click()
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
          <Receipt size={22} /> 経費申請
        </h1>
        <button
          onClick={() => setShowNew(true)}
          className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium px-4 py-2 rounded-lg"
        >
          <Plus size={16} /> 申請する
        </button>
      </div>

      {/* 一括登録セクション（経理・人事・管理者のみ）*/}
      {isAccounting && (
        <div className="bg-white rounded-xl border border-gray-200 p-5 mb-6">
          <h2 className="font-semibold text-gray-700 mb-3 flex items-center gap-2">
            <Upload size={16} /> 経費申請 一括登録
          </h2>
          <div className="flex flex-wrap gap-3 items-center">
            <button
              onClick={downloadTemplate}
              className="flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg text-sm text-gray-600 hover:bg-gray-50"
            >
              <Download size={15} /> テンプレートCSVダウンロード
            </button>
            <label className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium cursor-pointer transition-colors ${
              uploading
                ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                : 'bg-blue-600 hover:bg-blue-700 text-white'
            }`}>
              <Upload size={15} />
              {uploading ? 'アップロード中...' : 'CSVをアップロード'}
              <input
                ref={fileRef}
                type="file"
                accept=".csv"
                className="hidden"
                disabled={uploading}
                onChange={uploadCsv}
              />
            </label>
          </div>
          {uploadResult && (
            <div className="mt-4 p-4 bg-gray-50 rounded-lg text-sm">
              <p className="font-medium text-gray-800 mb-1">
                登録: {uploadResult.created}件
                {uploadResult.errors > 0 && (
                  <span className="text-red-600 ml-2">エラー: {uploadResult.errors}件</span>
                )}
              </p>
              {uploadResult.error_details?.length > 0 && (
                <ul className="mt-2 space-y-1">
                  {uploadResult.error_details.map((e: any, i: number) => (
                    <li key={i} className="text-red-600 text-xs">
                      {e.row}行目: {e.error}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )}
        </div>
      )}

      {/* サマリー */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        <div className="bg-white rounded-xl border border-gray-200 p-4">
          <p className="text-xs text-gray-400 mb-1">申請中合計</p>
          <p className="text-xl font-bold text-yellow-600">¥{totalPending.toLocaleString()}</p>
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-4">
          <p className="text-xs text-gray-400 mb-1">承認済合計</p>
          <p className="text-xl font-bold text-green-600">¥{totalApproved.toLocaleString()}</p>
        </div>
      </div>

      {/* 申請一覧 */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <div className="px-5 py-4 border-b border-gray-100">
          <h2 className="font-semibold text-gray-700">申請履歴</h2>
        </div>
        {isLoading ? (
          <p className="text-center text-gray-400 text-sm py-10">読み込み中...</p>
        ) : requests.length === 0 ? (
          <p className="text-center text-gray-400 text-sm py-10">申請履歴がありません</p>
        ) : (
          <div className="divide-y divide-gray-50">
            {requests.map((req) => {
              const st = STATUS_CONFIG[req.status]
              const isExpanded = expandedId === req.id
              return (
                <div key={req.id}>
                  {/* メイン行 */}
                  <div className="flex items-center gap-2 px-5 py-3 hover:bg-gray-50">
                    <div className="flex-1 grid grid-cols-5 gap-2 text-sm">
                      <span className="text-gray-600">{req.expense_date}</span>
                      <span className="text-gray-700">{req.account_item?.name ?? '—'}</span>
                      <span className="font-medium text-gray-800">¥{req.amount.toLocaleString()}</span>
                      <span className="text-gray-500 truncate">{req.description || '—'}</span>
                      <span>
                        <span className={`text-xs px-2.5 py-1 rounded-full font-medium ${st.color}`}>
                          {st.label}
                        </span>
                      </span>
                    </div>
                    {/* 添付ファイルボタン */}
                    <div className="flex items-center gap-2 shrink-0">
                      {req.attachments?.length > 0 && (
                        <button
                          onClick={() => setExpandedId(isExpanded ? null : req.id)}
                          className="flex items-center gap-1 text-xs text-blue-600 hover:text-blue-800"
                        >
                          <Paperclip size={13} />
                          {req.attachments.length}件
                        </button>
                      )}
                      <label className={`flex items-center gap-1 text-xs px-2 py-1 rounded border cursor-pointer transition-colors ${
                        attachUploading === req.id
                          ? 'border-gray-200 text-gray-400 cursor-not-allowed'
                          : 'border-gray-300 text-gray-500 hover:bg-gray-50'
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
                      {req.status === 'pending' && (
                        <button
                          onClick={() => confirm('取り消しますか？') && cancelMut.mutate(req.id)}
                          className="text-xs text-gray-400 hover:text-red-500 flex items-center gap-1"
                        >
                          <X size={12} /> 取消
                        </button>
                      )}
                    </div>
                  </div>

                  {/* 添付ファイル展開エリア */}
                  {isExpanded && req.attachments?.length > 0 && (
                    <div className="bg-gray-50 px-8 py-3 border-t border-gray-100">
                      <p className="text-xs font-medium text-gray-500 mb-2">添付ファイル</p>
                      <div className="flex flex-wrap gap-3">
                        {req.attachments.map((att) => {
                          const isImage = att.content_type.startsWith('image/')
                          return (
                            <div key={att.id}
                              className="flex items-center gap-2 bg-white border border-gray-200 rounded-lg px-3 py-2 text-xs">
                              {isImage ? (
                                <ImageIcon size={14} className="text-blue-400 shrink-0" />
                              ) : (
                                <File size={14} className="text-gray-400 shrink-0" />
                              )}
                              <span className="text-gray-700 max-w-[160px] truncate">{att.file_name}</span>
                              <span className="text-gray-400">{formatFileSize(att.file_size)}</span>
                              <button
                                onClick={() => downloadAttachment(req.id, att.id, att.file_name)}
                                className="text-blue-500 hover:text-blue-700 ml-1"
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
                          )
                        })}
                      </div>
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        )}
      </div>

      {showNew && (
        <NewExpenseModal
          onClose={() => setShowNew(false)}
          onSaved={() => { setShowNew(false); qc.invalidateQueries({ queryKey: ['expense-requests'] }) }}
        />
      )}
    </div>
  )
}

function NewExpenseModal({ onClose, onSaved }: { onClose: () => void; onSaved: () => void }) {
  const today = new Date().toISOString().slice(0, 10)
  const [date, setDate]         = useState(today)
  const [accountId, setAccount] = useState('')
  const [amount, setAmount]     = useState('')
  const [desc, setDesc]         = useState('')
  const [saving, setSaving]     = useState(false)

  const { data: items = [] } = useQuery<AccountItem[]>({
    queryKey: ['account-items'],
    queryFn: () => api.get('/api/v1/expense/account-items/').then((r) => r.data.results ?? r.data),
  })

  const save = async () => {
    setSaving(true)
    try {
      await api.post('/api/v1/expense/requests/', {
        expense_date: date,
        account_item: accountId,
        amount: Number(amount),
        description: desc,
      })
      onSaved()
    } catch (e: any) {
      alert(e.response?.data?.error ?? '申請に失敗しました')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-md">
        <div className="flex items-center justify-between p-6 border-b border-gray-100">
          <h2 className="font-bold text-gray-800">経費申請</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl">×</button>
        </div>
        <div className="p-6 space-y-4">
          <div>
            <label className="text-sm font-medium text-gray-700 block mb-1">経費発生日</label>
            <input type="date" value={date} onChange={(e) => setDate(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm" />
          </div>
          <div>
            <label className="text-sm font-medium text-gray-700 block mb-1">勘定科目</label>
            <select value={accountId} onChange={(e) => setAccount(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm">
              <option value="">選択してください</option>
              {items.map((it) => <option key={it.id} value={it.id}>{it.name}</option>)}
            </select>
          </div>
          <div>
            <label className="text-sm font-medium text-gray-700 block mb-1">金額（円）</label>
            <input type="number" min={1} value={amount} onChange={(e) => setAmount(e.target.value)}
              placeholder="例: 5000"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm" />
          </div>
          <div>
            <label className="text-sm font-medium text-gray-700 block mb-1">説明・用途</label>
            <textarea value={desc} onChange={(e) => setDesc(e.target.value)} rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm resize-none"
              placeholder="任意" />
          </div>
        </div>
        <div className="flex gap-3 px-6 pb-6">
          <button onClick={onClose}
            className="flex-1 py-2.5 border border-gray-300 rounded-lg text-sm text-gray-600 hover:bg-gray-50 font-medium">
            キャンセル
          </button>
          <button onClick={save} disabled={saving || !date || !accountId || !amount}
            className="flex-1 py-2.5 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white rounded-lg text-sm font-medium">
            {saving ? '申請中...' : '申請する'}
          </button>
        </div>
      </div>
    </div>
  )
}
