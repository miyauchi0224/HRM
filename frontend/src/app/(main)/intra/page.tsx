'use client'
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import api from '@/lib/api'
import { useAuthStore } from '@/lib/store'
import {
  Newspaper, Plus, Search, Pin, MessageCircle, Eye,
  CheckCircle, Clock, XCircle, FileEdit, Tag
} from 'lucide-react'

// ===== 型定義 =====
interface Article {
  id: string
  title: string
  category: string
  is_pinned: boolean
  status: 'draft' | 'pending' | 'approved' | 'rejected'
  author_name: string
  approver_name: string | null
  read_count: number
  comment_count: number
  is_read: boolean
  published_at: string | null
  created_at: string
}

const CATEGORY_LABEL: Record<string, { label: string; color: string }> = {
  announcement: { label: 'お知らせ',   color: 'bg-blue-100 text-blue-700' },
  technical:    { label: '技術情報',   color: 'bg-purple-100 text-purple-700' },
  company_news: { label: '社内報',     color: 'bg-green-100 text-green-700' },
  department:   { label: '部署連絡',   color: 'bg-yellow-100 text-yellow-700' },
  other:        { label: 'その他',     color: 'bg-gray-100 text-gray-600' },
}

const STATUS_LABEL: Record<string, { label: string; color: string; icon: React.ReactNode }> = {
  draft:    { label: '下書き',     color: 'text-gray-400',   icon: <FileEdit size={13} /> },
  pending:  { label: '承認待ち',   color: 'text-yellow-600', icon: <Clock size={13} /> },
  approved: { label: '公開中',     color: 'text-green-600',  icon: <CheckCircle size={13} /> },
  rejected: { label: '却下',       color: 'text-red-500',    icon: <XCircle size={13} /> },
}

export default function IntraPage() {
  const router = useRouter()
  const qc     = useQueryClient()
  const user   = useAuthStore((s) => s.user)
  const isManager = user?.role !== 'employee'

  const [q, setQ]           = useState('')
  const [category, setCat]  = useState('')
  const [debouncedQ, setDQ] = useState('')

  const { data: articles = [], isLoading } = useQuery<Article[]>({
    queryKey: ['intra-articles', debouncedQ, category],
    queryFn: () => {
      const params = new URLSearchParams()
      if (debouncedQ) params.set('q', debouncedQ)
      if (category)   params.set('category', category)
      return api.get(`/api/v1/intra/articles/?${params}`).then((r) => r.data.results ?? r.data)
    },
  })

  const approveMutation = useMutation({
    mutationFn: (id: string) => api.patch(`/api/v1/intra/articles/${id}/approve/`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['intra-articles'] }),
  })

  const pinMutation = useMutation({
    mutationFn: (id: string) => api.patch(`/api/v1/intra/articles/${id}/pin/`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['intra-articles'] }),
  })

  const handleSearch = (value: string) => {
    setQ(value)
    clearTimeout((window as any).__intraSearchTimer)
    ;(window as any).__intraSearchTimer = setTimeout(() => setDQ(value), 400)
  }

  const pinned    = articles.filter((a) => a.is_pinned && a.status === 'approved')
  const myDrafts  = articles.filter((a) => a.status !== 'approved' && a.author_name === user?.full_name)
  const published = articles.filter((a) => a.status === 'approved' && !a.is_pinned)
  const pending   = isManager ? articles.filter((a) => a.status === 'pending') : []

  return (
    <div>
      {/* ヘッダー */}
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
          <Newspaper size={22} /> イントラネット
        </h1>
        <Link
          href="/intra/new"
          className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
        >
          <Plus size={16} /> 記事を作成
        </Link>
      </div>

      {/* 検索・フィルタ */}
      <div className="flex gap-3 mb-6 flex-wrap">
        <div className="relative flex-1 min-w-[200px]">
          <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            type="text"
            value={q}
            onChange={(e) => handleSearch(e.target.value)}
            placeholder="タイトル・本文を検索..."
            className="w-full pl-9 pr-3 py-2 border border-gray-300 rounded-lg text-sm"
          />
        </div>
        <select
          value={category}
          onChange={(e) => setCat(e.target.value)}
          className="px-3 py-2 border border-gray-300 rounded-lg text-sm"
        >
          <option value="">すべてのカテゴリ</option>
          {Object.entries(CATEGORY_LABEL).map(([k, v]) => (
            <option key={k} value={k}>{v.label}</option>
          ))}
        </select>
      </div>

      {isLoading ? (
        <p className="text-gray-400 text-sm">読み込み中...</p>
      ) : (
        <div className="space-y-8">
          {/* 管理職：承認待ち */}
          {pending.length > 0 && (
            <section>
              <h2 className="text-sm font-semibold text-yellow-700 mb-3 flex items-center gap-1.5">
                <Clock size={14} /> 承認待ち（{pending.length}件）
              </h2>
              <div className="space-y-2">
                {pending.map((a) => (
                  <ArticleCard
                    key={a.id} article={a} isManager={isManager}
                    onApprove={() => approveMutation.mutate(a.id)}
                    onPin={() => pinMutation.mutate(a.id)}
                  />
                ))}
              </div>
            </section>
          )}

          {/* 自分の下書き・却下 */}
          {myDrafts.length > 0 && (
            <section>
              <h2 className="text-sm font-semibold text-gray-500 mb-3 flex items-center gap-1.5">
                <FileEdit size={14} /> 自分の記事
              </h2>
              <div className="space-y-2">
                {myDrafts.map((a) => (
                  <ArticleCard key={a.id} article={a} isManager={isManager}
                    onApprove={() => approveMutation.mutate(a.id)}
                    onPin={() => pinMutation.mutate(a.id)}
                  />
                ))}
              </div>
            </section>
          )}

          {/* ピン留め */}
          {pinned.length > 0 && (
            <section>
              <h2 className="text-sm font-semibold text-gray-500 mb-3 flex items-center gap-1.5">
                <Pin size={14} /> ピン留め
              </h2>
              <div className="space-y-2">
                {pinned.map((a) => (
                  <ArticleCard key={a.id} article={a} isManager={isManager}
                    onApprove={() => approveMutation.mutate(a.id)}
                    onPin={() => pinMutation.mutate(a.id)}
                  />
                ))}
              </div>
            </section>
          )}

          {/* 公開記事 */}
          <section>
            <h2 className="text-sm font-semibold text-gray-500 mb-3">
              公開記事（{published.length}件）
            </h2>
            {published.length === 0 ? (
              <div className="bg-white rounded-xl border border-dashed border-gray-300 py-16 text-center">
                <Newspaper size={32} className="mx-auto text-gray-300 mb-3" />
                <p className="text-gray-400 text-sm">公開されている記事はありません</p>
              </div>
            ) : (
              <div className="space-y-2">
                {published.map((a) => (
                  <ArticleCard key={a.id} article={a} isManager={isManager}
                    onApprove={() => approveMutation.mutate(a.id)}
                    onPin={() => pinMutation.mutate(a.id)}
                  />
                ))}
              </div>
            )}
          </section>
        </div>
      )}
    </div>
  )
}

