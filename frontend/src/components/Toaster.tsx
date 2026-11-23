'use client'
import { CheckCircle2, AlertCircle, Info, X } from 'lucide-react'
import { useToastStore, type ToastType } from '@/lib/toast'

const STYLE: Record<ToastType, { icon: React.ElementType; cls: string; iconCls: string }> = {
  success: { icon: CheckCircle2, cls: 'border-green-200', iconCls: 'text-green-600' },
  error:   { icon: AlertCircle,  cls: 'border-red-200',   iconCls: 'text-red-600' },
  info:    { icon: Info,         cls: 'border-blue-200',  iconCls: 'text-blue-600' },
}

export default function Toaster() {
  const { toasts, dismiss } = useToastStore()
  if (toasts.length === 0) return null

  return (
    <div
      className="fixed z-[200] bottom-4 right-4 left-4 sm:left-auto sm:w-96 flex flex-col gap-2"
      aria-live="polite"
    >
      {toasts.map((t) => {
        const { icon: Icon, cls, iconCls } = STYLE[t.type]
        return (
          <div
            key={t.id}
            role={t.type === 'error' ? 'alert' : 'status'}
            className={`flex items-start gap-3 bg-white border ${cls} shadow-lg rounded-xl px-4 py-3 text-sm text-gray-800 animate-toast-in`}
          >
            <Icon size={18} className={`${iconCls} shrink-0 mt-0.5`} />
            <p className="flex-1 whitespace-pre-line break-words">{t.message}</p>
            <button
              onClick={() => dismiss(t.id)}
              aria-label="閉じる"
              className="text-gray-400 hover:text-gray-600 shrink-0"
            >
              <X size={16} />
            </button>
          </div>
        )
      })}
    </div>
  )
}
