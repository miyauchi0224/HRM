'use client'
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'
import { CheckSquare, Plus, X, Calendar, Pencil } from 'lucide-react'

// ===== 型定義 =====
type TodoStatus = 'not_started' | 'in_progress' | 'done'

interface TodoItem {
  id: string
  title: string
  description: string
  status: TodoStatus
  due_date: string | null
  order: number
  created_at: string
}

// ===== カラム定義 =====
const COLUMNS: { key: TodoStatus; label: string; color: string; headerColor: string }[] = [
  { key: 'not_started', label: '未着手', color: 'bg-gray-50',   headerColor: 'bg-gray-200 text-gray-700' },
  { key: 'in_progress', label: '作業中',  color: 'bg-blue-50',  headerColor: 'bg-blue-200 text-blue-800' },
  { key: 'done',        label: '実施済み', color: 'bg-green-50', headerColor: 'bg-green-200 text-green-800' },
]

export default function TodoPage() {
  const qc = useQueryClient()
  const [showForm, setShowForm] = useState(false)

  const { data: todos = [], isLoading } = useQuery<TodoItem[]>({
    queryKey: ['todos'],
    queryFn: () => api.get('/api/v1/todo/items/').then((r) => r.data.results ?? r.data),
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

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
          <CheckSquare size={22} /> TODOリスト
        </h1>
        <button
          onClick={() => setShowForm(true)}
          className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
        >
          <Plus size={16} /> 追加
        </button>
      </div>

      {isLoading ? (
        <p className="text-gray-400 text-sm">読み込み中...</p>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {COLUMNS.map((col) => {
            const items = todos.filter((t) => t.status === col.key)
            return (
              <div key={col.key} className={`rounded-xl border border-gray-200 overflow-hidden`}>
                {/* カラムヘッダー */}
                <div className={`px-4 py-3 flex items-center justify-between ${col.headerColor}`}>
                  <span className="font-semibold text-sm">{col.label}</span>
                  <span className="text-xs font-medium bg-white/60 rounded-full px-2 py-0.5">
                    {items.length}
                  </span>
                </div>

                {/* カード一覧 */}
                <div className={`${col.color} p-3 min-h-[200px] space-y-2`}>
                  {items.length === 0 && (
                    <p className="text-xs text-gray-400 text-center py-8">なし</p>
                  )}
                  {items.map((item) => (
                    <TodoCard
                      key={item.id}
                      item={item}
                      currentStatus={col.key}
                      onMove={(newStatus) => moveMutation.mutate({ id: item.id, status: newStatus })}
                      onDelete={() => deleteMutation.mutate(item.id)}
                      onUpdate={() => qc.invalidateQueries({ queryKey: ['todos'] })}
                    />
                  ))}
                </div>
              </div>
            )
          })}
        </div>
      )}

      {showForm && (
        <NewTodoModal
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
  item, currentStatus, onMove, onDelete, onUpdate,
}: {
  item: TodoItem
  currentStatus: TodoStatus
  onMove: (s: TodoStatus) => void
  onDelete: () => void
  onUpdate: () => void
}) {
  const [editing, setEditing] = useState(false)
  const [title, setTitle]     = useState(item.title)
  const [desc, setDesc]       = useState(item.description)
  const [saving, setSaving]   = useState(false)

  const save = async () => {
    setSaving(true)
    try {
      await api.patch(`/api/v1/todo/items/${item.id}/`, { title, description: desc })
      setEditing(false)
      onUpdate()
    } finally {
      setSaving(false)
    }
  }

  const PREV: Record<TodoStatus, TodoStatus | null> = {
    not_started: null,
    in_progress: 'not_started',
    done: 'in_progress',
  }
  const NEXT: Record<TodoStatus, TodoStatus | null> = {
    not_started: 'in_progress',
    in_progress: 'done',
    done: null,
  }
  const MOVE_LABEL: Record<TodoStatus, string> = {
    not_started: '未着手へ',
    in_progress: '作業中へ',
    done: '実施済みへ',
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-3 shadow-sm">
      {editing ? (
        <div className="space-y-2">
          <input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
          />
          <textarea
            value={desc}
            onChange={(e) => setDesc(e.target.value)}
            rows={2}
            className="w-full px-2 py-1 border border-gray-300 rounded text-xs resize-none"
            placeholder="詳細（任意）"
          />
          <div className="flex gap-1">
            <button
              onClick={save}
              disabled={saving}
              className="px-2 py-1 bg-blue-600 text-white text-xs rounded font-medium"
            >
              {saving ? '保存中' : '保存'}
            </button>
            <button
              onClick={() => setEditing(false)}
              className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded"
            >
              キャンセル
            </button>
          </div>
        </div>
      ) : (
        <>
          <div className="flex items-start justify-between gap-1">
            <p className="text-sm font-medium text-gray-800 flex-1">{item.title}</p>
            <div className="flex gap-1 shrink-0">
              <button
                onClick={() => setEditing(true)}
                className="text-gray-300 hover:text-blue-500 transition-colors"
                title="編集"
              >
                <Pencil size={13} />
              </button>
              <button
                onClick={onDelete}
                className="text-gray-300 hover:text-red-500 transition-colors"
                title="削除"
              >
                <X size={14} />
              </button>
            </div>
          </div>

          {item.description && (
            <p className="text-xs text-gray-500 mt-1 whitespace-pre-wrap">{item.description}</p>
          )}

          {item.due_date && (
            <div className="flex items-center gap-1 mt-2 text-xs text-gray-400">
              <Calendar size={11} />
              {new Date(item.due_date).toLocaleDateString('ja-JP')}
            </div>
          )}

          {/* 移動ボタン */}
          <div className="flex gap-1 mt-2">
            {PREV[currentStatus] && (
              <button
                onClick={() => onMove(PREV[currentStatus]!)}
                className="text-xs px-2 py-0.5 bg-gray-100 hover:bg-gray-200 text-gray-600 rounded transition-colors"
              >
                ← {MOVE_LABEL[PREV[currentStatus]!]}
              </button>
            )}
            {NEXT[currentStatus] && (
              <button
                onClick={() => onMove(NEXT[currentStatus]!)}
                className="text-xs px-2 py-0.5 bg-blue-50 hover:bg-blue-100 text-blue-700 rounded transition-colors"
              >
                {MOVE_LABEL[NEXT[currentStatus]!]} →
              </button>
            )}
          </div>
        </>
      )}
    </div>
  )
}

// ===== 新規追加モーダル =====
function NewTodoModal({ onClose, onSaved }: { onClose: () => void; onSaved: () => void }) {
  const [title, setTitle]   = useState('')
  const [desc, setDesc]     = useState('')
  const [dueDate, setDue]   = useState('')
  const [status, setStatus] = useState<TodoStatus>('not_started')
  const [saving, setSaving] = useState(false)

  const save = async () => {
    if (!title.trim()) return
    setSaving(true)
    try {
      await api.post('/api/v1/todo/items/', {
        title,
        description: desc,
        status,
        due_date: dueDate || null,
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
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
              placeholder="例: 〇〇の対応"
            />
          </div>

          <div>
            <label className="text-sm font-medium text-gray-700 block mb-1">詳細</label>
            <textarea
              value={desc}
              onChange={(e) => setDesc(e.target.value)}
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm resize-none"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-sm font-medium text-gray-700 block mb-1">ステータス</label>
              <select
                value={status}
                onChange={(e) => setStatus(e.target.value as TodoStatus)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
              >
                <option value="not_started">未着手</option>
                <option value="in_progress">作業中</option>
                <option value="done">実施済み</option>
              </select>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-700 block mb-1">期限</label>
              <input
                type="date"
                value={dueDate}
                onChange={(e) => setDue(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
              />
            </div>
          </div>
        </div>

        <div className="flex gap-3 px-6 pb-6">
          <button
            onClick={onClose}
            className="flex-1 py-2.5 border border-gray-300 rounded-lg text-sm text-gray-600 hover:bg-gray-50"
          >
            キャンセル
          </button>
          <button
            onClick={save}
            disabled={!title.trim() || saving}
            className="flex-1 py-2.5 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white rounded-lg text-sm font-medium"
          >
            {saving ? '追加中...' : '追加'}
          </button>
        </div>
      </div>
    </div>
  )
}
