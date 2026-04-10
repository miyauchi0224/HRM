'use client'
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'
import { Clock, Play, Square, Coffee } from 'lucide-react'

type AttendanceStatus = 'not_started' | 'working' | 'break' | 'done'

export default function AttendancePage() {
  const qc = useQueryClient()
  const [breakMinutes, setBreakMinutes] = useState(60)

  // 今日の勤怠記録を取得
  const today = new Date().toISOString().slice(0, 10)
  const { data: records } = useQuery({
    queryKey: ['attendance', today],
    queryFn: () => api.get(`/api/v1/attendance/?year_month=${today.slice(0, 7)}`).then((r) => r.data.results),
  })

  const todayRecord = records?.find((r: any) => r.date === today)

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

  const status = getStatus()

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-800 mb-6">出退勤打刻</h1>

      {/* 打刻カード */}
      <div className="bg-white rounded-xl border border-gray-200 p-6 max-w-md mb-6">
        <div className="flex items-center gap-2 mb-4">
          <Clock size={20} className="text-blue-500" />
          <span className="font-semibold text-gray-700">本日 {today}</span>
        </div>

        {/* 現在の状態 */}
        <div className="mb-6">
          <StatusBadge status={status} />
          {todayRecord?.clock_in && (
            <p className="text-sm text-gray-500 mt-2">出勤: {todayRecord.clock_in}</p>
          )}
          {todayRecord?.clock_out && (
            <p className="text-sm text-gray-500">退勤: {todayRecord.clock_out}</p>
          )}
          {todayRecord?.work_minutes > 0 && (
            <p className="text-sm text-gray-500">
              労働時間: {Math.floor(todayRecord.work_minutes / 60)}時間{todayRecord.work_minutes % 60}分
            </p>
          )}
        </div>

        {/* ボタン */}
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

      {/* 今月の勤怠一覧 */}
      <div className="bg-white rounded-xl border border-gray-200 p-5">
        <h2 className="font-semibold text-gray-700 mb-4">今月の勤怠</h2>
        {records && records.length > 0 ? (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-gray-500 border-b">
                <th className="text-left py-2 font-medium">日付</th>
                <th className="text-left py-2 font-medium">出勤</th>
                <th className="text-left py-2 font-medium">退勤</th>
                <th className="text-left py-2 font-medium">労働時間</th>
                <th className="text-left py-2 font-medium">残業</th>
              </tr>
            </thead>
            <tbody>
              {records.map((r: any) => (
                <tr key={r.id} className="border-b border-gray-50 hover:bg-gray-50">
                  <td className="py-2">{r.date}</td>
                  <td className="py-2">{r.clock_in ?? '—'}</td>
                  <td className="py-2">{r.clock_out ?? '—'}</td>
                  <td className="py-2">
                    {r.work_minutes > 0
                      ? `${Math.floor(r.work_minutes / 60)}h${r.work_minutes % 60}m`
                      : '—'}
                  </td>
                  <td className={`py-2 ${r.overtime_minutes > 0 ? 'text-orange-500 font-medium' : ''}`}>
                    {r.overtime_minutes > 0
                      ? `${Math.floor(r.overtime_minutes / 60)}h${r.overtime_minutes % 60}m`
                      : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p className="text-gray-400 text-sm">打刻記録がありません</p>
        )}
      </div>
    </div>
  )
}

function StatusBadge({ status }: { status: AttendanceStatus }) {
  const config = {
    not_started: { label: '未出勤', className: 'bg-gray-100 text-gray-600' },
    working:     { label: '出勤中', className: 'bg-green-100 text-green-700' },
    break:       { label: '休憩中', className: 'bg-yellow-100 text-yellow-700' },
    done:        { label: '退勤済', className: 'bg-blue-100 text-blue-700' },
  }[status]
  return (
    <span className={`inline-block px-3 py-1 rounded-full text-sm font-medium ${config.className}`}>
      {config.label}
    </span>
  )
}
