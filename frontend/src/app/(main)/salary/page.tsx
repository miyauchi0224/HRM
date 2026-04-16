'use client'
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'
import { useAuthStore } from '@/lib/store'
import { DollarSign, Download, FileText } from 'lucide-react'

interface Payslip {
  id: string
  year: number
  month: number
  employee_name: string
  employee_number: string
  department: string
  bank_info: string
  // 支給
  base_salary: number
  technical_allowance: number
  secondment_allowance: number
  housing_allowance: number
  overtime_pay: number
  commute_allowance: number
  family_allowance: number
  certification_allowance: number
  position_allowance: number
  special_allowance: number
  perfect_attendance_allowance: number
  diligence_allowance: number
  extra_overtime_pay: number
  total_allowances: number
  gross_salary: number
  // 控除
  health_insurance: number
  pension: number
  employment_insurance: number
  nursing_insurance: number
  social_insurance_total: number
  property_savings: number
  company_housing_fee: number
  union_fee: number
  mutual_aid_fee: number
  employee_stock_contribution: number
  other_deductions: number
  income_tax: number
  resident_tax: number
  total_deductions: number
  // 差引
  net_salary: number
  // 勤怠
  work_days: number
  absence_days: number
  paid_leave_days: number
  // 管理
  cutoff_date: string | null
  payment_date: string | null
  note: string
  status: string
}

const fmt = (n: number) => `¥${Number(n ?? 0).toLocaleString()}`

// 金額が0でないもののみ表示するヘルパー
function Row({ label, value, bold, color }: {
  label: string; value: number; bold?: boolean; color?: string
}) {
  if (!value && value !== 0) return null
  return (
    <div className={`flex justify-between py-1 border-b border-gray-50 text-sm ${bold ? 'font-semibold' : ''}`}>
      <span className="text-gray-600">{label}</span>
      <span className={color ?? (bold ? 'text-gray-800' : 'text-gray-700')}>{fmt(value)}</span>
    </div>
  )
}

