'use client'
import { useState, useEffect, useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'
import { useAuthStore } from '@/lib/store'
import { MessageSquare, Plus, Send, Paperclip, X, FileText, Image as ImageIcon, Users, Sparkles, Loader2 } from 'lucide-react'

const MAX_TOTAL_BYTES = 10 * 1024 * 1024 // 10MB

interface ChatAttachment {
  id: string
  file_name: string
  file_size: number
  content_type: string
  is_image: boolean
  url: string
}

interface ChatRoom {
  id: string
  room_type: 'direct' | 'group'
  name: string
  created_by: string | null
  members: Array<{ id: string; full_name: string; email: string }>
  last_message: { content: string; sender: string; created_at: string } | null
  unread_count: number
}

interface ChatMessage {
  id: string
  sender: string | null
  sender_name: string
  sender_avatar: string | null
  content: string
  created_at: string
  is_deleted: boolean
  attachments: ChatAttachment[]
}

export default function ChatPage() {
  const user = useAuthStore((s) => s.user)
  const qc = useQueryClient()
  const [selectedRoom, setSelectedRoom] = useState<ChatRoom | null>(null)
  const [message, setMessage] = useState('')
  const [files, setFiles] = useState<File[]>([])
  const [sizeError, setSizeError] = useState('')
  const [aiPolishing, setAiPolishing] = useState(false)

  const polishWithAI = async () => {
    if (!message.trim()) return
    setAiPolishing(true)
    try {
      const res = await api.post('/api/v1/ai/draft-daily-report/', { bullet_points: message })
      setMessage(res.data.draft)
    } catch { /* silent */ } finally {
      setAiPolishing(false)
    }
  }
  const [showNewGroup, setShowNewGroup] = useState(false)
  const [showMemberMgmt, setShowMemberMgmt] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const { data: rooms = [] } = useQuery<ChatRoom[]>({
    queryKey: ['chat-rooms'],
    queryFn: () => api.get('/api/v1/chat/rooms/').then((r) => r.data.results ?? r.data),
    refetchInterval: 5000,
  })

  const { data: messages = [] } = useQuery<ChatMessage[]>({
    queryKey: ['chat-messages', selectedRoom?.id],
    queryFn: () =>
      selectedRoom
        ? api.get(`/api/v1/chat/messages/?room=${selectedRoom.id}`).then((r) => r.data.results ?? r.data)
        : Promise.resolve([]),
    enabled: !!selectedRoom,
    refetchInterval: 3000,
  })

  const sendMut = useMutation({
    mutationFn: ({ content, files }: { content: string; files: File[] }) => {
      const fd = new FormData()
      fd.append('room', selectedRoom!.id)
      fd.append('content', content)
      files.forEach((f) => fd.append('files', f))
      return api.post('/api/v1/chat/messages/', fd, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['chat-messages', selectedRoom?.id] })
      qc.invalidateQueries({ queryKey: ['chat-rooms'] })
      setMessage('')
      setFiles([])
      setSizeError('')
    },
  })

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // rooms が更新されたとき selectedRoom を同期する
  useEffect(() => {
    if (selectedRoom) {
      const updated = rooms.find((r) => r.id === selectedRoom.id)
      if (updated) setSelectedRoom(updated)
    }
  }, [rooms])

  const getRoomName = (room: ChatRoom) => {
    if (room.room_type === 'group') return room.name || 'グループ'
    const other = room.members.find((m) => m.email !== user?.email)
    return other?.full_name ?? 'DM'
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = Array.from(e.target.files ?? [])
    const combined = [...files, ...selected]
    const total = combined.reduce((s, f) => s + f.size, 0)
    if (total > MAX_TOTAL_BYTES) {
      setSizeError('合計ファイルサイズが10MBを超えています')
      return
    }
    setSizeError('')
    setFiles(combined)
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  const removeFile = (idx: number) => {
    const updated = files.filter((_, i) => i !== idx)
    setFiles(updated)
    if (updated.reduce((s, f) => s + f.size, 0) <= MAX_TOTAL_BYTES) setSizeError('')
  }

  const handleSend = () => {
    if ((!message.trim() && files.length === 0) || !selectedRoom) return
    sendMut.mutate({ content: message.trim(), files })
  }

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes}B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)}KB`
    return `${(bytes / 1024 / 1024).toFixed(1)}MB`
  }

  return (
    <div className="flex h-[calc(100vh-64px)] bg-gray-50">
      {/* サイドバー: ルーム一覧 */}
      <div className="w-72 bg-white border-r flex flex-col">
        <div className="p-4 border-b">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <MessageSquare className="text-indigo-600" size={20} />
              <h2 className="font-bold text-gray-800">チャット</h2>
            </div>
            <button
              onClick={() => setShowNewGroup(true)}
              className="p-1.5 rounded-lg hover:bg-gray-100 text-gray-500"
              title="グループ作成"
            >
              <Plus size={18} />
            </button>
          </div>
        </div>
        <div className="flex-1 overflow-y-auto">
          {rooms.length === 0 ? (
            <p className="text-center text-gray-400 text-sm p-6">チャットルームがありません</p>
          ) : (
            rooms.map((room) => (
              <button
                key={room.id}
                onClick={() => setSelectedRoom(room)}
                className={`w-full text-left px-4 py-3 hover:bg-gray-50 border-b transition-colors ${
                  selectedRoom?.id === room.id ? 'bg-indigo-50 border-l-4 border-l-indigo-500' : ''
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-gray-800 text-sm truncate">{getRoomName(room)}</p>
                    {room.last_message && (
                      <p className="text-xs text-gray-400 truncate mt-0.5">{room.last_message.content}</p>
                    )}
                  </div>
                  {room.unread_count > 0 && (
                    <span className="ml-2 bg-indigo-500 text-white text-xs rounded-full px-1.5 py-0.5 shrink-0">
                      {room.unread_count}
                    </span>
                  )}
                </div>
              </button>
            ))
          )}
        </div>
      </div>

      {/* メインエリア */}
      <div className="flex-1 flex flex-col">
        {selectedRoom ? (
          <>
            <div className="bg-white border-b px-6 py-3 flex items-center gap-3">
              <div className="w-8 h-8 rounded-full bg-indigo-100 text-indigo-600 flex items-center justify-center font-bold text-sm">
                {getRoomName(selectedRoom).slice(0, 1)}
              </div>
              <div className="flex-1">
                <p className="font-semibold text-gray-800">{getRoomName(selectedRoom)}</p>
                <p className="text-xs text-gray-400">
                  {selectedRoom.room_type === 'group'
                    ? `${selectedRoom.members.length}名`
                    : 'ダイレクトメッセージ'}
                </p>
              </div>
              {/* グループのみ: メンバー管理ボタン */}
              {selectedRoom.room_type === 'group' && (
                <button
                  onClick={() => setShowMemberMgmt(true)}
                  className="flex items-center gap-1.5 text-sm text-indigo-600 hover:bg-indigo-50 px-3 py-1.5 rounded-lg transition-colors"
                  title="メンバー管理"
                >
                  <Users size={16} />
                  <span>メンバー管理</span>
                </button>
              )}
            </div>

            <div className="flex-1 overflow-y-auto p-6 space-y-4">
              {messages.map((msg) => {
                const isMe = msg.sender_name === user?.full_name
                return (
                  <div key={msg.id} className={`flex ${isMe ? 'justify-end' : 'justify-start'}`}>
                    {!isMe && (
                      <div className="w-8 h-8 rounded-full overflow-hidden bg-gray-200 shrink-0 mr-2 mt-1">
                        {msg.sender_avatar ? (
                          <img src={msg.sender_avatar} alt="" className="w-full h-full object-cover" />
                        ) : (
                          <div className="w-full h-full flex items-center justify-center text-xs font-bold text-gray-600">
                            {msg.sender_name.slice(0, 1)}
                          </div>
                        )}
                      </div>
                    )}
                    <div className={`max-w-xs lg:max-w-md`}>
                      {!isMe && <p className="text-xs text-gray-400 mb-1">{msg.sender_name}</p>}
                      {(msg.content && !msg.is_deleted) && (
                        <div className={`px-4 py-2 rounded-2xl text-sm ${
                          isMe ? 'bg-indigo-500 text-white rounded-br-sm' : 'bg-white text-gray-800 shadow-sm rounded-bl-sm'
                        }`}>
                          {msg.content}
                        </div>
                      )}
                      {msg.is_deleted && (
                        <div className="px-4 py-2 rounded-2xl text-sm bg-gray-100 text-gray-400 italic">
                          このメッセージは削除されました
                        </div>
                      )}
                      {/* 添付ファイル */}
                      {msg.attachments.length > 0 && (
                        <div className={`mt-1 flex flex-wrap gap-2 ${isMe ? 'justify-end' : 'justify-start'}`}>
                          {msg.attachments.map((att) => (
                            att.is_image ? (
                              <a key={att.id} href={att.url} target="_blank" rel="noopener noreferrer">
                                <img
                                  src={att.url}
                                  alt={att.file_name}
                                  className="w-40 h-28 object-cover rounded-xl border shadow-sm hover:opacity-90 transition"
                                />
                              </a>
                            ) : (
                              <a
                                key={att.id}
                                href={att.url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="flex items-center gap-2 bg-white border rounded-xl px-3 py-2 text-sm hover:bg-gray-50 shadow-sm"
                              >
                                <FileText size={16} className="text-gray-500 shrink-0" />
                                <span className="text-gray-700 truncate max-w-[140px]">{att.file_name}</span>
                                <span className="text-xs text-gray-400 shrink-0">{formatSize(att.file_size)}</span>
                              </a>
                            )
                          ))}
                        </div>
                      )}
                      <p className={`text-xs text-gray-400 mt-1 ${isMe ? 'text-right' : 'text-left'}`}>
                        {new Date(msg.created_at).toLocaleTimeString('ja-JP', { hour: '2-digit', minute: '2-digit' })}
                      </p>
                    </div>
                  </div>
                )
              })}
              <div ref={messagesEndRef} />
            </div>

            {/* 入力エリア */}
            <div className="bg-white border-t p-4">
              {/* 選択中ファイルプレビュー */}
              {files.length > 0 && (
                <div className="flex flex-wrap gap-2 mb-3">
                  {files.map((f, i) => {
                    const isImg = f.type.startsWith('image/')
                    const previewUrl = isImg ? URL.createObjectURL(f) : null
                    return (
                      <div key={i} className="relative group">
                        {isImg && previewUrl ? (
                          <img src={previewUrl} alt={f.name} className="w-16 h-16 object-cover rounded-lg border" />
                        ) : (
                          <div className="flex items-center gap-1 bg-gray-100 rounded-lg px-2 py-1 text-xs text-gray-600 max-w-[120px]">
                            <FileText size={12} className="shrink-0" />
                            <span className="truncate">{f.name}</span>
                          </div>
                        )}
                        <button
                          onClick={() => removeFile(i)}
                          className="absolute -top-1.5 -right-1.5 bg-gray-700 text-white rounded-full w-4 h-4 flex items-center justify-center opacity-0 group-hover:opacity-100 transition"
                        >
                          <X size={10} />
                        </button>
                      </div>
                    )
                  })}
                </div>
              )}
              {sizeError && <p className="text-xs text-red-500 mb-2">{sizeError}</p>}
              <div className="flex gap-2 items-end">
                <input
                  ref={fileInputRef}
                  type="file"
                  multiple
                  className="hidden"
                  onChange={handleFileChange}
                  accept="image/*,.pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.txt,.zip"
                />
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="p-2.5 rounded-xl border text-gray-500 hover:bg-gray-50 shrink-0"
                  title="ファイルを添付（合計10MBまで）"
                >
                  <Paperclip size={18} />
                </button>
                <div className="flex-1 relative">
                  <textarea
                    className="w-full border border-gray-200 rounded-xl px-4 py-2 pr-10 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300 resize-none"
                    placeholder="メッセージを入力… (Sparklesボタンでメモ→AI文章化)"
                    rows={1}
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend() }
                    }}
                  />
                  <button
                    onClick={polishWithAI}
                    disabled={aiPolishing || !message.trim()}
                    className="absolute right-2 bottom-2 p-1 text-purple-400 hover:text-purple-600 disabled:opacity-30 disabled:cursor-not-allowed"
                    title="メモ・箇条書きをAIが文章化"
                  >
                    {aiPolishing ? <Loader2 size={14} className="animate-spin" /> : <Sparkles size={14} />}
                  </button>
                </div>
                <button
                  onClick={handleSend}
                  disabled={!message.trim() && files.length === 0}
                  className="bg-indigo-600 text-white p-2.5 rounded-xl hover:bg-indigo-700 disabled:opacity-40 shrink-0"
                >
                  <Send size={18} />
                </button>
              </div>
              <p className="text-xs text-gray-400 mt-1.5">
                Shift+Enter で改行 ／ ファイル合計 {formatSize(files.reduce((s, f) => s + f.size, 0))} / 10MB
              </p>
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center text-gray-400">
            <div className="text-center">
              <MessageSquare size={48} className="mx-auto mb-3 opacity-30" />
              <p>ルームを選択してチャットを開始</p>
            </div>
          </div>
        )}
      </div>

      {showNewGroup && (
        <NewGroupModal onClose={() => setShowNewGroup(false)} onCreated={(room) => {
          qc.invalidateQueries({ queryKey: ['chat-rooms'] })
          setSelectedRoom(room)
          setShowNewGroup(false)
        }} />
      )}

      {showMemberMgmt && selectedRoom && (
        <MemberManagementModal
          room={selectedRoom}
          onClose={() => setShowMemberMgmt(false)}
          onChanged={() => {
            qc.invalidateQueries({ queryKey: ['chat-rooms'] })
          }}
        />
      )}
    </div>
  )
}

