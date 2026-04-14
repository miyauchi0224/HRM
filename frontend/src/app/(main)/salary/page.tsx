'use client'
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import api from '@/lib/api'
import { DollarSign, Download } from 'lucide-react'

interface Payslip {
  id: string
  year: number
  month: number
  base_salary: number
  total_allowances: number
  overtime_pay: number
  gross_salary: number
  health_insurance: number
  pension: number
  employment_insurance: number
  income_tax: number
  resident_tax: number
  total_deductions: number
  net_salary: number
  status: string
}

const fmt = (n: number) => `¥${Number(n).toLocaleString()}`

export default function SalaryPage() {
  const [selected, setSelected] = useState<Payslip | null>(null)
  const [downloading, setDownloading] = useState<string | null>(null)

  const { data: payslips = [], isLoading } = useQuery<Payslip[]>({
    queryKey: ['payslips'],
    queryFn: () => api.get('/api/v1/salary/payslips/').then((r) => r.data.results ?? r.data),
  })

  const download = async (id: string, year: number, month: number) => {
    setDownloading(id)
    try {
      const res = await api.get(`/api/v1/salary/payslips/${id}/download/`, { responseType: 'blob' })
      const url = window.URL.createObjectURL(new Blob([res.data]))
      const a = document.createElement('a')
      a.href = url
      a.download = `payslip_${year}${String(month).padStart(2, '0')}.xlsx`
      a.click()
      window.URL.revokeObjectURL(url)
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
                  <button
                    onClick={(e) => { e.stopPropagation(); download(p.id, p.year, p.month) }}
                    disabled={downloading === p.id}
                    className="text-gray-400 hover:text-blue-600 transition-colors"
                    title="XLSX ダウンロード"
                  >
                    <Download size={16} />
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* 明細詳細 */}
        <div className="lg:col-span-2">
          {selected ? (
            <div className="bg-white rounded-xl border border-gray-200 p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="font-bold text-gray-800 text-lg">
                  {selected.year}年{selected.month}月分 給与明細
                </h2>
                <button
                  onClick={() => download(selected.id, selected.year, selected.month)}
                  disabled={downloading === selected.id}
                  className="flex items-center gap-2 text-sm text-blue-600 hover:text-blue-700"
                >
                  <Download size={15} /> XLSX
                </button>
              </div>

              <div className="grid grid-cols-2 gap-6">
                {/* 支給 */}
                <div>
                  <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">支給</h3>
                  <div className="space-y-2 text-sm">
                    {[
                      ['基本給', selected.base_salary],
                      ['手当合計', selected.total_allowances],
                      ['残業手当', selected.overtime_pay],
                    ].map(([label, val]) => (
                      <div key={label as string} className="flex justify-between">
                        <span className="text-gray-600">{label}</span>
                        <span className="font-medium text-gray-800">{fmt(val as number)}</span>
                      </div>
                    ))}
                    <div className="flex justify-between border-t border-gray-100 pt-2 font-semibold">
                      <span>支給合計</span>
                      <span className="text-blue-600">{fmt(selected.gross_salary)}</span>
                    </div>
                  </div>
                </div>

                {/* 控除 */}
                <div>
                  <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">控除</h3>
                  <div className="space-y-2 text-sm">
                    {[
                      ['健康保険料', selected.health_insurance],
                      ['厚生年金',   selected.pension],
                      ['雇用保険料', selected.employment_insurance],
                      ['所得税',     selected.income_tax],
                      ['住民税',     selected.resident_tax],
                    ].map(([label, val]) => (
                      <div key={label as string} className="flex justify-between">
                        <span className="text-gray-600">{label}</span>
                        <span className="font-medium text-gray-800">{fmt(val as number)}</span>
                      </div>
                    ))}
                    <div className="flex justify-between border-t border-gray-100 pt-2 font-semibold">
                      <span>控除合計</span>
                      <span className="text-red-500">{fmt(selected.total_deductions)}</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* 差引支給額 */}
              <div className="mt-6 bg-blue-50 rounded-xl p-4 flex items-center justify-between">
                <span className="font-bold text-gray-700">差引支給額（手取）</span>
                <span className="text-2xl font-bold text-blue-700">{fmt(selected.net_salary)}</span>
              </div>
            </div>
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
