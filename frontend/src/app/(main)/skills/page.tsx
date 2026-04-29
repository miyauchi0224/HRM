'use client'
import { useState, useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'
import { Award, Plus, AlertTriangle, Upload, Download, X, Image as ImageIcon } from 'lucide-react'

interface Skill {
  id: string
  skill_name: string
  category: string
  category_display: string
  level: string
  organizer: string
  certified_date: string | null
  expiry_date: string | null
  note: string
  certificate_file: string | null
  certificate_url: string | null
}

const CATEGORY_OPTIONS = [
  { value: 'language',    label: 'プログラミング言語' },
  { value: 'framework',   label: 'フレームワーク' },
  { value: 'infra',       label: 'インフラ' },
  { value: 'management',  label: 'マネジメント' },
  { value: 'lang_spoken', label: '語学' },
  { value: 'certificate', label: '資格' },
  { value: 'other',       label: 'その他' },
]

function daysUntil(dateStr: string | null): number | null {
  if (!dateStr) return null
  return Math.round((new Date(dateStr).getTime() - Date.now()) / 86400000)
}

export default function SkillsPage() {
  const [showNew, setShowNew] = useState(false)
  const [certUploading, setCertUploading] = useState<string | null>(null)
  const certRefs = useRef<Record<string, HTMLInputElement | null>>({})
  const qc = useQueryClient()

  const { data: skills = [], isLoading } = useQuery<Skill[]>({
    queryKey: ['skills'],
    queryFn: () => api.get('/api/v1/skills/').then((r) => r.data.results ?? r.data),
  })

  const deleteMut = useMutation({
    mutationFn: (id: string) => api.delete(`/api/v1/skills/${id}/`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['skills'] }),
  })

  const uploadCertificate = async (skillId: string, e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    setCertUploading(skillId)
    try {
      const form = new FormData()
      form.append('file', file)
      await api.post(`/api/v1/skills/${skillId}/upload-certificate/`, form)
      qc.invalidateQueries({ queryKey: ['skills'] })
    } catch {
      alert('認定証のアップロードに失敗しました')
    } finally {
      setCertUploading(null)
      const ref = certRefs.current[skillId]
      if (ref) ref.value = ''
    }
  }

  const downloadCertificate = async (skillId: string, skillName: string) => {
    const res = await api.get(`/api/v1/skills/${skillId}/download-certificate/`, { responseType: 'blob' })
    const a = document.createElement('a')
    a.href = window.URL.createObjectURL(new Blob([res.data]))
    a.download = `${skillName}_certificate`
    a.click()
  }

  const expiringSoon = skills.filter((s) => {
    const d = daysUntil(s.expiry_date)
    return d !== null && d <= 90 && d >= 0
  })

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
          <Award size={22} /> 取得資格登録
        </h1>
        <button onClick={() => setShowNew(true)}
          className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium px-4 py-2 rounded-lg">
          <Plus size={16} /> 追加
        </button>
      </div>

      {/* 期限アラート */}
      {expiringSoon.length > 0 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-4 mb-6">
          <p className="flex items-center gap-2 text-sm font-medium text-yellow-700 mb-2">
            <AlertTriangle size={16} /> 有効期限が近い資格
          </p>
          <ul className="space-y-1 text-xs text-yellow-700">
            {expiringSoon.map((s) => (
              <li key={s.id}>
                {s.skill_name}　あと {daysUntil(s.expiry_date)} 日（{s.expiry_date}）
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* スキル一覧 */}
      {isLoading ? (
        <p className="text-gray-400 text-sm">読み込み中...</p>
      ) : skills.length === 0 ? (
        <div className="bg-white rounded-xl border border-dashed border-gray-300 p-12 text-center">
          <Award size={32} className="mx-auto text-gray-300 mb-3" />
          <p className="text-gray-400 text-sm">スキル・資格が登録されていません</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {skills.map((s) => {
            const days = daysUntil(s.expiry_date)
            const expiring = days !== null && days <= 90 && days >= 0
            return (
              <div key={s.id}
                className={`bg-white rounded-xl border p-4 ${
                  days !== null && days < 0 ? 'border-red-300 bg-red-50'
                  : expiring ? 'border-yellow-300' : 'border-gray-200'
                }`}>
                <div className="flex items-start justify-between gap-2 mb-3">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <p className="font-medium text-gray-800 truncate">{s.skill_name}</p>
                      {days !== null && days < 0 && (
                        <span className="text-xs px-2 py-0.5 rounded-full font-bold bg-red-100 text-red-700 shrink-0">
                          失効
                        </span>
                      )}
                      {expiring && (
                        <span className="text-xs px-2 py-0.5 rounded-full font-medium bg-yellow-100 text-yellow-700 shrink-0">
                          まもなく期限切れ
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-gray-400 mt-0.5">{s.category_display || s.category || '—'}</p>
                  </div>
                  {s.level && (
                    <span className="text-xs px-2 py-0.5 rounded-full font-medium shrink-0 bg-blue-100 text-blue-700">
                      {s.level}
                    </span>
                  )}
                </div>
                <div className="text-xs text-gray-400 space-y-0.5">
                  {s.organizer && <p>主催者: {s.organizer}</p>}
                  {s.certified_date && <p>取得日: {s.certified_date}</p>}
                  {s.expiry_date && (
                    <p className={
                      days !== null && days < 0 ? 'text-red-600 font-semibold'
                      : expiring ? 'text-yellow-600 font-medium' : ''
                    }>
                      有効期限: {s.expiry_date}
                      {days !== null && days >= 0 && ` （あと${days}日）`}
                      {days !== null && days < 0 && ` （${Math.abs(days)}日前に失効）`}
                    </p>
                  )}
                  {s.note && <p className="truncate">備考: {s.note}</p>}
                </div>
                {/* 認定証ファイル */}
                <div className="mt-3 pt-3 border-t border-gray-100">
                  {s.certificate_url ? (
                    <div className="flex items-center gap-2">
                      {s.certificate_file && /\.(jpg|jpeg|png|gif|webp)$/i.test(s.certificate_file) ? (
                        <a href={s.certificate_url} target="_blank" rel="noopener noreferrer">
                          {/* eslint-disable-next-line @next/next/no-img-element */}
                          <img
                            src={s.certificate_url}
                            alt="認定証"
                            className="w-16 h-16 object-cover rounded border border-gray-200 cursor-pointer hover:opacity-80"
                          />
                        </a>
                      ) : (
                        <div className="flex items-center gap-1 text-xs text-gray-500">
                          <ImageIcon size={13} className="text-gray-400" />
                          <span>認定証あり</span>
                        </div>
                      )}
                      <button
                        onClick={() => downloadCertificate(s.id, s.skill_name)}
                        className="text-xs flex items-center gap-1 text-blue-500 hover:text-blue-700"
                      >
                        <Download size={12} /> DL
                      </button>
                      <label className={`text-xs flex items-center gap-1 cursor-pointer ${
                        certUploading === s.id ? 'text-gray-400 cursor-not-allowed' : 'text-gray-400 hover:text-blue-500'
                      }`} title="認定証を更新">
                        <Upload size={12} />
                        {certUploading === s.id ? '...' : '更新'}
                        <input
                          type="file"
                          className="hidden"
                          accept="image/*,.pdf"
                          disabled={certUploading === s.id}
                          ref={(el) => { certRefs.current[s.id] = el }}
                          onChange={(e) => uploadCertificate(s.id, e)}
                        />
                      </label>
                    </div>
                  ) : (
                    <label className={`flex items-center gap-1 text-xs cursor-pointer w-fit ${
                      certUploading === s.id
                        ? 'text-gray-400 cursor-not-allowed'
                        : 'text-blue-500 hover:text-blue-700'
                    }`}>
                      <Upload size={12} />
                      {certUploading === s.id ? 'アップロード中...' : '認定証を添付'}
                      <input
                        type="file"
                        className="hidden"
                        accept="image/*,.pdf"
                        disabled={certUploading === s.id}
                        ref={(el) => { certRefs.current[s.id] = el }}
                        onChange={(e) => uploadCertificate(s.id, e)}
                      />
                    </label>
                  )}
                </div>

                <button
                  onClick={() => confirm('削除しますか？') && deleteMut.mutate(s.id)}
                  className="mt-2 text-xs text-gray-300 hover:text-red-400 transition-colors"
                >
                  削除
                </button>
              </div>
            )
          })}
        </div>
      )}

      {showNew && (
        <NewSkillModal
          onClose={() => setShowNew(false)}
          onSaved={() => { setShowNew(false); qc.invalidateQueries({ queryKey: ['skills'] }) }}
        />
      )}
    </div>
  )
}

function NewSkillModal({ onClose, onSaved }: { onClose: () => void; onSaved: () => void }) {
  const [name, setName]           = useState('')
  const [category, setCategory]   = useState('certificate')
  const [level, setLevel]         = useState('')
  const [organizer, setOrganizer] = useState('')
  const [acquired, setAcquired]   = useState('')
  const [expiry, setExpiry]       = useState('')
  const [note, setNote]           = useState('')
  const [saving, setSaving]       = useState(false)

  const save = async () => {
    setSaving(true)
    try {
      await api.post('/api/v1/skills/', {
        skill_name: name,
        category,
        level,
        organizer,
        certified_date: acquired || null,
        expiry_date: expiry || null,
        note,
      })
      onSaved()
    } catch (e: any) {
      alert(e.response?.data?.skill_name?.[0] ?? '登録に失敗しました')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-md">
        <div className="flex items-center justify-between p-6 border-b border-gray-100">
          <h2 className="font-bold text-gray-800">スキル・資格を追加</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl">×</button>
        </div>
        <div className="p-6 space-y-4">
          <div>
            <label className="text-sm font-medium text-gray-700 block mb-1">
              スキル・資格名 <span className="text-red-500">*</span>
            </label>
            <input value={name} onChange={(e) => setName(e.target.value)}
              placeholder="例: AWS Solutions Architect"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm" />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-sm font-medium text-gray-700 block mb-1">カテゴリ</label>
              <select value={category} onChange={(e) => setCategory(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm">
                {CATEGORY_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-700 block mb-1">レベル</label>
              <input value={level} onChange={(e) => setLevel(e.target.value)}
                placeholder="例: 上級、合格、3級"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm" />
            </div>
          </div>
          <div>
            <label className="text-sm font-medium text-gray-700 block mb-1">主催者・発行機関</label>
            <input value={organizer} onChange={(e) => setOrganizer(e.target.value)}
              placeholder="例: IPA、AWS、TOEIC"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm" />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-sm font-medium text-gray-700 block mb-1">取得日</label>
              <input type="date" value={acquired} onChange={(e) => setAcquired(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm" />
            </div>
            <div>
              <label className="text-sm font-medium text-gray-700 block mb-1">有効期限</label>
              <input type="date" value={expiry} onChange={(e) => setExpiry(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm" />
            </div>
          </div>
          <div>
            <label className="text-sm font-medium text-gray-700 block mb-1">備考</label>
            <input value={note} onChange={(e) => setNote(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm" placeholder="任意" />
          </div>
        </div>
        <div className="flex gap-3 px-6 pb-6">
          <button onClick={onClose}
            className="flex-1 py-2.5 border border-gray-300 rounded-lg text-sm text-gray-600 hover:bg-gray-50 font-medium">
            キャンセル
          </button>
          <button onClick={save} disabled={!name.trim() || saving}
            className="flex-1 py-2.5 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white rounded-lg text-sm font-medium">
            {saving ? '登録中...' : '登録'}
          </button>
        </div>
      </div>
    </div>
  )
}
