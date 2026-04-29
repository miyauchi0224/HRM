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
  FolderOpen, ClipboardList, HeartPulse, GanttChartSquare, ShieldAlert,
} from 'lucide-react'
import { clsx } from 'clsx'

type NavItem = { href: string; label: string; icon: React.ElementType }

const ADMIN_URL = (process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000') + '/admin/'

// ロール判定
const SUPERVISOR_ROLES = ['supervisor', 'manager', 'hr', 'accounting', 'admin']
const ACCOUNTING_ROLES = ['accounting', 'hr', 'admin']
const HR_ROLES         = ['hr', 'admin']
const MANAGER_ROLES    = ['manager', 'hr', 'accounting', 'admin']

export default function Sidebar() {
  const pathname     = usePathname()
  const user         = useAuthStore((s) => s.user)
  const role         = user?.role ?? 'employee'
  const isCustomer   = role === 'customer'
  const isSupervisor = SUPERVISOR_ROLES.includes(role)
  const isManager    = MANAGER_ROLES.includes(role)
  const isAccounting = ACCOUNTING_ROLES.includes(role)
  const isHR         = HR_ROLES.includes(role)
  const isAdmin      = role === 'admin'

  const active = (href: string) =>
    href === '/' ? pathname === '/' : pathname.startsWith(href)

  if (isCustomer) {
    return (
      <aside className="w-60 bg-gray-900 text-white flex flex-col min-h-screen">
        <SidebarHeader user={user} role={role} />
        <nav className="flex-1 p-2 space-y-0.5 overflow-y-auto">
          <NavLink href="/"              label="ホーム"   icon={Home}      active={active('/')} />
          <NavLink href="/intra"         label="イントラ" icon={Newspaper} active={active('/intra')} />
          <NavLink href="/notifications" label="通知"     icon={Bell}      active={active('/notifications')} />
        </nav>
        <SidebarFooter pathname={pathname} />
      </aside>
    )
  }

  return (
    <aside className="w-60 bg-gray-900 text-white flex flex-col min-h-screen">
      <SidebarHeader user={user} role={role} />

      <nav className="flex-1 p-2 overflow-y-auto space-y-0.5">
        {/* ━━━ 社員の機能・基本機能 ━━━ */}
        <SectionLabel>社員の機能・基本機能</SectionLabel>
        <NavLink href="/"              label="ダッシュボード"    icon={Home}          active={active('/')} />
        <NavLink href="/attendance"    label="出退勤管理"        icon={Clock}         active={active('/attendance')} />
        <NavLink href="/leave"         label="有給・休暇"        icon={Calendar}      active={active('/leave')} />
        <NavLink href="/salary"        label="給与明細"          icon={DollarSign}    active={active('/salary')} />
        <NavLink href="/expense"       label="経費申請"          icon={Receipt}       active={active('/expense')} />
        <NavLink href="/approval"      label="電子稟議"          icon={FileText}      active={active('/approval')} />
        <NavLink href="/stress-check"  label="ストレスチェック"  icon={HeartPulse}    active={active('/stress-check')} />
        <NavLink href="/notifications" label="通知"              icon={Bell}          active={active('/notifications')} />
        <NavLink href="/chat"          label="チャット"          icon={MessageSquare} active={active('/chat')} />

        {/* ━━━ 業務・スキル ━━━ */}
        <SectionLabel>業務・スキル</SectionLabel>
        <NavLink href="/todo"       label="TODO／日報"        icon={CheckSquare} active={active('/todo')} />
        <NavLink href="/mbo"        label="目標管理/月報"     icon={Target}      active={active('/mbo')} />
        <NavLink href="/evaluation" label="360度評価"         icon={Star}        active={active('/evaluation')} />
        <NavLink href="/skills"     label="取得資格登録"      icon={Award}       active={active('/skills')} />
        <NavLink href="/learning"   label="研修・e-Learning"  icon={BookOpen}    active={active('/learning')} />
        <NavLink href="/intra"      label="イントラ"          icon={Newspaper}   active={active('/intra')} />

        {/* ━━━ プロジェクト・ドキュメント ━━━ */}
        <SectionLabel>プロジェクト・ドキュメント</SectionLabel>
        <NavLink href="/project"    label="プロジェクト管理"  icon={GanttChartSquare} active={active('/project')} />
        <NavLink href="/documents"  label="ドキュメント"      icon={FolderOpen}       active={active('/documents')} />
        <NavLink href="/onboarding" label="オンボーディング"  icon={ClipboardList}    active={active('/onboarding')} />
        <NavLink href="/ai"         label="AIアシスタント"    icon={Bot}              active={active('/ai')} />

        {/* ━━━ 上司の機能・承認機能 ━━━ */}
        {isSupervisor && (
          <>
            <SectionLabel>承認機能（上司）</SectionLabel>
            <NavLink href="/employees/org-chart" label="組織図"  icon={Building2}  active={active('/employees/org-chart')} />
          </>
        )}

        {/* ━━━ 労務部 ━━━ */}
        {isHR && (
          <>
            <SectionLabel>管理部門（労務部）</SectionLabel>
            <NavLink href="/attendance"   label="36協定状況"       icon={ShieldAlert}  active={active('/attendance')} />
            <NavLink href="/compliance"   label="コンプライアンス" icon={CheckSquare}  active={active('/compliance')} />
          </>
        )}

        {/* ━━━ 人事部 ━━━ */}
        {isHR && (
          <>
            <SectionLabel>管理部門（人事部）</SectionLabel>
            <NavLink href="/employees"    label="社員情報"          icon={Users}     active={active('/employees')} />
            <NavLink href="/recruitment"  label="採用管理"          icon={UserPlus}  active={active('/recruitment')} />
            <NavLink href="/analytics"    label="分析ダッシュボード" icon={BarChart2} active={active('/analytics')} />
          </>
        )}

        {/* ━━━ 管理職 ━━━ */}
        {isManager && !isHR && (
          <>
            <SectionLabel>管理部門（管理職）</SectionLabel>
            <NavLink href="/employees"           label="社員情報" icon={Users}     active={active('/employees')} />
            <NavLink href="/employees/org-chart" label="組織図"   icon={Building2} active={active('/employees/org-chart')} />
            <NavLink href="/assets"              label="資産管理" icon={Package}   active={active('/assets')} />
          </>
        )}
        {isHR && (
          <>
            <SectionLabel>管理部門（管理職）</SectionLabel>
            <NavLink href="/assets" label="資産管理" icon={Package} active={active('/assets')} />
          </>
        )}

        {/* ━━━ 経理部 ━━━ */}
        {isAccounting && (
          <>
            <SectionLabel>管理部門（経理職）</SectionLabel>
            <NavLink href="/salary/manage" label="給与計算" icon={Calculator} active={active('/salary/manage')} />
          </>
        )}

        {/* ━━━ システム管理 ━━━ */}
        {isAdmin && (
          <>
            <SectionLabel>システム管理機能</SectionLabel>
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

      <SidebarFooter pathname={pathname} />
    </aside>
  )
}

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <div className="pt-4 pb-1 px-2">
      <p className="text-xs font-semibold text-gray-500 tracking-wider uppercase">{children}</p>
    </div>
  )
}

function SidebarHeader({ user, role }: { user: any; role: string }) {
  return (
    <>
      <div className="p-4 border-b border-gray-700">
        <h1 className="text-lg font-bold">HRM</h1>
        <p className="text-xs text-gray-400 mt-0.5">人事管理システム</p>
      </div>
      <div className="p-4 border-b border-gray-700">
        <p className="text-sm font-medium truncate">{user?.full_name ?? user?.email}</p>
        <p className="text-xs text-gray-400 mt-0.5">{roleLabel(role)}</p>
      </div>
    </>
  )
}

function SidebarFooter({ pathname }: { pathname: string }) {
  return (
    <div className="p-2 border-t border-gray-700 space-y-0.5">
      <NavLink href="/settings" label="設定" icon={Settings} active={pathname === '/settings'} />
      <button
        onClick={logout}
        className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-gray-400 hover:text-white hover:bg-gray-700 transition-colors text-sm"
      >
        <LogOut size={16} />
        ログアウト
      </button>
    </div>
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
