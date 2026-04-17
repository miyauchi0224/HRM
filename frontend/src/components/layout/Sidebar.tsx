'use client'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useAuthStore } from '@/lib/store'
import { logout } from '@/lib/auth'
import {
  Home, Clock, Calendar, Target, Users, DollarSign,
  Receipt, Award, Bell, Settings, LogOut, Building2, CheckSquare, Newspaper
} from 'lucide-react'
import { clsx } from 'clsx'

// roles が未指定 → 全員に表示
// roles に配列指定 → その役割のユーザーにのみ表示
type NavItem = { href: string; label: string; icon: React.ElementType; roles?: string[] }

// 社員・管理職共通メニュー
const navItems: NavItem[] = [
  { href: '/',              label: 'ダッシュボード', icon: Home },
  { href: '/attendance',    label: '出退勤管理',     icon: Clock },
  { href: '/leave',         label: '有給・休暇',     icon: Calendar },
  { href: '/todo',          label: 'TODO／日報',     icon: CheckSquare },
  { href: '/intra',         label: 'イントラ',       icon: Newspaper },
  { href: '/mbo',           label: '目標管理/月報',  icon: Target },
  { href: '/salary',        label: '給与明細',       icon: DollarSign },
  { href: '/expense',       label: '経費申請',       icon: Receipt },
  { href: '/skills',        label: '取得資格登録',   icon: Award },
  { href: '/notifications', label: '通知',           icon: Bell },
]

// 顧客専用メニュー（社内情報は閲覧不可）
const customerNavItems: NavItem[] = [
  { href: '/',              label: 'ホーム',   icon: Home },
  { href: '/intra',         label: 'イントラ', icon: Newspaper },
  { href: '/notifications', label: '通知',     icon: Bell },
]

// 管理職（manager・hr・admin）のみ
const managerItems: NavItem[] = [
  { href: '/employees',          label: '社員情報', icon: Users },
  { href: '/employees/org-chart',label: '組織図',   icon: Building2 },
]

// システム管理者のみ（Django 管理サイトへの外部リンク）
const ADMIN_URL = (process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000') + '/admin/'

const MANAGER_ROLES = ['manager', 'hr', 'admin']

export default function Sidebar() {
  const pathname  = usePathname()
  const user      = useAuthStore((s) => s.user)
  const role       = user?.role ?? 'employee'
  const isManager  = MANAGER_ROLES.includes(role)
  const isAdmin    = role === 'admin'
  const isCustomer = role === 'customer'

  return (
    <aside className="w-60 bg-gray-900 text-white flex flex-col min-h-screen">
      <div className="p-4 border-b border-gray-700">
        <h1 className="text-lg font-bold">HRM</h1>
        <p className="text-xs text-gray-400 mt-0.5">人事管理システム</p>
      </div>

      {/* ユーザー情報 */}
      <div className="p-4 border-b border-gray-700">
        <p className="text-sm font-medium">{user?.full_name ?? user?.email}</p>
        <p className="text-xs text-gray-400 mt-0.5">{roleLabel(role)}</p>
      </div>

      {/* ナビゲーション */}
      <nav className="flex-1 p-2 space-y-0.5 overflow-y-auto">
        {(isCustomer ? customerNavItems : navItems).map((item) => (
          <NavLink key={item.href} {...item} active={pathname.startsWith(item.href) && (item.href === '/' ? pathname === '/' : true)} />
        ))}

        {/* 管理職セクション — 管理職以上かつ顧客でない場合のみ表示 */}
        {isManager && !isCustomer && (
          <>
            <div className="pt-3 pb-1 px-2">
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">管理者</p>
            </div>
            {managerItems.map((item) => (
              <NavLink key={item.href} {...item} active={pathname.startsWith(item.href)} />
            ))}
          </>
        )}

        {/* 管理サイト — システム管理者のみ（Djangoバックエンドへの外部リンク）*/}
        {isAdmin && (
          <>
            <div className="pt-3 pb-1 px-2">
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">システム</p>
            </div>
            <a
              href={ADMIN_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 px-3 py-2 rounded-lg transition-colors text-sm text-gray-400 hover:text-white hover:bg-gray-700"
            >
              <Settings size={16} />
              管理サイト
            </a>
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
    customer: '顧客',
  }
  return map[role ?? ''] ?? ''
}
