'use client'
import { useState, useRef } from 'react'
import { useQuery } from '@tanstack/react-query'
import api from '@/lib/api'
import { useAuthStore } from '@/lib/store'
import { Bot, MessageSquare, Target, FileText, Receipt, Send, Loader2 } from 'lucide-react'

type Tab = 'hr-chat' | 'mbo-goal' | 'daily-report' | 'receipt'

export default function AIAssistantPage() {
  const user = useAuthStore((s) => s.user)
  const isHR = user?.role && ['hr', 'admin'].includes(user.role)
  const [activeTab, setActiveTab] = useState<Tab>(isHR ? 'hr-chat' : 'daily-report')

  const tabs = [
    ...(isHR ? [{ key: 'hr-chat' as Tab, label: 'HRチャット', icon: MessageSquare }] : []),
    { key: 'mbo-goal'      as Tab, label: 'MBO目標下書き', icon: Target },
    { key: 'daily-report'  as Tab, label: '日報下書き',    icon: FileText },
    { key: 'receipt'       as Tab, label: '領収書OCR',     icon: Receipt },
  ]

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="flex items-center gap-3 mb-6">
        <Bot className="text-indigo-600" size={28} />
        <div>
          <h1 className="text-2xl font-bold text-gray-800">AIアシスタント</h1>
          <p className="text-sm text-gray-500">Claude AIが人事業務をサポートします</p>
        </div>
      </div>

      <div className="flex gap-1 mb-6 border-b border-gray-200">
        {tabs.map(({ key, label, icon: Icon }) => (
          <button
            key={key}
            onClick={() => setActiveTab(key)}
            className={`flex items-center gap-1.5 px-4 py-2 text-sm font-medium rounded-t-lg transition-colors ${
              activeTab === key
                ? 'bg-white border border-b-white border-gray-200 text-indigo-600 -mb-px'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            <Icon size={14} />
            {label}
          </button>
        ))}
      </div>

      {activeTab === 'hr-chat'     && <HRChatPanel />}
      {activeTab === 'mbo-goal'    && <MBOGoalPanel />}
      {activeTab === 'daily-report'&& <DailyReportPanel />}
      {activeTab === 'receipt'     && <ReceiptPanel />}
    </div>
  )
}

// ===== HR チャットパネル =====
function HRChatPanel() {
  const [question, setQuestion] = useState('')
  const [answer, setAnswer]     = useState('')
  const [loading, setLoading]   = useState(false)
  const [error, setError]       = useState('')

  const examples = [
    '田中さんの今月の残業時間を教えてください',
    '開発部の社員一覧を表示してください',
    '山田さんの有給残日数はいくらですか',
  ]

  const submit = async () => {
    if (!question.trim()) return
    setLoading(true); setError(''); setAnswer('')
    try {
      const res = await api.post('/api/v1/ai/hr-query/', { question })
      setAnswer(res.data.answer)
    } catch (e: any) {
      setError(e.response?.data?.error ?? 'エラーが発生しました')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-4">
      <div className="bg-indigo-50 border border-indigo-100 rounded-xl p-4">
        <p className="text-sm text-indigo-700 font-medium mb-2">質問例</p>
        <div className="flex flex-wrap gap-2">
          {examples.map((ex) => (
            <button
              key={ex}
              onClick={() => setQuestion(ex)}
              className="text-xs bg-white border border-indigo-200 text-indigo-600 px-3 py-1.5 rounded-full hover:bg-indigo-50"
            >
              {ex}
            </button>
          ))}
        </div>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 p-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">質問を入力</label>
        <div className="flex gap-2">
          <textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Enter' && e.metaKey) submit() }}
            placeholder="社員情報・勤怠・有給について自然言語で質問できます"
            rows={3}
            className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm resize-none focus:outline-none focus:ring-2 focus:ring-indigo-300"
          />
          <button
            onClick={submit}
            disabled={loading || !question.trim()}
            className="flex items-center gap-1.5 bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-300 text-white px-4 py-2 rounded-lg text-sm font-medium self-end"
          >
            {loading ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />}
            送信
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-sm text-red-700">{error}</div>
      )}
      {answer && (
        <div className="bg-white border border-gray-200 rounded-xl p-4">
          <p className="text-xs text-gray-400 mb-2">AI回答</p>
          <p className="text-sm text-gray-800 whitespace-pre-wrap">{answer}</p>
        </div>
      )}
    </div>
  )
}

// ===== MBO目標下書きパネル =====
function MBOGoalPanel() {
  const [role, setRole]           = useState('')
  const [focusArea, setFocusArea] = useState('')
  const [draft, setDraft]         = useState('')
  const [loading, setLoading]     = useState(false)
  const [error, setError]         = useState('')

  const submit = async () => {
    if (!role || !focusArea) return
    setLoading(true); setError(''); setDraft('')
    try {
      const res = await api.post('/api/v1/ai/draft-mbo-goal/', { role, focus_area: focusArea })
      setDraft(res.data.draft)
    } catch (e: any) {
      setError(e.response?.data?.error ?? 'エラーが発生しました')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-4 max-w-2xl">
      <div className="bg-white rounded-xl border border-gray-200 p-6 space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">役職・ポジション</label>
          <input
            value={role}
            onChange={(e) => setRole(e.target.value)}
            placeholder="例: フロントエンドエンジニア"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">注力したい分野・テーマ</label>
          <input
            value={focusArea}
            onChange={(e) => setFocusArea(e.target.value)}
            placeholder="例: チームの生産性向上とコードレビュー文化の醸成"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
          />
        </div>
        <button
          onClick={submit}
          disabled={loading || !role || !focusArea}
          className="w-full flex items-center justify-center gap-2 bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-300 text-white py-2.5 rounded-lg text-sm font-medium"
        >
          {loading ? <Loader2 size={16} className="animate-spin" /> : <Target size={16} />}
          目標を生成
        </button>
      </div>

      {error && <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-sm text-red-700">{error}</div>}
      {draft && (
        <div className="bg-white border border-gray-200 rounded-xl p-4">
          <p className="text-xs text-gray-400 mb-2">生成された目標案（編集してご使用ください）</p>
          <p className="text-sm text-gray-800 whitespace-pre-wrap">{draft}</p>
        </div>
      )}
    </div>
  )
}

// ===== 日報下書きパネル =====
function DailyReportPanel() {
  const [bullets, setBullets] = useState('')
  const [draft, setDraft]     = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError]     = useState('')

  const submit = async () => {
    if (!bullets.trim()) return
    setLoading(true); setError(''); setDraft('')
    try {
      const res = await api.post('/api/v1/ai/draft-daily-report/', { bullet_points: bullets })
      setDraft(res.data.draft)
    } catch (e: any) {
      setError(e.response?.data?.error ?? 'エラーが発生しました')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-4 max-w-2xl">
      <div className="bg-white rounded-xl border border-gray-200 p-6 space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">今日やったことを箇条書きで入力</label>
          <textarea
            value={bullets}
            onChange={(e) => setBullets(e.target.value)}
            placeholder={'・〇〇機能の実装\n・Aさんとのミーティング\n・バグ修正 x3'}
            rows={5}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm resize-none"
          />
        </div>
        <button
          onClick={submit}
          disabled={loading || !bullets.trim()}
          className="w-full flex items-center justify-center gap-2 bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-300 text-white py-2.5 rounded-lg text-sm font-medium"
        >
          {loading ? <Loader2 size={16} className="animate-spin" /> : <FileText size={16} />}
          日報を生成
        </button>
      </div>

      {error && <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-sm text-red-700">{error}</div>}
      {draft && (
        <div className="bg-white border border-gray-200 rounded-xl p-4">
          <p className="text-xs text-gray-400 mb-2">生成された日報（コピーしてご使用ください）</p>
          <p className="text-sm text-gray-800 whitespace-pre-wrap">{draft}</p>
        </div>
      )}
    </div>
  )
}

// ===== 領収書OCRパネル =====
function ReceiptPanel() {
  const [preview, setPreview]   = useState('')
  const [b64, setB64]           = useState('')
  const [mime, setMime]         = useState('image/jpeg')
  const [result, setResult]     = useState<any>(null)
  const [loading, setLoading]   = useState(false)
  const [error, setError]       = useState('')
  const fileRef = useRef<HTMLInputElement>(null)

  const onFile = (f: File) => {
    setMime(f.type || 'image/jpeg')
    const reader = new FileReader()
    reader.onload = (e) => {
      const dataUrl = e.target?.result as string
      setPreview(dataUrl)
      setB64(dataUrl.split(',')[1])
    }
    reader.readAsDataURL(f)
  }

  const submit = async () => {
    if (!b64) return
    setLoading(true); setError(''); setResult(null)
    try {
      const res = await api.post('/api/v1/ai/analyze-receipt/', { image_base64: b64, media_type: mime })
      setResult(res.data)
    } catch (e: any) {
      setError(e.response?.data?.error ?? 'エラーが発生しました')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-4 max-w-2xl">
      <div className="bg-white rounded-xl border border-gray-200 p-6 space-y-4">
        <div
          className="border-2 border-dashed border-gray-300 rounded-xl p-8 text-center cursor-pointer hover:border-indigo-400 transition-colors"
          onClick={() => fileRef.current?.click()}
          onDragOver={(e) => e.preventDefault()}
          onDrop={(e) => { e.preventDefault(); const f = e.dataTransfer.files[0]; if (f) onFile(f) }}
        >
          {preview ? (
            <img src={preview} alt="preview" className="max-h-48 mx-auto rounded-lg object-contain" />
          ) : (
            <>
              <Receipt size={32} className="mx-auto text-gray-400 mb-2" />
              <p className="text-sm text-gray-500">領収書画像をクリックまたはドラッグ＆ドロップ</p>
              <p className="text-xs text-gray-400 mt-1">JPEG / PNG</p>
            </>
          )}
          <input ref={fileRef} type="file" accept="image/*" className="hidden"
            onChange={(e) => { const f = e.target.files?.[0]; if (f) onFile(f) }} />
        </div>
        <button
          onClick={submit}
          disabled={loading || !b64}
          className="w-full flex items-center justify-center gap-2 bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-300 text-white py-2.5 rounded-lg text-sm font-medium"
        >
          {loading ? <Loader2 size={16} className="animate-spin" /> : <Receipt size={16} />}
          OCR解析
        </button>
      </div>

      {error && <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-sm text-red-700">{error}</div>}
      {result && (
        <div className="bg-white border border-gray-200 rounded-xl p-4">
          <p className="text-xs text-gray-400 mb-3">解析結果</p>
          <div className="grid grid-cols-3 gap-3">
            {[
              { label: '金額', value: result.amount ? `¥${Number(result.amount).toLocaleString()}` : '不明' },
              { label: '日付', value: result.date ?? '不明' },
              { label: '内容', value: result.description ?? '不明' },
            ].map(({ label, value }) => (
              <div key={label} className="bg-gray-50 rounded-lg p-3">
                <p className="text-xs text-gray-500 mb-1">{label}</p>
                <p className="text-sm font-medium text-gray-800">{value}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
