'use client'
import { useState, useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'
import { useAuthStore } from '@/lib/store'
import {
  FolderOpen, FileText, Upload, Download, Plus, File,
  BarChart2, LayoutTemplate, Image,
} from 'lucide-react'

// ===== 型定義 =====
interface DocumentCategory {
  id: string
  name: string
  slug: string
  order: number
  document_count: number
}

interface DocumentFile {
  id: string
  version: number
  file_name: string
  file_size: number
  file_size_display: string
  content_type: string
  uploaded_by_name: string | null
  uploaded_at: string
}

interface Document {
  id: string
  title: string
  category: string | null
  category_name: string | null
  target_employee: string | null
  target_employee_name: string | null
  target_project: string | null
  target_project_name: string | null
  visibility: 'all' | 'hr_only' | 'personal' | 'role_manager' | 'project'
  description: string
  created_by_name: string | null
  created_at: string
  updated_at: string
  latest_file: DocumentFile | null
  file_count: number
}

interface Project {
  id: string
  code: string
  name: string
}

// ===== 定数 =====
const VISIBILITY_LABELS: Record<string, string> = {
  all:          '全社員',
  hr_only:      '人事のみ',
  personal:     '個人',
  role_manager: '管理職以上',
  project:      'プロジェクト',
}
const VISIBILITY_COLORS: Record<string, string> = {
  all:          'bg-blue-100 text-blue-700',
  hr_only:      'bg-purple-100 text-purple-700',
  personal:     'bg-green-100 text-green-700',
  role_manager: 'bg-orange-100 text-orange-700',
  project:      'bg-teal-100 text-teal-700',
}
const HR_ROLES = ['hr', 'admin']

// ===== ファイル種別アイコン判定 =====
function FileIcon({ contentType, fileName }: { contentType?: string; fileName?: string }) {
  const ct = (contentType ?? '').toLowerCase()
  const fn = (fileName ?? '').toLowerCase()

  if (ct.startsWith('image/') || /\.(jpg|jpeg|png|gif|webp)$/.test(fn)) {
    return <Image className="text-pink-500" size={20} />
  }
  if (ct === 'application/pdf' || fn.endsWith('.pdf')) {
    return <FileText className="text-red-500" size={20} />
  }
  if (ct.includes('spreadsheet') || ct.includes('excel') || /\.(xls|xlsx)$/.test(fn)) {
    return <BarChart2 className="text-green-500" size={20} />
  }
  if (
    ct.includes('presentation') || ct.includes('powerpoint') ||
    /\.(ppt|pptx)$/.test(fn)
  ) {
    return <LayoutTemplate className="text-orange-500" size={20} />
  }
  if (
    ct.includes('word') || ct.includes('document') ||
    /\.(doc|docx)$/.test(fn)
  ) {
    return <FileText className="text-blue-500" size={20} />
  }
  return <File className="text-blue-400" size={20} />
}

// ===== メインコンポーネント =====
export default function DocumentsPage() {
  const user   = useAuthStore((s) => s.user)
  const isHR   = HR_ROLES.includes(user?.role ?? '')
  const qc     = useQueryClient()

  // UI state
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null)
  const [showNewDoc, setShowNewDoc]             = useState(false)
  const [uploadingDocId, setUploadingDocId]     = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  // 新規ドキュメントフォームの state
  const [newTitle,       setNewTitle]      = useState('')
  const [newCategory,    setNewCategory]   = useState('')
  const [newVisibility,  setNewVisibility] = useState<Document['visibility']>('all')
  const [newDescription, setNewDescription] = useState('')
  const [newProject,     setNewProject]    = useState('')

  // ===== データ取得 =====
  const { data: categories = [] } = useQuery<DocumentCategory[]>({
    queryKey: ['doc-categories'],
    queryFn:  () => api.get('/api/v1/documents/categories/').then((r) => r.data.results ?? r.data),
  })

  const { data: documents = [], isLoading } = useQuery<Document[]>({
    queryKey: ['documents', selectedCategory],
    queryFn:  () => {
      const params = selectedCategory ? `?category=${selectedCategory}` : ''
      return api.get(`/api/v1/documents/${params}`).then((r) => r.data.results ?? r.data)
    },
  })

  const { data: projects = [] } = useQuery<Project[]>({
    queryKey: ['projects-list'],
    queryFn:  () => api.get('/api/v1/attendance/projects/').then((r) => r.data.results ?? r.data),
    enabled: isHR,
  })

  // ===== ミューテーション =====
  const createMut = useMutation({
    mutationFn: (data: object) => api.post('/api/v1/documents/', data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['documents'] })
      qc.invalidateQueries({ queryKey: ['doc-categories'] })
      setShowNewDoc(false)
      setNewTitle('')
      setNewCategory('')
      setNewVisibility('all')
      setNewDescription('')
      setNewProject('')
    },
    onError: () => alert('ドキュメントの作成に失敗しました'),
  })

  // カテゴリでフィルタリングされたドキュメント
  const filteredDocs = selectedCategory
    ? documents.filter((d) => d.category === selectedCategory)
    : documents

  // ===== ファイルアップロード処理 =====
  const handleUpload = async (docId: string, file: File) => {
    setUploadingDocId(docId)
    try {
      const form = new FormData()
      form.append('file', file)
      await api.post(`/api/v1/documents/${docId}/upload/`, form)
      qc.invalidateQueries({ queryKey: ['documents'] })
    } catch {
      alert('アップロードに失敗しました')
    } finally {
      setUploadingDocId(null)
    }
  }

  // ===== ファイルダウンロード処理 =====
  const handleDownload = async (doc: Document) => {
    try {
      const res = await api.get(`/api/v1/documents/${doc.id}/download/`, { responseType: 'blob' })
      const fileName = doc.latest_file?.file_name ?? doc.title
      const url  = window.URL.createObjectURL(new Blob([res.data]))
      const link = document.createElement('a')
      link.href     = url
      link.download = fileName
      link.click()
      window.URL.revokeObjectURL(url)
    } catch {
      alert('ダウンロードに失敗しました')
    }
  }

  // ===== 新規ドキュメント作成送信 =====
  const handleCreate = () => {
    if (!newTitle.trim()) { alert('タイトルを入力してください'); return }
    createMut.mutate({
      title:          newTitle,
      category:       newCategory || null,
      visibility:     newVisibility,
      description:    newDescription,
      target_project: newVisibility === 'project' ? (newProject || null) : null,
    })
  }

  return (
    <div>
      {/* ヘッダー */}
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
          <FileText className="text-blue-600" size={28} />
          ドキュメント管理
        </h1>
        {isHR && (
          <button
            onClick={() => setShowNewDoc(true)}
            className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
          >
            <Plus size={16} />
            新規ドキュメント
          </button>
        )}
      </div>

      {/* 新規ドキュメント作成フォーム */}
      {showNewDoc && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-2xl p-6 w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto">
            <h2 className="text-lg font-bold text-gray-800 mb-4">新規ドキュメント作成</h2>

            <div className="space-y-4">
              {/* タイトル */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  タイトル <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  placeholder="例: 就業規則 2024年版"
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              {/* カテゴリ */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">カテゴリ</label>
                <select
                  value={newCategory}
                  onChange={(e) => setNewCategory(e.target.value)}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">カテゴリなし</option>
                  {categories.map((c) => (
                    <option key={c.id} value={c.id}>{c.name}</option>
                  ))}
                </select>
              </div>

              {/* 公開範囲 */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">公開範囲</label>
                <select
                  value={newVisibility}
                  onChange={(e) => setNewVisibility(e.target.value as Document['visibility'])}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="all">全社員</option>
                  <option value="hr_only">人事のみ</option>
                  <option value="personal">個人</option>
                  <option value="role_manager">管理職以上</option>
                  <option value="project">プロジェクトメンバー</option>
                </select>
              </div>

              {/* プロジェクト選択（project 選択時のみ表示） */}
              {newVisibility === 'project' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    対象プロジェクト
                  </label>
                  <select
                    value={newProject}
                    onChange={(e) => setNewProject(e.target.value)}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">プロジェクトを選択</option>
                    {projects.map((p) => (
                      <option key={p.id} value={p.id}>{p.code} {p.name}</option>
                    ))}
                  </select>
                </div>
              )}

              {/* 説明 */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">説明</label>
                <textarea
                  value={newDescription}
                  onChange={(e) => setNewDescription(e.target.value)}
                  rows={3}
                  placeholder="ドキュメントの説明（任意）"
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                />
              </div>
            </div>

            <div className="flex gap-3 mt-6">
              <button
                onClick={handleCreate}
                disabled={createMut.isPending}
                className="flex-1 bg-blue-600 text-white py-2 rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors disabled:opacity-50"
              >
                {createMut.isPending ? '作成中...' : '作成'}
              </button>
              <button
                onClick={() => setShowNewDoc(false)}
                className="flex-1 bg-gray-100 text-gray-700 py-2 rounded-lg text-sm font-medium hover:bg-gray-200 transition-colors"
              >
                キャンセル
              </button>
            </div>
          </div>
        </div>
      )}

      {/* メインレイアウト: サイドバー + コンテンツ */}
      <div className="flex gap-6">

        {/* カテゴリサイドバー */}
        <aside className="w-56 flex-shrink-0">
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
            <div className="px-4 py-3 bg-gray-50 border-b border-gray-100">
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">カテゴリ</p>
            </div>
            <nav className="p-2 space-y-0.5">
              {/* 全件表示 */}
              <button
                onClick={() => setSelectedCategory(null)}
                className={`w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors ${
                  selectedCategory === null
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                <FolderOpen size={15} />
                <span className="flex-1 text-left">すべて</span>
                <span className={`text-xs px-1.5 py-0.5 rounded-full ${
                  selectedCategory === null ? 'bg-white/20 text-white' : 'bg-gray-100 text-gray-500'
                }`}>
                  {documents.length}
                </span>
              </button>

              {/* カテゴリ一覧 */}
              {categories.map((cat) => (
                <button
                  key={cat.id}
                  onClick={() => setSelectedCategory(cat.id)}
                  className={`w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors ${
                    selectedCategory === cat.id
                      ? 'bg-blue-600 text-white'
                      : 'text-gray-600 hover:bg-gray-100'
                  }`}
                >
                  <FolderOpen size={15} />
                  <span className="flex-1 text-left truncate">{cat.name}</span>
                  <span className={`text-xs px-1.5 py-0.5 rounded-full flex-shrink-0 ${
                    selectedCategory === cat.id ? 'bg-white/20 text-white' : 'bg-gray-100 text-gray-500'
                  }`}>
                    {cat.document_count}
                  </span>
                </button>
              ))}

              {categories.length === 0 && (
                <p className="text-xs text-gray-400 px-3 py-2">カテゴリなし</p>
              )}
            </nav>
          </div>
        </aside>

        {/* ドキュメント一覧 */}
        <div className="flex-1 min-w-0">
          {isLoading ? (
            <div className="flex items-center justify-center h-40 text-gray-400 text-sm">読み込み中...</div>
          ) : filteredDocs.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-40 text-gray-400 gap-2">
              <FileText size={32} className="opacity-40" />
              <p className="text-sm">ドキュメントがありません</p>
            </div>
          ) : (
            <div className="space-y-3">
              {filteredDocs.map((doc) => (
                <DocumentCard
                  key={doc.id}
                  doc={doc}
                  isHR={isHR}
                  isUploading={uploadingDocId === doc.id}
                  onDownload={() => handleDownload(doc)}
                  onUpload={(file) => handleUpload(doc.id, file)}
                />
              ))}
            </div>
          )}
        </div>
      </div>

      {/* 隠しファイル入力（使わないが型エラー防止のため） */}
      <input ref={fileInputRef} type="file" className="hidden" />
    </div>
  )
}

// ===== ドキュメントカード コンポーネント =====
function DocumentCard({
  doc, isHR, isUploading, onDownload, onUpload,
}: {
  doc: Document
  isHR: boolean
  isUploading: boolean
  onDownload: () => void
  onUpload: (file: File) => void
}) {
  const uploadRef  = useRef<HTMLInputElement>(null)
  const [isDragOver, setIsDragOver] = useState(false)

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) onUpload(file)
    if (uploadRef.current) uploadRef.current.value = ''
  }

  const handleDragOver = (e: React.DragEvent) => {
    if (!isHR) return
    e.preventDefault()
    setIsDragOver(true)
  }

  const handleDragLeave = () => setIsDragOver(false)

  const handleDrop = (e: React.DragEvent) => {
    if (!isHR) return
    e.preventDefault()
    setIsDragOver(false)
    const file = e.dataTransfer.files?.[0]
    if (file) onUpload(file)
  }

  const lf = doc.latest_file
  const isImage = lf && lf.content_type.startsWith('image/')
  // ダウンロード URL（サムネイル表示用 — 認証込みの blob は別途取得が必要なため一旦アイコン表示）
  // サムネイルは API の download エンドポイント経由で表示。
  // 画像の場合は img タグで embed するが、認証が必要なのでアイコンのみにとどめる。

  return (
    <div
      className={`bg-white rounded-xl shadow-sm border transition-shadow ${
        isDragOver
          ? 'border-blue-400 border-dashed shadow-md bg-blue-50'
          : 'border-gray-100 hover:shadow-md'
      } p-4`}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      {isDragOver && (
        <div className="text-center text-blue-500 text-xs mb-2 font-medium">
          ここにドロップしてアップロード
        </div>
      )}
      <div className="flex items-start gap-3">
        {/* アイコン / サムネイル */}
        <div className="flex-shrink-0 w-10 h-10 bg-gray-50 rounded-lg flex items-center justify-center overflow-hidden border border-gray-100">
          {isImage ? (
            <Image className="text-pink-400" size={20} />
          ) : (
            <FileIcon
              contentType={lf?.content_type}
              fileName={lf?.file_name}
            />
          )}
        </div>

        {/* 情報 */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <h3 className="font-semibold text-gray-800 text-sm truncate">{doc.title}</h3>
            {/* 公開範囲バッジ */}
            <span className={`text-xs px-2 py-0.5 rounded-full font-medium flex-shrink-0 ${
              VISIBILITY_COLORS[doc.visibility] ?? 'bg-gray-100 text-gray-600'
            }`}>
              {VISIBILITY_LABELS[doc.visibility] ?? doc.visibility}
            </span>
            {/* カテゴリバッジ */}
            {doc.category_name && (
              <span className="text-xs px-2 py-0.5 rounded-full bg-gray-100 text-gray-600 flex-shrink-0">
                {doc.category_name}
              </span>
            )}
            {/* プロジェクトバッジ */}
            {doc.target_project_name && (
              <span className="text-xs px-2 py-0.5 rounded-full bg-teal-50 text-teal-600 flex-shrink-0">
                {doc.target_project_name}
              </span>
            )}
          </div>

          {doc.description && (
            <p className="text-xs text-gray-500 mt-1 line-clamp-2">{doc.description}</p>
          )}

          {/* ファイル情報 */}
          <div className="mt-2 flex items-center gap-4 text-xs text-gray-400">
            {lf ? (
              <>
                <span className="flex items-center gap-1">
                  <FileText size={11} />
                  {lf.file_name}
                </span>
                <span>{lf.file_size_display}</span>
                <span>v{lf.version}</span>
                {doc.file_count > 1 && (
                  <span>（計 {doc.file_count} バージョン）</span>
                )}
              </>
            ) : (
              <span className="text-gray-300 italic">ファイル未添付</span>
            )}
          </div>

          {/* 作成者・更新日 */}
          <div className="mt-1 text-xs text-gray-400">
            {doc.created_by_name && <span>作成: {doc.created_by_name} / </span>}
            更新: {new Date(doc.updated_at).toLocaleDateString('ja-JP')}
          </div>
        </div>

        {/* アクションボタン */}
        <div className="flex items-center gap-2 flex-shrink-0">
          {/* ダウンロード: ファイルがある場合のみ */}
          {lf && (
            <button
              onClick={onDownload}
              title="最新版をダウンロード"
              className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-gray-100 text-gray-600 hover:bg-gray-200 transition-colors text-xs font-medium"
            >
              <Download size={14} />
              DL
            </button>
          )}

          {/* アップロード: HRのみ */}
          {isHR && (
            <>
              <button
                onClick={() => uploadRef.current?.click()}
                disabled={isUploading}
                title="新バージョンをアップロード（ドラッグ＆ドロップも可）"
                className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-blue-600 text-white hover:bg-blue-700 transition-colors text-xs font-medium disabled:opacity-50"
              >
                <Upload size={14} />
                {isUploading ? '...' : 'UP'}
              </button>
              <input
                ref={uploadRef}
                type="file"
                className="hidden"
                onChange={handleFileChange}
              />
            </>
          )}
        </div>
      </div>
    </div>
  )
}
