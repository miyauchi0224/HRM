'use client'
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'
import { useAuthStore } from '@/lib/store'
import {
  Settings, Key, Eye, EyeOff, CheckCircle, AlertCircle,
  Bot, User, Mail, Shield, Lock, Phone, MapPin, Plus, Pencil, Trash2, X, Save,
} from 'lucide-react'

type AIProvider = 'anthropic' | 'openai'

// ===== 型定義 =====

interface AIKeyInfo {
  provider: AIProvider
  anthropic_has_key: boolean
  anthropic_masked: string
  openai_has_key: boolean
  openai_masked: string
}

interface EmergencyContact {
  id: string
  name: string
  relationship: string
  phone: string
  sort_order: number
}

interface MyProfile {
  id: string
  last_name: string
  first_name: string
  last_name_kana: string
  first_name_kana: string
  phone: string
  personal_email: string
  zip_code: string
  address: string
  nearest_station: string
  commute_route: string
  emergency_contacts: EmergencyContact[]
}

// ===== 定数 =====

const ROLE_LABEL: Record<string, string> = {
  employee:   '社員',
  supervisor: '上司',
  manager:    '管理職',
  hr:         '人事',
  accounting: '経理',
  customer:   '顧客',
  admin:      'システム管理者',
}

const PROVIDERS: { key: AIProvider; label: string; icon: string; placeholder: string }[] = [
  { key: 'anthropic', label: 'Anthropic (Claude)', icon: '🧠', placeholder: 'sk-ant-api03-...' },
  { key: 'openai',    label: 'OpenAI (ChatGPT)',   icon: '💬', placeholder: 'sk-proj-...'      },
]

// ===== メインページ =====

export default function SettingsPage() {
  const user = useAuthStore((s) => s.user)
  const qc   = useQueryClient()

  return (
    <div className="p-6 max-w-2xl mx-auto space-y-4">
      <div className="flex items-center gap-3 mb-6">
        <Settings className="text-indigo-600" size={28} />
        <div>
          <h1 className="text-2xl font-bold text-gray-800">設定</h1>
          <p className="text-sm text-gray-500">アカウント情報・プロフィール・AI機能の設定</p>
        </div>
      </div>

      {/* ── アカウント情報（読み取り専用） ── */}
      <div className="bg-white rounded-xl border shadow-sm p-5">
        <h2 className="font-semibold text-gray-700 mb-4 flex items-center gap-2">
          <User size={16} className="text-indigo-500" /> アカウント情報
        </h2>
        <div className="space-y-0">
          <InfoRow icon={<Mail size={14} />}   label="メールアドレス" value={user?.email ?? '—'} />
          <InfoRow icon={<User size={14} />}   label="氏名"           value={user?.full_name ?? '—'} />
          <InfoRow
            icon={<Shield size={14} />}
            label="ロール"
            value={
              <span className="bg-indigo-100 text-indigo-700 px-2.5 py-0.5 rounded-full text-xs font-medium">
                {ROLE_LABEL[user?.role ?? ''] ?? user?.role ?? '—'}
              </span>
            }
          />
        </div>
      </div>

      {/* ── プロフィール編集 ── */}
      <ProfileEditSection />

      {/* ── 緊急連絡先 ── */}
      <EmergencyContactsSection />

      {/* ── パスワード変更 ── */}
      <PasswordSection />

      {/* ── AI機能設定 ── */}
      <AIKeySection />
    </div>
  )
}

// ===== サブコンポーネント =====

/** アカウント情報の1行 */
function InfoRow({ icon, label, value }: { icon: React.ReactNode; label: string; value: React.ReactNode }) {
  return (
    <div className="flex items-center gap-3 py-2.5 border-b border-gray-100 last:border-0">
      <span className="text-gray-400 shrink-0">{icon}</span>
      <span className="text-sm text-gray-500 w-28 shrink-0">{label}</span>
      <span className="text-sm text-gray-800 font-medium">{value}</span>
    </div>
  )
}

