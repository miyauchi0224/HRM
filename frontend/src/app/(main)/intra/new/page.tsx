'use client'
import { useState, useRef } from 'react'
import { useRouter } from 'next/navigation'
import { useMutation } from '@tanstack/react-query'
import dynamic from 'next/dynamic'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import api from '@/lib/api'
import { ArrowLeft, Save, Send, ImagePlus, Eye, Edit3, Sparkles, Loader2 } from 'lucide-react'

// TipTap は DOM 操作を含むため SSR を無効にして動的インポート
const RichTextEditor = dynamic(
  () => import('@/components/editor/RichTextEditor'),
  {
    ssr: false,
    loading: () => (
      <div className="flex-1 flex items-center justify-center bg-gray-800 border border-gray-600 rounded-lg text-gray-500 text-sm">
        エディタを読み込み中...
      </div>
    ),
  }
)

type Format = 'text' | 'markdown' | 'html'

const CATEGORIES = [
  { value: 'announcement', label: 'お知らせ' },
  { value: 'technical',    label: '技術情報' },
  { value: 'company_news', label: '社内報' },
  { value: 'department',   label: '部署連絡' },
  { value: 'other',        label: 'その他' },
]

const FORMAT_OPTIONS: { value: Format; label: string; desc: string }[] = [
  { value: 'text',     label: 'テキスト',  desc: 'プレーンテキスト' },
  { value: 'markdown', label: 'Markdown', desc: '見出し・リスト・コード対応' },
  { value: 'html',     label: 'リッチテキスト', desc: 'ビジュアルエディタ（画像・リンク）' },
]

