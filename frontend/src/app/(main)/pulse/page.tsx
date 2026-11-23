'use client'
import { toast } from '@/lib/toast'
import { useState } from 'react'
import Link from 'next/link'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'
import { useAuthStore } from '@/lib/store'
import { BarChartHorizontal, CheckCircle2, Plus, Send } from 'lucide-react'

export interface PulseQuestion { id: string; order: number; text: string; kind: 'scale5' | 'enps' | 'text'; is_required: boolean }
export interface PulseSurvey {
  id: string
  title: string
  description: string
  start_date: string
  end_date: string
  is_published: boolean
  is_anonymous: boolean
  questions: PulseQuestion[]
  has_answered: boolean
  response_count: number
}

const HR_ROLES = ['hr', 'admin']

/** パルスサーベイ一覧（詳細設計書 7.10） */
export default function PulsePage() {
  const isHR = HR_ROLES.includes(useAuthStore((s) => s.user?.role ?? ''))
  const qc   = useQueryClient()
  const [showNew, setShowNew] = useState(false)
  const today = new Date().toISOString().slice(0, 10)

  const { data: surveys = [], isLoading } = useQuery<PulseSurvey[]>({
    queryKey: ['pulse-surveys'],
    queryFn: () => api.get('/api/v1/pulse/surveys/?page_size=100').then((r) => r.data.results ?? r.data),
  })

  const publish = useMutation({
    mutationFn: (id: string) => api.post(`/api/v1/pulse/surveys/${id}/publish/`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['pulse-surveys'] }),
    onError: (e: any) => toast.error(e.response?.data?.error ?? '公開に失敗しました'),
  })

  return (
    <div className="max-w-3xl">
      <div className="flex items-center justify-between mb-2">
        <h1 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
          <BarChartHorizontal size={22} /> パルスサーベイ
        </h1>
        {isHR && (
          <button onClick={() => setShowNew(true)}
                  className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium px-4 py-2 rounded-lg">
            <Plus size={16} /> 作成
          </button>
        )}
      </div>
      <p className="text-sm text-gray-500 mb-6">
        数分で答えられる短いアンケートです。匿名のサーベイでは、誰がどう答えたかは人事にも分かりません。
      </p>

      {isLoading ? (
        <p className="text-gray-400 text-sm">読み込み中...</p>
      ) : surveys.length === 0 ? (
        <p className="text-center text-gray-400 py-12">実施中のサーベイはありません</p>
      ) : (
        <div className="space-y-3">
          {surveys.map((s) => {
            const open = s.is_published && s.start_date <= today && today <= s.end_date
            return (
              <div key={s.id} className="bg-white rounded-xl border border-gray-200 p-5 flex items-center gap-4 flex-wrap">
                <div className="flex-1 min-w-[200px]">
                  <h3 className="font-bold text-gray-800">{s.title}</h3>
                  <p className="text-xs text-gray-500 mt-1">
                    {s.start_date} 〜 {s.end_date}・{s.is_anonymous ? '匿名' : '記名'}・{s.questions.length}問
                    {isHR && `・回答 ${s.response_count}人`}
                  </p>
                </div>
                {!s.is_published && <span className="text-xs px-2.5 py-1 rounded-full bg-gray-100 text-gray-500">下書き</span>}
                {s.has_answered ? (
                  <span className="text-xs text-green-600 flex items-center gap-1"><CheckCircle2 size={14} /> 回答済み</span>
                ) : open ? (
                  <Link href={`/pulse/${s.id}`} className="text-sm bg-blue-600 text-white px-4 py-1.5 rounded-lg hover:bg-blue-700">
                    回答する
                  </Link>
                ) : null}
                {isHR && !s.is_published && (
                  <button onClick={() => confirm('公開すると全社員に通知されます。公開しますか？') && publish.mutate(s.id)}
                          className="text-sm flex items-center gap-1 border border-gray-300 px-3 py-1.5 rounded-lg hover:bg-gray-50">
                    <Send size={14} /> 公開
                  </button>
                )}
                {isHR && s.is_published && (
                  <Link href={`/pulse/${s.id}?view=results`} className="text-sm border border-gray-300 px-3 py-1.5 rounded-lg hover:bg-gray-50">
                    集計
                  </Link>
                )}
              </div>
            )
          })}
        </div>
      )}

      {showNew && (
        <NewSurveyModal onClose={() => setShowNew(false)}
                        onSaved={() => { setShowNew(false); qc.invalidateQueries({ queryKey: ['pulse-surveys'] }) }} />
      )}
    </div>
  )
}

function NewSurveyModal({ onClose, onSaved }: { onClose: () => void; onSaved: () => void }) {
  const today = new Date()
  const iso = (d: Date) => d.toISOString().slice(0, 10)
  const [title, setTitle]   = useState(`${today.getMonth() + 1}月のパルスサーベイ`)
  const [start, setStart]   = useState(iso(today))
  const [end, setEnd]       = useState(iso(new Date(today.getTime() + 7 * 86400000)))
  const [anonymous, setAnonymous] = useState(true)
  const [saving, setSaving] = useState(false)

  const save = async () => {
    setSaving(true)
    try {
      // 質問を指定しない場合はサーバー側で既定の5問（eNPS など）が作られる
      await api.post('/api/v1/pulse/surveys/', { title, start_date: start, end_date: end, is_anonymous: anonymous })
      onSaved()
    } catch (e: any) {
      toast.error(e.response?.data?.end_date?.[0] ?? '作成に失敗しました')
    } finally {
      setSaving(false)
    }
  }

  const input = 'w-full px-3 py-2 border border-gray-300 rounded-lg text-sm'
  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-md">
        <div className="flex items-center justify-between p-6 border-b border-gray-100">
          <h2 className="font-bold text-gray-800">パルスサーベイを作成</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl leading-none">×</button>
        </div>
        <div className="p-6 space-y-4">
          <label className="block text-sm text-gray-700">タイトル
            <input value={title} onChange={(e) => setTitle(e.target.value)} className={`${input} mt-1`} />
          </label>
          <div className="grid grid-cols-2 gap-3">
            <label className="text-sm text-gray-700">開始日
              <input type="date" value={start} onChange={(e) => setStart(e.target.value)} className={`${input} mt-1`} />
            </label>
            <label className="text-sm text-gray-700">終了日
              <input type="date" value={end} min={start} onChange={(e) => setEnd(e.target.value)} className={`${input} mt-1`} />
            </label>
          </div>
          <label className="flex items-center gap-2 text-sm text-gray-700">
            <input type="checkbox" checked={anonymous} onChange={(e) => setAnonymous(e.target.checked)} />
            匿名で回答を集める（推奨）
          </label>
          <p className="text-xs text-gray-500">
            質問は既定の5問（eNPS・仕事のやりがい・上司のサポート・チームの雰囲気・自由記述）で作成します。
            下書きのあいだは API から質問を変更できます。
          </p>
        </div>
        <div className="flex gap-3 px-6 pb-6">
          <button onClick={onClose} className="flex-1 py-2.5 border border-gray-300 rounded-lg text-sm text-gray-600 hover:bg-gray-50 font-medium">
            キャンセル
          </button>
          <button onClick={save} disabled={saving || !title}
                  className="flex-1 py-2.5 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white rounded-lg text-sm font-medium">
            {saving ? '作成中...' : '下書きを作成'}
          </button>
        </div>
      </div>
    </div>
  )
}