// ── プロフィール編集セクション ──────────────────────────────

function ProfileEditSection() {
  const qc = useQueryClient()

  const { data: profile, isLoading } = useQuery<MyProfile>({
    queryKey: ['my-profile'],
    queryFn: () => api.get('/api/v1/employees/me/').then((r) => r.data),
  })

  const [form, setForm] = useState<Partial<MyProfile>>({})
  const [editing, setEditing] = useState(false)
  const [msg, setMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null)

  // 編集開始: フォームにプロフィールの現在値をセット
  const startEdit = () => {
    if (!profile) return
    setForm({
      last_name:       profile.last_name,
      first_name:      profile.first_name,
      last_name_kana:  profile.last_name_kana,
      first_name_kana: profile.first_name_kana,
      phone:           profile.phone,
      personal_email:  profile.personal_email,
      zip_code:        profile.zip_code,
      address:         profile.address,
      nearest_station: profile.nearest_station,
      commute_route:   profile.commute_route,
    })
    setEditing(true)
  }

  const mut = useMutation({
    mutationFn: (data: Partial<MyProfile>) => api.patch('/api/v1/employees/me/', data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['my-profile'] })
      setEditing(false)
      setMsg({ type: 'success', text: 'プロフィールを更新しました' })
      setTimeout(() => setMsg(null), 3000)
    },
    onError: (e: any) => {
      const detail = e.response?.data
      const text   = typeof detail === 'string' ? detail : JSON.stringify(detail)
      setMsg({ type: 'error', text: text ?? 'エラーが発生しました' })
    },
  })

  const f = (key: keyof MyProfile) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) =>
    setForm((prev) => ({ ...prev, [key]: e.target.value }))

  if (isLoading) {
    return (
      <div className="bg-white rounded-xl border shadow-sm p-5">
        <p className="text-sm text-gray-400">読み込み中...</p>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-xl border shadow-sm p-5">
      <div className="flex items-center justify-between mb-4">
        <h2 className="font-semibold text-gray-700 flex items-center gap-2">
          <User size={16} className="text-indigo-500" /> プロフィール編集
        </h2>
        {!editing && (
          <button
            onClick={startEdit}
            className="flex items-center gap-1.5 text-xs text-indigo-600 hover:text-indigo-800 border border-indigo-200 px-3 py-1.5 rounded-lg hover:bg-indigo-50 transition-colors"
          >
            <Pencil size={12} /> 編集
          </button>
        )}
      </div>

      {msg && (
        <p className={`text-sm flex items-center gap-1 mb-3 ${msg.type === 'success' ? 'text-green-600' : 'text-red-600'}`}>
          {msg.type === 'success' ? <CheckCircle size={13} /> : <AlertCircle size={13} />}
          {msg.text}
        </p>
      )}

      {editing ? (
        <div className="space-y-3">
          {/* 氏名 */}
          <div className="grid grid-cols-2 gap-3">
            <Field label="姓">
              <input className={inputCls} value={form.last_name ?? ''} onChange={f('last_name')} />
            </Field>
            <Field label="名">
              <input className={inputCls} value={form.first_name ?? ''} onChange={f('first_name')} />
            </Field>
            <Field label="姓（カナ）">
              <input className={inputCls} value={form.last_name_kana ?? ''} onChange={f('last_name_kana')} />
            </Field>
            <Field label="名（カナ）">
              <input className={inputCls} value={form.first_name_kana ?? ''} onChange={f('first_name_kana')} />
            </Field>
          </div>

          {/* 連絡先 */}
          <Field label="電話番号">
            <input className={inputCls} type="tel" value={form.phone ?? ''} onChange={f('phone')} placeholder="090-0000-0000" />
          </Field>
          <Field label="個人メール">
            <input className={inputCls} type="email" value={form.personal_email ?? ''} onChange={f('personal_email')} placeholder="example@gmail.com" />
          </Field>

          {/* 住所 */}
          <Field label="郵便番号">
            <input className={inputCls} value={form.zip_code ?? ''} onChange={f('zip_code')} placeholder="123-4567" />
          </Field>
          <Field label="住所">
            <input className={inputCls} value={form.address ?? ''} onChange={f('address')} placeholder="東京都〇〇区..." />
          </Field>
          <Field label="最寄り駅">
            <input className={inputCls} value={form.nearest_station ?? ''} onChange={f('nearest_station')} placeholder="〇〇駅" />
          </Field>
          <Field label="通勤経路">
            <textarea
              className={inputCls + ' resize-none'}
              rows={2}
              value={form.commute_route ?? ''}
              onChange={f('commute_route')}
              placeholder="〇〇線→〇〇駅乗換..."
            />
          </Field>

          {/* ボタン */}
          <div className="flex gap-2 pt-1">
            <button
              onClick={() => mut.mutate(form)}
              disabled={mut.isPending}
              className="flex items-center gap-1.5 bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-indigo-700 disabled:opacity-40"
            >
              <Save size={14} /> {mut.isPending ? '保存中...' : '保存'}
            </button>
            <button
              onClick={() => { setEditing(false); setMsg(null) }}
              className="flex items-center gap-1.5 border border-gray-300 text-gray-600 px-4 py-2 rounded-lg text-sm hover:bg-gray-50"
            >
              <X size={14} /> キャンセル
            </button>
          </div>
        </div>
      ) : (
        /* 表示モード */
        <div className="space-y-0">
          <InfoRow icon={<User size={14} />}   label="氏名"         value={`${profile?.last_name ?? ''} ${profile?.first_name ?? ''}`} />
          <InfoRow icon={<User size={14} />}   label="氏名（カナ）" value={`${profile?.last_name_kana ?? ''} ${profile?.first_name_kana ?? ''}`} />
          <InfoRow icon={<Phone size={14} />}  label="電話番号"     value={profile?.phone || '—'} />
          <InfoRow icon={<Mail size={14} />}   label="個人メール"   value={profile?.personal_email || '—'} />
          <InfoRow icon={<MapPin size={14} />} label="郵便番号"     value={profile?.zip_code || '—'} />
          <InfoRow icon={<MapPin size={14} />} label="住所"         value={profile?.address || '—'} />
          <InfoRow icon={<MapPin size={14} />} label="最寄り駅"     value={profile?.nearest_station || '—'} />
          <InfoRow icon={<MapPin size={14} />} label="通勤経路"     value={profile?.commute_route || '—'} />
        </div>
      )}
    </div>
  )
}

