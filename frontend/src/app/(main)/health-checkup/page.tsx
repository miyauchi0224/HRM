'use client'
import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'
import { useAuthStore } from '@/lib/store'
import { AlertTriangle, Pencil, Plus, Stethoscope } from 'lucide-react'

interface Checkup {
  id: string
  employee: string
  employee_name: string
  department: string
  fiscal_year: number
  checkup_type: string
  checkup_type_label: string
  scheduled_date: string | null
  checkup_date: string | null
  institution: string
  result: string
  result_label: string
  followup_required: boolean
  followup_pending: boolean
  followup_due_date: string | null
  followup_completed_date: string | null
  note: string
}

interface Summary {
  fiscal_year: number
  target_count: number
  checked_count: number
  checkup_rate: number
  followup_required_count: number
  followup_pending_count: number
  unchecked: { employee_id: string; full_name: string; department: string }[]
}

const LABOR_ROLES = ['labor', 'hr', 'admin']
const RESULTS = [
  { value: '',              label: '未判定' },
  { value: 'a_normal',      label: 'A 異常なし' },
  { value: 'b_minor',       label: 'B 軽度異常' },
  { value: 'c_observation', label: 'C 要経過観察' },
  { value: 'd_reexam',      label: 'D 要再検査' },
  { value: 'e_treatment',   label: 'E 要治療' },
]
const TYPES = [
  { value: 'regular', label: '定期健康診断' },
  { value: 'hiring',  label: '雇入時健康診断' },
  { value: 'special', label: '特殊健康診断' },
  { value: 'other',   label: 'その他' },
]

const currentFiscalYear = () => {
  const d = new Date()
  return d.getMonth() >= 3 ? d.getFullYear() : d.getFullYear() - 1
}

