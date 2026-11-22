'use client'
import { useState } from 'react'
import { KeyRound, Eye, EyeOff, AlertCircle } from 'lucide-react'
import api from '@/lib/api'
import { logout } from '@/lib/auth'
import { useAuthStore } from '@/lib/store'

/**
 * 初回ログイン時のパスワード変更（閉じられないモーダル）
 *
 * 初期パスワードは生年月日の 8 桁で推測されやすいため、
 * 変更が終わるまで他の画面を操作できないようにする。
 */
export default function InitialPasswordChangeModal() {
  const { user, setUser } = useAuthStore()
  const [form, setForm] = useState({ old_password: '', new_password: '', confirm: '' })
  const [show, setShow] = useState(false)
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    if (form.new_password !== form.confirm) { setError('新しいパスワードが一致しません'); return }
    if (form.new_password.length < 12) { setError('パスワードは12文字以上で入力してください'); return }
    setSaving(true)
    try {
      await api.post('/api/v1/auth/password/change/', {
        old_password: form.old_password,
        new_password: form.new_password,
      })
      if (user) setUser({ ...user, must_change_password: false })
    } catch (err: any) {
      const data = err.response?.data
      const msg = data?.old_password?.[0] ?? data?.new_password?.join?.('\n') ?? data?.new_password
        ?? data?.non_field_errors?.[0] ?? 'パスワードの変更に失敗しました'
      setError(String(msg))
    } finally {
      setSaving(false)
    }
  }

  const cls = 'w-full border border-gray-300 rounded-lg px-3 py-2 text-sm'

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-[100] p-4">
      <form onSubmit={submit} className="bg-white rounded-2xl shadow-xl w-full max-w-md p-6 space-y-4">
        <div className="flex items-start gap-3">
          <div className="w-10 h-10 shrink-0 rounded-full bg-amber-100 text-amber-600 flex items-center justify-center">
            <KeyRound size={20} />
          </div>
          <div>
            <h2 className="font-bold text-gray-800">パスワードを変更してください</h2>
            <p className="text-sm text-gray-500 mt-1">
              初回ログインのため、パスワードの変更が必要です。
              初期パスワードは生年月日（8桁・例: 19900401）です。
            </p>
          </div>
        </div>

        <div className="space-y-3">
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">現在のパスワード（生年月日 8桁）</label>
            <input type={show ? 'text' : 'password'} autoComplete="current-password" className={cls}
              value={form.old_password} onChange={(e) => setForm((f) => ({ ...f, old_password: e.target.value }))} />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">新しいパスワード</label>
            <input type={show ? 'text' : 'password'} autoComplete="new-password" className={cls}
              value={form.new_password} onChange={(e) => setForm((f) => ({ ...f, new_password: e.target.value }))} />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">新しいパスワード（確認）</label>
            <input type={show ? 'text' : 'password'} autoComplete="new-password" className={cls}
              value={form.confirm} onChange={(e) => setForm((f) => ({ ...f, confirm: e.target.value }))} />
          </div>
          <button type="button" onClick={() => setShow((s) => !s)}
            className="flex items-center gap-1 text-xs text-gray-500 hover:text-gray-700">
            {show ? <EyeOff size={13} /> : <Eye size={13} />} パスワードを{show ? '隠す' : '表示する'}
          </button>
          <p className="text-xs text-gray-400">
            12文字以上。数字だけ・よく使われるパスワード・現在と同じパスワードは使えません。
          </p>
        </div>

        {error && (
          <p className="text-sm text-red-600 flex items-start gap-1 whitespace-pre-line">
            <AlertCircle size={14} className="mt-0.5 shrink-0" /> {error}
          </p>
        )}

        <div className="flex items-center justify-between pt-2">
          <button type="button" onClick={logout} className="text-sm text-gray-500 hover:text-gray-700">
            ログアウト
          </button>
          <button type="submit"
            disabled={saving || !form.old_password || !form.new_password || !form.confirm}
            className="bg-blue-600 hover:bg-blue-700 disabled:opacity-40 text-white text-sm font-medium px-5 py-2 rounded-lg">
            {saving ? '変更中...' : 'パスワードを変更'}
          </button>
        </div>
      </form>
    </div>
  )
}
