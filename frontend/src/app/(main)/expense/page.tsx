'use client'
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'
import { Receipt, Plus, X } from 'lucide-react'

interface AccountItem { id: string; code: string; name: string; category: string }
interface ExpenseRequest {
  id: string
  expense_date: string
  account_item: { id: string; name: string }
  amount: number
  description: string
  status: 'pending' | 'approved' | 'rejected' | 'cancelled'
  created_at: string
}

const STATUS_CONFIG: Record<string, { label: string; color: string }> = {
  pending:   { label: '申請中', color: 'bg-yellow-100 text-yellow-700' },
  approved:  { label: '承認済', color: 'bg-green-100 text-green-700' },
  rejected:  { label: '却下',   color: 'bg-red-100 text-red-600' },
  cancelled: { label: '取消',   color: 'bg-gray-100 text-gray-500' },
}

export default function ExpensePage() {
  const [showNew, setShowNew] = useState(false)
  const qc = useQueryClient()

  const { data: requests = [], isLoading } = useQuery<ExpenseRequest[]>({
    queryKey: ['expense-requests'],
    queryFn: () => api.get('/api/v1/expense/requests/').then((r) => r.data.results ?? r.data),
  })

  const cancelMut = useMutation({
    mutationFn: (id: string) => api.patch(`/api/v1/expense/requests/${id}/`, { status: 'cancelled' }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['expense-requests'] }),
  })

  const totalPending  = requests.filter((r) => r.status === 'pending').reduce((s, r) => s + r.amount, 0)
  const totalApproved = requests.filter((r) => r.status === 'approved').reduce((s, r) => s + r.amount, 0)

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
          <table className="w-full text-sm">
            <thead>
              <tr className="text-gray-400 text-xs border-b border-gray-100">
                <th className="text-left px-5 py-3 font-medium">日付</th>
                <th className="text-left px-5 py-3 font-medium">勘定科目</th>
                <th className="text-left px-5 py-3 font-medium">金額</th>
                <th className="text-left px-5 py-3 font-medium">説明</th>
                <th className="text-left px-5 py-3 font-medium">状態</th>
                <th className="px-5 py-3" />
              </tr>
            </thead>
            <tbody>
              {requests.map((req) => {
                const st = STATUS_CONFIG[req.status]
                return (
                  <tr key={req.id} className="border-b border-gray-50 hover:bg-gray-50">
                    <td className="px-5 py-3 text-gray-600">{req.expense_date}</td>
                    <td className="px-5 py-3 text-gray-700">{req.account_item?.name ?? '—'}</td>
                    <td className="px-5 py-3 font-medium text-gray-800">¥{req.amount.toLocaleString()}</td>
                    <td className="px-5 py-3 text-gray-500 max-w-xs truncate">{req.description || '—'}</td>
                    <td className="px-5 py-3">
                      <span className={`text-xs px-2.5 py-1 rounded-full font-medium ${st.color}`}>
                        {st.label}
                      </span>
                    </td>
                    <td className="px-5 py-3">
                      {req.status === 'pending' && (
                        <button
                          onClick={() => confirm('取り消しますか？') && cancelMut.mutate(req.id)}
                          className="text-xs text-gray-400 hover:text-red-500 flex items-center gap-1"
                        >
                          <X size={12} /> 取消
                        </button>
                      )}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
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
