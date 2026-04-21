'use client'
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'
import { useAuthStore } from '@/lib/store'
import { Settings, Key, Eye, EyeOff, CheckCircle, AlertCircle, Bot, User, Mail, Shield } from 'lucide-react'

type AIProvider = 'anthropic' | 'openai'

interface AIKeyInfo {
  provider: AIProvider
  anthropic_has_key: boolean
  anthropic_masked: string
  openai_has_key: boolean
  openai_masked: string
}

const ROLE_LABEL: Record<string, string> = {
  employee:   '社員',
  supervisor: '上司',
  manager:    '管理職',
  hr:         '人事',
  accounting: '経理',
  customer:   '顧客',
  admin:      'システム管理者',
}

const PROVIDERS: { key: AIProvider; label: string; icon: string; prefix: string; placeholder: string }[] = [
  {
    key: 'anthropic',
    label: 'Anthropic (Claude)',
    icon: '🧠',
    prefix: 'sk-ant-',
    placeholder: 'sk-ant-api03-...',
  },
  {
    key: 'openai',
    label: 'OpenAI (ChatGPT)',
    icon: '💬',
    prefix: 'sk-',
    placeholder: 'sk-proj-...',
  },
]

export default function SettingsPage() {
  const user = useAuthStore((s) => s.user)
  const qc = useQueryClient()
  const [selectedProvider, setSelectedProvider] = useState<AIProvider>('anthropic')
  const [apiKey, setApiKey] = useState('')
  const [showKey, setShowKey] = useState(false)
  const [saved, setSaved] = useState(false)

  const { data: keyInfo, refetch } = useQuery<AIKeyInfo>({
    queryKey: ['my-api-key'],
    queryFn: () => api.get('/api/v1/auth/api-key/').then((r) => r.data),
    onSuccess: (data) => setSelectedProvider(data.provider),
  })

  const saveMut = useMutation({
    mutationFn: ({ provider, key }: { provider: AIProvider; key: string }) =>
      api.post('/api/v1/auth/api-key/', { provider, api_key: key }),
    onSuccess: () => {
      setSaved(true)
      setApiKey('')
      setShowKey(false)
      refetch()
      qc.invalidateQueries({ queryKey: ['my-api-key'] })
      setTimeout(() => setSaved(false), 3000)
    },
  })

  const currentProviderConfig = PROVIDERS.find((p) => p.key === selectedProvider)!
  const hasKey = selectedProvider === 'anthropic' ? keyInfo?.anthropic_has_key : keyInfo?.openai_has_key
  const maskedKey = selectedProvider === 'anthropic' ? keyInfo?.anthropic_masked : keyInfo?.openai_masked

  return (
    <div className="p-6 max-w-2xl mx-auto space-y-4">
      <div className="flex items-center gap-3 mb-6">
        <Settings className="text-indigo-600" size={28} />
        <div>
          <h1 className="text-2xl font-bold text-gray-800">設定</h1>
          <p className="text-sm text-gray-500">アカウント情報・AI機能の設定</p>
        </div>
      </div>

      {/* アカウント情報 */}
      <div className="bg-white rounded-xl border shadow-sm p-5">
        <h2 className="font-semibold text-gray-700 mb-4 flex items-center gap-2">
          <User size={16} className="text-indigo-500" /> アカウント情報
        </h2>
        <div className="space-y-3">
          <div className="flex items-center gap-3 py-2.5 border-b border-gray-100">
            <Mail size={15} className="text-gray-400 shrink-0" />
            <span className="text-sm text-gray-500 w-28 shrink-0">メールアドレス</span>
            <span className="text-sm text-gray-800 font-medium">{user?.email ?? '—'}</span>
          </div>
          <div className="flex items-center gap-3 py-2.5 border-b border-gray-100">
            <User size={15} className="text-gray-400 shrink-0" />
            <span className="text-sm text-gray-500 w-28 shrink-0">氏名</span>
            <span className="text-sm text-gray-800 font-medium">{user?.full_name ?? '—'}</span>
          </div>
          <div className="flex items-center gap-3 py-2.5">
            <Shield size={15} className="text-gray-400 shrink-0" />
            <span className="text-sm text-gray-500 w-28 shrink-0">ロール</span>
            <span className="text-sm bg-indigo-100 text-indigo-700 px-2.5 py-0.5 rounded-full font-medium">
              {ROLE_LABEL[user?.role ?? ''] ?? user?.role ?? '—'}
            </span>
          </div>
        </div>
      </div>

      {/* AI機能設定 */}
      <div className="bg-white rounded-xl border shadow-sm p-5">
        <div className="flex items-center gap-2 mb-1">
          <Bot className="text-indigo-600" size={18} />
          <h2 className="font-semibold text-gray-700">AI機能の設定</h2>
        </div>
        <p className="text-xs text-gray-500 mb-5">
          日報の自動下書き・MBO月報の文章生成などのAI機能に使用するAPIキーを登録します。
          AnthropicまたはOpenAIのいずれか一つを選択してください。
        </p>

        {/* プロバイダー選択 */}
        <div className="mb-5">
          <p className="text-sm font-medium text-gray-700 mb-2">使用するAIサービス</p>
          <div className="grid grid-cols-2 gap-3">
            {PROVIDERS.map((p) => {
              const pHasKey = p.key === 'anthropic' ? keyInfo?.anthropic_has_key : keyInfo?.openai_has_key
              const isSelected = selectedProvider === p.key
              return (
                <button
                  key={p.key}
                  onClick={() => { setSelectedProvider(p.key); setApiKey(''); setShowKey(false) }}
                  className={`flex flex-col items-start p-4 rounded-xl border-2 transition-all text-left ${
                    isSelected
                      ? 'border-indigo-500 bg-indigo-50'
                      : 'border-gray-200 hover:border-gray-300 bg-white'
                  }`}
                >
                  <div className="flex items-center justify-between w-full mb-1">
                    <span className="text-lg">{p.icon}</span>
                    {isSelected && <span className="text-xs bg-indigo-500 text-white px-2 py-0.5 rounded-full">使用中</span>}
                  </div>
                  <p className="text-sm font-medium text-gray-800">{p.label}</p>
                  {pHasKey ? (
                    <p className="text-xs text-green-600 mt-0.5 flex items-center gap-1">
                      <CheckCircle size={10} /> キー登録済
                    </p>
                  ) : (
                    <p className="text-xs text-gray-400 mt-0.5">未登録</p>
                  )}
                </button>
              )
            })}
          </div>
        </div>

        {/* 選択中プロバイダーのキー表示・入力 */}
        <div className="bg-gray-50 rounded-xl p-4">
          <p className="text-sm font-medium text-gray-700 mb-3">
            {currentProviderConfig.icon} {currentProviderConfig.label} のAPIキー
          </p>

          {/* 現在のキー状態 */}
          <div className={`flex items-center gap-2 text-sm px-3 py-2 rounded-lg mb-3 ${
            hasKey ? 'bg-green-50 text-green-700' : 'bg-amber-50 text-amber-700'
          }`}>
            {hasKey ? (
              <><CheckCircle size={14} /><span>登録済: <code className="font-mono text-xs">{maskedKey}</code></span></>
            ) : (
              <><AlertCircle size={14} /><span>未登録（AI機能は利用できません）</span></>
            )}
          </div>

          {/* キー入力 */}
          <div className="space-y-3">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">
                <Key size={12} className="inline mr-1" />
                新しいAPIキー {hasKey && <span className="text-gray-400 font-normal">（更新する場合のみ入力）</span>}
              </label>
              <div className="relative">
                <input
                  type={showKey ? 'text' : 'password'}
                  className="w-full border rounded-lg px-3 py-2 text-sm pr-10 font-mono bg-white"
                  placeholder={currentProviderConfig.placeholder}
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                />
                <button
                  type="button"
                  onClick={() => setShowKey(!showKey)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  {showKey ? <EyeOff size={15} /> : <Eye size={15} />}
                </button>
              </div>
            </div>

            <div className="flex gap-2">
              <button
                onClick={() => saveMut.mutate({ provider: selectedProvider, key: apiKey })}
                disabled={!apiKey || saveMut.isPending}
                className="bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-indigo-700 disabled:opacity-40 flex items-center gap-1.5"
              >
                {saveMut.isPending ? '保存中...' : 'APIキーを保存'}
              </button>
              {hasKey && (
                <button
                  onClick={() => saveMut.mutate({ provider: selectedProvider, key: '' })}
                  disabled={saveMut.isPending}
                  className="border border-red-300 text-red-600 px-4 py-2 rounded-lg text-sm hover:bg-red-50 disabled:opacity-40"
                >
                  削除
                </button>
              )}
            </div>

            {saved && (
              <p className="text-sm text-green-600 flex items-center gap-1">
                <CheckCircle size={13} /> 保存しました
              </p>
            )}
            {saveMut.error && (
              <p className="text-sm text-red-600">
                {(saveMut.error as any)?.response?.data?.error ?? 'エラーが発生しました'}
              </p>
            )}
          </div>
        </div>

        {/* セキュリティ注記 */}
        <div className="mt-4 text-xs text-gray-400 bg-gray-50 rounded-lg p-3">
          <p className="font-medium text-gray-500 mb-1">セキュリティ</p>
          <ul className="space-y-0.5 list-disc list-inside">
            <li>APIキーはサーバー上に暗号化して保存されます</li>
            <li>本システムのAI機能のみに使用されます</li>
            <li>退職・異動の際はAPIキーを削除してください</li>
          </ul>
        </div>
      </div>
    </div>
  )
}
