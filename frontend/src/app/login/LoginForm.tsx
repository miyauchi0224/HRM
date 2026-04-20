'use client'
import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { login } from '@/lib/auth'
import { useAuthStore } from '@/lib/store'
import { ChevronDown, ChevronUp } from 'lucide-react'

const schema = z.object({
  email:    z.string().email('有効なメールアドレスを入力してください'),
  password: z.string().min(1, 'パスワードを入力してください'),
})
type FormData = z.infer<typeof schema>

const COMPANY_NAME = '※※社'

export default function LoginForm() {
  const router  = useRouter()
  const setUser = useAuthStore((s) => s.setUser)

  const [error, setError]           = useState('')
  const [debugError, setDebugError] = useState('')
  const [agreed, setAgreed]         = useState(false)
  const [tosError, setTosError]     = useState(false)
  const [showTos, setShowTos]       = useState(false)

  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<FormData>({
    resolver: zodResolver(schema),
  })

  useEffect(() => {
    const dbg = localStorage.getItem('debug_last_error')
    if (dbg) {
      setDebugError(dbg)
      localStorage.removeItem('debug_last_error')
    }
    if (localStorage.getItem('access_token')) {
      router.replace('/')
    }
  }, [])

  const onSubmit = async (data: FormData) => {
    if (!agreed) {
      setTosError(true)
      return
    }
    setTosError(false)
    setError('')
    try {
      const res = await login(data.email, data.password)
      setUser(res.user)
      router.push('/')
    } catch {
      setError('メールアドレスまたはパスワードが正しくありません')
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 p-4">
      <div className="bg-white p-8 rounded-xl shadow-md w-full max-w-md">
        <h1 className="text-2xl font-bold text-center text-gray-800 mb-2">HRM</h1>
        <p className="text-center text-gray-500 mb-8 text-sm">人事管理システム</p>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-4 text-sm">
            {error}
          </div>
        )}
        {debugError && (
          <div className="bg-yellow-50 border border-yellow-300 text-yellow-800 px-4 py-3 rounded-lg mb-4 text-xs font-mono break-all">
            <p className="font-bold mb-1">デバッグ情報</p>
            {debugError}
          </div>
        )}

        {/* ===== ログインフォーム（submit ボタンのみ含む）===== */}
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
              メールアドレス
            </label>
            <input
              {...register('email')}
              id="email"
              type="email"
              autoComplete="email"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
              placeholder="example@company.com"
            />
            {errors.email && (
              <p className="text-red-500 text-xs mt-1">{errors.email.message}</p>
            )}
          </div>

          <div>
            <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
              パスワード
            </label>
            <input
              {...register('password')}
              id="password"
              type="password"
              autoComplete="current-password"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
              placeholder="••••••••••••"
            />
            {errors.password && (
              <p className="text-red-500 text-xs mt-1">{errors.password.message}</p>
            )}
          </div>

          {/* submit ボタンのみ form 内に置く */}
          {/* ボタンのクラスは固定（agreed による動的変更はハイドレーションエラーの原因）*/}
          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white font-medium py-2.5 rounded-lg transition-colors text-sm"
          >
            {isSubmitting ? 'ログイン中...' : 'ログイン'}
          </button>
        </form>

        {/* ===== 利用規約（form の外に配置してハイドレーションエラーを回避）===== */}
        <div className={`mt-4 rounded-lg border ${tosError ? 'border-red-400 bg-red-50' : 'border-gray-200 bg-gray-50'} p-4`}>
          {/* 折りたたみトグル */}
          <div
            role="button"
            tabIndex={0}
            onClick={() => setShowTos((v) => !v)}
            onKeyDown={(e) => e.key === 'Enter' && setShowTos((v) => !v)}
            className="flex items-center justify-between text-sm font-medium text-gray-700 mb-3 cursor-pointer select-none"
          >
            <span>利用規約</span>
            {showTos ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
          </div>

          {/* 規約本文（折りたたみ）*/}
          {showTos && (
            <div className="mb-4 max-h-48 overflow-y-auto text-xs text-gray-600 leading-relaxed bg-white rounded border border-gray-200 p-3 space-y-2">
              <p className="font-semibold text-gray-800">業務情報の機密保持に関する同意事項</p>
              <p>
                本人事管理システム（以下「本アプリ」）は、<strong>{COMPANY_NAME}</strong>（以下「当社」）の
                人事・給与・勤怠・その他業務に関わる情報（以下「業務情報」）を管理するシステムです。
              </p>
              <p>本アプリにログインすることで、利用者は以下の事項に同意したものとみなします。</p>
              <ol className="list-decimal list-inside space-y-1 pl-2">
                <li>
                  本アプリが当社の業務情報（社員個人情報・給与情報・勤怠情報等）を保有していることを理解し、
                  これらの情報が厳重に管理されていることを認識する。
                </li>
                <li>
                  本アプリを通じてアクセス・閲覧・取得した業務情報は、業務上の必要性がある場合に限り使用し、
                  第三者への漏洩・無断複製・目的外使用を一切行わない。
                </li>
                <li>
                  本アプリへのログイン情報（メールアドレス・パスワード）は自己の責任において厳重に管理し、
                  他者と共有しない。
                </li>
                <li>
                  本アプリの利用にあたっては、当社の情報セキュリティポリシーおよび
                  関係法令（個人情報保護法等）を遵守する。
                </li>
                <li>
                  上記に違反した場合、当社が定める就業規則・社内規程に基づく措置を受けることに同意する。
                </li>
              </ol>
              <p className="text-gray-500">
                ログインすることにより、上記の機密保持義務および適切な取り扱いに関する契約に同意したものとみなします。
              </p>
            </div>
          )}

          {/* 同意チェックボックス */}
          <label className="flex items-start gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={agreed}
              onChange={(e) => {
                setAgreed(e.target.checked)
                if (e.target.checked) setTosError(false)
              }}
              className="mt-0.5 w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500 cursor-pointer"
            />
            <span className="text-sm text-gray-700 leading-snug">
              利用規約を読み、{COMPANY_NAME}の業務情報の機密保持義務および
              適切な取り扱い契約に<strong>同意します</strong>
            </span>
          </label>

          {tosError && (
            <p className="mt-2 text-xs text-red-600 font-medium">
              ログインするには利用規約への同意が必要です
            </p>
          )}
        </div>
      </div>
    </div>
  )
}
