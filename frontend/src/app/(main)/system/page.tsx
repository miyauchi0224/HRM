'use client'
import { toast } from '@/lib/toast'
import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'
import { useAuthStore } from '@/lib/store'
import { Cog, Play, Plus, Send, Trash2 } from 'lucide-react'

interface JobRun {
  id: string
  job_name: string
  run_date: string
  status: 'running' | 'success' | 'failed'
  result: Record<string, unknown>
  error: string
  started_at: string
}
interface Job { name: string; description: string; last_run: JobRun | null }
interface Endpoint {
  id: string
  name: string
  provider: 'slack' | 'teams'
  url: string
  notification_types: string[]
  is_active: boolean
}
interface NotificationType { value: string; label: string; sensitive: boolean }

const RUN_STATUS: Record<string, string> = {
  success: 'bg-green-100 text-green-700',
  failed:  'bg-red-100 text-red-700',
  running: 'bg-blue-100 text-blue-700',
}

/** 全社の通知連携（Webhook）と定期ジョブ（詳細設計書 7.1・7.8）。人事は閲覧、管理者は編集・実行 */
export default function SystemPage() {
  const isAdmin = useAuthStore((s) => s.user?.role) === 'admin'
  return (
    <div className="max-w-4xl space-y-8">
      <h1 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
        <Cog size={22} /> 通知連携・定期ジョブ
      </h1>
      <WebhookEndpoints isAdmin={isAdmin} />
      <Jobs isAdmin={isAdmin} />
    </div>
  )
}

function WebhookEndpoints({ isAdmin }: { isAdmin: boolean }) {
  const qc = useQueryClient()
  const [showNew, setShowNew] = useState(false)
  const { data: endpoints = [] } = useQuery<Endpoint[]>({
    queryKey: ['webhook-endpoints'],
    queryFn: () => api.get('/api/v1/notifications/webhooks/').then((r) => r.data.results ?? r.data),
  })
  const { data: types = [] } = useQuery<NotificationType[]>({
    queryKey: ['notification-types'],
    queryFn: () => api.get('/api/v1/notifications/types/').then((r) => r.data),
  })
  const label = (v: string) => types.find((t) => t.value === v)?.label ?? v

  const refresh = () => qc.invalidateQueries({ queryKey: ['webhook-endpoints'] })
  const toggle = useMutation({
    mutationFn: (ep: Endpoint) => api.patch(`/api/v1/notifications/webhooks/${ep.id}/`, { is_active: !ep.is_active }),
    onSuccess: refresh,
  })
  const remove = useMutation({
    mutationFn: (id: string) => api.delete(`/api/v1/notifications/webhooks/${id}/`),
    onSuccess: refresh,
  })
  const test = useMutation({
    mutationFn: (id: string) => api.post(`/api/v1/notifications/webhooks/${id}/test/`),
    onSuccess: () => toast.success('テスト通知を送信しました'),
    onError: (e: any) => toast.error(e.response?.data?.error ?? '送信に失敗しました'),
  })

  return (
    <section className="bg-white rounded-xl border border-gray-200">
      <div className="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
        <div>
          <h2 className="font-semibold text-gray-700">全社の通知転送先（Slack / Teams）</h2>
          <p className="text-xs text-gray-500 mt-0.5">選んだ種類の通知を、宛先の氏名を付けてチャンネルに投稿します。健康診断・ストレスチェックは転送できません。</p>
        </div>
        {isAdmin && (
          <button onClick={() => setShowNew(true)} className="flex items-center gap-1 text-sm bg-blue-600 text-white px-3 py-1.5 rounded-lg">
            <Plus size={14} /> 追加
          </button>
        )}
      </div>
      {endpoints.length === 0 ? (
        <p className="px-5 py-6 text-sm text-gray-400">転送先は設定されていません</p>
      ) : (
        <ul className="divide-y divide-gray-50">
          {endpoints.map((ep) => (
            <li key={ep.id} className="px-5 py-3 flex items-start gap-3">
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-700">
                  {ep.name}
                  <span className="ml-2 text-xs text-gray-400">{ep.provider === 'slack' ? 'Slack' : 'Teams'}</span>
                  {!ep.is_active && <span className="ml-2 text-xs text-gray-400">（停止中）</span>}
                </p>
                <p className="text-xs text-gray-500 truncate">{ep.notification_types.map(label).join('、')}</p>
              </div>
              {isAdmin && (
                <div className="flex items-center gap-2 text-xs">
                  <button onClick={() => test.mutate(ep.id)} className="text-gray-500 hover:text-blue-600 flex items-center gap-1">
                    <Send size={12} /> テスト
                  </button>
                  <button onClick={() => toggle.mutate(ep)} className="text-gray-500 hover:text-blue-600">
                    {ep.is_active ? '停止' : '再開'}
                  </button>
                  <button onClick={() => confirm('削除しますか？') && remove.mutate(ep.id)} className="text-gray-300 hover:text-red-500">
                    <Trash2 size={14} />
                  </button>
                </div>
              )}
            </li>
          ))}
        </ul>
      )}
      {showNew && <NewEndpointModal types={types} onClose={() => setShowNew(false)} onSaved={() => { setShowNew(false); refresh() }} />}
    </section>
  )
}

