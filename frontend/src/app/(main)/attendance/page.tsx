'use client'
import { useState, useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'
import { useAuthStore } from '@/lib/store'
import {
  Clock, Play, Square, Download, Upload,
  FileSpreadsheet, FileText, File,
  ChevronLeft, ChevronRight, Plus, Pencil, Trash2, X, Check, ShieldAlert,
  GanttChartSquare, CheckCircle2, Circle,
} from 'lucide-react'

type AttendanceStatus = 'not_started' | 'working' | 'break' | 'done'
type Tab = 'clock' | 'export' | 'upload' | 'projects' | 'overtime36' | 'gantt'

// ===== 月ナビゲーション用ユーティリティ =====
function addMonths(ym: string, delta: number): string {
  const [y, m] = ym.split('-').map(Number)
  const d = new Date(y, m - 1 + delta, 1)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
}

interface ProjectEntry {
  project: string   // project UUID
  minutes: number
}

interface EditData {
  stamped_clock_in:  string
  clock_in:          string
  stamped_clock_out: string
  clock_out:         string
  break_minutes:     number
  project_records:   ProjectEntry[]
}

export default function AttendancePage() {
  const qc = useQueryClient()
  const user = useAuthStore((s) => s.user)
  const isManager = user?.role && ['supervisor', 'manager', 'hr', 'accounting', 'admin'].includes(user.role)
  const [breakMinutes, setBreakMinutes] = useState(60)
  const [activeTab, setActiveTab]       = useState<Tab>('clock')
  const [yearMonth, setYearMonth]       = useState(() => new Date().toISOString().slice(0, 7))
  const [editId, setEditId]             = useState<string | null>(null)
  const [editData, setEditData]         = useState<EditData>({ stamped_clock_in: '', clock_in: '', stamped_clock_out: '', clock_out: '', break_minutes: 60, project_records: [] })

  const today = new Date().toISOString().slice(0, 10)

  const { data: records = [] } = useQuery<any[]>({
    queryKey: ['attendance', yearMonth],
    queryFn: () => api.get(`/api/v1/attendance/?year_month=${yearMonth}`).then((r) => r.data.results ?? r.data),
  })

  const { data: projects = [] } = useQuery<any[]>({
    queryKey: ['projects'],
    queryFn: () => api.get('/api/v1/attendance/projects/').then((r) => r.data.results ?? r.data),
  })

  const todayRecord = records.find((r: any) => r.date === today)

  const getStatus = (): AttendanceStatus => {
    if (!todayRecord) return 'not_started'
    if (todayRecord.clock_out) return 'done'
    return 'working'
  }

  const clockInMutation = useMutation({
    mutationFn: () => api.post('/api/v1/attendance/clock-in/', {}),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['attendance'] }),
  })

  const clockOutMutation = useMutation({
    mutationFn: () => api.post('/api/v1/attendance/clock-out/', { break_minutes: breakMinutes }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['attendance'] }),
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<EditData> }) =>
      api.patch(`/api/v1/attendance/${id}/`, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['attendance'] })
      setEditId(null)
    },
  })

  const startEdit = (r: any) => {
    setEditId(r.id)
    setEditData({
      stamped_clock_in:  r.stamped_clock_in  ?? '',
      clock_in:          r.clock_in          ?? '',
      stamped_clock_out: r.stamped_clock_out ?? '',
      clock_out:         r.clock_out         ?? '',
      break_minutes:     r.break_minutes     ?? 60,
      project_records:   (r.project_records ?? []).map((pr: any) => ({
        project: pr.project,
        minutes: pr.minutes,
      })),
    })
  }

  const saveEdit = () => {
    if (!editId) return
    updateMutation.mutate({
      id: editId,
      data: {
        stamped_clock_in:  editData.stamped_clock_in  || null,
        clock_in:          editData.clock_in          || null,
        stamped_clock_out: editData.stamped_clock_out || null,
        clock_out:         editData.clock_out         || null,
        break_minutes:     editData.break_minutes,
        project_records:   editData.project_records.filter((pr) => pr.project),
      },
    })
  }

  // プロジェクト行の操作ヘルパー
  const addProjectEntry = () =>
    setEditData((d) => ({ ...d, project_records: [...d.project_records, { project: '', minutes: 0 }] }))

  const updateProjectEntry = (idx: number, field: keyof ProjectEntry, value: string | number) =>
    setEditData((d) => {
      const updated = [...d.project_records]
      updated[idx] = { ...updated[idx], [field]: value }
      return { ...d, project_records: updated }
    })

  const removeProjectEntry = (idx: number) =>
    setEditData((d) => ({ ...d, project_records: d.project_records.filter((_, i) => i !== idx) }))

  // 編集中のプロジェクト合計分数
  const editTotalPjMinutes = editData.project_records.reduce((s, pr) => s + (Number(pr.minutes) || 0), 0)

  // 編集行の労働時間（clock_in/out から計算）
  const calcWorkMinutes = (ci: string, co: string, brk: number): number => {
    if (!ci || !co) return 0
    const [ch, cm] = ci.split(':').map(Number)
    const [oh, om] = co.split(':').map(Number)
    return Math.max(0, (oh * 60 + om) - (ch * 60 + cm) - brk)
  }
  const editWorkMinutes = calcWorkMinutes(editData.clock_in, editData.clock_out, editData.break_minutes)

  const status = getStatus()

  const tabs: { key: Tab; label: string }[] = [
    { key: 'clock',      label: '打刻' },
    { key: 'export',     label: 'エクスポート' },
    { key: 'upload',     label: 'アップロード' },
    { key: 'projects',   label: 'プロジェクト' },
    { key: 'gantt',      label: 'ガントチャート' },
    ...(isManager ? [{ key: 'overtime36' as Tab, label: '36協定状況' }] : []),
  ]

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-800 mb-6">出退勤管理</h1>

      {/* タブ */}
      <div className="flex gap-1 mb-6 border-b border-gray-200">
        {tabs.map(({ key, label }) => (
          <button
            key={key}
            onClick={() => setActiveTab(key)}
            className={`px-5 py-2 text-sm font-medium rounded-t-lg transition-colors ${
              activeTab === key
                ? 'bg-white border border-b-white border-gray-200 text-blue-600 -mb-px'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {/* === タブ: 打刻 === */}
      {activeTab === 'clock' && (
        <div>
          <div className="bg-white rounded-xl border border-gray-200 p-6 max-w-md mb-6">
            <div className="flex items-center gap-2 mb-4">
              <Clock size={20} className="text-blue-500" />
              <span className="font-semibold text-gray-700">本日 {today}</span>
            </div>

            <div className="mb-6">
              <StatusBadge status={status} />
              {todayRecord?.clock_in && (
                <div className="mt-2 flex items-baseline gap-2">
                  <p className="text-sm text-gray-700 font-medium">出勤: {todayRecord.clock_in}</p>
                  {todayRecord.stamped_clock_in && todayRecord.stamped_clock_in !== todayRecord.clock_in && (
                    <p className="text-xs text-gray-400">打刻: {todayRecord.stamped_clock_in}</p>
                  )}
                </div>
              )}
              {todayRecord?.clock_out && (
                <div className="flex items-baseline gap-2">
                  <p className="text-sm text-gray-700 font-medium">退勤: {todayRecord.clock_out}</p>
                  {todayRecord.stamped_clock_out && todayRecord.stamped_clock_out !== todayRecord.clock_out && (
                    <p className="text-xs text-gray-400">打刻: {todayRecord.stamped_clock_out}</p>
                  )}
                </div>
              )}
              {todayRecord?.work_minutes > 0 && (
                <p className="text-sm text-gray-500 mt-1">
                  労働時間: {Math.floor(todayRecord.work_minutes / 60)}時間{todayRecord.work_minutes % 60}分
                </p>
              )}
            </div>

            <div className="space-y-3">
              {status === 'not_started' && (
                <button
                  onClick={() => clockInMutation.mutate()}
                  disabled={clockInMutation.isPending}
                  className="w-full flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white font-medium py-3 rounded-lg transition-colors"
                >
                  <Play size={18} />
                  {clockInMutation.isPending ? '処理中...' : '出勤'}
                </button>
              )}

              {status === 'working' && (
                <>
                  <div>
                    <label className="text-sm text-gray-600 block mb-1">休憩時間（分）</label>
                    <input
                      type="number"
                      value={breakMinutes}
                      onChange={(e) => setBreakMinutes(Number(e.target.value))}
                      min={0}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                    />
                  </div>
                  <button
                    onClick={() => clockOutMutation.mutate()}
                    disabled={clockOutMutation.isPending}
                    className="w-full flex items-center justify-center gap-2 bg-red-500 hover:bg-red-600 disabled:bg-red-300 text-white font-medium py-3 rounded-lg transition-colors"
                  >
                    <Square size={18} />
                    {clockOutMutation.isPending ? '処理中...' : '退勤'}
                  </button>
                </>
              )}

              {status === 'done' && (
                <p className="text-center text-gray-500 text-sm py-3">
                  本日の勤務が完了しました
                </p>
              )}
            </div>
          </div>

          {/* 月切り替えナビ */}
          <div className="flex items-center gap-3 mb-4">
            <button
              onClick={() => setYearMonth((ym) => addMonths(ym, -1))}
              className="p-1.5 rounded-lg hover:bg-gray-100 text-gray-600 transition-colors"
            >
              <ChevronLeft size={18} />
            </button>
            <span className="font-semibold text-gray-700 min-w-[80px] text-center">
              {yearMonth.replace('-', '年')}月
            </span>
            <button
              onClick={() => setYearMonth((ym) => addMonths(ym, 1))}
              className="p-1.5 rounded-lg hover:bg-gray-100 text-gray-600 transition-colors"
            >
              <ChevronRight size={18} />
            </button>
            {yearMonth !== today.slice(0, 7) && (
              <button
                onClick={() => setYearMonth(today.slice(0, 7))}
                className="text-xs text-blue-600 hover:underline"
              >
                今月に戻る
              </button>
            )}
          </div>

          {/* 勤怠一覧 */}
          <div className="bg-white rounded-xl border border-gray-200 p-5 overflow-x-auto">
            <h2 className="font-semibold text-gray-700 mb-4">
              {yearMonth.replace('-', '年')}月の勤怠
            </h2>
            {records.length > 0 ? (
              <table className="w-full text-sm min-w-[700px]">
                <thead>
                  <tr className="text-gray-500 border-b text-xs">
                    <th className="text-left py-2 font-medium">日付</th>
                    <th className="text-left py-2 font-medium">出勤打刻<br/><span className="text-gray-400 font-normal">出社時刻</span></th>
                    <th className="text-left py-2 font-medium">出勤時刻<br/><span className="text-gray-400 font-normal">勤務開始</span></th>
                    <th className="text-left py-2 font-medium">退勤打刻<br/><span className="text-gray-400 font-normal">退社時刻</span></th>
                    <th className="text-left py-2 font-medium">退勤時刻<br/><span className="text-gray-400 font-normal">勤務終了</span></th>
                    <th className="text-left py-2 font-medium">休憩(分)</th>
                    <th className="text-left py-2 font-medium">プロジェクト</th>
                    <th className="text-left py-2 font-medium">労働時間</th>
                    <th className="text-left py-2 font-medium">残業</th>
                    <th className="py-2 w-16" />
                  </tr>
                </thead>
                <tbody>
                  {records.map((r: any) => (
                    <tr key={r.id} className="border-b border-gray-50 hover:bg-gray-50" onDoubleClick={() => editId !== r.id && startEdit(r)} title="ダブルクリックで編集">
                      {editId === r.id ? (
                        <>
                          {/* 編集行 */}
                          <td className="py-2 pr-2 text-gray-600 text-xs whitespace-nowrap">{r.date}</td>
                          <td className="py-1 pr-1">
                            <input
                              type="time"
                              value={editData.stamped_clock_in}
                              onChange={(e) => setEditData((d) => ({ ...d, stamped_clock_in: e.target.value }))}
                              className="w-[90px] px-1.5 py-1 border border-orange-300 rounded text-xs focus:outline-none focus:ring-1 focus:ring-orange-400"
                              title="出社時刻（打刻）"
                            />
                          </td>
                          <td className="py-1 pr-1">
                            <input
                              type="time"
                              value={editData.clock_in}
                              onChange={(e) => setEditData((d) => ({ ...d, clock_in: e.target.value }))}
                              className="w-[90px] px-1.5 py-1 border border-blue-300 rounded text-xs focus:outline-none focus:ring-1 focus:ring-blue-400"
                              title="勤務開始時刻"
                            />
                          </td>
                          <td className="py-1 pr-1">
                            <input
                              type="time"
                              value={editData.stamped_clock_out}
                              onChange={(e) => setEditData((d) => ({ ...d, stamped_clock_out: e.target.value }))}
                              className="w-[90px] px-1.5 py-1 border border-orange-300 rounded text-xs focus:outline-none focus:ring-1 focus:ring-orange-400"
                              title="退社時刻（打刻）"
                            />
                          </td>
                          <td className="py-1 pr-1">
                            <input
                              type="time"
                              value={editData.clock_out}
                              onChange={(e) => setEditData((d) => ({ ...d, clock_out: e.target.value }))}
                              className="w-[90px] px-1.5 py-1 border border-blue-300 rounded text-xs focus:outline-none focus:ring-1 focus:ring-blue-400"
                              title="勤務終了時刻"
                            />
                          </td>
                          <td className="py-1 pr-1">
                            <input
                              type="number"
                              min={0}
                              value={editData.break_minutes}
                              onChange={(e) => setEditData((d) => ({ ...d, break_minutes: Number(e.target.value) }))}
                              className="w-[60px] px-1.5 py-1 border border-blue-300 rounded text-xs focus:outline-none focus:ring-1 focus:ring-blue-400"
                            />
                          </td>
                          <td className="py-1 pr-1 min-w-[220px]">
                            <div className="space-y-1">
                              {editData.project_records.map((pr, idx) => (
                                <div key={idx} className="flex items-center gap-1">
                                  <select
                                    value={pr.project}
                                    onChange={(e) => updateProjectEntry(idx, 'project', e.target.value)}
                                    className="w-[120px] px-1 py-1 border border-blue-300 rounded text-xs focus:outline-none focus:ring-1 focus:ring-blue-400"
                                  >
                                    <option value="">選択</option>
                                    {projects.map((p: any) => (
                                      <option key={p.id} value={p.id}>{p.code}</option>
                                    ))}
                                  </select>
                                  <input
                                    type="number"
                                    min={0}
                                    value={pr.minutes}
                                    onChange={(e) => updateProjectEntry(idx, 'minutes', Number(e.target.value))}
                                    className="w-[52px] px-1 py-1 border border-blue-300 rounded text-xs focus:outline-none focus:ring-1 focus:ring-blue-400"
                                    placeholder="分"
                                  />
                                  <span className="text-xs text-gray-400">分</span>
                                  <button
                                    onClick={() => removeProjectEntry(idx)}
                                    className="text-gray-300 hover:text-red-400"
                                  >
                                    <X size={12} />
                                  </button>
                                </div>
                              ))}
                              <button
                                onClick={addProjectEntry}
                                className="flex items-center gap-0.5 text-xs text-blue-500 hover:text-blue-700"
                              >
                                <Plus size={11} /> 追加
                              </button>
                              {editData.project_records.length > 0 && (
                                <p className={`text-xs mt-0.5 ${editTotalPjMinutes > editWorkMinutes ? 'text-red-500' : 'text-gray-400'}`}>
                                  合計 {editTotalPjMinutes}分
                                  {editWorkMinutes > 0 && ` / 労働 ${editWorkMinutes}分`}
                                </p>
                              )}
                            </div>
                          </td>
                          <td className="py-1 text-gray-400 text-xs">—</td>
                          <td className="py-1 text-gray-400 text-xs">—</td>
                          <td className="py-1 text-gray-400 text-xs">—</td>
                          <td className="py-1 text-gray-400 text-xs">—</td>
                          <td className="py-1">
                            <div className="flex gap-1">
                              <button
                                onClick={saveEdit}
                                disabled={updateMutation.isPending}
                                className="p-1 text-blue-600 hover:bg-blue-50 rounded disabled:opacity-50"
                                title="保存"
                              >
                                <Check size={14} />
                              </button>
                              <button
                                onClick={() => setEditId(null)}
                                className="p-1 text-gray-400 hover:bg-gray-100 rounded"
                                title="キャンセル"
                              >
                                <X size={14} />
                              </button>
                            </div>
                          </td>
                        </>
                      ) : (
                        <>
                          {/* 表示行 */}
                          <td className="py-2 text-xs text-gray-600 whitespace-nowrap">{r.date}</td>
                          <td className="py-2 text-xs whitespace-nowrap text-orange-600 font-medium">
                            {r.stamped_clock_in ?? '—'}
                          </td>
                          <td className="py-2 text-xs whitespace-nowrap text-blue-700">
                            {r.clock_in ?? '—'}
                          </td>
                          <td className="py-2 text-xs whitespace-nowrap text-orange-600 font-medium">
                            {r.stamped_clock_out ?? '—'}
                          </td>
                          <td className="py-2 text-xs whitespace-nowrap text-blue-700">
                            {r.clock_out ?? '—'}
                          </td>
                          <td className="py-2 text-xs">{r.break_minutes ?? '—'}</td>
                          <td className="py-2 text-xs text-gray-500">
                            {r.project_records?.length > 0
                              ? r.project_records.map((pr: any) => (
                                  <span key={pr.id} className="inline-block mr-1 whitespace-nowrap">
                                    {pr.project_code}
                                    <span className="text-gray-400 ml-0.5">{pr.minutes}m</span>
                                  </span>
                                ))
                              : '—'}
                          </td>
                          <td className="py-2 text-xs">
                            {r.work_minutes > 0
                              ? `${Math.floor(r.work_minutes / 60)}h${r.work_minutes % 60}m`
                              : '—'}
                          </td>
                          <td className={`py-2 text-xs ${r.overtime_minutes > 0 ? 'text-orange-500 font-medium' : ''}`}>
                            {r.overtime_minutes > 0
                              ? `${Math.floor(r.overtime_minutes / 60)}h${r.overtime_minutes % 60}m`
                              : '—'}
                          </td>
                          <td className="py-2">
                            <button
                              onClick={() => startEdit(r)}
                              className="p-1 text-gray-300 hover:text-blue-500 transition-colors"
                              title="編集"
                            >
                              <Pencil size={13} />
                            </button>
                          </td>
                        </>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <p className="text-gray-400 text-sm">打刻記録がありません</p>
            )}
          </div>
        </div>
      )}

      {/* === タブ: エクスポート === */}
      {activeTab === 'export' && (
        <ExportPanel />
      )}

      {/* === タブ: アップロード === */}
      {activeTab === 'upload' && (
        <UploadPanel onSuccess={() => {
          qc.invalidateQueries({ queryKey: ['attendance'] })
          setActiveTab('clock')
        }} />
      )}

      {/* === タブ: プロジェクト === */}
      {activeTab === 'projects' && (
        <ProjectsPanel />
      )}

      {/* === タブ: ガントチャート === */}
      {activeTab === 'gantt' && (
        <GanttPanel />
      )}

      {/* === タブ: 36協定状況 === */}
      {activeTab === 'overtime36' && (
        <OvertimeDashboardPanel />
      )}
    </div>
  )
}

// ===== エクスポートパネル =====
function ExportPanel() {
  const currentMonth = new Date().toISOString().slice(0, 7)
  const currentYear  = new Date().getFullYear()
  const [yearMonth, setYearMonth] = useState(currentMonth)
  const [year, setYear]           = useState(currentYear)
  const [loading, setLoading]     = useState<string | null>(null)

  const MIME_MAP: Record<string, string> = {
    xlsx: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    csv:  'text/csv; charset=utf-8',
    pdf:  'application/pdf',
  }

  const download = async (url: string, ext: 'xlsx' | 'csv' | 'pdf') => {
    setLoading(ext)
    try {
      const res = await api.get(url, { responseType: 'blob' })
      const cd = res.headers['content-disposition'] ?? ''
      const match = cd.match(/filename[^;=\n]*=(['"]?)([^'";\n]+)\1/)
      const serverFilename = match ? match[2].trim() : ''
      const filename = serverFilename && serverFilename.endsWith(`.${ext}`)
        ? serverFilename
        : `export_${Date.now()}.${ext}`

      const blob = new Blob([res.data], { type: MIME_MAP[ext] })
      const blobUrl = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = blobUrl
      a.download = filename
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      window.URL.revokeObjectURL(blobUrl)
    } catch {
      alert('ダウンロードに失敗しました')
    } finally {
      setLoading(null)
    }
  }

  return (
    <div className="max-w-lg space-y-6">
      {/* 月次エクスポート */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h2 className="font-semibold text-gray-700 mb-1 flex items-center gap-2">
          <Download size={16} /> 月次エクスポート（CSV / PDF）
        </h2>
        <p className="text-xs text-gray-400 mb-4">指定月の勤怠データを出力します</p>

        <div className="mb-4">
          <label className="text-sm text-gray-600 block mb-1">対象月</label>
          <input
            type="month"
            value={yearMonth}
            onChange={(e) => setYearMonth(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm w-full"
          />
        </div>

        <div className="flex gap-3">
          <button
            onClick={() => download(`/api/v1/attendance/csv-export/?year_month=${yearMonth}`, 'csv')}
            disabled={loading !== null}
            className="flex-1 flex items-center justify-center gap-2 bg-green-600 hover:bg-green-700 disabled:bg-green-300 text-white text-sm font-medium py-2.5 rounded-lg transition-colors"
          >
            <FileText size={16} />
            {loading === 'csv' ? '生成中...' : 'CSV ダウンロード'}
          </button>

          <button
            onClick={() => download(`/api/v1/attendance/pdf-export/?year_month=${yearMonth}`, 'pdf')}
            disabled={loading !== null}
            className="flex-1 flex items-center justify-center gap-2 bg-red-600 hover:bg-red-700 disabled:bg-red-300 text-white text-sm font-medium py-2.5 rounded-lg transition-colors"
          >
            <File size={16} />
            {loading === 'pdf' ? '生成中...' : 'PDF ダウンロード'}
          </button>
        </div>
      </div>

      {/* 年度エクスポート（XLSX） */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h2 className="font-semibold text-gray-700 mb-1 flex items-center gap-2">
          <FileSpreadsheet size={16} /> 年度エクスポート（XLSX）
        </h2>
        <p className="text-xs text-gray-400 mb-4">
          1年分の勤怠表（月別シート）を Excel 形式でダウンロードします
        </p>

        <div className="mb-4">
          <label className="text-sm text-gray-600 block mb-1">対象年度</label>
          <select
            value={year}
            onChange={(e) => setYear(Number(e.target.value))}
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm w-full"
          >
            {[currentYear - 1, currentYear, currentYear + 1].map((y) => (
              <option key={y} value={y}>{y}年度</option>
            ))}
          </select>
        </div>

        <button
          onClick={() => download(`/api/v1/attendance/template/?year=${year}`, 'xlsx')}
          disabled={loading !== null}
          className="w-full flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white text-sm font-medium py-2.5 rounded-lg transition-colors"
        >
          <FileSpreadsheet size={16} />
          {loading === 'xlsx' ? '生成中...' : 'XLSX ダウンロード'}
        </button>
      </div>
    </div>
  )
}

// ===== アップロードパネル =====
function UploadPanel({ onSuccess }: { onSuccess: () => void }) {
  const [file, setFile]       = useState<File | null>(null)
  const [result, setResult]   = useState<{ created: number; updated: number; errors: string[] } | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError]     = useState<string | null>(null)
  const fileRef = useRef<HTMLInputElement>(null)

  const handleUpload = async () => {
    if (!file) return
    setLoading(true)
    setResult(null)
    setError(null)

    const form = new FormData()
    form.append('file', file)

    try {
      const res = await api.post('/api/v1/attendance/upload/', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      setResult(res.data)
      setFile(null)
      if (fileRef.current) fileRef.current.value = ''
      if (res.data.created > 0 || res.data.updated > 0) onSuccess()
    } catch (e: any) {
      setError(e.response?.data?.error ?? 'アップロードに失敗しました')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-lg">
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h2 className="font-semibold text-gray-700 mb-1 flex items-center gap-2">
          <Upload size={16} /> 勤怠データのアップロード
        </h2>
        <p className="text-xs text-gray-400 mb-5">
          XLSX または CSV ファイルをアップロードして出退勤情報を一括登録・更新します
        </p>

        <div className="bg-gray-50 rounded-lg p-4 mb-5 text-xs text-gray-600">
          <p className="font-semibold mb-2">対応フォーマット</p>
          <p className="mb-1">
            <span className="font-medium">XLSX：</span>
            OC作業表テンプレート（年度エクスポートで取得したファイル）
          </p>
          <p>
            <span className="font-medium">CSV：</span>
            列順 — 日付, 曜日, 出勤時刻, 退勤時刻, 休憩(分), 労働時間(分), 残業時間(分), プロジェクト, 備考
          </p>
        </div>

        <div
          className="border-2 border-dashed border-gray-300 rounded-xl p-8 text-center mb-4 cursor-pointer hover:border-blue-400 transition-colors"
          onClick={() => fileRef.current?.click()}
          onDragOver={(e) => e.preventDefault()}
          onDrop={(e) => {
            e.preventDefault()
            const f = e.dataTransfer.files[0]
            if (f) setFile(f)
          }}
        >
          <Upload size={28} className="mx-auto text-gray-400 mb-2" />
          {file ? (
            <p className="text-sm font-medium text-blue-600">{file.name}</p>
          ) : (
            <>
              <p className="text-sm text-gray-500">クリックまたはドラッグ＆ドロップ</p>
              <p className="text-xs text-gray-400 mt-1">.xlsx / .csv</p>
            </>
          )}
          <input
            ref={fileRef}
            type="file"
            accept=".xlsx,.csv"
            className="hidden"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          />
        </div>

        <button
          onClick={handleUpload}
          disabled={!file || loading}
          className="w-full flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 text-white font-medium py-3 rounded-lg transition-colors"
        >
          <Upload size={16} />
          {loading ? 'アップロード中...' : 'アップロード'}
        </button>

        {result && (
          <div className={`mt-4 p-4 rounded-lg text-sm ${result.errors.length > 0 ? 'bg-yellow-50 border border-yellow-200' : 'bg-green-50 border border-green-200'}`}>
            <p className="font-semibold mb-1">
              {result.errors.length === 0 ? '✓ アップロード完了' : '⚠ 一部エラーがあります'}
            </p>
            <p className="text-gray-600">新規登録: {result.created}件　更新: {result.updated}件</p>
            {result.errors.length > 0 && (
              <ul className="mt-2 space-y-1">
                {result.errors.map((e, i) => (
                  <li key={i} className="text-red-600 text-xs">{e}</li>
                ))}
              </ul>
            )}
          </div>
        )}

        {error && (
          <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg text-sm text-red-600">
            {error}
          </div>
        )}
      </div>
    </div>
  )
}

// ===== プロジェクト管理パネル =====
interface Manager {
  id: string
  full_name: string
}

interface Project {
  id: string
  code: string
  name: string
  primary_managers: Manager[]
  secondary_managers: Manager[]
  primary_manager_ids?: string[]
  secondary_manager_ids?: string[]
  start_date: string | null
  end_date: string | null
}

function ProjectsPanel() {
  const qc = useQueryClient()
  const [showNew, setShowNew]   = useState(false)
  const [editId, setEditId]     = useState<string | null>(null)
  const [editData, setEditData] = useState<Partial<Project>>({})

  const { data: projects = [], isLoading } = useQuery<Project[]>({
    queryKey: ['projects'],
    queryFn: () => api.get('/api/v1/attendance/projects/').then((r) => r.data.results ?? r.data),
  })

  const { data: employees = [] } = useQuery<any[]>({
    queryKey: ['employees-list'],
    queryFn: () => api.get('/api/v1/employees/').then((r) => r.data.results ?? r.data),
  })

  const deleteMut = useMutation({
    mutationFn: (id: string) => api.delete(`/api/v1/attendance/projects/${id}/`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['projects'] }),
  })

  const updateMut = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Project> }) =>
      api.patch(`/api/v1/attendance/projects/${id}/`, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['projects'] })
      setEditId(null)
    },
  })

  const startEdit = (p: Project) => {
    setEditId(p.id)
    setEditData({ code: p.code, name: p.name, manager: p.manager })
  }

  return (
    <div className="max-w-2xl">
      <div className="flex items-center justify-between mb-4">
        <h2 className="font-semibold text-gray-700">プロジェクト一覧</h2>
        <button
          onClick={() => setShowNew(true)}
          className="flex items-center gap-1.5 text-sm bg-blue-600 hover:bg-blue-700 text-white px-3 py-1.5 rounded-lg"
        >
          <Plus size={14} /> 追加
        </button>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        {isLoading ? (
          <p className="text-gray-400 text-sm p-6">読み込み中...</p>
        ) : projects.length === 0 ? (
          <p className="text-gray-400 text-sm p-6">プロジェクトが登録されていません</p>
        ) : (
          <table className="w-full text-sm">
            <thead className="bg-gray-50">
              <tr className="text-gray-500 text-xs">
                <th className="text-left px-4 py-3 font-medium">件番</th>
                <th className="text-left px-4 py-3 font-medium">プロジェクト名</th>
                <th className="text-left px-4 py-3 font-medium">管理者</th>
                <th className="px-4 py-3 w-20" />
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {projects.map((p) => (
                <tr key={p.id} className="hover:bg-gray-50">
                  {editId === p.id ? (
                    <>
                      <td className="px-4 py-2">
                        <input
                          value={editData.code ?? ''}
                          onChange={(e) => setEditData((d) => ({ ...d, code: e.target.value }))}
                          className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
                        />
                      </td>
                      <td className="px-4 py-2">
                        <input
                          value={editData.name ?? ''}
                          onChange={(e) => setEditData((d) => ({ ...d, name: e.target.value }))}
                          className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
                        />
                      </td>
                      <td className="px-4 py-2 space-y-2">
                        <div>
                          <label className="text-xs text-gray-500 block mb-1">主管理者</label>
                          <select
                            multiple
                            value={editData.primary_manager_ids ?? []}
                            onChange={(e) => setEditData((d) => ({
                              ...d,
                              primary_manager_ids: Array.from(e.target.selectedOptions, (opt) => opt.value)
                            }))}
                            className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
                            size={2}
                          >
                            {employees.map((e: any) => (
                              <option key={e.id} value={e.id}>{e.full_name}</option>
                            ))}
                          </select>
                        </div>
                        <div>
                          <label className="text-xs text-gray-500 block mb-1">従管理者</label>
                          <select
                            multiple
                            value={editData.secondary_manager_ids ?? []}
                            onChange={(e) => setEditData((d) => ({
                              ...d,
                              secondary_manager_ids: Array.from(e.target.selectedOptions, (opt) => opt.value)
                            }))}
                            className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
                            size={2}
                          >
                            {employees.map((e: any) => (
                              <option key={e.id} value={e.id}>{e.full_name}</option>
                            ))}
                          </select>
                        </div>
                      </td>
                      <td className="px-4 py-2">
                        <div className="flex gap-1.5">
                          <button
                            onClick={() => updateMut.mutate({ id: p.id, data: editData })}
                            className="p-1 text-blue-600 hover:bg-blue-50 rounded"
                          >
                            <Check size={14} />
                          </button>
                          <button
                            onClick={() => setEditId(null)}
                            className="p-1 text-gray-400 hover:bg-gray-100 rounded"
                          >
                            <X size={14} />
                          </button>
                        </div>
                      </td>
                    </>
                  ) : (
                    <>
                      <td className="px-4 py-3 font-mono text-gray-700">{p.code}</td>
                      <td className="px-4 py-3 text-gray-800">{p.name}</td>
                      <td className="px-4 py-3 text-gray-500">
                        <div className="space-y-1">
                          {p.primary_managers?.length > 0 && (
                            <div className="text-xs">
                              <span className="font-medium text-gray-600">主: </span>
                              {p.primary_managers.map(m => m.full_name).join(', ')}
                            </div>
                          )}
                          {p.secondary_managers?.length > 0 && (
                            <div className="text-xs">
                              <span className="font-medium text-gray-600">従: </span>
                              {p.secondary_managers.map(m => m.full_name).join(', ')}
                            </div>
                          )}
                          {!p.primary_managers?.length && !p.secondary_managers?.length && '—'}
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex gap-1.5">
                          <button
                            onClick={() => startEdit(p)}
                            className="p-1 text-gray-300 hover:text-blue-500 transition-colors"
                          >
                            <Pencil size={13} />
                          </button>
                          <button
                            onClick={() => confirm('このプロジェクトを削除しますか？') && deleteMut.mutate(p.id)}
                            className="p-1 text-gray-300 hover:text-red-500 transition-colors"
                          >
                            <Trash2 size={13} />
                          </button>
                        </div>
                      </td>
                    </>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {showNew && (
        <NewProjectModal
          employees={employees}
          onClose={() => setShowNew(false)}
          onSaved={() => {
            setShowNew(false)
            qc.invalidateQueries({ queryKey: ['projects'] })
          }}
        />
      )}
    </div>
  )
}

function NewProjectModal({
  employees,
  onClose,
  onSaved,
}: {
  employees: any[]
  onClose: () => void
  onSaved: () => void
}) {
  const [code,              setCode]              = useState('')
  const [name,              setName]              = useState('')
  const [primaryManagers,   setPrimaryManagers]   = useState<string[]>([])
  const [secondaryManagers, setSecondaryManagers] = useState<string[]>([])
  const [saving,            setSaving]            = useState(false)
  const [error,             setError]             = useState('')

  const save = async () => {
    setSaving(true)
    setError('')
    try {
      await api.post('/api/v1/attendance/projects/', {
        code,
        name,
        primary_manager_ids: primaryManagers,
        secondary_manager_ids: secondaryManagers,
      })
      onSaved()
    } catch (e: any) {
      setError(
        e.response?.data?.code?.[0] ??
        e.response?.data?.name?.[0] ??
        e.response?.data?.primary_manager_ids?.[0] ??
        '登録に失敗しました'
      )
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-sm">
        <div className="flex items-center justify-between p-5 border-b border-gray-100">
          <h2 className="font-bold text-gray-800">プロジェクトを追加</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl">×</button>
        </div>
        <div className="p-5 space-y-4">
          <div>
            <label className="text-sm font-medium text-gray-700 block mb-1">
              件番 <span className="text-red-500">*</span>
            </label>
            <input
              value={code}
              onChange={(e) => setCode(e.target.value)}
              placeholder="例: PJ-2026-001"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
            />
          </div>
          <div>
            <label className="text-sm font-medium text-gray-700 block mb-1">
              プロジェクト名 <span className="text-red-500">*</span>
            </label>
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="例: ○○システム開発"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
            />
          </div>
          <div>
            <label className="text-sm font-medium text-gray-700 block mb-1">
              主管理者 <span className="text-red-500">*</span>
            </label>
            <select
              multiple
              value={primaryManagers}
              onChange={(e) => setPrimaryManagers(Array.from(e.target.selectedOptions, (opt) => opt.value))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
              size={3}
            >
              {employees.map((e: any) => (
                <option key={e.id} value={e.id}>{e.full_name}</option>
              ))}
            </select>
            <p className="text-xs text-gray-500 mt-1">Ctrl+クリックで複数選択</p>
          </div>
          <div>
            <label className="text-sm font-medium text-gray-700 block mb-1">
              従管理者
            </label>
            <select
              multiple
              value={secondaryManagers}
              onChange={(e) => setSecondaryManagers(Array.from(e.target.selectedOptions, (opt) => opt.value))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
              size={3}
            >
              {employees.map((e: any) => (
                <option key={e.id} value={e.id}>{e.full_name}</option>
              ))}
            </select>
          </div>
          {error && <p className="text-sm text-red-600">{error}</p>}
        </div>
        <div className="flex gap-3 px-5 pb-5">
          <button
            onClick={onClose}
            className="flex-1 py-2.5 border border-gray-300 rounded-lg text-sm text-gray-600 hover:bg-gray-50 font-medium"
          >
            キャンセル
          </button>
          <button
            onClick={save}
            disabled={!code.trim() || !name.trim() || primaryManagers.length === 0 || saving}
            className="flex-1 py-2.5 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white rounded-lg text-sm font-medium"
          >
            {saving ? '登録中...' : '登録'}
          </button>
        </div>
      </div>
    </div>
  )
}

// ===== ガントチャートパネル =====
function GanttPanel() {
  const qc = useQueryClient()
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null)
  const [showTaskForm, setShowTaskForm] = useState(false)
  const [editTask, setEditTask] = useState<any | null>(null)
  const [taskForm, setTaskForm] = useState({ title: '', start_date: '', end_date: '', status: 'todo', progress: 0, assignee: '', description: '' })

  const { data: projects = [] } = useQuery<any[]>({
    queryKey: ['projects-all'],
    queryFn: () => api.get('/api/v1/attendance/projects/').then(r => r.data.results ?? r.data),
  })
  const { data: employees = [] } = useQuery<any[]>({
    queryKey: ['employees-mini'],
    queryFn: () => api.get('/api/v1/employees/').then(r => r.data.results ?? r.data),
  })
  const { data: ganttData, isLoading } = useQuery<any>({
    queryKey: ['gantt', selectedProjectId],
    queryFn: () => api.get(`/api/v1/attendance/projects/${selectedProjectId}/gantt/`).then(r => r.data),
    enabled: !!selectedProjectId,
  })

  const createTaskMut = useMutation({
    mutationFn: (data: any) => api.post('/api/v1/attendance/project-tasks/', { ...data, project: selectedProjectId }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['gantt', selectedProjectId] }); setShowTaskForm(false); resetForm() },
  })
  const updateTaskMut = useMutation({
    mutationFn: ({ id, data }: any) => api.patch(`/api/v1/attendance/project-tasks/${id}/`, data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['gantt', selectedProjectId] }); setEditTask(null) },
  })
  const deleteTaskMut = useMutation({
    mutationFn: (id: string) => api.delete(`/api/v1/attendance/project-tasks/${id}/`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['gantt', selectedProjectId] }),
  })

  const resetForm = () => setTaskForm({ title: '', start_date: '', end_date: '', status: 'todo', progress: 0, assignee: '', description: '' })

  const tasks: any[] = ganttData?.tasks ?? []
  const project = ganttData?.project

  // ガントチャート描画用: 全タスクの日付範囲を計算
  const allDates = tasks.flatMap(t => [t.start_date, t.end_date].filter(Boolean))
  const minDate = allDates.length > 0 ? allDates.reduce((a, b) => a < b ? a : b) : new Date().toISOString().slice(0, 10)
  const maxDate = allDates.length > 0 ? allDates.reduce((a, b) => a > b ? a : b) : new Date().toISOString().slice(0, 10)
  const startMs = new Date(minDate).getTime()
  const endMs   = new Date(maxDate).getTime()
  const totalDays = Math.max(1, Math.ceil((endMs - startMs) / 86400000) + 1)

  const STATUS_COLOR: Record<string, string> = {
    todo: 'bg-gray-300', in_progress: 'bg-blue-400', review: 'bg-yellow-400', done: 'bg-green-400',
  }
  const STATUS_LABEL: Record<string, string> = {
    todo: '未着手', in_progress: '進行中', review: 'レビュー中', done: '完了',
  }

  const downloadTemplate = async () => {
    if (!selectedProjectId) return
    const res = await api.get(`/api/v1/attendance/projects/${selectedProjectId}/template-csv/`, { responseType: 'blob' })
    const url = URL.createObjectURL(res.data)
    const a = document.createElement('a')
    a.href = url; a.download = 'tasks_template.csv'; a.click()
    URL.revokeObjectURL(url)
  }

  const [importFile, setImportFile] = useState<File | null>(null)
  const importRef = useRef<HTMLInputElement>(null)
  const importMut = useMutation({
    mutationFn: (fd: FormData) => api.post(`/api/v1/attendance/projects/${selectedProjectId}/import-tasks/`, fd),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['gantt', selectedProjectId] }); setImportFile(null) },
  })

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <GanttChartSquare size={20} className="text-blue-500" />
        <h2 className="font-semibold text-gray-700">プロジェクト ガントチャート</h2>
        <select
          value={selectedProjectId ?? ''}
          onChange={e => setSelectedProjectId(e.target.value || null)}
          className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm ml-auto"
        >
          <option value="">プロジェクトを選択</option>
          {projects.map(p => <option key={p.id} value={p.id}>{p.code} {p.name}</option>)}
        </select>
      </div>

      {selectedProjectId && (
        <>
          {/* プロジェクト情報 */}
          {project && (
            <div className="bg-white border border-gray-200 rounded-xl p-4 text-sm">
              <div className="flex items-center justify-between">
                <div>
                  <span className="font-semibold text-gray-800">{project.code} {project.name}</span>
                  <span className="ml-3 text-gray-500 text-xs">{project.start_date} 〜 {project.end_date}</span>
                </div>
                <div className="flex gap-2">
                  <button onClick={downloadTemplate} className="text-xs border border-gray-300 px-2 py-1 rounded hover:bg-gray-50">テンプレートDL</button>
                  <button onClick={() => importRef.current?.click()} className="text-xs border border-blue-300 text-blue-600 px-2 py-1 rounded hover:bg-blue-50">CSV一括登録</button>
                  <input ref={importRef} type="file" accept=".csv" className="hidden"
                    onChange={e => { const f = e.target.files?.[0]; if (f) { const fd = new FormData(); fd.append('file', f); importMut.mutate(fd) } }} />
                  <button onClick={() => setShowTaskForm(true)} className="text-xs bg-blue-600 text-white px-2 py-1 rounded hover:bg-blue-700">+ タスク追加</button>
                </div>
              </div>
            </div>
          )}

          {/* ガントチャート */}
          {isLoading ? <p className="text-gray-400 text-sm">読み込み中...</p> : tasks.length === 0 ? (
            <p className="text-gray-400 text-sm bg-white border rounded-xl p-8 text-center">タスクがありません。「タスク追加」から作業項目を登録してください。</p>
          ) : (
            <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
              <div className="overflow-x-auto">
                <table className="text-xs w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="text-left px-3 py-2 font-medium text-gray-600 w-48 min-w-[12rem]">タスク名</th>
                      <th className="text-left px-3 py-2 font-medium text-gray-600 w-20">担当者</th>
                      <th className="text-left px-3 py-2 font-medium text-gray-600 w-20">ステータス</th>
                      <th className="text-right px-3 py-2 font-medium text-gray-600 w-12">進捗</th>
                      <th className="px-3 py-2 font-medium text-gray-600 min-w-[300px]">
                        <div className="flex justify-between text-gray-400">
                          <span>{minDate}</span><span>{maxDate}</span>
                        </div>
                      </th>
                      <th className="w-16" />
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {tasks.map(task => {
                      const taskStart = task.start_date ? new Date(task.start_date).getTime() : startMs
                      const taskEnd   = task.end_date   ? new Date(task.end_date).getTime()   : taskStart
                      const leftPct   = totalDays > 1 ? ((taskStart - startMs) / (endMs - startMs)) * 100 : 0
                      const widthPct  = totalDays > 1 ? Math.max(2, ((taskEnd - taskStart) / (endMs - startMs)) * 100) : 100
                      return (
                        <tr key={task.id} className="hover:bg-gray-50">
                          <td className="px-3 py-2 font-medium text-gray-800 truncate max-w-[12rem]">{task.title}</td>
                          <td className="px-3 py-2 text-gray-500 truncate">{task.assignee_name ?? '—'}</td>
                          <td className="px-3 py-2">
                            <span className={`px-1.5 py-0.5 rounded text-white text-xs ${STATUS_COLOR[task.status]}`}>
                              {STATUS_LABEL[task.status]}
                            </span>
                          </td>
                          <td className="px-3 py-2 text-right text-gray-600">{task.progress}%</td>
                          <td className="px-3 py-2">
                            <div className="relative h-5 bg-gray-100 rounded">
                              {task.start_date && (
                                <div
                                  className={`absolute h-full rounded ${STATUS_COLOR[task.status]} opacity-80`}
                                  style={{ left: `${leftPct}%`, width: `${widthPct}%` }}
                                  title={`${task.start_date} 〜 ${task.end_date}`}
                                />
                              )}
                            </div>
                          </td>
                          <td className="px-3 py-2 text-right">
                            <button onClick={() => { setEditTask(task); setTaskForm({ title: task.title, start_date: task.start_date ?? '', end_date: task.end_date ?? '', status: task.status, progress: task.progress, assignee: task.assignee ?? '', description: task.description }) }} className="p-1 text-gray-400 hover:text-blue-500"><Pencil size={12} /></button>
                            <button onClick={() => { if (confirm('削除しますか？')) deleteTaskMut.mutate(task.id) }} className="p-1 text-gray-400 hover:text-red-500"><Trash2 size={12} /></button>
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* タスク追加フォーム */}
          {(showTaskForm || editTask) && (
            <div className="bg-white border border-gray-200 rounded-xl p-4">
              <h3 className="font-medium text-gray-700 mb-3 text-sm">{editTask ? 'タスク編集' : 'タスク追加'}</h3>
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div className="col-span-2">
                  <label className="text-xs text-gray-500 block mb-1">タスク名 *</label>
                  <input value={taskForm.title} onChange={e => setTaskForm(f => ({...f, title: e.target.value}))} className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm" />
                </div>
                <div>
                  <label className="text-xs text-gray-500 block mb-1">担当者</label>
                  <select value={taskForm.assignee} onChange={e => setTaskForm(f => ({...f, assignee: e.target.value}))} className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm">
                    <option value="">未割当</option>
                    {employees.map((emp: any) => <option key={emp.id} value={emp.id}>{emp.full_name}</option>)}
                  </select>
                </div>
                <div>
                  <label className="text-xs text-gray-500 block mb-1">ステータス</label>
                  <select value={taskForm.status} onChange={e => setTaskForm(f => ({...f, status: e.target.value}))} className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm">
                    {Object.entries(STATUS_LABEL).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
                  </select>
                </div>
                <div>
                  <label className="text-xs text-gray-500 block mb-1">開始予定日</label>
                  <input type="date" value={taskForm.start_date} onChange={e => setTaskForm(f => ({...f, start_date: e.target.value}))} className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm" />
                </div>
                <div>
                  <label className="text-xs text-gray-500 block mb-1">終了予定日</label>
                  <input type="date" value={taskForm.end_date} onChange={e => setTaskForm(f => ({...f, end_date: e.target.value}))} className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm" />
                </div>
                <div>
                  <label className="text-xs text-gray-500 block mb-1">進捗率 ({taskForm.progress}%)</label>
                  <input type="range" min={0} max={100} value={taskForm.progress} onChange={e => setTaskForm(f => ({...f, progress: Number(e.target.value)}))} className="w-full" />
                </div>
              </div>
              <div className="flex gap-2 mt-3">
                <button
                  onClick={() => {
                    const payload = { title: taskForm.title, start_date: taskForm.start_date || null, end_date: taskForm.end_date || null, status: taskForm.status, progress: taskForm.progress, assignee: taskForm.assignee || null, description: taskForm.description }
                    editTask ? updateTaskMut.mutate({ id: editTask.id, data: payload }) : createTaskMut.mutate(payload)
                  }}
                  disabled={!taskForm.title}
                  className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white text-xs rounded-lg font-medium"
                >
                  {editTask ? '更新' : '追加'}
                </button>
                <button onClick={() => { setShowTaskForm(false); setEditTask(null); resetForm() }} className="px-3 py-1.5 bg-gray-200 hover:bg-gray-300 text-gray-700 text-xs rounded-lg">キャンセル</button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}

// ===== 36協定状況ダッシュボード =====
function OvertimeDashboardPanel() {
  const [yearMonth, setYearMonth] = useState(() => new Date().toISOString().slice(0, 7))

  const { data, isLoading } = useQuery<any>({
    queryKey: ['overtime-dashboard', yearMonth],
    queryFn: () => api.get(`/api/v1/attendance/overtime-dashboard/?year_month=${yearMonth}`).then((r) => r.data),
  })

  const RISK_CONFIG = {
    green:  { label: '正常',   badge: 'bg-green-100 text-green-700',  row: '' },
    yellow: { label: '警告',   badge: 'bg-yellow-100 text-yellow-700', row: 'bg-yellow-50' },
    red:    { label: '超過',   badge: 'bg-red-100 text-red-700',      row: 'bg-red-50' },
  }

  const employees: any[] = data?.employees ?? []
  const redCount    = employees.filter((e) => e.risk_level === 'red').length
  const yellowCount = employees.filter((e) => e.risk_level === 'yellow').length

  return (
    <div className="max-w-4xl">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <ShieldAlert size={20} className="text-orange-500" />
          <h2 className="font-semibold text-gray-700">36協定 残業時間モニタリング</h2>
        </div>
        <input
          type="month"
          value={yearMonth}
          onChange={(e) => setYearMonth(e.target.value)}
          className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm"
        />
      </div>

      <div className="grid grid-cols-3 gap-3 mb-4">
        {[
          { label: '全社員', value: employees.length, cls: 'bg-white border-gray-200 text-gray-700' },
          { label: '⚠ 警告（45h超）', value: yellowCount, cls: 'bg-yellow-50 border-yellow-200 text-yellow-700' },
          { label: '🚨 超過（60h超/360h超）', value: redCount, cls: 'bg-red-50 border-red-200 text-red-700' },
        ].map((item) => (
          <div key={item.label} className={`rounded-xl border p-4 text-center ${item.cls}`}>
            <p className="text-2xl font-bold">{item.value}</p>
            <p className="text-xs mt-1">{item.label}</p>
          </div>
        ))}
      </div>

      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        {isLoading ? (
          <p className="text-gray-400 text-sm p-6 text-center">読み込み中...</p>
        ) : (
          <table className="w-full text-sm">
            <thead className="bg-gray-50">
              <tr className="text-gray-500 text-xs">
                <th className="text-left px-4 py-3 font-medium">社員番号</th>
                <th className="text-left px-4 py-3 font-medium">氏名</th>
                <th className="text-left px-4 py-3 font-medium">部署</th>
                <th className="text-left px-4 py-3 font-medium">代表者</th>
                <th className="text-right px-4 py-3 font-medium">月間残業(h)</th>
                <th className="text-right px-4 py-3 font-medium">年間残業(h)</th>
                <th className="text-center px-4 py-3 font-medium">状態</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {employees.map((emp) => {
                const cfg = RISK_CONFIG[emp.risk_level as keyof typeof RISK_CONFIG]
                return (
                  <tr key={emp.employee_id} className={`hover:brightness-95 transition-colors ${cfg.row}`}>
                    <td className="px-4 py-3 text-gray-500">{emp.employee_number}</td>
                    <td className="px-4 py-3 font-medium text-gray-800">{emp.full_name}</td>
                    <td className="px-4 py-3 text-gray-600">{emp.department}</td>
                    <td className="px-4 py-3 text-gray-500 text-xs">{emp.representative || '—'}</td>
                    <td className="px-4 py-3 text-right font-mono">{emp.monthly_overtime_hours}</td>
                    <td className="px-4 py-3 text-right font-mono">{emp.annual_overtime_hours}</td>
                    <td className="px-4 py-3 text-center">
                      <span className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium ${cfg.badge}`}>
                        {cfg.label}
                      </span>
                    </td>
                  </tr>
                )
              })}
              {employees.length === 0 && (
                <tr><td colSpan={7} className="px-4 py-8 text-center text-gray-400">データがありません</td></tr>
              )}
            </tbody>
          </table>
        )}
      </div>
      <p className="text-xs text-gray-400 mt-2">
        閾値: 月45h超で警告 / 月60h超または年360h超で超過（36協定基準）
      </p>
    </div>
  )
}

function StatusBadge({ status }: { status: AttendanceStatus }) {
  const config = {
    not_started: { label: '未出勤',  className: 'bg-gray-100 text-gray-600' },
    working:     { label: '出勤中',  className: 'bg-green-100 text-green-700' },
    break:       { label: '休憩中',  className: 'bg-yellow-100 text-yellow-700' },
    done:        { label: '退勤済',  className: 'bg-blue-100 text-blue-700' },
  }[status]
  return (
    <span className={`inline-block px-3 py-1 rounded-full text-sm font-medium ${config.className}`}>
      {config.label}
    </span>
  )
}
