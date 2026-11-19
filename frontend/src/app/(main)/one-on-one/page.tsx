'use client'
import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'
import { Bot, CheckSquare, Lock, MessagesSquare, Plus, Square, Trash2 } from 'lucide-react'

interface ActionItem { text: string; owner: 'manager' | 'member'; done: boolean }

interface Meeting {
  id: string
  manager: string
  manager_name: string
  member: string
  member_name: string
  my_role: 'manager' | 'member'
  scheduled_at: string
  duration_minutes: number
  status: 'scheduled' | 'done' | 'cancelled'
  agenda: string
  shared_notes: string
  manager_private_notes?: string
  action_items: ActionItem[]
  ai_summary: string
}

interface Partner { id: string; full_name: string; department: string }

const STATUS_LABEL: Record<string, { label: string; color: string }> = {
  scheduled: { label: '予定',   color: 'bg-blue-100 text-blue-700' },
  done:      { label: '実施済', color: 'bg-green-100 text-green-700' },
  cancelled: { label: '中止',   color: 'bg-gray-100 text-gray-500' },
}

const fmt = (iso: string) =>
  new Date(iso).toLocaleString('ja-JP', { month: 'numeric', day: 'numeric', weekday: 'short', hour: '2-digit', minute: '2-digit' })

/** 1on1 の記録（詳細設計書 7.7）。参加者2名だけが閲覧・編集できる */
export default function OneOnOnePage() {
  const qc = useQueryClient()
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [showNew, setShowNew]       = useState(false)

  const { data: meetings = [], isLoading } = useQuery<Meeting[]>({
    queryKey: ['one-on-ones'],
    queryFn: () => api.get('/api/v1/one-on-one/meetings/?page_size=100').then((r) => r.data.results ?? r.data),
  })
  const selected = meetings.find((m) => m.id === selectedId) ?? null

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
          <MessagesSquare size={22} /> 1on1
        </h1>
        <button onClick={() => setShowNew(true)}
                className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium px-4 py-2 rounded-lg">
          <Plus size={16} /> 1on1 を登録
        </button>
      </div>

      <div className="grid md:grid-cols-[300px_1fr] gap-6">
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden self-start">
          {isLoading ? (
            <p className="text-center text-gray-400 text-sm py-10">読み込み中...</p>
          ) : meetings.length === 0 ? (
            <p className="text-center text-gray-400 text-sm py-10 px-4">まだ1on1の記録がありません</p>
          ) : (
            <ul className="divide-y divide-gray-50">
              {meetings.map((m) => {
                const partner = m.my_role === 'manager' ? m.member_name : m.manager_name
                const st = STATUS_LABEL[m.status]
                return (
                  <li key={m.id}>
                    <button onClick={() => setSelectedId(m.id)}
                            className={`w-full text-left px-4 py-3 hover:bg-gray-50 ${selectedId === m.id ? 'bg-blue-50' : ''}`}>
                      <div className="flex items-center justify-between gap-2">
                        <span className="font-medium text-gray-700 text-sm">{partner}さん</span>
                        <span className={`text-[11px] px-2 py-0.5 rounded-full ${st.color}`}>{st.label}</span>
                      </div>
                      <p className="text-xs text-gray-400 mt-0.5">
                        {fmt(m.scheduled_at)}・{m.my_role === 'manager' ? 'あなたが上司' : 'あなたが部下'}
                      </p>
                    </button>
                  </li>
                )
              })}
            </ul>
          )}
        </div>

        {selected ? (
          <MeetingDetail key={selected.id} meeting={selected}
                         onSaved={() => qc.invalidateQueries({ queryKey: ['one-on-ones'] })} />
        ) : (
          <div className="bg-white rounded-xl border border-dashed border-gray-300 p-10 text-center text-sm text-gray-400">
            左の一覧から1on1を選ぶと、アジェンダ・メモ・アクションアイテムを編集できます
          </div>
        )}
      </div>

      {showNew && (
        <NewMeetingModal
          onClose={() => setShowNew(false)}
          onSaved={(id) => { setShowNew(false); setSelectedId(id); qc.invalidateQueries({ queryKey: ['one-on-ones'] }) }}
        />
      )}
    </div>
  )
}

