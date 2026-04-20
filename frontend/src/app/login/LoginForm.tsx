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
            <div className="mb-4 max-h-64 overflow-y-auto text-xs text-gray-600 leading-relaxed bg-white rounded border border-gray-200 p-3 space-y-3">
              <p className="font-bold text-gray-800 text-sm">HRM システム 利用規約</p>
              <p className="text-gray-500">制定日：2025年4月1日　最終改定：2026年4月1日</p>

              <div>
                <p className="font-semibold text-gray-700 mb-1">第1条（目的・適用範囲）</p>
                <p>
                  本利用規約（以下「本規約」）は、<strong>{COMPANY_NAME}</strong>（以下「当社」）が提供する
                  人事管理システム「HRM」（以下「本システム」）の利用に際して、
                  すべての利用者が遵守すべき事項を定めるものです。
                  本システムへのログインをもって、本規約に同意したものとみなします。
                </p>
              </div>

              <div>
                <p className="font-semibold text-gray-700 mb-1">第2条（取り扱う情報）</p>
                <p>本システムは以下の情報を管理します。これらの情報は厳格に保護されます。</p>
                <ul className="list-disc list-inside pl-2 mt-1 space-y-0.5">
                  <li>社員の氏名・住所・連絡先等の個人識別情報</li>
                  <li>給与・賞与・控除に関する給与情報</li>
                  <li>勤怠・休暇・残業に関する勤務情報</li>
                  <li>目標管理（MBO）・評価に関する人事情報</li>
                  <li>経費・稟議・資産に関する業務情報</li>
                  <li>採用候補者に関する採用情報</li>
                </ul>
              </div>

              <div>
                <p className="font-semibold text-gray-700 mb-1">第3条（機密保持義務）</p>
                <ol className="list-decimal list-inside pl-2 space-y-1">
                  <li>本システムを通じて知り得た一切の情報は、業務遂行に必要な範囲に限り使用すること。</li>
                  <li>業務上知り得た情報を、当社の事前の書面による承諾なく、第三者に開示・提供・漏洩しないこと。</li>
                  <li>取得した情報の無断複製・スクリーンショット・外部送信を行わないこと。</li>
                  <li>退職・契約終了後も、在職中に知り得た情報の機密保持義務は継続するものとする。</li>
                </ol>
              </div>

              <div>
                <p className="font-semibold text-gray-700 mb-1">第4条（アカウント管理）</p>
                <ol className="list-decimal list-inside pl-2 space-y-1">
                  <li>ログイン情報（メールアドレス・パスワード）は自己の責任において厳重に管理すること。</li>
                  <li>アカウントの第三者への譲渡・貸与・共有を禁止する。</li>
                  <li>不正アクセスや情報漏洩の疑いが生じた場合は、直ちにシステム管理者へ報告すること。</li>
                  <li>退職・異動・役割変更の際は、速やかに管理者へアカウント処理を依頼すること。</li>
                </ol>
              </div>

              <div>
                <p className="font-semibold text-gray-700 mb-1">第5条（セキュリティ・禁止事項）</p>
                <ol className="list-decimal list-inside pl-2 space-y-1">
                  <li>当社の情報セキュリティポリシーおよび個人情報保護法・不正競争防止法等の関係法令を遵守すること。</li>
                  <li>本システムへの不正アクセス・改ざん・クラッキング行為を行わないこと。</li>
                  <li>マルウェア・ウイルス等の有害なプログラムを持ち込まないこと。</li>
                  <li>業務目的外での本システムの利用を行わないこと。</li>
                </ol>
              </div>

              <div>
                <p className="font-semibold text-gray-700 mb-1">第6条（AI機能の利用）</p>
                <p>
                  本システムはAI機能（文章生成・画像解析等）を提供する場合があります。
                  AI機能の利用にあたっては、社員個人情報・機密情報を外部AIサービスに送信しないよう
                  十分に注意し、当社のAI利用ガイドラインに従うこと。
                </p>
              </div>

              <div>
                <p className="font-semibold text-gray-700 mb-1">第7条（違反時の措置）</p>
                <p>
                  本規約に違反した場合、当社は就業規則・社内規程・関係法令に基づき、
                  アカウント停止・懲戒処分・損害賠償請求・刑事告訴等の措置を講じる場合があります。
                </p>
              </div>

              <p className="text-gray-400 text-xs pt-1 border-t">
                以上の内容を十分に理解の上、同意チェックボックスにチェックを入れてログインしてください。
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
              上記の利用規約を読み、{COMPANY_NAME} HRMシステムの利用規約・
              機密保持義務・個人情報の適切な取り扱いに<strong>同意します</strong>
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
