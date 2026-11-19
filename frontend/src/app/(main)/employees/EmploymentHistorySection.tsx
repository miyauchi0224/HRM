'use client'
import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'
import { useAuthStore } from '@/lib/store'
import { Plus } from 'lucide-react'

interface History {
  id: string
  effective_date: string
  change_type_label: string
  department_before: string
  department_after: string
  position_before: string
  position_after: string
  grade_before: number | null
  grade_after: number | null
  employment_type_before: string
  employment_type_after: string
  note: string
  is_applied: boolean
}

const EMPLOYMENT_TYPE: Record<string, string> = {
  full_time: '正社員', part_time: 'パート', contract: '契約社員', dispatch: '派遣社員',
}

/** 異動・昇格履歴（詳細設計書 7.5）。人事は発令（未来日は予約）を登録できる */
export default function EmploymentHistorySection({ employeeId }: { employeeId: string }) {
  const qc   = useQueryClient()
  const isHR = ['hr', 'admin'].includes(useAuthStore((s) => s.user?.role ?? ''))
  const [showForm, setShowForm] = useState(false)

  const { data: rows = [], isLoading } = useQuery<History[]>({
    queryKey: ['employment-history', employeeId],
    queryFn: () => api.get(`/api/v1/employees/${employeeId}/history/`).then((r) => r.data),
  })

  const changes = (h: History) => {
    const out: string[] = []
    if (h.department_before !== h.department_after) out.push(`部署 ${h.department_before || '—'} → ${h.department_after}`)
    if (h.position_before !== h.position_after) out.push(`役職 ${h.position_before || '—'} → ${h.position_after}`)
    if (h.grade_before !== h.grade_after) out.push(`等級 ${h.grade_before ?? '—'} → ${h.grade_after}`)
    if (h.employment_type_before !== h.employment_type_after) {
      out.push(`雇用形態 ${EMPLOYMENT_TYPE[h.employment_type_before] ?? '—'} → ${EMPLOYMENT_TYPE[h.employment_type_after] ?? h.employment_type_after}`)
    }
    return out
  }

  return (
    <section>
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wide">異動・昇格履歴</h3>
        {isHR && !showForm && (
          <button onClick={() => setShowForm(true)} className="text-xs text-blue-600 flex items-center gap-1">
            <Plus size={12} /> 発令を登録
          </button>
        )}
      </div>

      {showForm && (
        <OrderForm employeeId={employeeId} onDone={() => {
          setShowForm(false)
          qc.invalidateQueries({ queryKey: ['employment-history', employeeId] })
          qc.invalidateQueries({ queryKey: ['employee', employeeId] })
          qc.invalidateQueries({ queryKey: ['employees'] })
        }} onCancel={() => setShowForm(false)} />
      )}

      {isLoading ? (
        <p className="text-sm text-gray-400">読み込み中...</p>
      ) : rows.length === 0 ? (
        <p className="text-sm text-gray-400">履歴はありません</p>
      ) : (
        <ol className="relative border-l border-gray-200 ml-1.5 space-y-3">
          {rows.map((h) => (
            <li key={h.id} className="ml-4">
              <span className={`absolute -left-1.5 mt-1.5 w-3 h-3 rounded-full ${h.is_applied ? 'bg-blue-500' : 'bg-amber-400'}`} />
              <p className="text-sm text-gray-700">
                <span className="font-medium">{h.effective_date}</span>
                <span className="ml-2 text-xs px-2 py-0.5 rounded-full bg-gray-100 text-gray-600">{h.change_type_label}</span>
                {!h.is_applied && <span className="ml-1 text-xs px-2 py-0.5 rounded-full bg-amber-100 text-amber-700">予約</span>}
              </p>
              {changes(h).map((c) => <p key={c} className="text-xs text-gray-500">{c}</p>)}
              {h.note && <p className="text-xs text-gray-400 mt-0.5">{h.note}</p>}
            </li>
          ))}
        </ol>
      )}
    </section>
  )
}

function OrderForm({ employeeId, onDone, onCancel }: { employeeId: string; onDone: () => void; onCancel: () => void }) {
  const [form, setForm] = useState({
    effective_date: new Date().toISOString().slice(0, 10),
    department: '', position: '', grade: '', employment_type: '', note: '',
  })
  const [saving, setSaving] = useState(false)
  const set = (k: keyof typeof form, v: string) => setForm((f) => ({ ...f, [k]: v }))

  const save = async () => {
    setSaving(true)
    try {
      await api.post(`/api/v1/employees/${employeeId}/history/`, {
        ...form, grade: form.grade ? Number(form.grade) : null,
      })
      onDone()
    } catch (e: any) {
      const d = e.response?.data
      alert(d?.error ?? d?.non_field_errors?.[0] ?? d?.effective_date?.[0] ?? '登録に失敗しました')
    } finally {
      setSaving(false)
    }
  }

  const input = 'w-full px-3 py-1.5 border border-gray-300 rounded-lg text-sm'
  return (
    <div className="bg-gray-50 rounded-lg p-3 mb-3 space-y-2">
      <p className="text-xs text-gray-500">変更する項目だけ入力してください。発令日が未来の場合は、その日の朝に自動で反映されます。</p>
      <div className="grid grid-cols-2 gap-2">
        <label className="text-xs text-gray-600">発令日
          <input type="date" value={form.effective_date} onChange={(e) => set('effective_date', e.target.value)} className={input} />
        </label>
        <label className="text-xs text-gray-600">雇用形態
          <select value={form.employment_type} onChange={(e) => set('employment_type', e.target.value)} className={input}>
            <option value="">変更なし</option>
            {Object.entries(EMPLOYMENT_TYPE).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
          </select>
        </label>
        <label className="text-xs text-gray-600">部署
          <input value={form.department} onChange={(e) => set('department', e.target.value)} className={input} />
        </label>
        <label className="text-xs text-gray-600">役職
          <input value={form.position} onChange={(e) => set('position', e.target.value)} className={input} />
        </label>
        <label className="text-xs text-gray-600">等級
          <input type="number" min={1} value={form.grade} onChange={(e) => set('grade', e.target.value)} className={input} />
        </label>
        <label className="text-xs text-gray-600">発令内容・理由
          <input value={form.note} onChange={(e) => set('note', e.target.value)} className={input} />
        </label>
      </div>
      <div className="flex gap-2">
        <button onClick={save} disabled={saving} className="px-3 py-1.5 bg-blue-600 text-white text-xs rounded-lg font-medium">
          {saving ? '登録中...' : '登録'}
        </button>
        <button onClick={onCancel} className="px-3 py-1.5 border border-gray-300 text-gray-600 text-xs rounded-lg">キャンセル</button>
      </div>
    </div>
  )
}
