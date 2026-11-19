'use client'
import { useEffect, useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, LogIn, LogOut, MapPin, MapPinOff } from 'lucide-react'
import api from '@/lib/api'
import { getPunchLocation } from '@/lib/geo'

interface TodayRecord {
  id: string
  date: string
  clock_in: string | null
  clock_out: string | null
  clock_in_latitude: string | null
  clock_out_latitude: string | null
  rest_interval_minutes: number | null
}

const localToday = () => {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

/** スマホ用の全画面打刻ページ（PWA のショートカット先。詳細設計書 7.9） */
export default function ClockPage() {
  const router = useRouter()
  const qc     = useQueryClient()
  const [now, setNow]           = useState(new Date())
  const [breakMin, setBreakMin] = useState(60)
  const [message, setMessage]   = useState<string | null>(null)

  useEffect(() => {
    if (!localStorage.getItem('access_token')) router.replace('/login')
    const t = setInterval(() => setNow(new Date()), 1000)
    return () => clearInterval(t)
  }, [router])

  const today = localToday()
  const { data: record, isLoading } = useQuery<TodayRecord | null>({
    queryKey: ['attendance-today', today],
    queryFn: async () => {
      const r = await api.get(`/api/v1/attendance/?year_month=${today.slice(0, 7)}`)
      const rows: TodayRecord[] = r.data.results ?? r.data
      return rows.find((x) => x.date === today) ?? null
    },
  })

  const punch = useMutation({
    mutationFn: async (kind: 'in' | 'out') => {
      const loc = await getPunchLocation()
      if (kind === 'in') return api.post('/api/v1/attendance/clock-in/', loc)
      return api.post('/api/v1/attendance/clock-out/', { break_minutes: breakMin, ...loc })
    },
    onSuccess: (res, kind) => {
      const located = kind === 'in' ? res.data.clock_in_latitude : res.data.clock_out_latitude
      setMessage(`${kind === 'in' ? '出勤' : '退勤'}を記録しました${located ? '' : '（位置情報なし）'}`)
      qc.invalidateQueries({ queryKey: ['attendance-today'] })
      qc.invalidateQueries({ queryKey: ['attendance'] })
    },
    onError: (e: any) => setMessage(e.response?.data?.error ?? '打刻に失敗しました'),
  })

  const clockedIn  = !!record?.clock_in
  const clockedOut = !!record?.clock_out
  const time = now.toLocaleTimeString('ja-JP', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
  const dateLabel = now.toLocaleDateString('ja-JP', { month: 'long', day: 'numeric', weekday: 'short' })

  return (
    <div className="min-h-screen bg-gray-900 text-white flex flex-col px-4 py-6">
      <Link href="/" className="flex items-center gap-1 text-sm text-gray-400 mb-8">
        <ArrowLeft size={16} /> ホームへ
      </Link>

      <div className="text-center mb-10">
        <p className="text-gray-400">{dateLabel}</p>
        <p className="text-5xl font-bold tabular-nums mt-2">{time}</p>
      </div>

      <div className="grid grid-cols-2 gap-3 mb-6 text-center">
        <div className="bg-gray-800 rounded-xl p-4">
          <p className="text-xs text-gray-400">出勤</p>
          <p className="text-2xl font-semibold mt-1">{record?.clock_in?.slice(0, 5) ?? '--:--'}</p>
          <LocationBadge recorded={!!record?.clock_in_latitude} show={clockedIn} />
        </div>
        <div className="bg-gray-800 rounded-xl p-4">
          <p className="text-xs text-gray-400">退勤</p>
          <p className="text-2xl font-semibold mt-1">{record?.clock_out?.slice(0, 5) ?? '--:--'}</p>
          <LocationBadge recorded={!!record?.clock_out_latitude} show={clockedOut} />
        </div>
      </div>

      {record?.rest_interval_minutes != null && record.rest_interval_minutes < 660 && (
        <p className="text-sm text-amber-300 bg-amber-900/40 rounded-lg px-3 py-2 mb-4">
          前回の退勤から {Math.floor(record.rest_interval_minutes / 60)}時間{record.rest_interval_minutes % 60}分 しか空いていません。無理のないようにしてください。
        </p>
      )}

      <div className="mt-auto space-y-3">
        {clockedIn && !clockedOut && (
          <label className="flex items-center justify-between bg-gray-800 rounded-xl px-4 py-3 text-sm">
            休憩時間
            <select value={breakMin} onChange={(e) => setBreakMin(Number(e.target.value))}
                    className="bg-gray-700 rounded-lg px-2 py-1">
              {[0, 30, 45, 60, 90, 120].map((m) => <option key={m} value={m}>{m}分</option>)}
            </select>
          </label>
        )}

        {message && <p className="text-center text-sm text-gray-200">{message}</p>}

        {isLoading ? (
          <p className="text-center text-gray-400">読み込み中...</p>
        ) : !clockedIn ? (
          <button onClick={() => punch.mutate('in')} disabled={punch.isPending}
                  className="w-full py-5 rounded-2xl bg-blue-600 active:bg-blue-700 disabled:opacity-50 text-xl font-bold flex items-center justify-center gap-2">
            <LogIn size={24} /> {punch.isPending ? '記録中...' : '出勤する'}
          </button>
        ) : !clockedOut ? (
          <button onClick={() => punch.mutate('out')} disabled={punch.isPending}
                  className="w-full py-5 rounded-2xl bg-orange-600 active:bg-orange-700 disabled:opacity-50 text-xl font-bold flex items-center justify-center gap-2">
            <LogOut size={24} /> {punch.isPending ? '記録中...' : '退勤する'}
          </button>
        ) : (
          <p className="text-center text-gray-400 py-5">本日の打刻は完了しています。お疲れさまでした。</p>
        )}
        <p className="text-center text-xs text-gray-500">
          位置情報は打刻した瞬間のみ記録します（ブラウザで許可した場合）
        </p>
      </div>
    </div>
  )
}

function LocationBadge({ recorded, show }: { recorded: boolean; show: boolean }) {
  if (!show) return null
  return (
    <p className={`text-xs mt-1 flex items-center justify-center gap-1 ${recorded ? 'text-green-400' : 'text-gray-500'}`}>
      {recorded ? <MapPin size={12} /> : <MapPinOff size={12} />}
      {recorded ? '位置あり' : '位置なし'}
    </p>
  )
}
