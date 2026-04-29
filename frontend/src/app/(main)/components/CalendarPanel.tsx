'use client'
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'
import FullCalendar from '@fullcalendar/react'
import dayGridPlugin from '@fullcalendar/daygrid'
import { Calendar, Unlink, X } from 'lucide-react'

interface NewEventData {
  date: string
  title: string
  provider: 'ms' | 'google'
}

interface EditEventData {
  id: string
  title: string
  start: string
  end: string
  provider: 'ms' | 'google'
  url?: string
}

export default function CalendarPanel() {
  const [year, setYear] = useState(new Date().getFullYear())
  const [month, setMonth] = useState(new Date().getMonth() + 1)
  const [revoking, setRevoking] = useState<string | null>(null)
  const [newEventModal, setNewEventModal] = useState<NewEventData | null>(null)
  const [eventTitle, setEventTitle] = useState('')
  const [editEventModal, setEditEventModal] = useState<EditEventData | null>(null)
  const [editTitle, setEditTitle] = useState('')
  const [editStart, setEditStart] = useState('')
  const [editEnd, setEditEnd] = useState('')
  const qc = useQueryClient()

  // 祝日取得
  const { data: holidays = [] } = useQuery({
    queryKey: ['holidays', year, month],
    queryFn: () =>
      api.get(`/api/v1/calendar/holidays/?year=${year}&month=${month}`)
        .then(r => r.data.holidays ?? []),
  })

  // カレンダーイベント取得（MS/Google）
  const { data: events = [] } = useQuery({
    queryKey: ['calendar-events', year, month],
    queryFn: () =>
      api.get(`/api/v1/calendar/events/?year=${year}&month=${month}`)
        .then(r => r.data.events ?? []),
  })

  // 保存済みプロバイダー取得
  const { data: providers = [] } = useQuery({
    queryKey: ['calendar-tokens'],
    queryFn: () =>
      api.get('/api/v1/calendar/tokens/')
        .then(r => r.data.providers ?? []),
  })

  // FullCalendarのイベントリストを構築
  const calendarEvents = [
    // 祝日
    ...holidays.map(h => ({
      id: `holiday-${h.date}`,
      title: h.name,
      date: h.date,
      backgroundColor: '#ef4444',
      borderColor: '#dc2626',
      textColor: '#ffffff',
      classNames: 'font-semibold text-xs',
    })),
    // カレンダーイベント
    ...events.map(e => ({
      id: e.id,
      title: e.title,
      start: e.start,
      end: e.end,
      backgroundColor: e.provider === 'microsoft' ? '#3b82f6' : '#8b5cf6',
      borderColor: e.provider === 'microsoft' ? '#1d4ed8' : '#6d28d9',
      url: e.url,
      extendedProps: { provider: e.provider },
    })),
  ]

  const handleRevoke = async (provider: string) => {
    setRevoking(provider)
    try {
      await api.post('/api/v1/calendar/oauth/revoke/', { provider })
      // トークン情報をリロード
      window.location.reload()
    } catch (error) {
      alert('連携解除に失敗しました')
    } finally {
      setRevoking(null)
    }
  }

  const handleOAuthStart = (provider: 'ms' | 'google') => {
    const endpoint = provider === 'ms'
      ? '/api/v1/calendar/oauth/ms/start/'
      : '/api/v1/calendar/oauth/google/start/'
    window.location.href = `${api.defaults.baseURL || '/api/v1'}${endpoint}`
  }

  const createEventMutation = useMutation({
    mutationFn: (data: { title: string; date: string; provider: 'ms' | 'google' }) =>
      api.post('/api/v1/calendar/events/create/', data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['calendar-events'] })
      setNewEventModal(null)
      setEventTitle('')
    },
    onError: () => {
      alert('予定の追加に失敗しました')
    },
  })

  const updateEventMutation = useMutation({
    mutationFn: (data: {
      event_id: string
      provider: 'ms' | 'google'
      title: string
      start: string
      end: string
    }) => api.post('/api/v1/calendar/events/update_event/', data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['calendar-events'] })
      setEditEventModal(null)
      setEditTitle('')
      setEditStart('')
      setEditEnd('')
    },
    onError: () => {
      alert('予定の更新に失敗しました')
    },
  })

  const deleteEventMutation = useMutation({
    mutationFn: (data: { event_id: string; provider: 'ms' | 'google' }) =>
      api.post('/api/v1/calendar/events/delete_event/', data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['calendar-events'] })
      setEditEventModal(null)
    },
    onError: () => {
      alert('予定の削除に失敗しました')
    },
  })

  const handleDateDblClick = (date: string, provider: 'ms' | 'google') => {
    if (providers.includes(provider)) {
      setNewEventModal({ date, title: '', provider })
      setEventTitle('')
    } else {
      alert(`${provider === 'ms' ? 'Microsoft' : 'Google'} カレンダーを同期してください`)
    }
  }

  const handleAddEvent = () => {
    if (!eventTitle.trim() || !newEventModal) return
    createEventMutation.mutate({
      title: eventTitle,
      date: newEventModal.date,
      provider: newEventModal.provider,
    })
  }

  const isWeekend = (date: Date) => {
    const day = date.getDay()
    return day === 0 || day === 6
  }

  const isSaturday = (date: Date) => {
    return date.getDay() === 6
  }

  const isSunday = (date: Date) => {
    return date.getDay() === 0
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6 mb-8">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <Calendar className="text-blue-600" size={22} />
          <h2 className="text-lg font-bold text-gray-800">カレンダー</h2>
        </div>
        <div className="flex gap-2">
          {!providers.includes('ms') && (
            <button
              onClick={() => handleOAuthStart('ms')}
              className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs rounded-lg font-medium transition-colors"
            >
              Microsoft と同期
            </button>
          )}
          {providers.includes('ms') && (
            <button
              onClick={() => handleRevoke('ms')}
              disabled={revoking === 'ms'}
              className="flex items-center gap-1 px-3 py-1.5 bg-blue-100 hover:bg-blue-200 text-blue-700 text-xs rounded-lg font-medium transition-colors disabled:bg-gray-200 disabled:text-gray-400"
            >
              <Unlink size={12} /> {revoking === 'ms' ? '解除中...' : '解除'}
            </button>
          )}
          {!providers.includes('google') && (
            <button
              onClick={() => handleOAuthStart('google')}
              className="px-3 py-1.5 bg-purple-600 hover:bg-purple-700 text-white text-xs rounded-lg font-medium transition-colors"
            >
              Google と同期
            </button>
          )}
          {providers.includes('google') && (
            <button
              onClick={() => handleRevoke('google')}
              disabled={revoking === 'google'}
              className="flex items-center gap-1 px-3 py-1.5 bg-purple-100 hover:bg-purple-200 text-purple-700 text-xs rounded-lg font-medium transition-colors disabled:bg-gray-200 disabled:text-gray-400"
            >
              <Unlink size={12} /> {revoking === 'google' ? '解除中...' : '解除'}
            </button>
          )}
        </div>
      </div>

      {/* カレンダー表示 */}
      <div className="bg-gray-50 rounded-lg p-4 mb-4">
        <FullCalendar
          plugins={[dayGridPlugin]}
          initialView="dayGridMonth"
          headerToolbar={{
            left: 'prev,next today',
            center: 'title',
            right: '',
          }}
          events={calendarEvents}
          height="auto"
          eventClick={(info) => {
            // カレンダーイベントの編集モーダルを表示
            if (info.event.extendedProps.provider) {
              setEditEventModal({
                id: info.event.id,
                title: info.event.title,
                start: info.event.startStr,
                end: info.event.endStr,
                provider: info.event.extendedProps.provider,
                url: info.event.url,
              })
              setEditTitle(info.event.title)
              setEditStart(info.event.startStr || '')
              setEditEnd(info.event.endStr || '')
            }
          }}
          eventDidMount={(info) => {
            if (info.event.extendedProps.provider) {
              info.el.classList.add('cursor-pointer')
              info.el.title = `${info.event.extendedProps.provider === 'microsoft' ? 'Microsoft' : 'Google'} カレンダー`
            }
          }}
          dayCellDidMount={(info) => {
            // 土曜日を青色背景に、日曜日を赤色背景に設定
            const dayText = info.el.querySelector('.fc-daygrid-day-number')
            if (isSaturday(info.date)) {
              info.el.classList.add('bg-blue-50')
              if (dayText) {
                dayText.classList.add('text-blue-600', 'font-semibold')
              }
            } else if (isSunday(info.date)) {
              info.el.classList.add('bg-red-50')
              if (dayText) {
                dayText.classList.add('text-red-600', 'font-semibold')
              }
            }
          }}
          dateClick={(info) => {
            // ダブルクリック判定用のカウンター
            const clickKey = `click-${info.dateStr}`
            let clicks = (window as any)[clickKey] || 0
            clicks++
            ;(window as any)[clickKey] = clicks

            if (clicks === 1) {
              setTimeout(() => {
                ;(window as any)[clickKey] = 0
              }, 300)
            } else if (clicks === 2) {
              ;(window as any)[clickKey] = 0
              // ダブルクリック時に予定追加モーダルを表示
              handleDateDblClick(info.dateStr, providers.includes('google') ? 'google' : 'ms')
            }
          }}
          locale="ja"
          buttonText={{
            today: '今月',
            month: '月',
          }}
          datesSet={(info) => {
            setYear(info.view.currentStart.getFullYear())
            setMonth(info.view.currentStart.getMonth() + 1)
          }}
        />
      </div>

      {/* 凡例 */}
      <div className="flex items-center gap-4 text-xs text-gray-600 flex-wrap">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded bg-red-500" />
          <span>日本の祝日</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded bg-blue-50 border border-blue-300" />
          <span>土曜日</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded bg-red-50 border border-red-300" />
          <span>日曜日</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded bg-blue-500" />
          <span>Microsoft カレンダー</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded bg-purple-500" />
          <span>Google カレンダー</span>
        </div>
      </div>

      {/* 予定追加モーダル */}
      {newEventModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-96 shadow-lg">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold text-gray-800">予定を追加</h3>
              <button
                onClick={() => {
                  setNewEventModal(null)
                  setEventTitle('')
                }}
                className="text-gray-400 hover:text-gray-600"
              >
                <X size={20} />
              </button>
            </div>

            <div className="mb-4">
              <p className="text-sm text-gray-600 mb-2">
                日付: <span className="font-semibold text-gray-800">{newEventModal.date}</span>
              </p>
              <p className="text-sm text-gray-600 mb-3">
                カレンダー: <span className="font-semibold text-gray-800">
                  {newEventModal.provider === 'ms' ? 'Microsoft' : 'Google'}
                </span>
              </p>
              <input
                type="text"
                placeholder="予定のタイトル"
                value={eventTitle}
                onChange={(e) => setEventTitle(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleAddEvent()}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                autoFocus
              />
            </div>

            <div className="flex gap-2 justify-end">
              <button
                onClick={() => {
                  setNewEventModal(null)
                  setEventTitle('')
                }}
                className="px-4 py-2 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg text-sm font-medium transition-colors"
              >
                キャンセル
              </button>
              <button
                onClick={handleAddEvent}
                disabled={!eventTitle.trim() || createEventMutation.isPending}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white rounded-lg text-sm font-medium transition-colors"
              >
                {createEventMutation.isPending ? '追加中...' : '追加'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 予定編集モーダル */}
      {editEventModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-96 shadow-lg">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold text-gray-800">予定を編集</h3>
              <button
                onClick={() => {
                  setEditEventModal(null)
                  setEditTitle('')
                  setEditStart('')
                  setEditEnd('')
                }}
                className="text-gray-400 hover:text-gray-600"
              >
                <X size={20} />
              </button>
            </div>

            <div className="space-y-4 mb-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  タイトル
                </label>
                <input
                  type="text"
                  value={editTitle}
                  onChange={(e) => setEditTitle(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  開始
                </label>
                <input
                  type="datetime-local"
                  value={editStart}
                  onChange={(e) => setEditStart(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  終了
                </label>
                <input
                  type="datetime-local"
                  value={editEnd}
                  onChange={(e) => setEditEnd(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div className="text-xs text-gray-500 bg-gray-50 p-2 rounded">
                カレンダー: {editEventModal.provider === 'ms' ? 'Microsoft' : 'Google'}
              </div>
            </div>

            <div className="flex gap-2 justify-between">
              <button
                onClick={() => {
                  if (confirm('この予定を削除しますか？')) {
                    deleteEventMutation.mutate({
                      event_id: editEventModal.id,
                      provider: editEventModal.provider,
                    })
                  }
                }}
                disabled={deleteEventMutation.isPending}
                className="px-4 py-2 bg-red-600 hover:bg-red-700 disabled:bg-red-300 text-white rounded-lg text-sm font-medium transition-colors"
              >
                {deleteEventMutation.isPending ? '削除中...' : '削除'}
              </button>
              <div className="flex gap-2">
                <button
                  onClick={() => {
                    setEditEventModal(null)
                    setEditTitle('')
                    setEditStart('')
                    setEditEnd('')
                  }}
                  className="px-4 py-2 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg text-sm font-medium transition-colors"
                >
                  キャンセル
                </button>
                <button
                  onClick={() => {
                    updateEventMutation.mutate({
                      event_id: editEventModal.id,
                      provider: editEventModal.provider,
                      title: editTitle,
                      start: editStart,
                      end: editEnd,
                    })
                  }}
                  disabled={!editTitle.trim() || updateEventMutation.isPending}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white rounded-lg text-sm font-medium transition-colors"
                >
                  {updateEventMutation.isPending ? '更新中...' : '更新'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
