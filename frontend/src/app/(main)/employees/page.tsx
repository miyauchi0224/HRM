'use client'
import { useState, useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'
import { useAuthStore } from '@/lib/store'
import { Users, Plus, Search, X, Pencil, Check, Trash2, PhoneCall, AlertCircle, Camera } from 'lucide-react'

interface EmergencyContact {
  id: string
  name: string
  relationship: string
  phone: string
  sort_order: number
}

interface Employee {
  id: string
  employee_number: string
  full_name: string
  last_name: string
  first_name: string
  last_name_kana: string
  first_name_kana: string
  department: string
  position: string
  grade: number
  hire_date: string
  retire_date: string | null
  is_active: boolean
  email?: string
  role?: string
  roles?: string[]
  gender?: string
  birth_date?: string
  employment_type?: string
  phone?: string
  personal_email?: string
  zip_code?: string
  address?: string
  nearest_station?: string
  workplace_name?: string
  workplace_address?: string
  workplace_phone?: string
  commute_route?: string
  avatar_url?: string | null
  emergency_contacts?: EmergencyContact[]
}

const EMPLOYMENT_LABEL: Record<string, string> = {
  full_time: '正社員', part_time: 'パート', contract: '契約社員', dispatch: '派遣社員',
}
const POSITION_OPTIONS = [
  '社員', '主任', '係長', '次長', '課長', '部長', '取締役', '副社長', '社長',
]
const GENDER_LABEL: Record<string, string> = { male: '男性', female: '女性', other: 'その他' }
const ROLE_OPTIONS = [
  { value: 'employee',   label: '社員' },
  { value: 'manager',    label: '管理職' },
  { value: 'hr',         label: '人事' },
  { value: 'accounting', label: '経理' },
  { value: 'admin',      label: 'システム管理者' },
]

export default function EmployeesPage() {
  const [search, setSearch]     = useState('')
  const [selected, setSelected] = useState<Employee | null>(null)
  const [showNew, setShowNew]   = useState(false)
  const qc = useQueryClient()

  const { data: employees = [], isLoading } = useQuery<Employee[]>({
    queryKey: ['employees'],
    queryFn: () => api.get('/api/v1/employees/').then((r) => r.data.results ?? r.data),
  })

  // 詳細取得
  const { data: detail } = useQuery<Employee>({
    queryKey: ['employee', selected?.id],
    queryFn: () => api.get(`/api/v1/employees/${selected!.id}/`).then((r) => r.data),
    enabled: !!selected,
  })

  const filtered = employees.filter((e) =>
    [e.full_name, e.department, e.position, e.employee_number]
      .some((v) => v?.toLowerCase().includes(search.toLowerCase()))
  )

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
          <Users size={22} /> 社員情報
        </h1>
        <button
          onClick={() => setShowNew(true)}
          className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium px-4 py-2 rounded-lg"
        >
          <Plus size={16} /> 社員を追加
        </button>
      </div>

      <div className="flex gap-6">
        {/* 左: 一覧 */}
        <div className="w-80 shrink-0">
          {/* 検索 */}
          <div className="relative mb-3">
            <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="氏名・部署・社員番号で検索"
              className="w-full pl-9 pr-4 py-2 border border-gray-300 rounded-lg text-sm"
            />
            {search && (
              <button onClick={() => setSearch('')} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400">
                <X size={14} />
              </button>
            )}
          </div>

          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
            <div className="px-4 py-2 bg-gray-50 border-b text-xs text-gray-500 font-medium">
              {filtered.length} 名
            </div>
            {isLoading ? (
              <p className="text-center text-gray-400 text-sm py-8">読み込み中...</p>
            ) : filtered.length === 0 ? (
              <p className="text-center text-gray-400 text-sm py-8">該当なし</p>
            ) : (
              <ul className="divide-y divide-gray-50 max-h-[calc(100vh-220px)] overflow-y-auto">
                {filtered.map((emp) => (
                  <li
                    key={emp.id}
                    onClick={() => setSelected(emp)}
                    className={`flex items-center gap-3 px-4 py-3 cursor-pointer hover:bg-gray-50 transition-colors ${
                      selected?.id === emp.id ? 'bg-blue-50' : ''
                    }`}
                  >
                    {/* アバター */}
                    <div className="w-9 h-9 rounded-full overflow-hidden shrink-0">
                      {emp.avatar_url ? (
                        <img src={emp.avatar_url} alt={emp.full_name} className="w-full h-full object-cover" />
                      ) : (
                        <div className="w-full h-full bg-blue-100 text-blue-700 flex items-center justify-center text-sm font-bold">
                          {emp.full_name?.slice(0, 1) ?? '?'}
                        </div>
                      )}
                    </div>
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-gray-800 flex items-center gap-1.5">
                        {emp.full_name}
                        {!emp.is_active && (
                          <span className="text-xs bg-gray-200 text-gray-500 px-1.5 py-0.5 rounded">退職</span>
                        )}
                      </p>
                      <p className="text-xs text-gray-400 truncate">{emp.department} · {emp.position}</p>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>

        {/* 右: 詳細 */}
        <div className="flex-1 min-w-0">
          {selected && detail ? (
            <EmployeeDetail emp={detail} />
          ) : (
            <div className="bg-white rounded-xl border border-dashed border-gray-300 h-64 flex items-center justify-center">
              <p className="text-gray-400 text-sm">左の一覧から社員を選択してください</p>
            </div>
          )}
        </div>
      </div>

      {showNew && (
        <NewEmployeeModal
          onClose={() => setShowNew(false)}
          onSaved={() => { setShowNew(false); qc.invalidateQueries({ queryKey: ['employees'] }) }}
        />
      )}
    </div>
  )
}

// ===== 社員詳細 =====
function EmployeeDetail({ emp }: { emp: Employee }) {
  const qc          = useQueryClient()
  const user        = useAuthStore((s) => s.user)
  const canEdit     = user?.role !== 'employee' || emp.email === user?.email
  const avatarRef   = useRef<HTMLInputElement>(null)
  const [avatarUploading, setAvatarUploading] = useState(false)

  const uploadAvatar = async (file: File) => {
    setAvatarUploading(true)
    try {
      const form = new FormData()
      form.append('avatar', file)
      await api.post(`/api/v1/employees/${emp.id}/upload-avatar/`, form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      qc.invalidateQueries({ queryKey: ['employee', emp.id] })
      qc.invalidateQueries({ queryKey: ['employees'] })
    } catch {
      alert('アップロードに失敗しました')
    } finally {
      setAvatarUploading(false)
    }
  }

  // ── 電話番号インライン編集 ──
  const [editPhone, setEditPhone]   = useState(false)
  const [phoneVal, setPhoneVal]     = useState(emp.phone ?? '')
  const [savingPhone, setSavingPhone] = useState(false)

  const savePhone = async () => {
    setSavingPhone(true)
    try {
      await api.patch(`/api/v1/employees/${emp.id}/update-phone/`, { phone: phoneVal })
      qc.invalidateQueries({ queryKey: ['employee', emp.id] })
      setEditPhone(false)
    } finally {
      setSavingPhone(false)
    }
  }

  // ── 緊急連絡先 ──
  const [showAddContact, setShowAdd] = useState(false)
  const [newContact, setNewContact]  = useState({ name: '', relationship: '', phone: '' })
  const [editContactId, setEditContactId] = useState<string | null>(null)
  const [editContact, setEditContact] = useState({ name: '', relationship: '', phone: '' })

  const addContact = async () => {
    if (!newContact.name || !newContact.phone) return
    await api.post(`/api/v1/employees/${emp.id}/emergency-contacts/`, newContact)
    qc.invalidateQueries({ queryKey: ['employee', emp.id] })
    setNewContact({ name: '', relationship: '', phone: '' })
    setShowAdd(false)
  }

  const updateContact = async (id: string) => {
    await api.patch(`/api/v1/employees/${emp.id}/emergency-contacts/${id}/`, editContact)
    qc.invalidateQueries({ queryKey: ['employee', emp.id] })
    setEditContactId(null)
  }

  const deleteContact = async (id: string) => {
    if (!confirm('この緊急連絡先を削除しますか？')) return
    await api.delete(`/api/v1/employees/${emp.id}/emergency-contacts/${id}/`)
    qc.invalidateQueries({ queryKey: ['employee', emp.id] })
  }

  const rows: [string, string | undefined][] = [
    ['社員番号',   emp.employee_number],
    ['氏名（カナ）', `${emp.last_name_kana ?? ''} ${emp.first_name_kana ?? ''}`],
    ['性別',       GENDER_LABEL[emp.gender ?? ''] ?? '—'],
    ['生年月日',   emp.birth_date ?? '—'],
    ['メール',     emp.email ?? '—'],
    ['部署',       emp.department],
    ['役職',       emp.position],
    ['等級',       `${emp.grade} 級`],
    ['雇用形態',   EMPLOYMENT_LABEL[emp.employment_type ?? ''] ?? '—'],
    ['入社日',     emp.hire_date],
    ['退職日',     emp.retire_date ?? '在職中'],
  ]

  return (
    <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
      {/* ヘッダー */}
      <div className="flex items-center gap-4 p-6 border-b border-gray-100">
        {/* アバター（クリックでアップロード） */}
        <div className="relative shrink-0">
          <div
            className="w-14 h-14 rounded-full overflow-hidden cursor-pointer group"
            onClick={() => canEdit && avatarRef.current?.click()}
          >
            {emp.avatar_url ? (
              <img src={emp.avatar_url} alt={emp.full_name} className="w-full h-full object-cover" />
            ) : (
              <div className="w-full h-full bg-blue-100 text-blue-700 flex items-center justify-center text-xl font-bold">
                {emp.full_name?.slice(0, 1) ?? '?'}
              </div>
            )}
            {canEdit && (
              <div className="absolute inset-0 bg-black/40 rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                {avatarUploading ? (
                  <span className="text-white text-xs">...</span>
                ) : (
                  <Camera size={16} className="text-white" />
                )}
              </div>
            )}
          </div>
          {canEdit && (
            <input
              ref={avatarRef}
              type="file"
              accept="image/*"
              className="hidden"
              onChange={(e) => {
                const file = e.target.files?.[0]
                if (file) uploadAvatar(file)
                e.target.value = ''
              }}
            />
          )}
        </div>
        <div>
          <h2 className="text-xl font-bold text-gray-800">{emp.full_name}</h2>
          <p className="text-sm text-gray-500">{emp.department} · {emp.position}</p>
          <span className={`mt-1 inline-block text-xs px-2.5 py-0.5 rounded-full font-medium ${
            emp.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'
          }`}>
            {emp.is_active ? '在職中' : '退職済'}
          </span>
        </div>
      </div>

      <div className="p-6 space-y-6">
        {/* 基本情報 */}
        <section>
          <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-3">基本情報</h3>
          <dl className="grid grid-cols-2 gap-x-8 gap-y-4">
            {rows.map(([label, value]) => (
              <div key={label}>
                <dt className="text-xs text-gray-400 mb-0.5">{label}</dt>
                <dd className="text-sm font-medium text-gray-800">{value}</dd>
              </div>
            ))}
          </dl>
        </section>

        {/* 電話番号（インライン編集） */}
        <section>
          <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-3 flex items-center gap-1.5">
            <PhoneCall size={12} /> 電話番号
          </h3>
          {editPhone ? (
            <div className="flex items-center gap-2">
              <input
                type="tel"
                value={phoneVal}
                onChange={(e) => setPhoneVal(e.target.value)}
                placeholder="090-0000-0000"
                className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm"
                autoFocus
              />
              <button
                onClick={savePhone}
                disabled={savingPhone}
                className="p-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg"
                title="保存"
              >
                <Check size={15} />
              </button>
              <button
                onClick={() => { setEditPhone(false); setPhoneVal(emp.phone ?? '') }}
                className="p-2 bg-gray-100 hover:bg-gray-200 text-gray-600 rounded-lg"
                title="キャンセル"
              >
                <X size={15} />
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-gray-800">{emp.phone || '未登録'}</span>
              {canEdit && (
                <button
                  onClick={() => setEditPhone(true)}
                  className="text-gray-300 hover:text-blue-500 transition-colors"
                  title="編集"
                >
                  <Pencil size={13} />
                </button>
              )}
            </div>
          )}
        </section>

        {/* 緊急連絡先 */}
        <section>
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wide flex items-center gap-1.5">
              <AlertCircle size={12} /> 緊急連絡先
            </h3>
            {canEdit && (
              <button
                onClick={() => setShowAdd(!showAddContact)}
                className="flex items-center gap-1 text-xs text-blue-600 hover:underline"
              >
                <Plus size={12} /> 追加
              </button>
            )}
          </div>

          {/* 追加フォーム */}
          {showAddContact && (
            <div className="mb-3 p-3 bg-blue-50 border border-blue-200 rounded-lg space-y-2">
              <div className="grid grid-cols-3 gap-2">
                <input
                  value={newContact.name}
                  onChange={(e) => setNewContact((c) => ({ ...c, name: e.target.value }))}
                  placeholder="氏名 *"
                  className="px-2 py-1.5 border border-gray-300 rounded text-sm"
                />
                <input
                  value={newContact.relationship}
                  onChange={(e) => setNewContact((c) => ({ ...c, relationship: e.target.value }))}
                  placeholder="続柄（父・配偶者など）"
                  className="px-2 py-1.5 border border-gray-300 rounded text-sm"
                />
                <input
                  value={newContact.phone}
                  onChange={(e) => setNewContact((c) => ({ ...c, phone: e.target.value }))}
                  placeholder="電話番号 *"
                  type="tel"
                  className="px-2 py-1.5 border border-gray-300 rounded text-sm"
                />
              </div>
              <div className="flex gap-2">
                <button
                  onClick={addContact}
                  disabled={!newContact.name || !newContact.phone}
                  className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white text-xs rounded-lg font-medium"
                >
                  追加する
                </button>
                <button
                  onClick={() => { setShowAdd(false); setNewContact({ name: '', relationship: '', phone: '' }) }}
                  className="px-3 py-1.5 bg-white border border-gray-300 text-gray-600 text-xs rounded-lg"
                >
                  キャンセル
                </button>
              </div>
            </div>
          )}

          {/* 一覧 */}
          {!emp.emergency_contacts || emp.emergency_contacts.length === 0 ? (
            <p className="text-sm text-gray-400">登録なし</p>
          ) : (
            <div className="space-y-2">
              {emp.emergency_contacts.map((c) => (
                <div key={c.id} className="border border-gray-200 rounded-lg overflow-hidden">
                  {editContactId === c.id ? (
                    <div className="p-3 bg-gray-50 space-y-2">
                      <div className="grid grid-cols-3 gap-2">
                        <input
                          value={editContact.name}
                          onChange={(e) => setEditContact((x) => ({ ...x, name: e.target.value }))}
                          placeholder="氏名"
                          className="px-2 py-1.5 border border-gray-300 rounded text-sm"
                        />
                        <input
                          value={editContact.relationship}
                          onChange={(e) => setEditContact((x) => ({ ...x, relationship: e.target.value }))}
                          placeholder="続柄"
                          className="px-2 py-1.5 border border-gray-300 rounded text-sm"
                        />
                        <input
                          value={editContact.phone}
                          onChange={(e) => setEditContact((x) => ({ ...x, phone: e.target.value }))}
                          placeholder="電話番号"
                          type="tel"
                          className="px-2 py-1.5 border border-gray-300 rounded text-sm"
                        />
                      </div>
                      <div className="flex gap-2">
                        <button
                          onClick={() => updateContact(c.id)}
                          className="px-3 py-1.5 bg-blue-600 text-white text-xs rounded-lg font-medium"
                        >
                          保存
                        </button>
                        <button
                          onClick={() => setEditContactId(null)}
                          className="px-3 py-1.5 bg-white border border-gray-300 text-gray-600 text-xs rounded-lg"
                        >
                          キャンセル
                        </button>
                      </div>
                    </div>
                  ) : (
                    <div className="flex items-center gap-4 px-4 py-3">
                      <PhoneCall size={14} className="text-gray-400 shrink-0" />
                      <div className="flex-1 grid grid-cols-3 gap-2 text-sm">
                        <span className="font-medium text-gray-800">{c.name}</span>
                        <span className="text-gray-500">{c.relationship || '—'}</span>
                        <span className="text-gray-700 font-mono">{c.phone}</span>
                      </div>
                      {canEdit && (
                        <div className="flex gap-1.5 shrink-0">
                          <button
                            onClick={() => {
                              setEditContactId(c.id)
                              setEditContact({ name: c.name, relationship: c.relationship, phone: c.phone })
                            }}
                            className="text-gray-300 hover:text-blue-500 transition-colors"
                            title="編集"
                          >
                            <Pencil size={13} />
                          </button>
                          <button
                            onClick={() => deleteContact(c.id)}
                            className="text-gray-300 hover:text-red-500 transition-colors"
                            title="削除"
                          >
                            <Trash2 size={13} />
                          </button>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </section>

        {/* 住所・最寄り駅 */}
        <AddressSection emp={emp} canEdit={canEdit} onSaved={() => qc.invalidateQueries({ queryKey: ['employee', emp.id] })} />

        {/* 勤務先・通勤経路 */}
        <WorkplaceSection emp={emp} canEdit={canEdit} onSaved={() => qc.invalidateQueries({ queryKey: ['employee', emp.id] })} />
      </div>
    </div>
  )
}

// ===== 住所セクション =====
function AddressSection({ emp, canEdit, onSaved }: { emp: Employee; canEdit: boolean; onSaved: () => void }) {
  const [editing, setEditing] = useState(false)
  const [form, setForm] = useState({
    zip_code: emp.zip_code ?? '',
    address:  emp.address ?? '',
    nearest_station: emp.nearest_station ?? '',
  })
  const [saving, setSaving] = useState(false)

  const save = async () => {
    setSaving(true)
    try {
      await api.patch(`/api/v1/employees/${emp.id}/`, form)
      onSaved()
      setEditing(false)
    } finally { setSaving(false) }
  }

  return (
    <section>
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wide">住所・最寄り駅</h3>
        {canEdit && !editing && (
          <button onClick={() => setEditing(true)} className="text-gray-300 hover:text-blue-500">
            <Pencil size={13} />
          </button>
        )}
      </div>
      {editing ? (
        <div className="space-y-2">
          <div className="grid grid-cols-3 gap-2">
            <input value={form.zip_code} onChange={(e) => setForm((f) => ({ ...f, zip_code: e.target.value }))}
              placeholder="〒000-0000" className="px-3 py-2 border border-gray-300 rounded-lg text-sm" />
            <input value={form.address} onChange={(e) => setForm((f) => ({ ...f, address: e.target.value }))}
              placeholder="都道府県・市区町村・番地" className="col-span-2 px-3 py-2 border border-gray-300 rounded-lg text-sm" />
          </div>
          <input value={form.nearest_station} onChange={(e) => setForm((f) => ({ ...f, nearest_station: e.target.value }))}
            placeholder="最寄り駅（例: 渋谷駅）" className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm" />
          <div className="flex gap-2">
            <button onClick={save} disabled={saving}
              className="px-3 py-1.5 bg-blue-600 text-white text-xs rounded-lg font-medium">
              {saving ? '保存中' : '保存'}
            </button>
            <button onClick={() => setEditing(false)}
              className="px-3 py-1.5 bg-gray-100 text-gray-600 text-xs rounded-lg">キャンセル</button>
          </div>
        </div>
      ) : (
        <dl className="grid grid-cols-2 gap-x-6 gap-y-3 text-sm">
          <div><dt className="text-xs text-gray-400">郵便番号</dt><dd className="font-medium text-gray-800">{emp.zip_code || '—'}</dd></div>
          <div><dt className="text-xs text-gray-400">最寄り駅</dt><dd className="font-medium text-gray-800">{emp.nearest_station || '—'}</dd></div>
          <div className="col-span-2"><dt className="text-xs text-gray-400">住所</dt><dd className="font-medium text-gray-800">{emp.address || '—'}</dd></div>
        </dl>
      )}
    </section>
  )
}

// ===== 勤務先・通勤経路セクション =====
function WorkplaceSection({ emp, canEdit, onSaved }: { emp: Employee; canEdit: boolean; onSaved: () => void }) {
  const [editing, setEditing] = useState(false)
  const [form, setForm] = useState({
    workplace_name:    emp.workplace_name ?? '',
    workplace_address: emp.workplace_address ?? '',
    workplace_phone:   emp.workplace_phone ?? '',
    commute_route:     emp.commute_route ?? '',
  })
  const [saving, setSaving] = useState(false)

  const save = async () => {
    setSaving(true)
    try {
      await api.patch(`/api/v1/employees/${emp.id}/`, form)
      onSaved()
      setEditing(false)
    } finally { setSaving(false) }
  }

  return (
    <section>
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wide">勤務先・通勤経路</h3>
        {canEdit && !editing && (
          <button onClick={() => setEditing(true)} className="text-gray-300 hover:text-blue-500">
            <Pencil size={13} />
          </button>
        )}
      </div>
      {editing ? (
        <div className="space-y-2">
          <input value={form.workplace_name} onChange={(e) => setForm((f) => ({ ...f, workplace_name: e.target.value }))}
            placeholder="勤務先名" className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm" />
          <div className="grid grid-cols-2 gap-2">
            <input value={form.workplace_address} onChange={(e) => setForm((f) => ({ ...f, workplace_address: e.target.value }))}
              placeholder="勤務先住所" className="px-3 py-2 border border-gray-300 rounded-lg text-sm" />
            <input value={form.workplace_phone} onChange={(e) => setForm((f) => ({ ...f, workplace_phone: e.target.value }))}
              placeholder="勤務先電話番号" className="px-3 py-2 border border-gray-300 rounded-lg text-sm" />
          </div>
          <textarea value={form.commute_route} onChange={(e) => setForm((f) => ({ ...f, commute_route: e.target.value }))}
            placeholder="通勤経路（例: 自宅 → 渋谷駅（徒歩5分） → 東急東横線 → 横浜駅）" rows={3}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm resize-none" />
          <div className="flex gap-2">
            <button onClick={save} disabled={saving}
              className="px-3 py-1.5 bg-blue-600 text-white text-xs rounded-lg font-medium">
              {saving ? '保存中' : '保存'}
            </button>
            <button onClick={() => setEditing(false)}
              className="px-3 py-1.5 bg-gray-100 text-gray-600 text-xs rounded-lg">キャンセル</button>
          </div>
        </div>
      ) : (
        <dl className="grid grid-cols-2 gap-x-6 gap-y-3 text-sm">
          <div><dt className="text-xs text-gray-400">勤務先名</dt><dd className="font-medium text-gray-800">{emp.workplace_name || '—'}</dd></div>
          <div><dt className="text-xs text-gray-400">勤務先電話</dt><dd className="font-medium text-gray-800">{emp.workplace_phone || '—'}</dd></div>
          <div className="col-span-2"><dt className="text-xs text-gray-400">勤務先住所</dt><dd className="font-medium text-gray-800">{emp.workplace_address || '—'}</dd></div>
          <div className="col-span-2"><dt className="text-xs text-gray-400">通勤経路</dt><dd className="font-medium text-gray-800 whitespace-pre-wrap">{emp.commute_route || '—'}</dd></div>
        </dl>
      )}
    </section>
  )
}

// ===== 新規社員登録モーダル =====
function NewEmployeeModal({ onClose, onSaved }: { onClose: () => void; onSaved: () => void }) {
  const [form, setForm] = useState({
    email: '', employee_number: '',
    last_name: '', first_name: '',
    last_name_kana: '', first_name_kana: '',
    birth_date: '', gender: 'male',
    hire_date: new Date().toISOString().slice(0, 10),
    department: '', position: '',
    grade: 1, employment_type: 'full_time', roles: ['employee'] as string[],
  })
  const [saving, setSaving] = useState(false)
  const [result, setResult] = useState<{ email: string; temp_password: string } | null>(null)

  const set = (k: string, v: string | number) => setForm((f) => ({ ...f, [k]: v }))

  const save = async () => {
    setSaving(true)
    try {
      const res = await api.post('/api/v1/employees/', form)
      setResult(res.data)
    } catch (e: any) {
      const data = e.response?.data
      const msg = data?.error ?? Object.values(data ?? {}).flat().join('\n') ?? '登録に失敗しました'
      alert(msg)
    } finally {
      setSaving(false)
    }
  }

  if (result) {
    return (
      <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
        <div className="bg-white rounded-2xl shadow-xl w-full max-w-sm p-8 text-center">
          <div className="w-14 h-14 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <span className="text-2xl">✓</span>
          </div>
          <h2 className="font-bold text-gray-800 mb-1">社員登録完了</h2>
          <p className="text-sm text-gray-500 mb-4">以下の情報を本人に共有してください</p>
          <div className="bg-gray-50 rounded-lg p-4 text-left text-sm space-y-2 mb-6">
            <p><span className="text-gray-400">メール：</span>{result.email}</p>
            <p><span className="text-gray-400">仮パスワード：</span>
              <code className="font-mono bg-yellow-100 px-1 rounded">{result.temp_password}</code>
            </p>
          </div>
          <button onClick={onSaved}
            className="w-full py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium">
            閉じる
          </button>
        </div>
      </div>
    )
  }

  const Field = ({ label, children }: { label: string; children: React.ReactNode }) => (
    <div>
      <label className="text-xs font-medium text-gray-600 block mb-1">{label}</label>
      {children}
    </div>
  )

  const Input = ({ k, ...rest }: { k: string } & React.InputHTMLAttributes<HTMLInputElement>) => (
    <input
      {...rest}
      value={(form as any)[k]}
      onChange={(e) => set(k, e.target.value)}
      className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
    />
  )

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-2xl max-h-[90vh] flex flex-col">
        <div className="flex items-center justify-between p-6 border-b border-gray-100">
          <h2 className="font-bold text-gray-800">新規社員登録</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl">×</button>
        </div>

        <div className="overflow-y-auto p-6 space-y-4">
          {/* ログイン情報 */}
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">ログイン情報</p>
          <div className="grid gap-3">
            <Field label="メールアドレス *">
              <Input k="email" type="email" placeholder="example@company.com" />
            </Field>
            <Field label="ロール（複数選択可） *">
              <div className="grid grid-cols-3 gap-2">
                {ROLE_OPTIONS.map(opt => (
                  <label key={opt.value} className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={(form as any).roles.includes(opt.value)}
                      onChange={(e) => {
                        const roles = (form as any).roles as string[]
                        if (e.target.checked) {
                          set('roles', [...roles, opt.value])
                        } else {
                          if (roles.length > 1) {
                            set('roles', roles.filter(r => r !== opt.value))
                          }
                        }
                      }}
                      className="rounded"
                    />
                    <span className="text-sm">{opt.label}</span>
                  </label>
                ))}
              </div>
            </Field>
          </div>

          {/* 基本情報 */}
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide pt-2">基本情報</p>
          <div className="grid grid-cols-2 gap-3">
            <Field label="社員番号 *"><Input k="employee_number" placeholder="EMP002" /></Field>
            <Field label="雇用形態">
              <select value={form.employment_type} onChange={(e) => set('employment_type', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm">
                {Object.entries(EMPLOYMENT_LABEL).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
              </select>
            </Field>
            <Field label="姓 *"><Input k="last_name" placeholder="山田" /></Field>
            <Field label="名 *"><Input k="first_name" placeholder="太郎" /></Field>
            <Field label="姓（カナ）*"><Input k="last_name_kana" placeholder="ヤマダ" /></Field>
            <Field label="名（カナ）*"><Input k="first_name_kana" placeholder="タロウ" /></Field>
            <Field label="生年月日 *"><Input k="birth_date" type="date" /></Field>
            <Field label="性別">
              <select value={form.gender} onChange={(e) => set('gender', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm">
                {Object.entries(GENDER_LABEL).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
              </select>
            </Field>
          </div>

          {/* 所属情報 */}
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide pt-2">所属</p>
          <div className="grid grid-cols-2 gap-3">
            <Field label="部署 *"><Input k="department" placeholder="開発部" /></Field>
            <Field label="役職 *">
              <select value={form.position} onChange={(e) => set('position', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm">
                <option value="">選択してください</option>
                {POSITION_OPTIONS.map((p) => <option key={p} value={p}>{p}</option>)}
              </select>
            </Field>
            <Field label="等級">
              <input type="number" min={1} max={10} value={form.grade}
                onChange={(e) => set('grade', Number(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm" />
            </Field>
            <Field label="入社日 *"><Input k="hire_date" type="date" /></Field>
          </div>
        </div>

        <div className="flex gap-3 p-6 border-t border-gray-100">
          <button onClick={onClose}
            className="flex-1 py-2.5 border border-gray-300 rounded-lg text-sm text-gray-600 hover:bg-gray-50 font-medium">
            キャンセル
          </button>
          <button onClick={save} disabled={saving}
            className="flex-1 py-2.5 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white rounded-lg text-sm font-medium">
            {saving ? '登録中...' : '登録する'}
          </button>
        </div>
      </div>
    </div>
  )
}
