'use client'
import { useEffect, useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'
import { Webhook } from 'lucide-react'

/** 本人宛て通知の Slack / Teams 転送設定（詳細設計書 7.8） */
export default function WebhookSection() {
  const qc = useQueryClient()
  const { data } = useQuery<{ provider: string; url: string }>({
    queryKey: ['personal-webhook'],
    queryFn: () => api.get('/api/v1/notifications/personal-webhook/').then((r) => r.data),
  })
  const [provider, setProvider] = useState('slack')
  const [url, setUrl]           = useState('')
  const [busy, setBusy]         = useState(false)
  const [msg, setMsg]           = useState<{ ok: boolean; text: string } | null>(null)

  useEffect(() => {
    if (data) {
      setProvider(data.provider || 'slack')
      setUrl(data.url)
    }
  }, [data])

  const errorText = (e: any, fallback: string) => {
    const d = e.response?.data
    return d?.error ?? d?.url?.[0] ?? d?.provider?.[0] ?? fallback
  }

  const save = async (clear = false) => {
    setBusy(true)
    setMsg(null)
    try {
      await api.put('/api/v1/notifications/personal-webhook/', clear ? { provider: '', url: '' } : { provider, url })
      if (clear) setUrl('')
      setMsg({ ok: true, text: clear ? '転送を解除しました' : '保存しました' })
      qc.invalidateQueries({ queryKey: ['personal-webhook'] })
    } catch (e: any) {
      setMsg({ ok: false, text: errorText(e, '保存に失敗しました') })
    } finally {
      setBusy(false)
    }
  }

  const test = async () => {
    setBusy(true)
    setMsg(null)
    try {
      await api.post('/api/v1/notifications/personal-webhook/test/')
      setMsg({ ok: true, text: 'テスト通知を送信しました' })
    } catch (e: any) {
      setMsg({ ok: false, text: errorText(e, '送信に失敗しました') })
    } finally {
      setBusy(false)
    }
  }

  const saved = !!data?.url
  return (
    <div className="bg-white rounded-xl border shadow-sm p-5">
      <h2 className="font-semibold text-gray-700 mb-1 flex items-center gap-2">
        <Webhook size={16} className="text-indigo-500" /> 通知の転送（Slack / Teams）
      </h2>
      <p className="text-xs text-gray-500 mb-4">
        あなた宛ての通知を、自分の Slack / Teams にも届けます。Slack は Incoming Webhook、
        Teams は Workflows の「Webhook 要求を受信したらチャネルに投稿する」で URL を発行してください。
      </p>
      <div className="space-y-3">
        <div className="flex gap-2">
          {[['slack', 'Slack'], ['teams', 'Teams']].map(([v, l]) => (
            <button key={v} onClick={() => setProvider(v)}
                    className={`px-3 py-1.5 rounded-lg text-sm border ${provider === v ? 'bg-indigo-600 text-white border-indigo-600' : 'border-gray-300 text-gray-600'}`}>
              {l}
            </button>
          ))}
        </div>
        <input value={url} onChange={(e) => setUrl(e.target.value)}
               placeholder={provider === 'slack' ? 'https://hooks.slack.com/services/...' : 'https://....logic.azure.com/workflows/...'}
               className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm" />
        {msg && <p className={`text-xs ${msg.ok ? 'text-green-600' : 'text-red-600'}`}>{msg.text}</p>}
        <div className="flex gap-2">
          <button onClick={() => save()} disabled={busy || !url}
                  className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-300 text-white rounded-lg text-sm font-medium">
            保存
          </button>
          {saved && (
            <>
              <button onClick={test} disabled={busy}
                      className="px-4 py-2 border border-gray-300 text-gray-600 rounded-lg text-sm hover:bg-gray-50">
                テスト送信
              </button>
              <button onClick={() => save(true)} disabled={busy} className="px-4 py-2 text-sm text-red-500 hover:underline">
                解除
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
