'use client'
import { toast } from '@/lib/toast'
import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'
import { useAuthStore } from '@/lib/store'
import { Plus, Trash2, UserCheck } from 'lucide-react'

interface Delegation {
  id: string
  delegator: string
  delegator_name: string
  delegate: string
  delegate_name: string
  start_date: string
  end_date: string
  reason: string
  is_active: boolean
}

interface EmployeeOption { id: string; full_name: string; department: string }

/** 代理承認の設定（詳細設計書 7.3） */
export default function DelegationPage() {
  const qc   = useQueryClient()
  const user = useAuthStore((s) => s.user)
  const [showNew, setShowNew] = useState(false)

  const { data: rows = [], isLoading } = useQuery<Delegation[]>({
    queryKey: ['approval-delegations'],
    queryFn: () => api.get('/api/v1/approval/delegations/').then((r) => r.data.results ?? r.data),
  })

  const remove = useMutation({
    mutationFn: (id: string) => api.delete(`/api/v1/approval/delegations/${id}/`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['approval-delegations'] }),
    onError: (e: any) => toast.error(e.response?.data?.error ?? '削除に失敗しました'),
  })

  const mine     = rows.filter((r) => r.delegator_name === user?.full_name)
  const received = rows.filter((r) => r.delegate_name === user?.full_name)
  const others   = rows.filter((r) => !mine.includes(r) && !received.includes(r))

  return (
    <div className="max-w-3xl">
      <div className="flex items-center justify-between mb-2">
        <h1 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
          <UserCheck size={22} /> 代理承認設定
        </h1>
        <button
          onClick={() => setShowNew(true)}
          className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium px-4 py-2 rounded-lg"
        >
          <Plus size={16} /> 代理人を設定
        </button>
      </div>
      <p className="text-sm text-gray-500 mb-6">
        休暇などで不在の間、代理人があなたの代わりに休暇・経費・打刻修正・稟議を承認できます。承認依頼の通知も代理人に届きます。
      </p>

      {isLoading ? (
        <p className="text-gray-400 text-sm">読み込み中...</p>
      ) : (
        <div className="space-y-6">
          <Section title="自分の不在時の代理人" rows={mine} onDelete={(id) => confirm('この設定を削除しますか？') && remove.mutate(id)} showDelete />
          <Section title="自分が代理人になっている設定" rows={received} />
          {others.length > 0 && (
            <Section title="その他の設定（人事）" rows={others} onDelete={(id) => confirm('この設定を削除しますか？') && remove.mutate(id)} showDelete />
          )}
        </div>
      )}

      {showNew && (
        <NewDelegationModal
          onClose={() => setShowNew(false)}
          onSaved={() => { setShowNew(false); qc.invalidateQueries({ queryKey: ['approval-delegations'] }) }}
        />
      )}
    </div>
  )
}

function Section({ title, rows, onDelete, showDelete = false }: {
  title: string; rows: Delegation[]; onDelete?: (id: string) => void; showDelete?: boolean
}) {
  return (
    <section className="bg-white rounded-xl border border-gray-200">
      <h2 className="px-5 py-3 border-b border-gray-100 font-semibold text-gray-700 text-sm">{title}</h2>
      {rows.length === 0 ? (
        <p className="px-5 py-6 text-sm text-gray-400">設定はありません</p>
      ) : (
        <ul className="divide-y divide-gray-50">
          {rows.map((r) => (
            <li key={r.id} className="px-5 py-3 flex items-center gap-3 text-sm">
              <div className="flex-1">
                <p className="text-gray-700">
                  <span className="font-medium">{r.delegator_name}</span>
                  <span className="text-gray-400 mx-2">→</span>
                  <span className="font-medium">{r.delegate_name}</span>
                </p>
                <p className="text-xs text-gray-500">
                  {r.start_date} 〜 {r.end_date}{r.reason && `（${r.reason}）`}
                </p>
              </div>
              {r.is_active && (
                <span className="text-xs px-2 py-0.5 rounded-full bg-green-100 text-green-700">有効</span>
              )}
              {showDelete && onDelete && (
                <button onClick={() => onDelete(r.id)} className="text-gray-300 hover:text-red-500" title="削除">
                  <Trash2 size={15} />
                </button>
              )}
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}

function NewDelegationModal({ onClose, onSaved }: { onClose: () => void; onSaved: () => void }) {
  const today = new Date().toISOString().slice(0, 10)
  const [delegate, setDelegate] = useState('')
  const [start, setStart]       = useState(today)
  const [end, setEnd]           = useState(today)
  const [reason, setReason]     = useState('')
  const [saving, setSaving]     = useState(false)

  // 代理人の候補（プロジェクト管理者選択と同じく全社員を取得）
  const { data: employees = [] } = useQuery<EmployeeOption[]>({
    queryKey: ['employees-all-options'],
    queryFn: () => api.get('/api/v1/employees/?for_project=true&page_size=100').then((r) => r.data.results ?? r.data),
  })

  const save = async () => {
    setSaving(true)
    try {
      await api.post('/api/v1/approval/delegations/', { delegate, start_date: start, end_date: end, reason })
      onSaved()
    } catch (e: any) {
      const d = e.response?.data
      toast.error(d?.error ?? d?.detail ?? d?.delegate?.[0] ?? d?.end_date?.[0] ?? '登録に失敗しました')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-md">
        <div className="flex items-center justify-between p-6 border-b border-gray-100">
          <h2 className="font-bold text-gray-800">代理人を設定</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl leading-none">×</button>
        </div>
        <div className="p-6 space-y-4">
          <div>
            <label className="text-sm font-medium text-gray-700 block mb-1">代理人</label>
            <select value={delegate} onChange={(e) => setDelegate(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm">
              <option value="">選択してください</option>
              {employees.map((e) => (
                <option key={e.id} value={e.id}>{e.full_name}（{e.department}）</option>
              ))}
            </select>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-sm font-medium text-gray-700 block mb-1">開始日</label>
              <input type="date" value={start} onChange={(e) => setStart(e.target.value)}
                     className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm" />
            </div>
            <div>
              <label className="text-sm font-medium text-gray-700 block mb-1">終了日</label>
              <input type="date" value={end} min={start} onChange={(e) => setEnd(e.target.value)}
                     className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm" />
            </div>
          </div>
          <div>
            <label className="text-sm font-medium text-gray-700 block mb-1">理由</label>
            <input value={reason} onChange={(e) => setReason(e.target.value)} placeholder="例：夏季休暇"
                   className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm" />
          </div>
        </div>
        <div className="flex gap-3 px-6 pb-6">
          <button onClick={onClose}
                  className="flex-1 py-2.5 border border-gray-300 rounded-lg text-sm text-gray-600 hover:bg-gray-50 font-medium">
            キャンセル
          </button>
          <button onClick={save} disabled={saving || !delegate}
                  className="flex-1 py-2.5 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white rounded-lg text-sm font-medium">
            {saving ? '登録中...' : '登録する'}
          </button>
        </div>
      </div>
    </div>
  )
}
