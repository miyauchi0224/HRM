'use client'
import { useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'
import { useAuthStore } from '@/lib/store'
import {
  ArrowLeft, Eye, MessageCircle, Pin, CheckCircle,
  XCircle, Users, Send, Trash2, Tag, Calendar, User
} from 'lucide-react'

// ===== 型定義 =====
interface Comment { id: string; author_name: string; content: string; created_at: string }
interface Reader  { id: string; user_name: string; read_at: string }
interface ArticleDetail {
  id: string; title: string; content: string; format: 'text' | 'markdown' | 'html'; category: string
  is_pinned: boolean; status: string; reject_reason: string
  author_name: string; approver_name: string | null
  read_count: number; comment_count: number; comments: Comment[]; is_read: boolean
  published_at: string | null; created_at: string
}

const CATEGORY_LABEL: Record<string, { label: string; color: string }> = {
  announcement: { label: 'お知らせ',  color: 'bg-blue-100 text-blue-700' },
  technical:    { label: '技術情報',  color: 'bg-purple-100 text-purple-700' },
  company_news: { label: '社内報',    color: 'bg-green-100 text-green-700' },
  department:   { label: '部署連絡',  color: 'bg-yellow-100 text-yellow-700' },
  other:        { label: 'その他',    color: 'bg-gray-100 text-gray-600' },
}

export default function IntraDetailPage() {
  const { id }    = useParams<{ id: string }>()
  const router    = useRouter()
  const qc        = useQueryClient()
  const user      = useAuthStore((s) => s.user)
  const isManager = user?.role !== 'employee'

  const [comment, setComment]       = useState('')
  const [showReaders, setReaders]   = useState(false)
  const [rejectReason, setReason]   = useState('')
  const [showReject, setShowReject] = useState(false)

  const { data: article, isLoading } = useQuery<ArticleDetail>({
    queryKey: ['intra-article', id],
    queryFn:  () => api.get(`/api/v1/intra/articles/${id}/`).then((r) => r.data),
  })

  const { data: readersData, refetch: fetchReaders } = useQuery<{
    readers: Reader[]; read_count: number; total_employees: number; read_rate: number
  }>({
    queryKey: ['intra-readers', id],
    queryFn:  () => api.get(`/api/v1/intra/articles/${id}/readers/`).then((r) => r.data),
    enabled:  showReaders,
  })

  const approveMutation = useMutation({
    mutationFn: () => api.patch(`/api/v1/intra/articles/${id}/approve/`),
    onSuccess:  () => qc.invalidateQueries({ queryKey: ['intra-article', id] }),
  })

  const rejectMutation = useMutation({
    mutationFn: () => api.patch(`/api/v1/intra/articles/${id}/reject/`, { reject_reason: rejectReason }),
    onSuccess:  () => { qc.invalidateQueries({ queryKey: ['intra-article', id] }); setShowReject(false) },
  })

  const pinMutation = useMutation({
    mutationFn: () => api.patch(`/api/v1/intra/articles/${id}/pin/`),
    onSuccess:  () => qc.invalidateQueries({ queryKey: ['intra-article', id] }),
  })

  const submitMutation = useMutation({
    mutationFn: () => api.patch(`/api/v1/intra/articles/${id}/submit/`),
    onSuccess:  () => qc.invalidateQueries({ queryKey: ['intra-article', id] }),
  })

  const commentMutation = useMutation({
    mutationFn: (content: string) => api.post(`/api/v1/intra/articles/${id}/comments/`, { content }),
    onSuccess:  () => { qc.invalidateQueries({ queryKey: ['intra-article', id] }); setComment('') },
  })

  const deleteCommentMutation = useMutation({
    mutationFn: (commentId: string) => api.delete(`/api/v1/intra/articles/${id}/comments/${commentId}/`),
    onSuccess:  () => qc.invalidateQueries({ queryKey: ['intra-article', id] }),
  })

  if (isLoading) return <p className="text-gray-400 text-sm">読み込み中...</p>
  if (!article)  return <p className="text-red-500 text-sm">記事が見つかりません</p>

  const cat = CATEGORY_LABEL[article.category] ?? CATEGORY_LABEL.other
  const isAuthor = article.author_name === user?.full_name

  return (
    <div className="max-w-3xl mx-auto">
      {/* 戻るボタン */}
      <button
        onClick={() => router.back()}
        className="flex items-center gap-1.5 text-gray-400 hover:text-gray-600 text-sm mb-5 transition-colors"
      >
        <ArrowLeft size={15} /> イントラ一覧へ
      </button>

      {/* 承認待ちバナー（管理職） */}
      {isManager && article.status === 'pending' && (
        <div className="mb-5 bg-yellow-50 border border-yellow-300 rounded-xl p-4">
          <p className="text-sm font-semibold text-yellow-800 mb-3">この記事は承認待ちです</p>
          <div className="flex gap-2">
            <button
              onClick={() => approveMutation.mutate()}
              disabled={approveMutation.isPending}
              className="flex items-center gap-1.5 px-4 py-2 bg-green-600 hover:bg-green-700 text-white text-sm rounded-lg font-medium"
            >
              <CheckCircle size={15} /> 承認・公開する
            </button>
            <button
              onClick={() => setShowReject(true)}
              className="flex items-center gap-1.5 px-4 py-2 bg-red-100 hover:bg-red-200 text-red-700 text-sm rounded-lg font-medium"
            >
              <XCircle size={15} /> 却下する
            </button>
          </div>

          {showReject && (
            <div className="mt-3 space-y-2">
              <textarea
                value={rejectReason}
                onChange={(e) => setReason(e.target.value)}
                rows={2}
                placeholder="却下理由を入力してください"
                className="w-full px-3 py-2 border border-red-200 rounded-lg text-sm resize-none"
              />
              <div className="flex gap-2">
                <button
                  onClick={() => rejectMutation.mutate()}
                  disabled={!rejectReason.trim() || rejectMutation.isPending}
                  className="px-4 py-1.5 bg-red-600 text-white text-sm rounded-lg font-medium disabled:opacity-40"
                >
                  却下確定
                </button>
                <button
                  onClick={() => setShowReject(false)}
                  className="px-4 py-1.5 bg-gray-100 text-gray-600 text-sm rounded-lg"
                >
                  キャンセル
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* 下書き・却下バナー（投稿者） */}
      {isAuthor && article.status === 'draft' && (
        <div className="mb-5 bg-blue-50 border border-blue-200 rounded-xl p-4 flex items-center justify-between">
          <p className="text-sm text-blue-700">この記事はまだ下書きです</p>
          <button
            onClick={() => submitMutation.mutate()}
            disabled={submitMutation.isPending}
            className="flex items-center gap-1.5 px-4 py-2 bg-blue-600 text-white text-sm rounded-lg font-medium"
          >
            <Send size={13} /> 承認申請する
          </button>
        </div>
      )}
      {isAuthor && article.status === 'rejected' && (
        <div className="mb-5 bg-red-50 border border-red-200 rounded-xl p-4">
          <p className="text-sm font-semibold text-red-700 mb-1">この記事は却下されました</p>
          {article.reject_reason && (
            <p className="text-xs text-red-600 mb-3">理由: {article.reject_reason}</p>
          )}
          <button
            onClick={() => submitMutation.mutate()}
            disabled={submitMutation.isPending}
            className="flex items-center gap-1.5 px-4 py-2 bg-blue-600 text-white text-sm rounded-lg font-medium"
          >
            <Send size={13} /> 再申請する
          </button>
        </div>
      )}

      {/* 記事本体 */}
      <article className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        {/* 記事ヘッダー */}
        <div className="px-8 pt-8 pb-5 border-b border-gray-100">
          <div className="flex items-center gap-2 mb-3 flex-wrap">
            {article.is_pinned && <Pin size={14} className="text-yellow-500" />}
            <span className={`text-xs px-2.5 py-1 rounded-full font-medium ${cat.color}`}>
              <Tag size={10} className="inline mr-1" />{cat.label}
            </span>
          </div>
          <h1 className="text-2xl font-bold text-gray-900 mb-4">{article.title}</h1>
          <div className="flex items-center gap-4 text-sm text-gray-500 flex-wrap">
            <span className="flex items-center gap-1.5">
              <User size={14} /> {article.author_name}
            </span>
            {article.published_at && (
              <span className="flex items-center gap-1.5">
                <Calendar size={14} />
                {new Date(article.published_at).toLocaleDateString('ja-JP', {
                  year: 'numeric', month: 'long', day: 'numeric'
                })}
              </span>
            )}
            {article.approver_name && (
              <span className="text-green-600 flex items-center gap-1.5">
                <CheckCircle size={14} /> 承認: {article.approver_name}
              </span>
            )}
          </div>
          {/* 既読数・コメント数 + 管理職アクション */}
          <div className="flex items-center gap-4 mt-3 pt-3 border-t border-gray-50">
            <span className="flex items-center gap-1.5 text-xs text-gray-400">
              <Eye size={13} /> {article.read_count}人が既読
            </span>
            <span className="flex items-center gap-1.5 text-xs text-gray-400">
              <MessageCircle size={13} /> {article.comment_count}件のコメント
            </span>
            {/* 既読者一覧ボタン */}
            {(isAuthor || isManager) && article.status === 'approved' && (
              <button
                onClick={() => { setReaders(!showReaders); if (!showReaders) fetchReaders() }}
                className="flex items-center gap-1.5 text-xs text-blue-600 hover:underline"
              >
                <Users size={13} /> 既読者を確認
              </button>
            )}
            {/* ピン留めボタン */}
            {isManager && article.status === 'approved' && (
              <button
                onClick={() => pinMutation.mutate()}
                className={`flex items-center gap-1.5 text-xs transition-colors ${
                  article.is_pinned ? 'text-yellow-600' : 'text-gray-400 hover:text-yellow-600'
                }`}
              >
                <Pin size={13} /> {article.is_pinned ? 'ピン解除' : 'ピン留め'}
              </button>
            )}
          </div>
        </div>

        {/* 既読者一覧（展開） */}
        {showReaders && readersData && (
          <div className="px-8 py-4 bg-gray-50 border-b border-gray-100">
            <div className="flex items-center justify-between mb-3">
              <p className="text-sm font-semibold text-gray-700">
                既読者一覧 ({readersData.read_count}/{readersData.total_employees}人・既読率{readersData.read_rate}%)
              </p>
              {/* 既読率バー */}
              <div className="flex items-center gap-2">
                <div className="w-32 bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-blue-500 h-2 rounded-full transition-all"
                    style={{ width: `${readersData.read_rate}%` }}
                  />
                </div>
                <span className="text-xs text-gray-500">{readersData.read_rate}%</span>
              </div>
            </div>
            <div className="flex flex-wrap gap-2">
              {readersData.readers.map((r) => (
                <span key={r.id} className="text-xs bg-white border border-gray-200 rounded-full px-3 py-1 text-gray-600">
                  {r.user_name}
                  <span className="text-gray-400 ml-1">
                    {new Date(r.read_at).toLocaleDateString('ja-JP', { month: 'short', day: 'numeric' })}
                  </span>
                </span>
              ))}
            </div>
          </div>
        )}

        {/* 記事本文 — format別レンダリング */}
        <div className="px-8 py-8">
          <ArticleBody content={article.content} format={article.format} />
        </div>
      </article>

      {/* コメントセクション */}
      {article.status === 'approved' && (
        <div className="mt-6">
          <h2 className="text-base font-semibold text-gray-700 mb-4 flex items-center gap-2">
            <MessageCircle size={16} /> コメント（{article.comment_count}件）
          </h2>

          {/* コメント一覧 */}
          {article.comments.length > 0 ? (
            <div className="space-y-3 mb-5">
              {article.comments.map((c) => (
                <div key={c.id} className="bg-white rounded-xl border border-gray-200 p-4">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-gray-800">{c.author_name}</span>
                      <span className="text-xs text-gray-400">
                        {new Date(c.created_at).toLocaleDateString('ja-JP', {
                          month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
                        })}
                      </span>
                    </div>
                    {(c.author_name === user?.full_name || isManager) && (
                      <button
                        onClick={() => deleteCommentMutation.mutate(c.id)}
                        className="text-gray-300 hover:text-red-500 transition-colors"
                        title="コメントを削除"
                      >
                        <Trash2 size={13} />
                      </button>
                    )}
                  </div>
                  <p className="text-sm text-gray-700 whitespace-pre-wrap">{c.content}</p>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-400 text-sm mb-5">まだコメントはありません</p>
          )}

          {/* コメント投稿フォーム */}
          <div className="bg-white rounded-xl border border-gray-200 p-4">
            <textarea
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              rows={3}
              placeholder="コメントを入力してください..."
              className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 mb-3"
            />
            <div className="flex justify-end">
              <button
                onClick={() => commentMutation.mutate(comment)}
                disabled={!comment.trim() || commentMutation.isPending}
                className="flex items-center gap-1.5 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white text-sm rounded-lg font-medium"
              >
                <Send size={13} /> {commentMutation.isPending ? '送信中...' : 'コメントする'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

// ── format別 記事本文レンダリング ───────────────────────────────
function ArticleBody({ content, format }: { content: string; format: 'text' | 'markdown' | 'html' }) {
  if (format === 'html') {
    return (
      <div
        className="prose prose-sm max-w-none"
        dangerouslySetInnerHTML={{ __html: content }}
      />
    )
  }

  if (format === 'markdown') {
    // react-markdown の代わりにシンプルな変換（外部パッケージ不要）
    const html = simpleMarkdownToHtml(content)
    return (
      <div
        className="prose prose-sm max-w-none"
        dangerouslySetInnerHTML={{ __html: html }}
      />
    )
  }

  // text（プレーンテキスト）
  return (
    <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">{content}</p>
  )
}

/**
 * 最低限の Markdown → HTML 変換（外部ライブラリ不要）
 * 対応: 見出し・太字・斜体・コード・リンク・リスト・水平線・改行
 */
function simpleMarkdownToHtml(md: string): string {
  return md
    // コードブロック（```...```）
    .replace(/```([\s\S]*?)```/g, '<pre class="bg-gray-900 text-gray-100 rounded p-3 overflow-x-auto text-xs"><code>$1</code></pre>')
    // インラインコード
    .replace(/`([^`]+)`/g, '<code class="bg-gray-100 rounded px-1 text-sm font-mono">$1</code>')
    // 見出し
    .replace(/^### (.+)$/gm, '<h3 class="text-lg font-bold mt-4 mb-2">$1</h3>')
    .replace(/^## (.+)$/gm,  '<h2 class="text-xl font-bold mt-5 mb-2">$1</h2>')
    .replace(/^# (.+)$/gm,   '<h1 class="text-2xl font-bold mt-6 mb-3">$1</h1>')
    // 水平線
    .replace(/^---$/gm, '<hr class="my-4 border-gray-200" />')
    // 太字・斜体
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
    .replace(/\*([^*]+)\*/g,     '<em>$1</em>')
    // リンク
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" class="text-blue-600 underline" target="_blank" rel="noopener">$1</a>')
    // リスト（- item）
    .replace(/^- (.+)$/gm, '<li class="ml-4 list-disc">$1</li>')
    // 番号付きリスト（1. item）
    .replace(/^\d+\. (.+)$/gm, '<li class="ml-4 list-decimal">$1</li>')
    // 改行 → <br>（連続する改行は段落区切り）
    .replace(/\n\n/g, '</p><p class="mb-3">')
    .replace(/\n/g, '<br />')
    // 全体を段落で包む
    .replace(/^/, '<p class="mb-3">')
    .replace(/$/, '</p>')
}
