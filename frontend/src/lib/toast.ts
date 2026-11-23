import { create } from 'zustand'

/**
 * 画面右下に出る通知（トースト）
 *
 *   import { toast } from '@/lib/toast'
 *   toast.success('保存しました')
 *   toast.error('保存に失敗しました')
 *
 * ブラウザ標準の alert() と違い、操作を止めずに数秒で自動的に消える。
 * エラーは読み終える前に消えないよう、成功より長く表示する。
 */
export type ToastType = 'success' | 'error' | 'info'

export interface ToastItem {
  id: number
  type: ToastType
  message: string
}

interface ToastStore {
  toasts: ToastItem[]
  push: (type: ToastType, message: string) => void
  dismiss: (id: number) => void
}

let nextId = 1

export const useToastStore = create<ToastStore>((set, get) => ({
  toasts: [],
  push: (type, message) => {
    const id = nextId++
    // 同じ内容が連続した場合は重ねない
    const rest = get().toasts.filter((t) => t.message !== message).slice(-3)
    set({ toasts: [...rest, { id, type, message }] })
    setTimeout(() => get().dismiss(id), type === 'error' ? 7000 : 3500)
  },
  dismiss: (id) => set({ toasts: get().toasts.filter((t) => t.id !== id) }),
}))

const show = (type: ToastType) => (message: unknown) =>
  useToastStore.getState().push(type, String(message ?? ''))

export const toast = {
  success: show('success'),
  error:   show('error'),
  info:    show('info'),
}
