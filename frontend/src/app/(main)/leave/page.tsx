'use client'
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'
import { AlertTriangle, CalendarCheck, CalendarOff, CheckCircle2, Plus, X } from 'lucide-react'

// ===== 型定義 =====
interface LeaveBalance {
  id: string
  fiscal_year: number
  granted_days: string
  used_days: string
  carried_days: string
  remaining_days: number
}

interface Obligation {
  status: 'ok' | 'warning' | 'overdue' | 'not_applicable'
  grant_date?: string
  deadline?: string
  granted_days?: number
  taken_days?: number
  required_days?: number
  remaining_required?: number
  days_until_deadline?: number
}

interface LeaveGrant {
  id: string
  grant_date: string
  days: string
  expires_on: string
  source: 'auto' | 'manual'
  note: string
}

interface HolidayWork {
  id: string
  date: string
  day_type: string
  work_minutes: number
  valid_until: string
}

interface LeaveRequest {
  id: string
  leave_type: string
  start_date: string
  end_date: string
  days: string
  reason: string
  status: 'pending' | 'approved' | 'rejected' | 'cancelled'
  approved_at: string | null
  created_at: string
  holiday_work_date: string | null
}

const LEAVE_TYPE_LABEL: Record<string, string> = {
  annual: '有給休暇', special: '特別休暇', sick: '病気休暇',
  maternity: '産休', childcare: '育休', bereavement: '忌引き', compensatory: '代休',
}

const STATUS_CONFIG: Record<string, { label: string; color: string }> = {
  pending:   { label: '申請中', color: 'bg-yellow-100 text-yellow-700' },
  approved:  { label: '承認済', color: 'bg-green-100 text-green-700' },
  rejected:  { label: '却下',   color: 'bg-red-100 text-red-600' },
  cancelled: { label: '取消',   color: 'bg-gray-100 text-gray-500' },
}

