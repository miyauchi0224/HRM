'use client'
import { useState, useRef } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'
import { useAuthStore } from '@/lib/store'
import { useRouter } from 'next/navigation'
import { Calculator, Download, Upload, Play, Users } from 'lucide-react'

interface Employee { id: string; employee_number: string; full_name: string; department: string }
interface CalcResult { employee_number: string; employee_id: string; year: number; month: number; net_salary: number }

export default function SalaryManagePage() {
  const user   = useAuthStore((s) => s.user)
  const router = useRouter()
  const qc     = useQueryClient()

  // 経理・人事・管理者以外はリダイレクト
  const ACCOUNTING_ROLES = ['hr', 'accounting', 'admin']
  if (user && !ACCOUNTING_ROLES.includes(user.role ?? '')) {
    router.replace('/salary')
    return null
  }

  const today     = new Date()
  const [year, setYear]   = useState(today.getFullYear())
  const [month, setMonth] = useState(today.getMonth() + 1)
  const [empId, setEmpId] = useState('')        // 空 = 全員
  const [running, setRunning]   = useState(false)
  const [calcResult, setCalcResult] = useState<CalcResult[] | null>(null)
  const [uploading, setUploading]   = useState(false)
  const [uploadResult, setUploadResult] = useState<any>(null)
  const fileRef = useRef<HTMLInputElement>(null)

  const { data: employees = [] } = useQuery<Employee[]>({
    queryKey: ['employees-list'],
    queryFn: () => api.get('/api/v1/employees/').then((r) => r.data.results ?? r.data),
  })

  // ===== 給与計算（自動算出）=====
  const runCalc = async () => {
    setRunning(true)
    setCalcResult(null)
    try {
      const body: any = { year, month }
      if (empId) body.employee_id = empId
      const res = await api.post('/api/v1/salary/payslips/calculate/', body)
      setCalcResult(res.data.payslips ?? [])
      qc.invalidateQueries({ queryKey: ['payslips'] })
    } catch (e: any) {
      alert(e.response?.data?.error ?? '給与計算に失敗しました')
    } finally {
      setRunning(false)
    }
  }

  // ===== テンプレートダウンロード =====
  const downloadTemplate = async () => {
    const res = await api.get('/api/v1/salary/payslips/template-csv/', { responseType: 'blob' })
    const a = document.createElement('a')
    a.href = window.URL.createObjectURL(new Blob([res.data]))
    a.download = 'payslip_upload_template.csv'
    a.click()
  }

  // ===== CSVアップロード（一括登録）=====
  const uploadCsv = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    setUploading(true)
    setUploadResult(null)
    try {
      const form = new FormData()
      form.append('file', file)
      const res = await api.post('/api/v1/salary/payslips/import-csv/', form)
      setUploadResult(res.data)
      qc.invalidateQueries({ queryKey: ['payslips'] })
    } catch {
      alert('アップロードに失敗しました')
    } finally {
      setUploading(false)
      if (fileRef.current) fileRef.current.value = ''
    }
  }

  return (
    <div className="max-w-4xl">
      <h1 className="text-2xl font-bold text-gray-800 mb-6 flex items-center gap-2">
        <Calculator size={22} /> 給与計算管理
      </h1>

      {/* ===== 自動計算 ===== */}
      <section className="bg-white rounded-xl border border-gray-200 p-6 mb-6">
        <h2 className="font-semibold text-gray-700 mb-4 flex items-center gap-2">
          <Play size={16} className="text-green-600" /> 自動給与計算
        </h2>
        <p className="text-xs text-gray-400 mb-4">
          勤怠記録・等級・手当マスタをもとに給与を自動計算します。既存の明細は上書きされます。
        </p>

        <div className="flex flex-wrap gap-4 items-end">
          <div>
            <label className="text-xs font-medium text-gray-600 block mb-1">年</label>
            <input
              type="number"
              value={year}
              onChange={(e) => setYear(Number(e.target.value))}
              className="w-24 px-3 py-2 border border-gray-300 rounded-lg text-sm"
              min={2020} max={2099}
            />
          </div>
          <div>
            <label className="text-xs font-medium text-gray-600 block mb-1">月</label>
            <select
              value={month}
              onChange={(e) => setMonth(Number(e.target.value))}
              className="w-24 px-3 py-2 border border-gray-300 rounded-lg text-sm"
            >
              {Array.from({ length: 12 }, (_, i) => i + 1).map((m) => (
                <option key={m} value={m}>{m}月</option>
              ))}
            </select>
          </div>
          <div className="flex-1 min-w-40">
            <label className="text-xs font-medium text-gray-600 block mb-1">
              対象社員（空欄 = 全員）
            </label>
            <select
              value={empId}
              onChange={(e) => setEmpId(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
            >
              <option value="">全員</option>
              {employees.map((emp) => (
                <option key={emp.id} value={emp.id}>
                  [{emp.employee_number}] {emp.full_name}（{emp.department}）
                </option>
              ))}
            </select>
          </div>
          <button
            onClick={runCalc}
            disabled={running}
            className="flex items-center gap-2 px-5 py-2 bg-green-600 hover:bg-green-700 disabled:bg-green-300 text-white text-sm font-medium rounded-lg transition-colors"
          >
            <Play size={15} />
            {running ? '計算中...' : '給与計算を実行'}
          </button>
        </div>

        {/* 計算結果 */}
        {calcResult && (
          <div className="mt-5 border-t border-gray-100 pt-4">
            <p className="text-sm font-medium text-gray-700 mb-3">
              計算完了 — {calcResult.length}件
            </p>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-xs text-gray-400 border-b border-gray-100">
                    <th className="text-left py-2 pr-4 font-medium">社員番号</th>
                    <th className="text-left py-2 pr-4 font-medium">対象月</th>
                    <th className="text-right py-2 font-medium">手取額</th>
                  </tr>
                </thead>
                <tbody>
                  {calcResult.map((r, i) => (
                    <tr key={i} className="border-b border-gray-50">
                      <td className="py-2 pr-4 text-gray-700">{r.employee_number ?? '—'}</td>
                      <td className="py-2 pr-4 text-gray-500">{r.year}年{r.month}月</td>
                      <td className="py-2 text-right font-medium text-gray-800">
                        ¥{Number(r.net_salary ?? 0).toLocaleString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </section>

      {/* ===== CSV一括登録 ===== */}
      <section className="bg-white rounded-xl border border-gray-200 p-6 mb-6">
        <h2 className="font-semibold text-gray-700 mb-4 flex items-center gap-2">
          <Upload size={16} className="text-blue-600" /> CSV一括登録
        </h2>
        <p className="text-xs text-gray-400 mb-4">
          CSVファイルで給与明細を一括登録・更新します。同一社員・年月の明細は上書きされます。
        </p>
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
            <p className="font-medium text-gray-800">
              登録: {uploadResult.created}件　更新: {uploadResult.updated}件
              {uploadResult.errors > 0 && (
                <span className="text-red-600 ml-2">エラー: {uploadResult.errors}件</span>
              )}
            </p>
            {uploadResult.error_details?.length > 0 && (
              <ul className="mt-2 space-y-1">
                {uploadResult.error_details.map((e: any, i: number) => (
                  <li key={i} className="text-red-600 text-xs">{e.row}行目: {e.error}</li>
                ))}
              </ul>
            )}
          </div>
        )}
      </section>

      {/* ===== テンプレートの列説明 ===== */}
      <section className="bg-white rounded-xl border border-gray-200 p-6">
        <h2 className="font-semibold text-gray-700 mb-4">CSVテンプレート 列の説明</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="text-gray-400 border-b border-gray-100">
                <th className="text-left py-2 pr-4 font-medium">列名</th>
                <th className="text-left py-2 pr-4 font-medium">必須</th>
                <th className="text-left py-2 font-medium">説明</th>
              </tr>
            </thead>
            <tbody>
              {[
                ['社員番号', '○', '登録済みの社員番号'],
                ['年', '○', '例: 2026'],
                ['月', '○', '例: 4'],
                ['基本給', '○', '金額（円）'],
                ['技術手当〜時間外手当', '—', '各手当（円、省略時は0）'],
                ['健康保険料〜住民税', '—', '各控除（円、省略時は0）'],
                ['出勤日数・欠勤日数・有給取得日数', '—', '日数（省略時は0）'],
                ['締め日・支給日', '—', 'YYYY/MM/DD 形式（例: 2026/04/15）'],
                ['備考', '—', '任意テキスト'],
              ].map(([col, req, desc]) => (
                <tr key={col} className="border-b border-gray-50">
                  <td className="py-1.5 pr-4 font-mono text-gray-700">{col}</td>
                  <td className="py-1.5 pr-4 text-center">
                    {req === '○'
                      ? <span className="text-red-500 font-medium">○</span>
                      : <span className="text-gray-300">—</span>}
                  </td>
                  <td className="py-1.5 text-gray-500">{desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  )
}
