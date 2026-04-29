'use client'
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import api from '@/lib/api'
import Link from 'next/link'
import { ClipboardList, Calendar, CheckCircle2, Clock, AlertCircle } from 'lucide-react'

interface StressCheckPeriod {
  id: string
  title: string
  start_date: string
  end_date: string
  is_published: boolean
  response_count: number
  high_stress_count: number
  created_at: string
}

export default function StressCheckPage() {
  const { data: periods = [], isLoading } = useQuery<StressCheckPeriod[]>({
    queryKey: ['stress-check-periods'],
    queryFn: () => api.get('/api/v1/stress-check/periods/').then((r) => r.data.results ?? r.data),
  })

  const today = new Date().toISOString().slice(0, 10)
  const active = periods.filter((p) => p.start_date <= today && today <= p.end_date)
  const upcoming = periods.filter((p) => p.start_date > today)
  const past = periods.filter((p) => p.end_date < today)

  const PeriodCard = ({ period, status }: { period: StressCheckPeriod; status: 'active' | 'upcoming' | 'past' }) => (
    <Link href={`/stress-check/${period.id}`}>
      <div className="bg-white rounded-xl border border-gray-200 hover:shadow-md transition-shadow p-5 cursor-pointer">
        <div className="flex items-start justify-between mb-3">
          <h3 className="font-bold text-gray-800">{period.title}</h3>
          <span className={`text-xs px-2.5 py-1 rounded-full font-medium ${
            status === 'active'
              ? 'bg-blue-100 text-blue-700'
              : status === 'upcoming'
              ? 'bg-gray-100 text-gray-700'
              : 'bg-gray-50 text-gray-500'
          }`}>
            {status === 'active' ? '期間中' : status === 'upcoming' ? '予定' : '終了'}
          </span>
        </div>

        <div className="space-y-2 text-sm text-gray-600 mb-3">
          <div className="flex items-center gap-2">
            <Calendar size={14} />
            {period.start_date} 〜 {period.end_date}
          </div>
        </div>

        {status !== 'upcoming' && (
          <div className="flex items-center gap-4 text-xs text-gray-500">
            <span className="flex items-center gap-1">
              <CheckCircle2 size={14} />
              {period.response_count} 人が回答
            </span>
            {period.high_stress_count > 0 && (
              <span className="flex items-center gap-1 text-red-600">
                <AlertCircle size={14} />
                {period.high_stress_count} 人が高ストレス
              </span>
            )}
          </div>
        )}
      </div>
    </Link>
  )

  return (
    <div>
      <div className="flex items-center gap-2 mb-6">
        <ClipboardList size={24} className="text-blue-600" />
        <h1 className="text-2xl font-bold text-gray-800">ストレスチェック</h1>
      </div>

      {isLoading ? (
        <p className="text-gray-500">読み込み中...</p>
      ) : (
        <div className="space-y-6">
          {/* 期間中 */}
          {active.length > 0 && (
            <section>
              <div className="flex items-center gap-2 mb-3">
                <Clock size={16} className="text-blue-600" />
                <h2 className="text-sm font-semibold text-gray-700 uppercase tracking-wide">期間中</h2>
              </div>
              <div className="grid gap-4">
                {active.map((p) => (
                  <PeriodCard key={p.id} period={p} status="active" />
                ))}
              </div>
            </section>
          )}

          {/* 予定 */}
          {upcoming.length > 0 && (
            <section>
              <div className="flex items-center gap-2 mb-3">
                <Calendar size={16} className="text-gray-400" />
                <h2 className="text-sm font-semibold text-gray-700 uppercase tracking-wide">予定</h2>
              </div>
              <div className="grid gap-4">
                {upcoming.map((p) => (
                  <PeriodCard key={p.id} period={p} status="upcoming" />
                ))}
              </div>
            </section>
          )}

          {/* 終了 */}
          {past.length > 0 && (
            <section>
              <div className="flex items-center gap-2 mb-3">
                <CheckCircle2 size={16} className="text-gray-400" />
                <h2 className="text-sm font-semibold text-gray-700 uppercase tracking-wide">終了</h2>
              </div>
              <div className="grid gap-4">
                {past.map((p) => (
                  <PeriodCard key={p.id} period={p} status="past" />
                ))}
              </div>
            </section>
          )}

          {periods.length === 0 && (
            <div className="text-center py-12 text-gray-400">
              <ClipboardList size={48} className="mx-auto mb-3 opacity-30" />
              <p>実施予定のストレスチェックはありません</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