/** 健康診断の受診管理（詳細設計書 7.6）。本人は閲覧のみ、労務・人事は全社員分を管理 */
export default function HealthCheckupPage() {
  const role    = useAuthStore((s) => s.user?.role ?? 'employee')
  const isLabor = LABOR_ROLES.includes(role)
  const qc      = useQueryClient()
  const [fy, setFy]                 = useState(currentFiscalYear())
  const [onlyPending, setOnlyPending] = useState(false)
  const [editing, setEditing]       = useState<Checkup | 'new' | null>(null)

  const { data: rows = [], isLoading } = useQuery<Checkup[]>({
    queryKey: ['health-checkups', fy, onlyPending],
    queryFn: () => api.get(`/api/v1/health-checkups/?fiscal_year=${fy}&page_size=100${onlyPending ? '&followup_pending=true' : ''}`)
      .then((r) => r.data.results ?? r.data),
  })
  const { data: summary } = useQuery<Summary>({
    queryKey: ['health-checkups-summary', fy],
    queryFn: () => api.get(`/api/v1/health-checkups/summary/?fiscal_year=${fy}`).then((r) => r.data),
    enabled: isLabor,
  })

  const refresh = () => {
    qc.invalidateQueries({ queryKey: ['health-checkups'] })
    qc.invalidateQueries({ queryKey: ['health-checkups-summary'] })
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-2 flex-wrap gap-2">
        <h1 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
          <Stethoscope size={22} /> 健康診断
        </h1>
        <div className="flex items-center gap-2">
          <select value={fy} onChange={(e) => setFy(Number(e.target.value))}
                  className="px-3 py-2 border border-gray-300 rounded-lg text-sm">
            {[0, 1, 2].map((i) => {
              const y = currentFiscalYear() - i
              return <option key={y} value={y}>{y}年度</option>
            })}
          </select>
          {isLabor && (
            <button onClick={() => setEditing('new')}
                    className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium px-4 py-2 rounded-lg">
              <Plus size={16} /> 登録
            </button>
          )}
        </div>
      </div>
      <p className="text-sm text-gray-500 mb-6">
        {isLabor
          ? '健康情報は要配慮個人情報です。閲覧できるのは本人と労務・人事のみです（上司には表示されません）。'
          : 'あなたの健康診断の記録です。再検査が必要な場合は期限までに受診し、労務担当に報告してください。'}
      </p>

      {isLabor && summary && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          {[
            { label: '受診率',     value: `${summary.checkup_rate}%`, sub: `${summary.checked_count} / ${summary.target_count} 人` },
            { label: '未受診',     value: `${summary.unchecked.length}人`, sub: '定期健診' },
            { label: '要フォロー', value: `${summary.followup_required_count}件`, sub: 'D・E 判定' },
            { label: '再検査 未完了', value: `${summary.followup_pending_count}件`, sub: '' },
          ].map((c) => (
            <div key={c.label} className="bg-white rounded-xl border border-gray-200 p-4 text-center">
              <p className="text-xs text-gray-400 mb-1">{c.label}</p>
              <p className="text-2xl font-bold text-gray-800">{c.value}</p>
              {c.sub && <p className="text-xs text-gray-400 mt-0.5">{c.sub}</p>}
            </div>
          ))}
        </div>
      )}

      <div className="bg-white rounded-xl border border-gray-200 overflow-x-auto">
        <div className="px-5 py-3 border-b border-gray-100 flex items-center justify-between">
          <h2 className="font-semibold text-gray-700">受診記録</h2>
          {isLabor && (
            <label className="text-sm text-gray-600 flex items-center gap-2">
              <input type="checkbox" checked={onlyPending} onChange={(e) => setOnlyPending(e.target.checked)} />
              再検査未完了のみ
            </label>
          )}
        </div>
        {isLoading ? (
          <p className="text-center text-gray-400 text-sm py-10">読み込み中...</p>
        ) : rows.length === 0 ? (
          <p className="text-center text-gray-400 text-sm py-10">記録がありません</p>
        ) : (
          <table className="w-full text-sm min-w-[720px]">
            <thead>
              <tr className="text-gray-400 text-xs border-b border-gray-100">
                {isLabor && <th className="text-left px-5 py-3 font-medium">氏名</th>}
                <th className="text-left px-5 py-3 font-medium">種別</th>
                <th className="text-left px-5 py-3 font-medium">受診日</th>
                <th className="text-left px-5 py-3 font-medium">判定</th>
                <th className="text-left px-5 py-3 font-medium">再検査・受診</th>
                {isLabor && <th className="px-5 py-3" />}
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.id} className="border-b border-gray-50">
                  {isLabor && (
                    <td className="px-5 py-3">
                      <p className="font-medium text-gray-700">{r.employee_name}</p>
                      <p className="text-xs text-gray-400">{r.department}</p>
                    </td>
                  )}
                  <td className="px-5 py-3 text-gray-600">{r.checkup_type_label}</td>
                  <td className="px-5 py-3 text-gray-600">
                    {r.checkup_date ?? <span className="text-gray-400">未受診{r.scheduled_date && `（予定 ${r.scheduled_date}）`}</span>}
                  </td>
                  <td className="px-5 py-3">
                    <span className={`text-xs px-2.5 py-1 rounded-full font-medium ${
                      r.followup_required ? 'bg-red-100 text-red-700' : r.result ? 'bg-gray-100 text-gray-700' : 'text-gray-400'
                    }`}>{r.result_label}</span>
                  </td>
                  <td className="px-5 py-3 text-gray-600">
                    {!r.followup_required ? '—' : r.followup_completed_date ? (
                      <span className="text-green-600">{r.followup_completed_date} 完了</span>
                    ) : (
                      <span className="text-red-600 flex items-center gap-1">
                        <AlertTriangle size={13} /> 期限 {r.followup_due_date ?? '未設定'}
                      </span>
                    )}
                  </td>
                  {isLabor && (
                    <td className="px-5 py-3">
                      <button onClick={() => setEditing(r)} className="text-gray-300 hover:text-blue-500" title="編集">
                        <Pencil size={14} />
                      </button>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {isLabor && summary && summary.unchecked.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 mt-6 p-5">
          <h2 className="font-semibold text-gray-700 mb-3">定期健診 未受診者（{summary.unchecked.length}人）</h2>
          <div className="flex flex-wrap gap-2">
            {summary.unchecked.map((u) => (
              <span key={u.employee_id} className="text-xs bg-gray-100 text-gray-700 rounded-full px-3 py-1">
                {u.full_name}（{u.department}）
              </span>
            ))}
          </div>
        </div>
      )}

      {editing && (
        <CheckupModal
          initial={editing === 'new' ? null : editing}
          fiscalYear={fy}
          onClose={() => setEditing(null)}
          onSaved={() => { setEditing(null); refresh() }}
        />
      )}
    </div>
  )
}

function CheckupModal({ initial, fiscalYear, onClose, onSaved }: {
  initial: Checkup | null; fiscalYear: number; onClose: () => void; onSaved: () => void
}) {
  const [form, setForm] = useState({
    employee:                initial?.employee ?? '',
    fiscal_year:             initial?.fiscal_year ?? fiscalYear,
    checkup_type:            initial?.checkup_type ?? 'regular',
    scheduled_date:          initial?.scheduled_date ?? '',
    checkup_date:            initial?.checkup_date ?? '',
    institution:             initial?.institution ?? '',
    result:                  initial?.result ?? '',
    followup_due_date:       initial?.followup_due_date ?? '',
    followup_completed_date: initial?.followup_completed_date ?? '',
    note:                    initial?.note ?? '',
  })
  const [saving, setSaving] = useState(false)
  const set = (k: keyof typeof form, v: string | number) => setForm((f) => ({ ...f, [k]: v }))
  const needsFollowup = form.result === 'd_reexam' || form.result === 'e_treatment'

  const { data: employees = [] } = useQuery<{ id: string; full_name: string; department: string }[]>({
    queryKey: ['employees-options'],
    // 労務ロールは社員一覧の閲覧権限がないため、全社員を返す選択肢用の一覧を使う
    queryFn: () => api.get('/api/v1/employees/?for_project=true&page_size=100').then((r) => r.data.results ?? r.data),
    enabled: !initial,
  })

  const save = async () => {
    setSaving(true)
    // 空欄の日付は null で送る
    const body = Object.fromEntries(Object.entries(form).map(([k, v]) => [k, v === '' && k.endsWith('date') ? null : v]))
    try {
      if (initial) await api.patch(`/api/v1/health-checkups/${initial.id}/`, body)
      else await api.post('/api/v1/health-checkups/', body)
      onSaved()
    } catch (e: any) {
      const d = e.response?.data
      alert(d?.error ?? d?.checkup_date?.[0] ?? d?.followup_due_date?.[0] ?? d?.employee?.[0] ?? '保存に失敗しました')
    } finally {
      setSaving(false)
    }
  }

  const input = 'w-full px-3 py-2 border border-gray-300 rounded-lg text-sm'
  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-6 border-b border-gray-100">
          <h2 className="font-bold text-gray-800">{initial ? `${initial.employee_name}さんの健康診断` : '健康診断を登録'}</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl leading-none">×</button>
        </div>
        <div className="p-6 grid grid-cols-2 gap-4">
          {!initial && (
            <label className="col-span-2 text-sm text-gray-700">社員
              <select value={form.employee} onChange={(e) => set('employee', e.target.value)} className={`${input} mt-1`}>
                <option value="">選択してください</option>
                {employees.map((e) => <option key={e.id} value={e.id}>{e.full_name}（{e.department}）</option>)}
              </select>
            </label>
          )}
          <label className="text-sm text-gray-700">年度
            <input type="number" value={form.fiscal_year} onChange={(e) => set('fiscal_year', Number(e.target.value))} className={`${input} mt-1`} />
          </label>
          <label className="text-sm text-gray-700">種別
            <select value={form.checkup_type} onChange={(e) => set('checkup_type', e.target.value)} className={`${input} mt-1`}>
              {TYPES.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
            </select>
          </label>
          <label className="text-sm text-gray-700">受診予定日
            <input type="date" value={form.scheduled_date} onChange={(e) => set('scheduled_date', e.target.value)} className={`${input} mt-1`} />
          </label>
          <label className="text-sm text-gray-700">受診日
            <input type="date" value={form.checkup_date} onChange={(e) => set('checkup_date', e.target.value)} className={`${input} mt-1`} />
          </label>
          <label className="col-span-2 text-sm text-gray-700">医療機関
            <input value={form.institution} onChange={(e) => set('institution', e.target.value)} className={`${input} mt-1`} />
          </label>
          <label className="col-span-2 text-sm text-gray-700">判定
            <select value={form.result} onChange={(e) => set('result', e.target.value)} className={`${input} mt-1`}>
              {RESULTS.map((r) => <option key={r.value} value={r.value}>{r.label}</option>)}
            </select>
          </label>
          {needsFollowup && (
            <>
              <label className="text-sm text-gray-700">再検査・受診の期限
                <input type="date" value={form.followup_due_date} onChange={(e) => set('followup_due_date', e.target.value)} className={`${input} mt-1`} />
              </label>
              <label className="text-sm text-gray-700">完了日
                <input type="date" value={form.followup_completed_date} onChange={(e) => set('followup_completed_date', e.target.value)} className={`${input} mt-1`} />
              </label>
            </>
          )}
          <label className="col-span-2 text-sm text-gray-700">備考
            <textarea rows={2} value={form.note} onChange={(e) => set('note', e.target.value)} className={`${input} mt-1 resize-none`} />
          </label>
        </div>
        <div className="flex gap-3 px-6 pb-6">
          <button onClick={onClose} className="flex-1 py-2.5 border border-gray-300 rounded-lg text-sm text-gray-600 hover:bg-gray-50 font-medium">
            キャンセル
          </button>
          <button onClick={save} disabled={saving || (!initial && !form.employee)}
                  className="flex-1 py-2.5 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white rounded-lg text-sm font-medium">
            {saving ? '保存中...' : '保存する'}
          </button>
        </div>
      </div>
    </div>
  )
}