export default function SalaryPage() {
  const user = useAuthStore((s) => s.user)
  const isHR = user?.role === 'hr' || user?.role === 'admin'

  const [selected, setSelected]     = useState<Payslip | null>(null)
  const [downloading, setDownloading] = useState<string | null>(null)

  const { data: payslips = [], isLoading } = useQuery<Payslip[]>({
    queryKey: ['payslips'],
    queryFn: () => api.get('/api/v1/salary/payslips/').then((r) => r.data.results ?? r.data),
  })

  const download = async (id: string, year: number, month: number, type: 'xlsx' | 'pdf') => {
    setDownloading(`${id}-${type}`)
    try {
      const url = type === 'xlsx'
        ? `/api/v1/salary/payslips/${id}/download/`
        : `/api/v1/salary/payslips/${id}/download-pdf/`
      const res = await api.get(url, { responseType: 'blob' })
      const blob = new Blob([res.data], {
        type: type === 'xlsx'
          ? 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
          : 'application/pdf',
      })
      const a = document.createElement('a')
      a.href = window.URL.createObjectURL(blob)
      a.download = `payslip_${year}${String(month).padStart(2, '0')}.${type}`
      a.click()
      window.URL.revokeObjectURL(a.href)
    } catch {
      alert('ダウンロードに失敗しました')
    } finally {
      setDownloading(null)
    }
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-800 mb-6 flex items-center gap-2">
        <DollarSign size={22} /> 給与明細
      </h1>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 明細一覧 */}
        <div className="lg:col-span-1 bg-white rounded-xl border border-gray-200 overflow-hidden">
          <div className="px-4 py-3 border-b border-gray-100 text-sm font-semibold text-gray-700">
            明細一覧
          </div>
          {isLoading ? (
            <p className="text-center text-gray-400 text-sm py-10">読み込み中...</p>
          ) : payslips.length === 0 ? (
            <p className="text-center text-gray-400 text-sm py-10">給与明細がありません</p>
          ) : (
            <ul>
              {payslips.map((p) => (
                <li
                  key={p.id}
                  onClick={() => setSelected(p)}
                  className={`flex items-center justify-between px-4 py-3 cursor-pointer border-b border-gray-50 hover:bg-gray-50 transition-colors ${selected?.id === p.id ? 'bg-blue-50' : ''}`}
                >
                  <div>
                    <p className="font-medium text-gray-800 text-sm">{p.year}年{p.month}月分</p>
                    <p className="text-xs text-gray-400 mt-0.5">手取 {fmt(p.net_salary)}</p>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={(e) => { e.stopPropagation(); download(p.id, p.year, p.month, 'xlsx') }}
                      disabled={downloading !== null}
                      className="text-gray-400 hover:text-green-600 transition-colors"
                      title="XLSX ダウンロード"
                    >
                      <Download size={15} />
                    </button>
                    <button
                      onClick={(e) => { e.stopPropagation(); download(p.id, p.year, p.month, 'pdf') }}
                      disabled={downloading !== null}
                      className="text-gray-400 hover:text-red-500 transition-colors"
                      title="PDF ダウンロード"
                    >
                      <FileText size={15} />
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* 明細詳細 */}
        <div className="lg:col-span-2 overflow-y-auto max-h-[calc(100vh-180px)]">
          {selected ? (
            <PayslipDetail
              payslip={selected}
              downloading={downloading}
              onDownload={download}
            />
          ) : (
            <div className="bg-white rounded-xl border border-dashed border-gray-300 h-64 flex items-center justify-center">
              <p className="text-gray-400 text-sm">左の一覧から月を選択してください</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function PayslipDetail({ payslip: p, downloading, onDownload }: {
  payslip: Payslip
  downloading: string | null
  onDownload: (id: string, year: number, month: number, type: 'xlsx' | 'pdf') => void
}) {
  return (
    <div className="bg-white rounded-xl border border-gray-200">
      {/* ヘッダー */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100 bg-blue-700 rounded-t-xl">
        <div>
          <h2 className="font-bold text-white text-lg">
            {p.year}年{p.month}月分 給与明細
          </h2>
          {p.payment_date && (
            <p className="text-blue-200 text-xs mt-0.5">支給日: {p.payment_date}</p>
          )}
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => onDownload(p.id, p.year, p.month, 'xlsx')}
            disabled={downloading !== null}
            className="flex items-center gap-1.5 text-xs bg-white/20 hover:bg-white/30 text-white px-3 py-1.5 rounded-lg transition-colors"
          >
            <Download size={13} /> XLSX
          </button>
          <button
            onClick={() => onDownload(p.id, p.year, p.month, 'pdf')}
            disabled={downloading !== null}
            className="flex items-center gap-1.5 text-xs bg-white/20 hover:bg-white/30 text-white px-3 py-1.5 rounded-lg transition-colors"
          >
            <FileText size={13} /> PDF
          </button>
        </div>
      </div>

      <div className="p-6 space-y-6">
        {/* 社員情報 */}
        <section className="grid grid-cols-2 gap-4 text-sm bg-gray-50 rounded-lg p-4">
          <InfoItem label="社員番号" value={p.employee_number} />
          <InfoItem label="氏名"     value={p.employee_name} />
          <InfoItem label="部署"     value={p.department} />
          {p.cutoff_date && <InfoItem label="締め日" value={p.cutoff_date} />}
          {p.bank_info && (
            <div className="col-span-2">
              <InfoItem label="振込口座" value={p.bank_info} />
            </div>
          )}
        </section>

        {/* 勤怠情報 */}
        <section>
          <SectionHeader label="勤怠情報" />
          <div className="grid grid-cols-3 gap-3 mt-2">
            {[
              { label: '出勤日数', value: `${p.work_days}日` },
              { label: '欠勤日数', value: `${p.absence_days}日` },
              { label: '有給取得', value: `${p.paid_leave_days}日` },
            ].map((item) => (
              <div key={item.label} className="bg-gray-50 rounded-lg px-3 py-2 text-center">
                <p className="text-xs text-gray-500">{item.label}</p>
                <p className="font-semibold text-gray-800 mt-0.5">{item.value}</p>
              </div>
            ))}
          </div>
        </section>

        <div className="grid grid-cols-2 gap-6">
          {/* 支給明細 */}
          <section>
            <SectionHeader label="支給明細" color="blue" />
            <div className="mt-2 space-y-0">
              <Row label="基本給"               value={p.base_salary} />
              <Row label="技術手当"             value={p.technical_allowance} />
              <Row label="出向手当"             value={p.secondment_allowance} />
              <Row label="住宅手当"             value={p.housing_allowance} />
              <Row label="残業手当"             value={p.overtime_pay} />
              <Row label="通勤手当（交通費）"   value={p.commute_allowance} />
              <Row label="家族手当"             value={p.family_allowance} />
              <Row label="資格手当"             value={p.certification_allowance} />
              <Row label="役職手当"             value={p.position_allowance} />
              <Row label="特別手当（賞与・臨時）" value={p.special_allowance} />
              <Row label="皆勤手当"             value={p.perfect_attendance_allowance} />
              <Row label="精勤手当"             value={p.diligence_allowance} />
              <Row label="時間外手当（深夜・休日）" value={p.extra_overtime_pay} />
            </div>
            <div className="flex justify-between pt-2 mt-1 border-t-2 border-blue-200 text-sm font-bold">
              <span className="text-gray-700">支給合計</span>
              <span className="text-blue-700">{fmt(p.gross_salary)}</span>
            </div>
          </section>

          {/* 控除明細 */}
          <section>
            <SectionHeader label="控除明細" color="red" />
            <div className="mt-2 space-y-0">
              <Row label="健康保険料"     value={p.health_insurance} />
              <Row label="厚生年金"       value={p.pension} />
              <Row label="雇用保険料"     value={p.employment_insurance} />
              {p.nursing_insurance > 0 && (
                <Row label="介護保険料" value={p.nursing_insurance} />
              )}
              <div className="flex justify-between py-1 border-b border-gray-100 text-sm bg-blue-50 px-1 rounded font-medium">
                <span className="text-gray-600">社会保険料合計</span>
                <span className="text-gray-700">{fmt(p.social_insurance_total)}</span>
              </div>
              <Row label="財形貯蓄"       value={p.property_savings} />
              <Row label="社宅・寮費"     value={p.company_housing_fee} />
              <Row label="組合費"         value={p.union_fee} />
              <Row label="共済会費"       value={p.mutual_aid_fee} />
              <Row label="持株会拠出金"   value={p.employee_stock_contribution} />
              <Row label="その他控除"     value={p.other_deductions} />
              <Row label="所得税"         value={p.income_tax} />
              <Row label="住民税"         value={p.resident_tax} />
            </div>
            <div className="flex justify-between pt-2 mt-1 border-t-2 border-red-200 text-sm font-bold">
              <span className="text-gray-700">控除合計</span>
              <span className="text-red-600">{fmt(p.total_deductions)}</span>
            </div>
          </section>
        </div>

        {/* 差引支給額 */}
        <div className="bg-blue-700 rounded-xl p-5 flex items-center justify-between">
          <span className="font-bold text-white text-base">差引支給額（手取）</span>
          <span className="text-2xl font-bold text-white">{fmt(p.net_salary)}</span>
        </div>

        {/* 備考 */}
        {p.note && (
          <section className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
            <p className="text-xs font-semibold text-yellow-700 mb-1">備考</p>
            <p className="text-sm text-gray-700 whitespace-pre-wrap">{p.note}</p>
          </section>
        )}
      </div>
    </div>
  )
}

function SectionHeader({ label, color }: { label: string; color?: 'blue' | 'red' }) {
  const bg = color === 'blue'
    ? 'bg-blue-600 text-white'
    : color === 'red'
    ? 'bg-red-500 text-white'
    : 'bg-gray-700 text-white'
  return (
    <div className={`text-xs font-semibold px-3 py-1.5 rounded-lg ${bg}`}>
      {label}
    </div>
  )
}

function InfoItem({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs text-gray-400">{label}</p>
      <p className="text-sm font-medium text-gray-800">{value || '—'}</p>
    </div>
  )
}