// ─────────────────────────────────────────────
// メンバー管理モーダル
// ─────────────────────────────────────────────
function MemberManagementModal({
  room,
  onClose,
  onChanged,
}: {
  room: ChatRoom
  onClose: () => void
  onChanged: () => void
}) {
  const qc = useQueryClient()
  const [search, setSearch] = useState('')

  const { data: employees = [] } = useQuery({
    queryKey: ['employees-for-chat'],
    queryFn: () => api.get('/api/v1/employees/').then((r) => r.data.results ?? r.data),
  })

  const addMut = useMutation({
    mutationFn: (userId: string) =>
      api.post(`/api/v1/chat/rooms/${room.id}/add-member/`, { user_id: userId }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['chat-rooms'] })
      onChanged()
    },
  })

  const removeMut = useMutation({
    mutationFn: (userId: string) =>
      api.post(`/api/v1/chat/rooms/${room.id}/remove-member/`, { user_id: userId }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['chat-rooms'] })
      onChanged()
    },
  })

  // 現在のメンバーIDセット
  const memberIds = new Set(room.members.map((m) => m.id))

  // 検索フィルタ: まだメンバーでない従業員を対象に絞り込む
  const filtered = employees.filter((emp: any) => {
    const uid = emp.user?.id
    if (!uid || memberIds.has(uid)) return false
    return emp.full_name?.includes(search) || emp.user?.email?.includes(search)
  })

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-bold text-gray-800 flex items-center gap-2">
            <Users size={20} className="text-indigo-600" />
            メンバー管理
          </h2>
          <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-gray-100 text-gray-400">
            <X size={18} />
          </button>
        </div>

        {/* 現在のメンバー一覧 */}
        <div className="mb-5">
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
            現在のメンバー（{room.members.length}名）
          </p>
          <div className="border rounded-xl divide-y max-h-44 overflow-y-auto">
            {room.members.map((member) => {
              const isCreator = member.id === room.created_by
              return (
                <div key={member.id} className="flex items-center justify-between px-3 py-2">
                  <div className="flex items-center gap-2">
                    <div className="w-7 h-7 rounded-full bg-indigo-100 text-indigo-600 flex items-center justify-center text-xs font-bold shrink-0">
                      {member.full_name.slice(0, 1)}
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-800">{member.full_name}</p>
                      <p className="text-xs text-gray-400">{member.email}</p>
                    </div>
                    {isCreator && (
                      <span className="ml-2 text-xs bg-indigo-100 text-indigo-600 px-2 py-0.5 rounded-full">
                        作成者
                      </span>
                    )}
                  </div>
                  {!isCreator && (
                    <button
                      onClick={() => removeMut.mutate(member.id)}
                      disabled={removeMut.isPending}
                      className="text-xs text-red-500 hover:bg-red-50 px-2 py-1 rounded-lg transition-colors disabled:opacity-50"
                    >
                      削除
                    </button>
                  )}
                </div>
              )
            })}
          </div>
        </div>

        {/* メンバー追加エリア */}
        <div>
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
            メンバーを追加
          </p>
          <input
            className="w-full border rounded-lg px-3 py-2 text-sm mb-2 focus:outline-none focus:ring-2 focus:ring-indigo-300"
            placeholder="名前・メールで検索..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          <div className="border rounded-xl divide-y max-h-44 overflow-y-auto">
            {filtered.length === 0 ? (
              <p className="text-sm text-gray-400 text-center py-4">
                {search ? '該当なし' : '追加できるユーザーがいません'}
              </p>
            ) : (
              filtered.map((emp: any) => (
                <div key={emp.id} className="flex items-center justify-between px-3 py-2">
                  <div className="flex items-center gap-2">
                    <div className="w-7 h-7 rounded-full bg-gray-100 text-gray-600 flex items-center justify-center text-xs font-bold shrink-0">
                      {emp.full_name?.slice(0, 1)}
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-800">{emp.full_name}</p>
                      <p className="text-xs text-gray-400">{emp.user?.email}</p>
                    </div>
                  </div>
                  <button
                    onClick={() => addMut.mutate(emp.user?.id)}
                    disabled={addMut.isPending}
                    className="text-xs text-indigo-600 hover:bg-indigo-50 px-2 py-1 rounded-lg transition-colors disabled:opacity-50"
                  >
                    追加
                  </button>
                </div>
              ))
            )}
          </div>
        </div>

        <div className="mt-5 flex justify-end">
          <button
            onClick={onClose}
            className="bg-gray-100 text-gray-700 px-5 py-2 rounded-lg text-sm hover:bg-gray-200"
          >
            閉じる
          </button>
        </div>
      </div>
    </div>
  )
}

