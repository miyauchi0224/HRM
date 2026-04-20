'use client'
import { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import api from '@/lib/api'
import { useAuthStore } from '@/lib/store'
import { Settings, Key, Eye, EyeOff, CheckCircle, AlertCircle, Bot } from 'lucide-react'

export default function SettingsPage() {
  const user = useAuthStore((s) => s.user)
  const [apiKey, setApiKey] = useState('')
  const [showKey, setShowKey] = useState(false)
  const [saved, setSaved] = useState(false)

  const { data: keyInfo, refetch } = useQuery({
    queryKey: ['my-api-key'],
    queryFn: () => api.get('/api/v1/auth/api-key/').then((r) => r.data),
  })

  const saveMut = useMutation({
    mutationFn: (key: string) => api.post('/api/v1/auth/api-key/', { api_key: key }),
    onSuccess: () => {
      setSaved(true)
      setApiKey('')
      refetch()
      setTimeout(() => setSaved(false), 3000)
    },
  })

  return (
    <div className="p-6 max-w-2xl mx-auto">
      <div className="flex items-center gap-3 mb-6">
        <Settings className="text-indigo-600" size={28} />
        <div>
          <h1 className="text-2xl font-bold text-gray-800">設定</h1>
          <p className="text-sm text-gray-500">アカウント設定・AI機能の設定</p>
        </div>
      </div>

      {/* プロフィール */}
      <div className="bg-white rounded-xl border shadow-sm p-5 mb-4">
        <h2 className="font-semibold text-gray-700 mb-3">アカウント情報</h2>
        <div className="space-y-2 text-sm">
          <div className="flex justify-between py-2 border-b">
            <span className="text-gray-500">メールアドレス</span>
            <span className="text-gray-800 font-medium">{user?.email}</span>
          </div>
          <div className="flex justify-between py-2 border-b">
            <span className="text-gray-500">氏名</span>
            <span className="text-gray-800 font-medium">{user?.full_name}</span>
          </div>
          <div className="flex justify-between py-2">
            <span className="text-gray-500">ロール</span>
            <span className="text-gray-800 font-medium">{user?.role}</span>
          </div>
        </div>
      </div>

      {/* AI APIキー設定 */}
      <div className="bg-white rounded-xl border shadow-sm p-5">
        <div className="flex items-center gap-2 mb-1">
          <Bot className="text-indigo-600" size={20} />
          <h2 className="font-semibold text-gray-700">AI機能の設定</h2>
        </div>
        <p className="text-xs text-gray-500 mb-4">
          日報の自動下書き・MBO月報の文章生成・領収書OCRなどのAI機能を使用するには、
          Anthropic の API キーが必要です。
          <a
            href="https://console.anthropic.com/"
            target="_blank"
            rel="noopener noreferrer"
            className="text-indigo-600 hover:underline ml-1"
          >
            Anthropic Console で取得 →
          </a>
        </p>

        {/* 現在の設定状態 */}
        <div className={`flex items-center gap-2 text-sm px-3 py-2 rounded-lg mb-4 ${
          keyInfo?.has_key ? 'bg-green-50 text-green-700' : 'bg-gray-50 text-gray-500'
        }`}>
          {keyInfo?.has_key ? (
            <><CheckCircle size={16} /><span>APIキー登録済: <code className="font-mono text-xs">{keyInfo.masked}</code></>
          ) : (
            <><AlertCircle size={16} /><span>APIキーが未登録です（AI機能は利用できません）</>
          )}
        </div>

        <div className="space-y-3">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              <Key size={14} className="inline mr-1" />
              新しい Anthropic APIキー
            </label>
            <div className="relative">
              <input
                type={showKey ? 'text' : 'password'}
                className="w-full border rounded-lg px-3 py-2 text-sm pr-10 font-mono"
                placeholder="sk-ant-api03-..."
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
              />
              <button
                type="button"
                onClick={() => setShowKey(!showKey)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
              >
                {showKey ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </div>
          <div className="flex gap-3">
            <button
              onClick={() => saveMut.mutate(apiKey)}
              disabled={!apiKey || saveMut.isPending}
              className="bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-indigo-700 disabled:opacity-50"
            >
              {saveMut.isPending ? '保存中...' : 'APIキーを保存'}
            </button>
            {keyInfo?.has_key && (
              <button
                onClick={() => saveMut.mutate('')}
                className="border border-red-300 text-red-600 px-4 py-2 rounded-lg text-sm hover:bg-red-50"
              >
                APIキーを削除
              </button>
            )}
          </div>
          {saved && (
            <p className="text-sm text-green-600 flex items-center gap-1">
              <CheckCircle size={14} /> APIキーを保存しました
            </p>
          )}
          {saveMut.error && (
            <p className="text-sm text-red-600">{(saveMut.error as any)?.response?.data?.error ?? 'エラーが発生しました'}</p>
          )}
        </div>

        <div className="mt-4 text-xs text-gray-400 bg-gray-50 rounded-lg p-3">
          <p className="font-medium text-gray-500 mb-1">セキュリティについて</p>
          <ul className="space-y-0.5 list-disc list-inside">
            <li>APIキーはサーバー上に暗号化して保存されます</li>
            <li>APIキーは本システムのAI機能のみに使用されます</li>
            <li>第三者への共有・外部送信はいたしません</li>
            <li>退職・異動の際はAPIキーを削除してください</li>
          </ul>
        </div>
      </div>
    </div>
  )
}
