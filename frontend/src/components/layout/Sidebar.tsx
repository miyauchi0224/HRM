'use client'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useAuthStore } from '@/lib/store'
import { logout } from '@/lib/auth'
import {
  Home, Clock, Calendar, Target, Users, DollarSign,
  Receipt, Award, Bell, Settings, LogOut, Building2
} from 'lucide-react'
import { clsx } from 'clsx'

const navItems = [
  { href: '/',             label: 'ダッシュボード',   icon: Home },
  { href: '/attendance',   label: '出退勤打刻',       icon: Clock },
  { href: '/leave',        label: '有給・休暇',       icon: Calendar },
  { href: '/mbo',          label: 'MBO目標管理',      icon: Target },
  { href: '/salary',       label: '給与明細',         icon: DollarSign },
  { href: '/expense',      label: '経費申請',         icon: Receipt },
  { href: '/skills',       label: 'スキル管理',       icon: Award },
  { href: '/notifications',label: '通知',             icon: Bell },
]

const managerItems = [
  { href: '/employees',    label: '社員情報',         icon: Users },
  { href: '/employees/org-chart', label: '組織図',   icon: Building2 },
]

export default function Sidebar() {
  const pathname = usePathname()
  const user     = useAuthStore((s) => s.user)
  const isManager = user?.role !== 'employee'

  return (
    <aside className="w-60 bg-gray-900 text-white flex flex-col min-h-screen">
      <div className="p-4 border-b border-gray-700">
        <h1 className="text-lg font-bold">HRM</h1>
        <p className="text-xs text-gray-400 mt-0.5">人事管理システム</p>
      </div>

      {/* ユーザー情報 */}
      <div className="p-4 border-b border-gray-700">
        <p className="text-sm font-medium">{user?.full_name ?? user?.email}</p>
        <p className="text-xs text-gray-400 mt-0.5">{roleLabel(user?.role)}</p>
      </div>

      {/* ナビゲーション */}
      <nav className="flex-1 p-2 space-y-0.5 overflow-y-auto">
        {navItems.map((item) => (
          <NavLink key={item.href} {...item} active={pathname === item.href} />
        ))}

        {isManager && (
          <>
            <div className="pt-3 pb-1 px-2">
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">管理者</p>
            </div>
            {managerItems.map((item) => (
              <NavLink key={item.href} {...item} active={pathname === item.href} />
            ))}
          </>
        )}
      </nav>

      {/* ログアウト */}
      <div className="p-2 border-t border-gray-700">
        <button
          onClick={logout}
          className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-gray-400 hover:text-white hover:bg-gray-700 transition-colors text-sm"
        >
          <LogOut size={16} />
          ログアウト
        </button>
      </div>
    </aside>
  )
}

function NavLink({ href, label, icon: Icon, active }: {
  href: string; label: string; icon: React.ElementType; active: boolean
}) {
  return (
    <Link
      href={href}
      className={clsx(
        'flex items-center gap-2 px-3 py-2 rounded-lg transition-colors text-sm',
        active
          ? 'bg-blue-600 text-white'
          : 'text-gray-400 hover:text-white hover:bg-gray-700'
      )}
    >
      <Icon size={16} />
      {label}
    </Link>
  )
}

function roleLabel(role?: string) {
  const map: Record<string, string> = {
    employee: '社員',
    manager:  '管理職',
    hr:       '人事担当',
    admin:    'システム管理者',
  }
  return map[role ?? ''] ?? ''
}