function MeetingDetail({ meeting, onSaved }: { meeting: Meeting; onSaved: () => void }) {
  const isManager = meeting.my_role === 'manager'
  const [status, setStatus]   = useState(meeting.status)
  const [agenda, setAgenda]   = useState(meeting.agenda)
  const [notes, setNotes]     = useState(meeting.shared_notes)
  const [privateNotes, setPrivateNotes] = useState(meeting.manager_private_notes ?? '')
  const [items, setItems]     = useState<ActionItem[]>(meeting.action_items)
  const [newItem, setNewItem] = useState('')
  const [suggestion, setSuggestion] = useState<{ action_items: ActionItem[]; next_agenda: string[] } | null>(null)
  const [summary, setSummary] = useState(meeting.ai_summary)

  useEffect(() => { setSummary(meeting.ai_summary) }, [meeting.ai_summary])

  const patch = () => api.patch(`/api/v1/one-on-one/meetings/${meeting.id}/`, {
    status, agenda, shared_notes: notes, action_items: items,
    ...(isManager ? { manager_private_notes: privateNotes } : {}),
  })

  const save = useMutation({
    mutationFn: patch,
    onSuccess: onSaved,
    onError: (e: any) => alert(e.response?.data?.error ?? '保存に失敗しました'),
  })

  const ai = useMutation({
    mutationFn: async () => {
      // 入力中の内容で要約できるよう先に保存する
      await patch()
      return api.post(`/api/v1/one-on-one/meetings/${meeting.id}/ai-summary/`).then((r) => r.data)
    },
    onSuccess: (data) => {
      setSummary(data.summary)
      setSuggestion({ action_items: data.action_items, next_agenda: data.next_agenda })
      onSaved()
    },
    onError: (e: any) => alert(e.response?.data?.error ?? 'AI 要約に失敗しました'),
  })

  const addItem = (owner: 'manager' | 'member') => {
    if (!newItem.trim()) return
    setItems([...items, { text: newItem.trim(), owner, done: false }])
    setNewItem('')
  }

  const area = 'w-full px-3 py-2 border border-gray-300 rounded-lg text-sm resize-y'
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 space-y-5">
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h2 className="font-bold text-gray-800">{meeting.manager_name} × {meeting.member_name}</h2>
          <p className="text-sm text-gray-500">{fmt(meeting.scheduled_at)}（{meeting.duration_minutes}分）</p>
        </div>
        <select value={status} onChange={(e) => setStatus(e.target.value as Meeting['status'])}
                className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm">
          <option value="scheduled">予定</option>
          <option value="done">実施済</option>
          <option value="cancelled">中止</option>
        </select>
      </div>

      <div>
        <label className="text-sm font-medium text-gray-700 block mb-1">アジェンダ</label>
        <textarea rows={3} value={agenda} onChange={(e) => setAgenda(e.target.value)} className={area}
                  placeholder="話したいこと（どちらも編集できます）" />
      </div>
      <div>
        <label className="text-sm font-medium text-gray-700 block mb-1">共有メモ</label>
        <textarea rows={5} value={notes} onChange={(e) => setNotes(e.target.value)} className={area}
                  placeholder="話した内容・決まったこと" />
      </div>
      {isManager && (
        <div>
          <label className="text-sm font-medium text-gray-700 mb-1 flex items-center gap-1">
            <Lock size={13} /> 上司メモ（部下には表示されません・AI 要約にも使いません）
          </label>
          <textarea rows={3} value={privateNotes} onChange={(e) => setPrivateNotes(e.target.value)} className={`${area} bg-amber-50`} />
        </div>
      )}

      <div>
        <p className="text-sm font-medium text-gray-700 mb-2">アクションアイテム</p>
        <ul className="space-y-1.5 mb-2">
          {items.map((it, i) => (
            <li key={i} className="flex items-center gap-2 text-sm">
              <button onClick={() => setItems(items.map((x, j) => j === i ? { ...x, done: !x.done } : x))}
                      className="text-gray-400 hover:text-blue-600">
                {it.done ? <CheckSquare size={16} className="text-green-600" /> : <Square size={16} />}
              </button>
              <span className={`flex-1 ${it.done ? 'line-through text-gray-400' : 'text-gray-700'}`}>{it.text}</span>
              <span className="text-xs text-gray-400">{it.owner === 'manager' ? meeting.manager_name : meeting.member_name}</span>
              <button onClick={() => setItems(items.filter((_, j) => j !== i))} className="text-gray-300 hover:text-red-500">
                <Trash2 size={13} />
              </button>
            </li>
          ))}
        </ul>
        <div className="flex gap-2">
          <input value={newItem} onChange={(e) => setNewItem(e.target.value)} placeholder="やること"
                 className="flex-1 px-3 py-1.5 border border-gray-300 rounded-lg text-sm" />
          <button onClick={() => addItem('member')} className="text-xs px-3 py-1.5 border border-gray-300 rounded-lg hover:bg-gray-50">部下が対応</button>
          <button onClick={() => addItem('manager')} className="text-xs px-3 py-1.5 border border-gray-300 rounded-lg hover:bg-gray-50">上司が対応</button>
        </div>
      </div>

      {(summary || suggestion) && (
        <div className="rounded-lg bg-indigo-50 border border-indigo-100 p-4 text-sm space-y-3">
          {summary && (
            <div>
              <p className="font-medium text-indigo-800 mb-1 flex items-center gap-1"><Bot size={14} /> AI 要約</p>
              <p className="text-gray-700 whitespace-pre-wrap">{summary}</p>
            </div>
          )}
          {suggestion && suggestion.action_items.length > 0 && (
            <div>
              <p className="font-medium text-indigo-800 mb-1">アクションアイテムの候補</p>
              <ul className="list-disc pl-5 text-gray-700">
                {suggestion.action_items.map((a, i) => <li key={i}>{a.text}（{a.owner === 'manager' ? '上司' : '部下'}）</li>)}
              </ul>
              <button onClick={() => { setItems([...items, ...suggestion.action_items]); setSuggestion({ ...suggestion, action_items: [] }) }}
                      className="mt-2 text-xs px-3 py-1 rounded-lg bg-indigo-600 text-white">
                アクションアイテムに追加
              </button>
            </div>
          )}
          {suggestion && suggestion.next_agenda.length > 0 && (
            <div>
              <p className="font-medium text-indigo-800 mb-1">次回のアジェンダ案</p>
              <ul className="list-disc pl-5 text-gray-700">
                {suggestion.next_agenda.map((a, i) => <li key={i}>{a}</li>)}
              </ul>
            </div>
          )}
        </div>
      )}

      <div className="flex gap-3 justify-end">
        <button onClick={() => ai.mutate()} disabled={ai.isPending}
                className="flex items-center gap-1.5 px-4 py-2 border border-indigo-300 text-indigo-700 rounded-lg text-sm hover:bg-indigo-50 disabled:opacity-50">
          <Bot size={15} /> {ai.isPending ? '要約中...' : 'AI で要約'}
        </button>
        <button onClick={() => save.mutate()} disabled={save.isPending}
                className="px-5 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white rounded-lg text-sm font-medium">
          {save.isPending ? '保存中...' : '保存'}
        </button>
      </div>
    </div>
  )
}