function NewEndpointModal({ types, onClose, onSaved }: { types: NotificationType[]; onClose: () => void; onSaved: () => void }) {
  const [name, setName]         = useState('')
  const [provider, setProvider] = useState<'slack' | 'teams'>('slack')
  const [url, setUrl]           = useState('')
  const [selected, setSelected] = useState<string[]>([])
  const [saving, setSaving]     = useState(false)

  const save = async () => {
    setSaving(true)
    try {
      await api.post('/api/v1/notifications/webhooks/', { name, provider, url, notification_types: selected })
      onSaved()
    } catch (e: any) {
      const d = e.response?.data
      toast.error(d?.url?.[0] ?? d?.notification_types?.[0] ?? d?.name?.[0] ?? '登録に失敗しました')
    } finally {
      setSaving(false)
    }
  }

  const input = 'w-full px-3 py-2 border border-gray-300 rounded-lg text-sm'
  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-6 border-b border-gray-100">
          <h2 className="font-bold text-gray-800">通知転送先を追加</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl leading-none">×</button>
        </div>
        <div className="p-6 space-y-4">
          <label className="block text-sm text-gray-700">名前
            <input value={name} onChange={(e) => setName(e.target.value)} placeholder="例：労務チャンネル" className={`${input} mt-1`} />
          </label>
          <label className="block text-sm text-gray-700">種類
            <select value={provider} onChange={(e) => setProvider(e.target.value as 'slack' | 'teams')} className={`${input} mt-1`}>
              <option value="slack">Slack</option>
              <option value="teams">Microsoft Teams</option>
            </select>
          </label>
          <label className="block text-sm text-gray-700">Webhook URL
            <input value={url} onChange={(e) => setUrl(e.target.value)} className={`${input} mt-1`} />
          </label>
          <div>
            <p className="text-sm text-gray-700 mb-2">転送する通知</p>
            <div className="grid grid-cols-2 gap-1.5">
              {types.filter((t) => !t.sensitive).map((t) => (
                <label key={t.value} className="text-sm text-gray-600 flex items-center gap-2">
                  <input type="checkbox" checked={selected.includes(t.value)}
                         onChange={(e) => setSelected(e.target.checked ? [...selected, t.value] : selected.filter((v) => v !== t.value))} />
                  {t.label}
                </label>
              ))}
            </div>
          </div>
        </div>
        <div className="flex gap-3 px-6 pb-6">
          <button onClick={onClose} className="flex-1 py-2.5 border border-gray-300 rounded-lg text-sm text-gray-600 hover:bg-gray-50 font-medium">
            キャンセル
          </button>
          <button onClick={save} disabled={saving || !name || !url || selected.length === 0}
                  className="flex-1 py-2.5 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white rounded-lg text-sm font-medium">
            {saving ? '登録中...' : '登録する'}
          </button>
        </div>
      </div>
    </div>
  )
}

function Jobs({ isAdmin }: { isAdmin: boolean }) {
  const qc = useQueryClient()
  const { data: jobs = [] } = useQuery<Job[]>({
    queryKey: ['scheduler-jobs'],
    queryFn: () => api.get('/api/v1/scheduler/jobs/').then((r) => r.data),
  })
  const run = useMutation({
    mutationFn: (name: string) => api.post(`/api/v1/scheduler/jobs/${name}/run/`, { force: true }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['scheduler-jobs'] }),
    onError: (e: any) => toast.error(e.response?.data?.error ?? '実行に失敗しました'),
  })

  return (
    <section className="bg-white rounded-xl border border-gray-200 overflow-x-auto">
      <div className="px-5 py-4 border-b border-gray-100">
        <h2 className="font-semibold text-gray-700">定期ジョブ</h2>
        <p className="text-xs text-gray-500 mt-0.5">毎朝（既定 6:00）に上から順に実行されます。同じ日に二重には実行されません。</p>
      </div>
      <table className="w-full text-sm min-w-[640px]">
        <thead>
          <tr className="text-gray-400 text-xs border-b border-gray-100">
            <th className="text-left px-5 py-3 font-medium">ジョブ</th>
            <th className="text-left px-5 py-3 font-medium">最終実行</th>
            <th className="text-left px-5 py-3 font-medium">結果</th>
            {isAdmin && <th className="px-5 py-3" />}
          </tr>
        </thead>
        <tbody>
          {jobs.map((j) => (
            <tr key={j.name} className="border-b border-gray-50 align-top">
              <td className="px-5 py-3">
                <p className="text-gray-700">{j.description}</p>
                <p className="text-xs text-gray-400 font-mono">{j.name}</p>
              </td>
              <td className="px-5 py-3 text-gray-500 whitespace-nowrap">
                {j.last_run ? new Date(j.last_run.started_at).toLocaleString('ja-JP') : '未実行'}
              </td>
              <td className="px-5 py-3">
                {j.last_run && (
                  <>
                    <span className={`text-xs px-2 py-0.5 rounded-full ${RUN_STATUS[j.last_run.status]}`}>{j.last_run.status}</span>
                    {j.last_run.status === 'success' && Object.keys(j.last_run.result ?? {}).length > 0 && (
                      <span className="ml-2 text-xs text-gray-500">
                        {Object.entries(j.last_run.result).map(([k, v]) => `${k}: ${v}`).join(', ')}
                      </span>
                    )}
                    {j.last_run.status === 'failed' && (
                      <pre className="mt-1 text-[11px] text-red-600 whitespace-pre-wrap max-h-24 overflow-y-auto">
                        {j.last_run.error.split('\n').slice(-3).join('\n')}
                      </pre>
                    )}
                  </>
                )}
              </td>
              {isAdmin && (
                <td className="px-5 py-3">
                  <button onClick={() => confirm(`「${j.description}」を今すぐ実行しますか？`) && run.mutate(j.name)}
                          disabled={run.isPending}
                          className="text-xs flex items-center gap-1 border border-gray-300 px-2.5 py-1 rounded-lg hover:bg-gray-50">
                    <Play size={12} /> 実行
                  </button>
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  )
}