// ===== 記事カード =====
function ArticleCard({
  article, isManager, onApprove, onPin,
}: {
  article: Article
  isManager: boolean
  onApprove: () => void
  onPin: () => void
}) {
  const st  = STATUS_LABEL[article.status]
  const cat = CATEGORY_LABEL[article.category]

  return (
    <div className={`bg-white rounded-xl border ${article.is_pinned ? 'border-yellow-300' : 'border-gray-200'} p-4 hover:shadow-sm transition-shadow`}>
      <div className="flex items-start gap-3">
        <div className="flex-1 min-w-0">
          {/* タイトル行 */}
          <div className="flex items-center gap-2 flex-wrap mb-1">
            {article.is_pinned && <Pin size={13} className="text-yellow-500 shrink-0" />}
            <Link
              href={`/intra/${article.id}`}
              className="font-semibold text-gray-800 hover:text-blue-600 truncate"
            >
              {article.title}
            </Link>
            {!article.is_read && article.status === 'approved' && (
              <span className="text-xs bg-blue-600 text-white px-1.5 py-0.5 rounded-full shrink-0">NEW</span>
            )}
          </div>
          {/* メタ情報 */}
          <div className="flex items-center gap-3 text-xs text-gray-400 flex-wrap">
            <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${cat.color}`}>
              <Tag size={10} />{cat.label}
            </span>
            <span className={`inline-flex items-center gap-1 ${st.color}`}>
              {st.icon}{st.label}
            </span>
            <span>{article.author_name}</span>
            {article.published_at && (
              <span>{new Date(article.published_at).toLocaleDateString('ja-JP')}</span>
            )}
            {article.status === 'approved' && (
              <>
                <span className="flex items-center gap-0.5"><Eye size={11} />{article.read_count}</span>
                <span className="flex items-center gap-0.5"><MessageCircle size={11} />{article.comment_count}</span>
              </>
            )}
          </div>
        </div>

        {/* 管理職アクション */}
        {isManager && (
          <div className="flex gap-2 shrink-0">
            {article.status === 'pending' && (
              <button
                onClick={onApprove}
                className="text-xs px-3 py-1.5 bg-green-600 hover:bg-green-700 text-white rounded-lg font-medium"
              >
                承認
              </button>
            )}
            {article.status === 'approved' && (
              <button
                onClick={onPin}
                className={`text-xs px-3 py-1.5 rounded-lg font-medium transition-colors ${
                  article.is_pinned
                    ? 'bg-yellow-100 text-yellow-700 hover:bg-yellow-200'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                {article.is_pinned ? 'ピン解除' : 'ピン留め'}
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
