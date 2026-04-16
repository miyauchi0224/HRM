'use client'
import { useState, useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'
import { CheckSquare, Plus, X, Calendar, Pencil, BookOpen, GripVertical, Send } from 'lucide-react'

// ===== 型定義 =====
type TodoStatus = 'not_started' | 'in_progress' | 'done'
type Tab = 'kanban' | 'daily'

interface Project { id: string; code: string; name: string }
interface TodoItem {
  id: string
  title: string
  description: string
  status: TodoStatus
  due_date: string | null
  order: number
  project: string | null
  project_name: string | null
  project_code: string | null
  created_at: string
}
interface DailyReport {
  id: string
  report_date: string
  content: string
  tomorrow: string
  issues: string
  status: 'draft' | 'submitted'
}

// ===== カラム定義 =====
const COLUMNS: { key: TodoStatus; label: string; color: string; headerColor: string }[] = [
  { key: 'not_started', label: '未着手',  color: 'bg-gray-50',   headerColor: 'bg-gray-200 text-gray-700' },
  { key: 'in_progress', label: '作業中',  color: 'bg-blue-50',   headerColor: 'bg-blue-200 text-blue-800' },
  { key: 'done',        label: '実施済み', color: 'bg-green-50',  headerColor: 'bg-green-200 text-green-800' },
]

// ===== メインページ =====
export default function TodoPage() {
  const qc = useQueryClient()
  const [tab, setTab]           = useState<Tab>('kanban')
  const [showForm, setShowForm] = useState(false)
  const [dragOverCol, setDragOverCol] = useState<TodoStatus | null>(null)
  const draggingId = useRef<string | null>(null)

  const { data: todos = [], isLoading } = useQuery<TodoItem[]>({
    queryKey: ['todos'],
    queryFn: () => api.get('/api/v1/todo/items/').then((r) => r.data.results ?? r.data),
  })
  const { data: projects = [] } = useQuery<Project[]>({
    queryKey: ['projects'],
    queryFn: () => api.get('/api/v1/attendance/projects/').then((r) => r.data.results ?? r.data),
  })

  const moveMutation = useMutation({
    mutationFn: ({ id, status }: { id: string; status: TodoStatus }) =>
      api.patch(`/api/v1/todo/items/${id}/move/`, { status }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['todos'] }),
  })
  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.delete(`/api/v1/todo/items/${id}/`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['todos'] }),
  })

  // ===== HTML5 Drag & Drop ハンドラ =====
  const handleDragStart = (id: string) => {
    draggingId.current = id
  }
  const handleDragOver = (colKey: TodoStatus, e: React.DragEvent) => {
    e.preventDefault()
    setDragOverCol(colKey)
  }
  const handleDrop = (colKey: TodoStatus) => {
    const id = draggingId.current
    if (!id) return
    const item = todos.find((t) => t.id === id)
    if (item && item.status !== colKey) {
      moveMutation.mutate({ id, status: colKey })
    }
    draggingId.current = null
    setDragOverCol(null)
  }
  const handleDragEnd = () => {
    draggingId.current = null
    setDragOverCol(null)
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
          <CheckSquare size={22} /> TODOリスト
        </h1>
        {tab === 'kanban' && (
          <button
            onClick={() => setShowForm(true)}
            className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
          >
            <Plus size={16} /> 追加
          </button>
        )}
      </div>

      {/* タブ */}
      <div className="flex gap-1 mb-6 border-b border-gray-200">
        {([['kanban', 'カンバン'], ['daily', '日報']] as [Tab, string][]).map(([key, label]) => (
          <button
            key={key}
            onClick={() => setTab(key)}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              tab === key
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {tab === 'kanban' ? (
        isLoading ? (
          <p className="text-gray-400 text-sm">読み込み中...</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            {COLUMNS.map((col) => {
              const items = todos.filter((t) => t.status === col.key)
              const isOver = dragOverCol === col.key
              return (
                <div
                  key={col.key}
                  className={`rounded-xl border-2 overflow-hidden transition-colors ${
                    isOver ? 'border-blue-400 shadow-md' : 'border-gray-200'
                  }`}
                  onDragOver={(e) => handleDragOver(col.key, e)}
                  onDrop={() => handleDrop(col.key)}
                  onDragLeave={() => setDragOverCol(null)}
                >
                  <div className={`px-4 py-3 flex items-center justify-between ${col.headerColor}`}>
                    <span className="font-semibold text-sm">{col.label}</span>
                    <span className="text-xs font-medium bg-white/60 rounded-full px-2 py-0.5">
                      {items.length}
                    </span>
                  </div>
                  <div className={`${col.color} p-3 min-h-[200px] space-y-2`}>
                    {items.length === 0 && (
                      <p className="text-xs text-gray-400 text-center py-8">ここにドラッグ</p>
                    )}
                    {items.map((item) => (
                      <TodoCard
                        key={item.id}
                        item={item}
                        currentStatus={col.key}
                        projects={projects}
                        onMove={(s) => moveMutation.mutate({ id: item.id, status: s })}
                        onDelete={() => deleteMutation.mutate(item.id)}
                        onUpdate={() => qc.invalidateQueries({ queryKey: ['todos'] })}
                        onDragStart={() => handleDragStart(item.id)}
                        onDragEnd={handleDragEnd}
                      />
                    ))}
                  </div>
                </div>
              )
            })}
          </div>
        )
      ) : (
        <DailyReportTab />
      )}

      {showForm && (
        <NewTodoModal
          projects={projects}
          onClose={() => setShowForm(false)}
          onSaved={() => {
            setShowForm(false)
            qc.invalidateQueries({ queryKey: ['todos'] })
          }}
        />
      )}
    </div>
  )
}

// ===== TODOカード =====
function TodoCard({
  item, currentStatus, projects, onMove, onDelete, onUpdate, onDragStart, onDragEnd,
}: {
  item: TodoItem
  currentStatus: TodoStatus
  projects: Project[]
  onMove: (s: TodoStatus) => void
  onDelete: () => void
  onUpdate: () => void
  onDragStart: () => void
  onDragEnd: () => void
}) {
  const [editing, setEditing]   = useState(false)
  const [title, setTitle]       = useState(item.title)
  const [desc, setDesc]         = useState(item.description)
  const [projectId, setProject] = useState(item.project ?? '')
  const [saving, setSaving]     = useState(false)
  const [isDragging, setIsDragging] = useState(false)

  const save = async () => {
    setSaving(true)
    try {
      await api.patch(`/api/v1/todo/items/${item.id}/`, {
        title, description: desc, project: projectId || null,
      })
      setEditing(false)
      onUpdate()
    } finally {
      setSaving(false)
    }
  }

  const NEXT: Record<TodoStatus, TodoStatus | null> = {
    not_started: 'in_progress', in_progress: 'done', done: null,
  }
  const PREV: Record<TodoStatus, TodoStatus | null> = {
    not_started: null, in_progress: 'not_started', done: 'in_progress',
  }

  return (
    <div
      draggable
      onDragStart={(e) => {
        e.dataTransfer.effectAllowed = 'move'
        setIsDragging(true)
        onDragStart()
      }}
      onDragEnd={() => {
        setIsDragging(false)
        onDragEnd()
      }}
      className={`bg-white rounded-lg border border-gray-200 p-3 shadow-sm cursor-grab active:cursor-grabbing transition-opacity ${
        isDragging ? 'opacity-40' : 'opacity-100'
      }`}
    >
      {/* ドラッグハンドルアイコン */}
      <div className="flex items-start gap-1">
        <GripVertical size={14} className="text-gray-300 mt-0.5 shrink-0" />

        <div className="flex-1 min-w-0">
          {editing ? (
            <div className="space-y-2">
              <input value={title} onChange={(e) => setTitle(e.target.value)}
                className="w-full px-2 py-1 border border-gray-300 rounded text-sm" />
              <textarea value={desc} onChange={(e) => setDesc(e.target.value)} rows={2}
                className="w-full px-2 py-1 border border-gray-300 rounded text-xs resize-none"
                placeholder="詳細（任意）" />
              <select value={projectId} onChange={(e) => setProject(e.target.value)}
                className="w-full px-2 py-1 border border-gray-300 rounded text-xs">
                <option value="">プロジェクトなし</option>
                {projects.map((p) => (
                  <option key={p.id} value={p.id}>[{p.code}] {p.name}</option>
                ))}
              </select>
              <div className="flex gap-1">
                <button onClick={save} disabled={saving}
                  className="px-2 py-1 bg-blue-600 text-white text-xs rounded font-medium">
                  {saving ? '保存中' : '保存'}
                </button>
                <button onClick={() => setEditing(false)}
                  className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded">
                  キャンセル
                </button>
              </div>
            </div>
          ) : (
            <>
              <div className="flex items-start justify-between gap-1">
                <p className="text-sm font-medium text-gray-800 flex-1 break-words">{item.title}</p>
                <div className="flex gap-1 shrink-0">
                  <button onClick={() => setEditing(true)}
                    className="text-gray-300 hover:text-blue-500 transition-colors" title="編集">
                    <Pencil size={13} />
                  </button>
                  <button onClick={onDelete}
                    className="text-gray-300 hover:text-red-500 transition-colors" title="削除">
                    <X size={14} />
                  </button>
                </div>
              </div>

              {item.project_code && (
                <span className="inline-block mt-1 text-xs bg-blue-50 text-blue-700 border border-blue-200 rounded px-1.5 py-0.5">
                  {item.project_code}
                </span>
              )}
              {item.description && (
                <p className="text-xs text-gray-500 mt-1 whitespace-pre-wrap">{item.description}</p>
              )}
              {item.due_date && (
                <div className="flex items-center gap-1 mt-2 text-xs text-gray-400">
                  <Calendar size={11} />
                  {new Date(item.due_date).toLocaleDateString('ja-JP')}
                </div>
              )}

              <div className="flex gap-1 mt-2">
                {PREV[currentStatus] && (
                  <button onClick={() => onMove(PREV[currentStatus]!)}
                    className="text-xs px-2 py-0.5 bg-gray-100 hover:bg-gray-200 text-gray-600 rounded">←</button>
                )}
                {NEXT[currentStatus] && (
                  <button onClick={() => onMove(NEXT[currentStatus]!)}
                    className="text-xs px-2 py-0.5 bg-blue-50 hover:bg-blue-100 text-blue-700 rounded">→</button>
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}

// ===== 新規追加モーダル =====
function NewTodoModal({
  projects, onClose, onSaved,
}: {
  projects: Project[]
  onClose: () => void
  onSaved: () => void
}) {
  const [title, setTitle]    = useState('')
  const [desc, setDesc]      = useState('')
  const [dueDate, setDue]    = useState('')
  const [projectId, setProj] = useState('')
  const [status, setStatus]  = useState<TodoStatus>('not_started')
  const [saving, setSaving]  = useState(false)

  const save = async () => {
    if (!title.trim()) return
    setSaving(true)
    try {
      await api.post('/api/v1/todo/items/', {
        title, description: desc, status,
        due_date: dueDate || null,
        project: projectId || null,
      })
      onSaved()
    } catch {
      alert('登録に失敗しました')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-md">
        <div className="flex items-center justify-between p-6 border-b border-gray-100">
          <h2 className="font-bold text-gray-800">TODOを追加</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl">×</button>
        </div>
        <div className="p-6 space-y-4">
          <div>
            <label className="text-sm font-medium text-gray-700 block mb-1">
              タイトル <span className="text-red-500">*</span>
            </label>
            <input type="text" value={title} onChange={(e) => setTitle(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
              placeholder="例: 〇〇の対応" />
          </div>
          <div>
            <label className="text-sm font-medium text-gray-700 block mb-1">詳細</label>
            <textarea value={desc} onChange={(e) => setDesc(e.target.value)} rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm resize-none" />
          </div>
          <div>
            <label className="text-sm font-medium text-gray-700 block mb-1">プロジェクト</label>
            <select value={projectId} onChange={(e) => setProj(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm">
              <option value="">なし</option>
              {projects.map((p) => (
                <option key={p.id} value={p.id}>[{p.code}] {p.name}</option>
              ))}
            </select>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-sm font-medium text-gray-700 block mb-1">ステータス</label>
              <select value={status} onChange={(e) => setStatus(e.target.value as TodoStatus)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm">
                <option value="not_started">未着手</option>
                <option value="in_progress">作業中</option>
                <option value="done">実施済み</option>
              </select>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-700 block mb-1">期限</label>
              <input type="date" value={dueDate} onChange={(e) => setDue(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm" />
            </div>
          </div>
        </div>
        <div className="flex gap-3 px-6 pb-6">
          <button onClick={onClose}
            className="flex-1 py-2.5 border border-gray-300 rounded-lg text-sm text-gray-600 hover:bg-gray-50">
            キャンセル
          </button>
          <button onClick={save} disabled={!title.trim() || saving}
            className="flex-1 py-2.5 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white rounded-lg text-sm font-medium">
            {saving ? '追加中...' : '追加'}
          </button>
        </div>
      </div>
    </div>
  )
}

// ===== 日報タブ =====
function DailyReportTab() {
  const qc = useQueryClient()
  const today = new Date().toISOString().slice(0, 10)
  const [date, setDate]     = useState(today)
  const [content, setContent]   = useState('')
  const [tomorrow, setTomorrow] = useState('')
  const [issues, setIssues]     = useState('')
  const [saving, setSaving]     = useState(false)

  const { data: reports = [] } = useQuery<DailyReport[]>({
    queryKey: ['daily-reports'],
    queryFn: () => api.get('/api/v1/todo/daily-reports/').then((r) => r.data.results ?? r.data),
    onSuccess: (data: DailyReport[]) => {
      const existing = data.find((r) => r.report_date === today)
      if (existing) {
        setContent(existing.content)
        setTomorrow(existing.tomorrow)
        setIssues(existing.issues)
      }
    },
  } as any)

  const todayReport = reports.find((r) => r.report_date === date)

  const handleDateChange = (d: string) => {
    setDate(d)
    const existing = reports.find((r) => r.report_date === d)
    setContent(existing?.content ?? '')
    setTomorrow(existing?.tomorrow ?? '')
    setIssues(existing?.issues ?? '')
  }

  const save = async (submit = false) => {
    setSaving(true)
    try {
      if (todayReport) {
        await api.patch(`/api/v1/todo/daily-reports/${todayReport.id}/`, { content, tomorrow, issues })
        if (submit) await api.patch(`/api/v1/todo/daily-reports/${todayReport.id}/submit/`)
      } else {
        const res = await api.post('/api/v1/todo/daily-reports/', { report_date: date, content, tomorrow, issues })
        if (submit) await api.patch(`/api/v1/todo/daily-reports/${res.data.id}/submit/`)
      }
      qc.invalidateQueries({ queryKey: ['daily-reports'] })
    } catch {
      alert('保存に失敗しました')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="max-w-2xl">
      <div className="flex items-center gap-3 mb-6">
        <BookOpen size={18} className="text-gray-500" />
        <h2 className="font-semibold text-gray-700">日報</h2>
        <input type="date" value={date} onChange={(e) => handleDateChange(e.target.value)}
          className="ml-auto px-3 py-1.5 border border-gray-300 rounded-lg text-sm" />
      </div>

      {reports.length > 0 && (
        <div className="mb-6 flex flex-wrap gap-2">
          {reports.map((r) => (
            <button key={r.id} onClick={() => handleDateChange(r.report_date)}
              className={`px-3 py-1 text-xs rounded-full border transition-colors ${
                r.report_date === date
                  ? 'bg-blue-600 text-white border-blue-600'
                  : r.status === 'submitted'
                  ? 'bg-green-50 text-green-700 border-green-300'
                  : 'bg-gray-50 text-gray-600 border-gray-200'
              }`}>
              {new Date(r.report_date).toLocaleDateString('ja-JP', { month: 'short', day: 'numeric' })}
              {r.status === 'submitted' && ' ✓'}
            </button>
          ))}
        </div>
      )}

      <div className="space-y-4 bg-white rounded-xl border border-gray-200 p-6">
        <div>
          <label className="text-sm font-medium text-gray-700 block mb-1">
            本日の作業内容 <span className="text-red-500">*</span>
          </label>
          <textarea value={content} onChange={(e) => setContent(e.target.value)} rows={5}
            disabled={todayReport?.status === 'submitted'}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm resize-none disabled:bg-gray-50"
            placeholder="本日取り組んだ作業内容を記入してください" />
        </div>
        <div>
          <label className="text-sm font-medium text-gray-700 block mb-1">明日の予定</label>
          <textarea value={tomorrow} onChange={(e) => setTomorrow(e.target.value)} rows={3}
            disabled={todayReport?.status === 'submitted'}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm resize-none disabled:bg-gray-50"
            placeholder="明日取り組む予定の作業" />
        </div>
        <div>
          <label className="text-sm font-medium text-gray-700 block mb-1">課題・連絡事項</label>
          <textarea value={issues} onChange={(e) => setIssues(e.target.value)} rows={2}
            disabled={todayReport?.status === 'submitted'}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm resize-none disabled:bg-gray-50"
            placeholder="課題や上長への連絡事項" />
        </div>

        {todayReport?.status === 'submitted' ? (
          <p className="text-sm text-green-600 font-medium">✓ 提出済みです</p>
        ) : (
          <div className="flex gap-3">
            <button onClick={() => save(false)} disabled={!content.trim() || saving}
              className="flex-1 py-2.5 border border-gray-300 rounded-lg text-sm text-gray-600 hover:bg-gray-50 disabled:opacity-50">
              {saving ? '保存中...' : '下書き保存'}
            </button>
            <button onClick={() => save(true)} disabled={!content.trim() || saving}
              className="flex-1 py-2.5 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white rounded-lg text-sm font-medium flex items-center justify-center gap-2">
              <Send size={14} />
              {saving ? '提出中...' : '提出'}
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