// ── 緊急連絡先セクション ────────────────────────────────────

function EmergencyContactsSection() {
  const qc = useQueryClient()

  const { data: profile } = useQuery<MyProfile>({
    queryKey: ['my-profile'],
    queryFn: () => api.get('/api/v1/employees/me/').then((r) => r.data),
  })

  const contacts = profile?.emergency_contacts ?? []
  const empId    = profile?.id

  // 新規追加フォームの表示状態
  const [addOpen, setAddOpen] = useState(false)
  const [addForm, setAddForm] = useState({ name: '', relationship: '', phone: '' })

  // 編集中の連絡先
  const [editId, setEditId]   = useState<string | null>(null)
  const [editForm, setEditForm] = useState({ name: '', relationship: '', phone: '' })

  const invalidate = () => qc.invalidateQueries({ queryKey: ['my-profile'] })

  // 追加ミューテーション
  const addMut = useMutation({
    mutationFn: (data: typeof addForm) =>
      api.post(`/api/v1/employees/${empId}/emergency-contacts/`, data),
    onSuccess: () => { invalidate(); setAddOpen(false); setAddForm({ name: '', relationship: '', phone: '' }) },
  })

  // 更新ミューテーション
  const updateMut = useMutation({
    mutationFn: ({ id, data }: { id: string; data: typeof editForm }) =>
      api.patch(`/api/v1/employees/${empId}/emergency-contacts/${id}/`, data),
    onSuccess: () => { invalidate(); setEditId(null) },
  })

  // 削除ミューテーション
  const deleteMut = useMutation({
    mutationFn: (id: string) =>
      api.delete(`/api/v1/employees/${empId}/emergency-contacts/${id}/`),
    onSuccess: () => invalidate(),
  })

  const startEdit = (c: EmergencyContact) => {
    setEditId(c.id)
    setEditForm({ name: c.name, relationship: c.relationship, phone: c.phone })
  }

  return (
    <div className="bg-white rounded-xl border shadow-sm p-5">
      <div className="flex items-center justify-between mb-4">
        <h2 className="font-semibold text-gray-700 flex items-center gap-2">
          <Phone size={16} className="text-indigo-500" /> 緊急連絡先
        </h2>
        {!addOpen && (
          <button
            onClick={() => setAddOpen(true)}
            className="flex items-center gap-1.5 text-xs text-indigo-600 hover:text-indigo-800 border border-indigo-200 px-3 py-1.5 rounded-lg hover:bg-indigo-50 transition-colors"
          >
            <Plus size={12} /> 追加
          </button>
        )}
      </div>

      {/* 既存の連絡先一覧 */}
      <div className="space-y-2 mb-3">
        {contacts.length === 0 && !addOpen && (
          <p className="text-sm text-gray-400">緊急連絡先が登録されていません</p>
        )}

        {contacts.map((c) => (
          <div key={c.id} className="border border-gray-100 rounded-lg p-3 bg-gray-50">
            {editId === c.id ? (
              /* 編集フォーム */
              <div className="space-y-2">
                <div className="grid grid-cols-2 gap-2">
                  <Field label="氏名">
                    <input className={inputCls} value={editForm.name} onChange={(e) => setEditForm((f) => ({ ...f, name: e.target.value }))} />
                  </Field>
                  <Field label="続柄">
                    <input className={inputCls} value={editForm.relationship} onChange={(e) => setEditForm((f) => ({ ...f, relationship: e.target.value }))} placeholder="配偶者・親など" />
                  </Field>
                </div>
                <Field label="電話番号">
                  <input className={inputCls} type="tel" value={editForm.phone} onChange={(e) => setEditForm((f) => ({ ...f, phone: e.target.value }))} />
                </Field>
                <div className="flex gap-2 pt-1">
                  <button
                    onClick={() => updateMut.mutate({ id: c.id, data: editForm })}
                    disabled={updateMut.isPending}
                    className="flex items-center gap-1 bg-indigo-600 text-white px-3 py-1.5 rounded text-xs hover:bg-indigo-700 disabled:opacity-40"
                  >
                    <Save size={12} /> 保存
                  </button>
                  <button
                    onClick={() => setEditId(null)}
                    className="flex items-center gap-1 border border-gray-300 text-gray-600 px-3 py-1.5 rounded text-xs hover:bg-gray-50"
                  >
                    <X size={12} /> キャンセル
                  </button>
                </div>
              </div>
            ) : (
              /* 表示モード */
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-800">{c.name}
                    <span className="ml-2 text-xs text-gray-400 font-normal">{c.relationship}</span>
                  </p>
                  <p className="text-xs text-gray-500 mt-0.5">{c.phone}</p>
                </div>
                <div className="flex gap-1">
                  <button
                    onClick={() => startEdit(c)}
                    className="p-1.5 text-gray-400 hover:text-indigo-500 hover:bg-indigo-50 rounded transition-colors"
                    title="編集"
                  >
                    <Pencil size={13} />
                  </button>
                  <button
                    onClick={() => { if (confirm(`${c.name} を削除しますか？`)) deleteMut.mutate(c.id) }}
                    className="p-1.5 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded transition-colors"
                    title="削除"
                  >
                    <Trash2 size={13} />
                  </button>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* 新規追加フォーム */}
      {addOpen && (
        <div className="border border-indigo-200 rounded-lg p-3 bg-indigo-50 space-y-2">
          <p className="text-xs font-medium text-indigo-700 mb-1">新しい緊急連絡先</p>
          <div className="grid grid-cols-2 gap-2">
            <Field label="氏名">
              <input className={inputCls} value={addForm.name} onChange={(e) => setAddForm((f) => ({ ...f, name: e.target.value }))} placeholder="山田 太郎" />
            </Field>
            <Field label="続柄">
              <input className={inputCls} value={addForm.relationship} onChange={(e) => setAddForm((f) => ({ ...f, relationship: e.target.value }))} placeholder="配偶者" />
            </Field>
          </div>
          <Field label="電話番号">
            <input className={inputCls} type="tel" value={addForm.phone} onChange={(e) => setAddForm((f) => ({ ...f, phone: e.target.value }))} placeholder="090-0000-0000" />
          </Field>
          <div className="flex gap-2 pt-1">
            <button
              onClick={() => addMut.mutate(addForm)}
              disabled={!addForm.name || !addForm.phone || addMut.isPending}
              className="flex items-center gap-1 bg-indigo-600 text-white px-3 py-1.5 rounded text-xs hover:bg-indigo-700 disabled:opacity-40"
            >
              <Plus size={12} /> 追加
            </button>
            <button
              onClick={() => { setAddOpen(false); setAddForm({ name: '', relationship: '', phone: '' }) }}
              className="flex items-center gap-1 border border-gray-300 text-gray-600 px-3 py-1.5 rounded text-xs hover:bg-gray-50"
            >
              <X size={12} /> キャンセル
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

// ── パスワード変更セクション ────────────────────────────────

function PasswordSection() {
  const [pwForm, setPwForm] = useState({ old_password: '', new_password: '', confirm: '' })
  const [showPw, setShowPw] = useState({ old: false, new: false, confirm: false })
  const [pwMsg,  setPwMsg]  = useState<{ type: 'success' | 'error'; text: string } | null>(null)

  const pwMut = useMutation({
    mutationFn: (data: { old_password: string; new_password: string }) =>
      api.post('/api/v1/auth/password/change/', data),
    onSuccess: () => {
      setPwForm({ old_password: '', new_password: '', confirm: '' })
      setPwMsg({ type: 'success', text: 'パスワードを変更しました' })
      setTimeout(() => setPwMsg(null), 4000)
    },
    onError: (e: any) => {
      const data = e.response?.data
      const msg  = data?.old_password?.[0] ?? data?.new_password?.[0] ?? data?.non_field_errors?.[0] ?? 'エラーが発生しました'
      setPwMsg({ type: 'error', text: msg })
    },
  })

  const submitPw = () => {
    if (pwForm.new_password !== pwForm.confirm) { setPwMsg({ type: 'error', text: '新しいパスワードが一致しません' }); return }
    if (pwForm.new_password.length < 12) { setPwMsg({ type: 'error', text: 'パスワードは12文字以上で入力してください' }); return }
    setPwMsg(null)
    pwMut.mutate({ old_password: pwForm.old_password, new_password: pwForm.new_password })
  }

  return (
    <div className="bg-white rounded-xl border shadow-sm p-5">
      <h2 className="font-semibold text-gray-700 mb-4 flex items-center gap-2">
        <Lock size={16} className="text-indigo-500" /> パスワード変更
      </h2>
      <div className="space-y-3">
        {([
          { key: 'old_password' as const, label: '現在のパスワード',        show: showPw.old,     toggle: () => setShowPw((s) => ({ ...s, old: !s.old })) },
          { key: 'new_password' as const, label: '新しいパスワード（12文字以上）', show: showPw.new,  toggle: () => setShowPw((s) => ({ ...s, new: !s.new })) },
          { key: 'confirm'      as const, label: '新しいパスワード（確認）', show: showPw.confirm, toggle: () => setShowPw((s) => ({ ...s, confirm: !s.confirm })) },
        ] as const).map(({ key, label, show, toggle }) => (
          <div key={key}>
            <label className="block text-xs font-medium text-gray-600 mb-1">{label}</label>
            <div className="relative">
              <input
                type={show ? 'text' : 'password'}
                value={pwForm[key]}
                onChange={(e) => setPwForm((f) => ({ ...f, [key]: e.target.value }))}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm pr-10"
              />
              <button type="button" onClick={toggle}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600">
                {show ? <EyeOff size={15} /> : <Eye size={15} />}
              </button>
            </div>
          </div>
        ))}

        {pwMsg && (
          <p className={`text-sm flex items-center gap-1 ${pwMsg.type === 'success' ? 'text-green-600' : 'text-red-600'}`}>
            {pwMsg.type === 'success' ? <CheckCircle size={13} /> : <AlertCircle size={13} />}
            {pwMsg.text}
          </p>
        )}
        <button
          onClick={submitPw}
          disabled={!pwForm.old_password || !pwForm.new_password || !pwForm.confirm || pwMut.isPending}
          className="bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-indigo-700 disabled:opacity-40"
        >
          {pwMut.isPending ? '変更中...' : 'パスワードを変更'}
        </button>
      </div>
    </div>
  )
}

// ── AI機能設定セクション ────────────────────────────────────

function AIKeySection() {
  const qc = useQueryClient()
  const [selectedProvider, setSelectedProvider] = useState<AIProvider>('anthropic')
  const [apiKey,  setApiKey]  = useState('')
  const [showKey, setShowKey] = useState(false)
  const [saved,   setSaved]   = useState(false)

  const { data: keyInfo, refetch } = useQuery<AIKeyInfo>({
    queryKey: ['my-api-key'],
    queryFn: () => api.get('/api/v1/auth/api-key/').then((r) => r.data),
  })

  const saveMut = useMutation({
    mutationFn: ({ provider, key }: { provider: AIProvider; key: string }) =>
      api.post('/api/v1/auth/api-key/', { provider, api_key: key }),
    onSuccess: () => {
      setSaved(true); setApiKey(''); setShowKey(false)
      refetch(); qc.invalidateQueries({ queryKey: ['my-api-key'] })
      setTimeout(() => setSaved(false), 3000)
    },
  })

  const currentConf = PROVIDERS.find((p) => p.key === selectedProvider)!
  const hasKey      = selectedProvider === 'anthropic' ? keyInfo?.anthropic_has_key : keyInfo?.openai_has_key
  const maskedKey   = selectedProvider === 'anthropic' ? keyInfo?.anthropic_masked  : keyInfo?.openai_masked

  return (
    <div className="bg-white rounded-xl border shadow-sm p-5">
      <div className="flex items-center gap-2 mb-1">
        <Bot className="text-indigo-600" size={18} />
        <h2 className="font-semibold text-gray-700">AI機能の設定</h2>
      </div>
      <p className="text-xs text-gray-500 mb-5">
        日報の自動下書き・MBO月報の文章生成などに使用するAPIキーを登録します。
      </p>

      {/* プロバイダー選択 */}
      <div className="grid grid-cols-2 gap-3 mb-5">
        {PROVIDERS.map((p) => {
          const pHasKey  = p.key === 'anthropic' ? keyInfo?.anthropic_has_key : keyInfo?.openai_has_key
          const selected = selectedProvider === p.key
          return (
            <button key={p.key} onClick={() => { setSelectedProvider(p.key); setApiKey(''); setShowKey(false) }}
              className={`flex flex-col items-start p-4 rounded-xl border-2 transition-all text-left ${selected ? 'border-indigo-500 bg-indigo-50' : 'border-gray-200 hover:border-gray-300 bg-white'}`}>
              <div className="flex items-center justify-between w-full mb-1">
                <span className="text-lg">{p.icon}</span>
                {selected && <span className="text-xs bg-indigo-500 text-white px-2 py-0.5 rounded-full">使用中</span>}
              </div>
              <p className="text-sm font-medium text-gray-800">{p.label}</p>
              {pHasKey
                ? <p className="text-xs text-green-600 mt-0.5 flex items-center gap-1"><CheckCircle size={10} /> キー登録済</p>
                : <p className="text-xs text-gray-400 mt-0.5">未登録</p>}
            </button>
          )
        })}
      </div>

      {/* キー入力 */}
      <div className="bg-gray-50 rounded-xl p-4">
        <p className="text-sm font-medium text-gray-700 mb-3">{currentConf.icon} {currentConf.label} のAPIキー</p>
        <div className={`flex items-center gap-2 text-sm px-3 py-2 rounded-lg mb-3 ${hasKey ? 'bg-green-50 text-green-700' : 'bg-amber-50 text-amber-700'}`}>
          {hasKey
            ? <><CheckCircle size={14} /><span>登録済: <code className="font-mono text-xs">{maskedKey}</code></span></>
            : <><AlertCircle size={14} /><span>未登録（AI機能は利用できません）</span></>}
        </div>
        <div className="space-y-3">
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">
              <Key size={12} className="inline mr-1" />
              新しいAPIキー {hasKey && <span className="text-gray-400 font-normal">（更新する場合のみ入力）</span>}
            </label>
            <div className="relative">
              <input
                type={showKey ? 'text' : 'password'}
                className="w-full border rounded-lg px-3 py-2 text-sm pr-10 font-mono bg-white"
                placeholder={currentConf.placeholder}
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
              />
              <button type="button" onClick={() => setShowKey(!showKey)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600">
                {showKey ? <EyeOff size={15} /> : <Eye size={15} />}
              </button>
            </div>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => saveMut.mutate({ provider: selectedProvider, key: apiKey })}
              disabled={!apiKey || saveMut.isPending}
              className="bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-indigo-700 disabled:opacity-40"
            >
              {saveMut.isPending ? '保存中...' : 'APIキーを保存'}
            </button>
            {hasKey && (
              <button
                onClick={() => saveMut.mutate({ provider: selectedProvider, key: '' })}
                disabled={saveMut.isPending}
                className="border border-red-300 text-red-600 px-4 py-2 rounded-lg text-sm hover:bg-red-50 disabled:opacity-40"
              >
                削除
              </button>
            )}
          </div>
          {saved && <p className="text-sm text-green-600 flex items-center gap-1"><CheckCircle size={13} /> 保存しました</p>}
          {saveMut.error && <p className="text-sm text-red-600">{(saveMut.error as any)?.response?.data?.error ?? 'エラーが発生しました'}</p>}
        </div>
      </div>

      <div className="mt-4 text-xs text-gray-400 bg-gray-50 rounded-lg p-3">
        <p className="font-medium text-gray-500 mb-1">セキュリティ</p>
        <ul className="space-y-0.5 list-disc list-inside">
          <li>APIキーはサーバー上に暗号化して保存されます</li>
          <li>本システムのAI機能のみに使用されます</li>
          <li>退職・異動の際はAPIキーを削除してください</li>
        </ul>
      </div>
    </div>
  )
}

// ===== ユーティリティ =====

/** フォームフィールドのラベル付きラッパー */
function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <label className="block text-xs font-medium text-gray-600 mb-1">{label}</label>
      {children}
    </div>
  )
}

/** 共通インプットのスタイル */
const inputCls = 'w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300 bg-white'
