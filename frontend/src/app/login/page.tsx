/**
 * ログインページ
 * LoginForm はクライアント専用状態（agreed, showTos など）を持つため
 * SSR を無効化して hydration エラーを防ぐ。
 */
import dynamic from 'next/dynamic'

const LoginForm = dynamic(() => import('./LoginForm'), {
  ssr: true,
  loading: () => (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="bg-white p-8 rounded-xl shadow-md w-full max-w-md">
        <div className="h-8 bg-gray-100 rounded animate-pulse mb-4" />
        <div className="h-4 bg-gray-100 rounded animate-pulse mb-8 w-1/2 mx-auto" />
        <div className="space-y-4">
          <div className="h-10 bg-gray-100 rounded animate-pulse" />
          <div className="h-10 bg-gray-100 rounded animate-pulse" />
          <div className="h-10 bg-gray-100 rounded animate-pulse" />
        </div>
      </div>
    </div>
  ),
})

export default function LoginPage() {
  return <LoginForm />
}