export default function LeavePage() {
  const currentYear = new Date().getFullYear()
  const fiscalYear  = new Date().getMonth() >= 3 ? currentYear : currentYear - 1
  const [showNew, setShowNew] = useState(false)
  const qc = useQueryClient()

  // 有給残日数
  const { data: balances = [] } = useQuery<LeaveBalance[]>({
    queryKey: ['leave-balances'],
    queryFn: () => api.get('/api/v1/leave/balances/').then((r) => r.data.results ?? r.data),
  })

  // 申請一覧
  const { data: requests = [], isLoading } = useQuery<LeaveRequest[]>({
    queryKey: ['leave-requests'],
    queryFn: () => api.get('/api/v1/leave/requests/').then((r) => r.data.results ?? r.data),
  })

  // 年5日取得義務の状況・付与履歴
  const { data: obligation } = useQuery<Obligation>({
    queryKey: ['leave-obligation'],
    queryFn: () => api.get('/api/v1/leave/grants/obligation/').then((r) => r.data),
  })
  const { data: grants = [] } = useQuery<LeaveGrant[]>({
    queryKey: ['leave-grants'],
    queryFn: () => api.get('/api/v1/leave/grants/').then((r) => r.data.results ?? r.data),
  })

  const cancelMutation = useMutation({
    mutationFn: (id: string) => api.patch(`/api/v1/leave/requests/${id}/cancel/`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['leave-requests'] }),
  })

  const currentBalance = balances.find((b) => b.fiscal_year === fiscalYear)

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
          <CalendarOff size={22} /> 休暇申請
        </h1>
        <button
          onClick={() => setShowNew(true)}
          className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
        >
          <Plus size={16} /> 申請する
        </button>
      </div>

      {/* 有給残日数カード */}
      {currentBalance && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
          {[
            { label: '付与日数', value: currentBalance.granted_days, color: 'text-gray-800' },
            { label: '繰越日数', value: currentBalance.carried_days, color: 'text-gray-800' },
            { label: '使用日数', value: currentBalance.used_days,    color: 'text-orange-600' },
            { label: '残日数',   value: currentBalance.remaining_days, color: 'text-blue-600' },
          ].map(({ label, value, color }) => (
            <div key={label} className="bg-white rounded-xl border border-gray-200 p-4 text-center">
              <p className="text-xs text-gray-400 mb-1">{label}</p>
              <p className={`text-2xl font-bold ${color}`}>{value}<span className="text-sm font-normal ml-1">日</span></p>
            </div>
          ))}
        </div>
      )}

      {/* 年5日取得義務 */}
      {obligation && obligation.status !== 'not_applicable' && <ObligationCard ob={obligation} />}

      {/* 申請一覧 */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <div className="px-5 py-4 border-b border-gray-100">
          <h2 className="font-semibold text-gray-700">申請履歴</h2>
        </div>

        {isLoading ? (
          <p className="text-center text-gray-400 text-sm py-10">読み込み中...</p>
        ) : requests.length === 0 ? (
          <div className="text-center py-12">
            <CalendarOff size={28} className="mx-auto text-gray-300 mb-3" />
            <p className="text-gray-400 text-sm">申請履歴がありません</p>
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-gray-400 text-xs border-b border-gray-100">
                <th className="text-left px-5 py-3 font-medium">種別</th>
                <th className="text-left px-5 py-3 font-medium">期間</th>
                <th className="text-left px-5 py-3 font-medium">日数</th>
                <th className="text-left px-5 py-3 font-medium">理由</th>
                <th className="text-left px-5 py-3 font-medium">状態</th>
                <th className="px-5 py-3" />
              </tr>
            </thead>
            <tbody>
              {requests.map((req) => {
                const st = STATUS_CONFIG[req.status]
                return (
                  <tr key={req.id} className="border-b border-gray-50 hover:bg-gray-50">
                    <td className="px-5 py-3 font-medium text-gray-700">
                      {LEAVE_TYPE_LABEL[req.leave_type] ?? req.leave_type}
                      {req.holiday_work_date && (
                        <span className="block text-xs font-normal text-gray-400">{req.holiday_work_date} 出勤分</span>
                      )}
                    </td>
                    <td className="px-5 py-3 text-gray-600">
                      {req.start_date} 〜 {req.end_date}
                    </td>
                    <td className="px-5 py-3 text-gray-600">{req.days}日</td>
                    <td className="px-5 py-3 text-gray-500 max-w-xs truncate">{req.reason || '—'}</td>
                    <td className="px-5 py-3">
                      <span className={`text-xs px-2.5 py-1 rounded-full font-medium ${st.color}`}>
                        {st.label}
                      </span>
                    </td>
                    <td className="px-5 py-3">
                      {(req.status === 'pending' || req.status === 'approved') && (
                        <button
                          onClick={() => {
                            if (confirm('この申請を取り消しますか？')) {
                              cancelMutation.mutate(req.id)
                            }
                          }}
                          className="text-xs text-gray-400 hover:text-red-500 transition-colors flex items-center gap-1"
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

      {/* 付与履歴 */}
      {grants.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden mt-6">
          <div className="px-5 py-4 border-b border-gray-100">
            <h2 className="font-semibold text-gray-700">有給の付与履歴</h2>
          </div>
          <table className="w-full text-sm">
            <thead>
              <tr className="text-gray-400 text-xs border-b border-gray-100">
                <th className="text-left px-5 py-3 font-medium">付与日</th>
                <th className="text-left px-5 py-3 font-medium">日数</th>
                <th className="text-left px-5 py-3 font-medium">有効期限</th>
                <th className="text-left px-5 py-3 font-medium">区分</th>
              </tr>
            </thead>
            <tbody>
              {grants.map((g) => (
                <tr key={g.id} className="border-b border-gray-50">
                  <td className="px-5 py-3 text-gray-700">{g.grant_date}</td>
                  <td className="px-5 py-3 text-gray-700">{g.days}日</td>
                  <td className="px-5 py-3 text-gray-500">{g.expires_on}</td>
                  <td className="px-5 py-3 text-gray-500">
                    {g.source === 'auto' ? '自動付与' : `手動付与${g.note ? `（${g.note}）` : ''}`}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* 新規申請モーダル */}
      {showNew && (
        <NewLeaveModal
          onClose={() => setShowNew(false)}
          onSaved={() => {
            setShowNew(false)
            qc.invalidateQueries({ queryKey: ['leave-requests'] })
            qc.invalidateQueries({ queryKey: ['leave-balances'] })
            qc.invalidateQueries({ queryKey: ['holiday-work'] })
          }}
        />
      )}
    </div>
  )
}

// ===== 新規申請モーダル =====
function NewLeaveModal({ onClose, onSaved }: { onClose: () => void; onSaved: () => void }) {
  const today = new Date().toISOString().slice(0, 10)
  const [leaveType, setLeaveType] = useState('annual')
  const [startDate, setStart]     = useState(today)
  const [endDate,   setEnd]       = useState(today)
  const [days,      setDays]      = useState('1')
  const [reason,    setReason]    = useState('')
  const [saving,    setSaving]    = useState(false)
  const [holidayWork, setHolidayWork] = useState('')
  const isCompensatory = leaveType === 'compensatory'

  // 代休の元にできる休日出勤（未使用・期限内）
  const { data: holidayWorks = [] } = useQuery<HolidayWork[]>({
    queryKey: ['holiday-work'],
    queryFn: () => api.get('/api/v1/attendance/holiday-work/?unused=true').then((r) => r.data),
    enabled: isCompensatory,
  })

  // 日付変更時に日数を自動計算
  const calcDays = (start: string, end: string) => {
    const s = new Date(start)
    const e = new Date(end)
    if (e >= s) {
      const diff = Math.round((e.getTime() - s.getTime()) / 86400000) + 1
      setDays(String(diff))
    }
  }

  const save = async () => {
    setSaving(true)
    try {
      await api.post('/api/v1/leave/requests/', {
        leave_type: leaveType,
        start_date: startDate,
        end_date: endDate,
        days,
        reason,
        ...(isCompensatory ? { holiday_work: holidayWork } : {}),
      })
      onSaved()
    } catch (e: any) {
      const data = e.response?.data
      const msg = data?.error ?? data?.days?.[0] ?? data?.holiday_work?.[0] ?? data?.start_date?.[0]
        ?? data?.non_field_errors?.[0] ?? '申請に失敗しました'
      alert(msg)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-md">
        <div className="flex items-center justify-between p-6 border-b border-gray-100">
          <h2 className="font-bold text-gray-800">休暇申請</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl leading-none">×</button>
        </div>

        <div className="p-6 space-y-4">
          {/* 種別 */}
          <div>
            <label className="text-sm font-medium text-gray-700 block mb-1">休暇種別</label>
            <select
              value={leaveType}
              onChange={(e) => setLeaveType(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
            >
              {Object.entries(LEAVE_TYPE_LABEL).map(([val, label]) => (
                <option key={val} value={val}>{label}</option>
              ))}
            </select>
          </div>

          {/* 代休の元になる休日出勤 */}
          {isCompensatory && (
            <div>
              <label className="text-sm font-medium text-gray-700 block mb-1">休日出勤日</label>
              {holidayWorks.length === 0 ? (
                <p className="text-sm text-gray-400">代休を取得できる休日出勤がありません</p>
              ) : (
                <select
                  value={holidayWork}
                  onChange={(e) => setHolidayWork(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                >
                  <option value="">選択してください</option>
                  {holidayWorks.map((h) => (
                    <option key={h.id} value={h.id}>
                      {h.date}（{h.day_type === 'legal_holiday' ? '法定休日' : '所定休日'}・
                      {Math.floor(h.work_minutes / 60)}h{h.work_minutes % 60}m）〜{h.valid_until}まで
                    </option>
                  ))}
                </select>
              )}
            </div>
          )}

          {/* 期間 */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-sm font-medium text-gray-700 block mb-1">開始日</label>
              <input
                type="date"
                value={startDate}
                onChange={(e) => { setStart(e.target.value); calcDays(e.target.value, endDate) }}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-gray-700 block mb-1">終了日</label>
              <input
                type="date"
                value={endDate}
                min={startDate}
                onChange={(e) => { setEnd(e.target.value); calcDays(startDate, e.target.value) }}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
              />
            </div>
          </div>

          {/* 日数 */}
          <div>
            <label className="text-sm font-medium text-gray-700 block mb-1">
              日数 <span className="text-xs text-gray-400">（半日の場合は 0.5）</span>
            </label>
            <input
              type="number"
              min={0.5}
              step={0.5}
              value={days}
              onChange={(e) => setDays(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
            />
          </div>

          {/* 理由 */}
          <div>
            <label className="text-sm font-medium text-gray-700 block mb-1">理由・備考</label>
            <textarea
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm resize-none"
              placeholder="任意"
            />
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
            disabled={saving || !startDate || !endDate || !days || (isCompensatory && !holidayWork)}
            className="flex-1 py-2.5 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white rounded-lg text-sm font-medium transition-colors"
          >
            {saving ? '申請中...' : '申請する'}
          </button>
        </div>
      </div>
    </div>
  )
}

// ===== 年5日取得義務カード =====
function ObligationCard({ ob }: { ob: Obligation }) {
  const done    = (ob.remaining_required ?? 0) === 0
  const style   = done
    ? 'border-green-200 bg-green-50'
    : ob.status === 'overdue' ? 'border-red-200 bg-red-50'
    : ob.status === 'warning' ? 'border-amber-200 bg-amber-50'
    : 'border-gray-200 bg-white'
  const percent = Math.min(100, ((ob.taken_days ?? 0) / (ob.required_days ?? 5)) * 100)

  return (
    <div className={`rounded-xl border p-5 mb-6 ${style}`}>
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h2 className="font-semibold text-gray-700 flex items-center gap-2">
            {done
              ? <CheckCircle2 size={16} className="text-green-600" />
              : ob.status === 'ok'
              ? <CalendarCheck size={16} className="text-gray-500" />
              : <AlertTriangle size={16} className={ob.status === 'overdue' ? 'text-red-600' : 'text-amber-600'} />}
            有給の年5日取得義務
          </h2>
          <p className="text-xs text-gray-500 mt-1">
            対象期間 {ob.grant_date} 〜 {ob.deadline}（{ob.granted_days}日付与分）
          </p>
        </div>
        <p className="text-sm text-gray-700">
          {done
            ? '5日の取得が完了しています'
            : ob.status === 'overdue'
            ? `期限を過ぎています。あと ${ob.remaining_required} 日の取得が必要です`
            : `期限まで ${ob.days_until_deadline} 日。あと ${ob.remaining_required} 日の取得が必要です`}
        </p>
      </div>
      <div className="mt-3 h-2 bg-gray-200 rounded-full overflow-hidden">
        <div className={`h-full ${done ? 'bg-green-500' : 'bg-blue-500'}`} style={{ width: `${percent}%` }} />
      </div>
      <p className="text-xs text-gray-500 mt-1">取得済み {ob.taken_days} / {ob.required_days} 日</p>
    </div>
  )
}