function NewMeetingModal({ onClose, onSaved }: { onClose: () => void; onSaved: (id: string) => void }) {
  const { data: partners } = useQuery<{ members: Partner[]; managers: Partner[] }>({
    queryKey: ['one-on-one-partners'],
    queryFn: () => api.get('/api/v1/one-on-one/meetings/partners/').then((r) => r.data),
  })
  const { data: me } = useQuery<{ id: string }>({
    queryKey: ['employee-me'],
    queryFn: () => api.get('/api/v1/employees/me/').then((r) => r.data),
  })
  const [partner, setPartner] = useState('')
  const [at, setAt]           = useState('')
  const [duration, setDuration] = useState(30)
  const [agenda, setAgenda]   = useState('')
  const [saving, setSaving]   = useState(false)

  const save = async () => {
    if (!me) return
    const [role, id] = partner.split(':')
    setSaving(true)
    try {
      const res = await api.post('/api/v1/one-on-one/meetings/', {
        manager: role === 'member' ? me.id : id,
        member:  role === 'member' ? id : me.id,
        scheduled_at: new Date(at).toISOString(),
        duration_minutes: duration,
        agenda,
      })
      onSaved(res.data.id)
    } catch (e: any) {
      const d = e.response?.data
      alert(d?.error ?? d?.manager?.[0] ?? d?.non_field_errors?.[0] ?? '登録に失敗しました')
    } finally {
      setSaving(false)
    }
  }

  const empty = partners && partners.members.length === 0 && partners.managers.length === 0
  const input = 'w-full px-3 py-2 border border-gray-300 rounded-lg text-sm'
  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-md">
        <div className="flex items-center justify-between p-6 border-b border-gray-100">
          <h2 className="font-bold text-gray-800">1on1 を登録</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl leading-none">×</button>
        </div>
        <div className="p-6 space-y-4">
          {empty ? (
            <p className="text-sm text-gray-500">上司・部下が登録されていません。社員情報で上司を設定してください。</p>
          ) : (
            <label className="block text-sm text-gray-700">相手
              <select value={partner} onChange={(e) => setPartner(e.target.value)} className={`${input} mt-1`}>
                <option value="">選択してください</option>
                {partners?.members.length ? (
                  <optgroup label="部下">
                    {partners.members.map((p) => <option key={p.id} value={`member:${p.id}`}>{p.full_name}</option>)}
                  </optgroup>
                ) : null}
                {partners?.managers.length ? (
                  <optgroup label="上司">
                    {partners.managers.map((p) => <option key={p.id} value={`manager:${p.id}`}>{p.full_name}</option>)}
                  </optgroup>
                ) : null}
              </select>
            </label>
          )}
          <div className="grid grid-cols-[1fr_100px] gap-3">
            <label className="text-sm text-gray-700">日時
              <input type="datetime-local" value={at} onChange={(e) => setAt(e.target.value)} className={`${input} mt-1`} />
            </label>
            <label className="text-sm text-gray-700">時間
              <select value={duration} onChange={(e) => setDuration(Number(e.target.value))} className={`${input} mt-1`}>
                {[15, 30, 45, 60].map((m) => <option key={m} value={m}>{m}分</option>)}
              </select>
            </label>
          </div>
          <label className="block text-sm text-gray-700">アジェンダ（任意）
            <textarea rows={3} value={agenda} onChange={(e) => setAgenda(e.target.value)} className={`${input} mt-1 resize-none`} />
          </label>
        </div>
        <div className="flex gap-3 px-6 pb-6">
          <button onClick={onClose} className="flex-1 py-2.5 border border-gray-300 rounded-lg text-sm text-gray-600 hover:bg-gray-50 font-medium">
            キャンセル
          </button>
          <button onClick={save} disabled={saving || !partner || !at || !me}
                  className="flex-1 py-2.5 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white rounded-lg text-sm font-medium">
            {saving ? '登録中...' : '登録する'}
          </button>
        </div>
      </div>
    </div>
  )
}
