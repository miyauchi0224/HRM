'use client'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useAuthStore } from '@/lib/store'
import { logout } from '@/lib/auth'
import {
  Home, Clock, Calendar, Target, Users, DollarSign,
  Receipt, Award, Bell, Settings, LogOut, Building2,
  CheckSquare, Newspaper, Calculator, FileText, MessageSquare,
  UserPlus, Package, BarChart2, Star, BookOpen, Bot,
} from 'lucide-react'
import { clsx } from 'clsx'

type NavItem = { href: string; label: string; icon: React.ElementType }

// ===== 社員・上司・管理職 共通メニュー =====
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
  { href: '/approval',     label: '電子稟議',       icon: FileText },
  { href: '/chat',         label: 'チャット',       icon: MessageSquare },
  { href: '/evaluation',   label: '360度評価',      icon: Star },
  { href: '/learning',     label: '研修・e-Learning', icon: BookOpen },
]

// ===== 顧客専用メニュー（社内情報は閲覧不可）=====
const customerNavItems: NavItem[] = [
  { href: '/',              label: 'ホーム',   icon: Home },
  { href: '/intra',         label: 'イントラ', icon: Newspaper },
  { href: '/notifications', label: '通知',     icon: Bell },
]

// ===== 上司・管理職・人事・経理・管理者（is_supervisor）が見る管理メニュー =====
const supervisorItems: NavItem[] = [
  { href: '/employees',          label: '社員情報', icon: Users },
  { href: '/employees/org-chart',label: '組織図',   icon: Building2 },
  { href: '/assets',             label: '資産管理', icon: Package },
]

// ===== 経理・人事・管理者（is_accounting）が見る経理メニュー =====
const accountingItems: NavItem[] = [
  { href: '/salary/manage', label: '給与計算', icon: Calculator },
]

// ===== 人事・管理者が見る人事メニュー =====
const hrItems: NavItem[] = [
  { href: '/recruitment', label: '採用管理',        icon: UserPlus },
  { href: '/analytics',   label: '分析ダッシュボード', icon: BarChart2 },
]

// システム管理者のみ（Django 管理サイトへの外部リンク）
const ADMIN_URL = (process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000') + '/admin/'

// 上司以上のロール
const SUPERVISOR_ROLES = ['supervisor', 'manager', 'hr', 'accounting', 'admin']
// 経理以上のロール
const ACCOUNTING_ROLES = ['accounting', 'hr', 'admin']

export default function Sidebar() {
  const pathname    = usePathname()
  const user        = useAuthStore((s) => s.user)
  const role        = user?.role ?? 'employee'
  const isCustomer  = role === 'customer'
  const isSupervisor = SUPERVISOR_ROLES.includes(role)
  const isAccounting = ACCOUNTING_ROLES.includes(role)
  const isHR = ['hr', 'admin'].includes(role)
  const isAdmin     = role === 'admin'

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
        {/* 通常メニュー（顧客は専用メニュー）*/}
        {(isCustomer ? customerNavItems : navItems).map((item) => (
          <NavLink
            key={item.href}
            {...item}
            active={pathname.startsWith(item.href) && (item.href === '/' ? pathname === '/' : true)}
          />
        ))}

        {/* 上司セクション（上司・管理職・人事・経理・管理者）*/}
        {isSupervisor && !isCustomer && (
          <>
            <div className="pt-3 pb-1 px-2">
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">管理</p>
            </div>
            {supervisorItems.map((item) => (
              <NavLink key={item.href} {...item} active={pathname.startsWith(item.href)} />
            ))}
          </>
        )}

        {/* 経理セクション（経理・人事・管理者）*/}
        {isAccounting && !isCustomer && (
          <>
            <div className="pt-3 pb-1 px-2">
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">経理</p>
            </div>
            {accountingItems.map((item) => (
              <NavLink key={item.href} {...item} active={pathname.startsWith(item.href)} />
            ))}
          </>
        )}

        {/* 人事セクション（人事・管理者）*/}
        {isHR && !isCustomer && (
          <>
            <div className="pt-3 pb-1 px-2">
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">人事</p>
            </div>
            {hrItems.map((item) => (
              <NavLink key={item.href} {...item} active={pathname.startsWith(item.href)} />
            ))}
          </>
        )}

        {/* 管理サイト — システム管理者のみ */}
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
    employee:   '社員',
    supervisor: '上司',
    manager:    '管理職',
    hr:         '人事',
    accounting: '経理',
    admin:      'システム管理者',
    customer:   '顧客',
  }
  return map[role ?? ''] ?? ''
}