// ── 画像アップロードユーティリティ ──────────────────────────────────
async function uploadImage(file: File): Promise<string> {
  const form = new FormData()
  form.append('image', file)
  const res = await api.post('/api/v1/intra/upload/', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  // バックエンドが /media/... を返す → フロントからは http://localhost:8000 経由で参照
  const url: string = res.data.url
  return url.startsWith('http') ? url : `http://localhost:8000${url}`
}

// ── メインページ ──────────────────────────────────────────────────
export default function IntraNewPage() {
  const router = useRouter()
  const [title, setTitle]       = useState('')
  const [content, setContent]   = useState('')
  const [format, setFormat]     = useState<Format>('markdown')
  const [category, setCategory] = useState('announcement')
  const [mdPreview, setMdPreview] = useState(false)
  const [aiLoading, setAiLoading] = useState(false)
  const fileRef = useRef<HTMLInputElement>(null)

  const requestAI = async () => {
    if (!title.trim()) { alert('タイトルを先に入力してください'); return }
    setAiLoading(true)
    try {
      const res = await api.post('/api/v1/ai/draft-intra-article/', {
        title,
        summary: content || 'なし',
      })
      setContent(res.data.draft)
    } catch { /* silent */ } finally {
      setAiLoading(false)
    }
  }

  // Markdownエディタ用：画像アップロードして URL をカーソル位置に挿入
  const [uploading, setUploading] = useState(false)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const handleMdImageUpload = async (file: File) => {
    setUploading(true)
    try {
      const url = await uploadImage(file)
      const alt = file.name.replace(/\.[^/.]+$/, '')
      const insertion = `\n![${alt}](${url})\n`
      const el = textareaRef.current
      if (el) {
        const start = el.selectionStart
        const newContent = content.slice(0, start) + insertion + content.slice(start)
        setContent(newContent)
      } else {
        setContent((c) => c + insertion)
      }
    } catch {
      alert('画像のアップロードに失敗しました')
    } finally {
      setUploading(false)
    }
  }

  const saveMutation = useMutation({
    mutationFn: async (submit: boolean) => {
      const res = await api.post('/api/v1/intra/articles/', { title, content, format, category })
      if (submit) await api.patch(`/api/v1/intra/articles/${res.data.id}/submit/`)
      return res
    },
    onSuccess: () => router.push('/intra'),
  })

  const canSave = title.trim().length > 0 && content.trim().length > 0

  return (
    <div className="flex flex-col h-[calc(100vh-48px)] bg-gray-900 -m-6 p-6">
      {/* ヘッダー */}
      <div className="flex items-center justify-between mb-4 shrink-0">
        <div className="flex items-center gap-3">
          <button onClick={() => router.back()} className="text-gray-400 hover:text-white transition-colors">
            <ArrowLeft size={18} />
          </button>
          <h1 className="text-lg font-bold text-white">記事を作成</h1>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => saveMutation.mutate(false)}
            disabled={!canSave || saveMutation.isPending}
            className="flex items-center gap-1.5 px-3 py-1.5 text-sm border border-gray-600 text-gray-300 hover:bg-gray-700 rounded-lg disabled:opacity-40"
          >
            <Save size={14} /> 下書き保存
          </button>
          <button
            onClick={() => saveMutation.mutate(true)}
            disabled={!canSave || saveMutation.isPending}
            className="flex items-center gap-1.5 px-4 py-1.5 text-sm bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white rounded-lg font-medium"
          >
            <Send size={14} /> {saveMutation.isPending ? '処理中...' : '申請する'}
          </button>
        </div>
      </div>

      {/* タイトル・カテゴリ */}
      <div className="flex gap-3 mb-3 shrink-0">
        <input
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="記事タイトルを入力してください"
          className="flex-1 px-4 py-2.5 bg-gray-800 border border-gray-600 text-white rounded-lg text-base font-medium placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <select
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          className="px-3 py-2.5 bg-gray-800 border border-gray-600 text-gray-200 rounded-lg text-sm"
        >
          {CATEGORIES.map((c) => <option key={c.value} value={c.value}>{c.label}</option>)}
        </select>
      </div>

      {/* 形式セレクタ + AI生成 */}
      <div className="flex items-center gap-2 mb-3 shrink-0">
        {FORMAT_OPTIONS.map((f) => (
          <button
            key={f.value}
            onClick={() => setFormat(f.value)}
            className={`px-4 py-2 rounded-lg text-sm font-medium border transition-colors ${
              format === f.value
                ? 'bg-blue-600 border-blue-600 text-white'
                : 'bg-gray-800 border-gray-600 text-gray-300 hover:border-gray-400'
            }`}
          >
            {f.label}
            <span className="ml-1.5 text-xs opacity-60">{f.desc}</span>
          </button>
        ))}
        <button
          onClick={requestAI}
          disabled={aiLoading || !title.trim()}
          className="ml-auto flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium bg-purple-700 hover:bg-purple-600 disabled:opacity-50 disabled:cursor-not-allowed text-white border border-purple-600 transition-colors"
          title="タイトルと概要からAIが本文を作成します"
        >
          {aiLoading ? <Loader2 size={14} className="animate-spin" /> : <Sparkles size={14} />}
          AI本文生成
        </button>
      </div>

      {/* ── テキスト形式 ── */}
      {format === 'text' && (
        <div className="flex-1 flex flex-col min-h-0">
          <TextImageBar onUpload={handleMdImageUpload} uploading={uploading} fileRef={fileRef} />
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="本文をプレーンテキストで記述してください"
            className="flex-1 w-full px-4 py-3 bg-gray-800 border border-gray-600 text-gray-100 rounded-lg text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 placeholder-gray-500"
          />
        </div>
      )}

      {/* ── Markdown形式 ── */}
      {format === 'markdown' && (
        <div className="flex-1 flex flex-col min-h-0">
          <div className="flex items-center justify-between mb-2 shrink-0">
            <TextImageBar onUpload={handleMdImageUpload} uploading={uploading} fileRef={fileRef} />
            <button
              onClick={() => setMdPreview(!mdPreview)}
              className={`flex items-center gap-1.5 px-3 py-1.5 text-xs rounded-lg border transition-colors ${
                mdPreview
                  ? 'bg-gray-700 border-gray-500 text-white'
                  : 'bg-gray-800 border-gray-600 text-gray-400 hover:text-white'
              }`}
            >
              {mdPreview ? <Edit3 size={13} /> : <Eye size={13} />}
              {mdPreview ? '編集に戻る' : 'プレビュー'}
            </button>
          </div>
          {mdPreview ? (
            <div className="flex-1 bg-white rounded-lg p-6 overflow-y-auto">
              <article className="prose prose-sm max-w-none">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
              </article>
            </div>
          ) : (
            <textarea
              ref={textareaRef}
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder={`# 記事タイトル\n\n本文をMarkdown形式で記述してください。\n\n## セクション\n\n- リスト\n\n[リンク](URL)\n\n![画像](画像URL)`}
              className="flex-1 w-full px-4 py-3 bg-gray-800 border border-gray-600 text-gray-100 rounded-lg text-sm font-mono resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 placeholder-gray-500"
            />
          )}
        </div>
      )}

      {/* ── リッチテキスト（HTML）形式 ── */}
      {format === 'html' && (
        <div className="flex-1 flex flex-col min-h-0">
          <RichTextEditor content={content} onChange={setContent} />
        </div>
      )}
    </div>
  )
}

// ── テキスト/MD 用 画像挿入バー ─────────────────────────────────
function TextImageBar({
  onUpload, uploading, fileRef,
}: {
  onUpload: (f: File) => void
  uploading: boolean
  fileRef: React.RefObject<HTMLInputElement>
}) {
  return (
    <div className="flex items-center gap-2 mb-2 shrink-0">
      <button
        type="button"
        onClick={() => fileRef.current?.click()}
        disabled={uploading}
        className="flex items-center gap-1.5 px-3 py-1.5 text-xs bg-gray-700 hover:bg-gray-600 text-gray-300 rounded-lg border border-gray-600 disabled:opacity-50"
      >
        <ImagePlus size={13} /> {uploading ? 'アップロード中...' : '画像を挿入'}
      </button>
      <p className="text-xs text-gray-500">JPG・PNG・GIF・WebP（10MB以下）</p>
      <input
        ref={fileRef}
        type="file"
        accept="image/*"
        className="hidden"
        onChange={(e) => { if (e.target.files?.[0]) onUpload(e.target.files[0]) }}
      />
    </div>
  )
}
