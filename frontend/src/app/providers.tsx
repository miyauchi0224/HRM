'use client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useState } from 'react'

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(() => new QueryClient({
    defaultOptions: {
      queries: {
        // キャッシュが有効な時間：5分間はキャッシュをそのまま使う（再フェッチしない）
        // → ページ遷移時にローディング表示が出なくなる（即座に表示）
        staleTime: 5 * 60 * 1000,

        // キャッシュを保持する時間：10分間メモリに保持
        // → 10分以内なら戻ったページも即表示
        gcTime: 10 * 60 * 1000,

        retry: 1,

        // タブを切り替えたときに再フェッチしない
        // → 不要なAPI呼び出しを削減
        refetchOnWindowFocus: false,

        // マウント時に必ずフェッチしない（staleTimeが切れていない限り）
        refetchOnMount: true,
      },
    },
  }))
  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  )
}