// ─────────────────────────────────────────────
// グループ作成モーダル
// ─────────────────────────────────────────────
function NewGroupModal({ onClose, onCreated }: { onClose: () => void; onCreated: (room: any) => void }) {
  const [name, setName] = useState('')
  const [memberIds, setMemberIds] = useState<string[]>([])
  const { data: employees = [] } = useQuery({
    queryKey: ['employees-for-chat'],
    queryFn: () => api.get('/api/v1/employees/').then((r) => r.data.results ?? r.data),
  })

  const createMut = useMutation({
    mutationFn: () =>
      api.post('/api/v1/chat/rooms/', { room_type: 'group', name, member_ids: memberIds }),
    onSuccess: (res) => onCreated(res.data),
  })

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-md p-6">
        <h2 className="text-lg font-bold text-gray-800 mb-4">グループ作成</h2>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">グループ名</label>
            <input
              className="w-full border rounded-lg px-3 py-2 text-sm"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="グループ名を入力"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">メンバーを選択</label>
            <div className="border rounded-lg divide-y max-h-48 overflow-y-auto">
              {employees.map((emp: any) => (
                <label key={emp.id} className="flex items-center gap-3 px-3 py-2 hover:bg-gray-50 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={memberIds.includes(emp.user?.id)}
                    onChange={(e) => {
                      const uid = emp.user?.id
                      if (!uid) return
                      setMemberIds(e.target.checked
                        ? [...memberIds, uid]
                        : memberIds.filter((id) => id !== uid)
                      )
                    }}
                  />
                  <span className="text-sm text-gray-700">{emp.full_name}</span>
                </label>
              ))}
            </div>
          </div>
        </div>
        <div className="flex gap-3 mt-6">
          <button onClick={onClose} className="flex-1 border border-gray-300 text-gray-700 py-2 rounded-lg text-sm">キャンセル</button>
          <button
            onClick={() => createMut.mutate()}
            disabled={!name || memberIds.length === 0}
            className="flex-1 bg-indigo-600 text-white py-2 rounded-lg text-sm hover:bg-indigo-700 disabled:opacity-50"
          >作成</button>
        </div>
      </div>
    </div>
  )
}
