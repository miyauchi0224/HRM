'use client'
import { useEffect, useMemo, useRef, useState } from 'react'
import Link from 'next/link'
import { usePathname, useRouter, useSearchParams } from 'next/navigation'
import { useQuery } from '@tanstack/react-query'
import { useAuthStore } from '@/lib/store'
import { logout } from '@/lib/auth'
import api from '@/lib/api'
import {
  Home, Clock, Calendar, Target, Users, DollarSign,
  Receipt, Award, Bell, Settings, LogOut, Building2,
  CheckSquare, Newspaper, Calculator, FileText, MessageSquare,
  UserPlus, Package, BarChart2, Star, BookOpen, Bot,
  FolderOpen, ClipboardList, HeartPulse, GanttChartSquare, ShieldAlert,
  MessagesSquare, BarChartHorizontal, Stethoscope, UserCheck, CalendarCheck, Cog,
  ChevronDown, Search, X, ExternalLink,
} from 'lucide-react'
import { clsx } from 'clsx'

const ADMIN_URL = (process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000') + '/admin/'
const COLLAPSE_KEY = 'hrm.sidebar.collapsed'

// ロール判定
const SUPERVISOR_ROLES = ['supervisor', 'manager', 'hr', 'accounting', 'admin']
const ACCOUNTING_ROLES = ['accounting', 'hr', 'admin']
const HR_ROLES         = ['hr', 'admin']
const MANAGER_ROLES    = ['manager', 'hr', 'accounting', 'admin']
const LABOR_ROLES      = ['labor', 'hr', 'admin']

interface Perm {
  isSupervisor: boolean; isManager: boolean; isAccounting: boolean
  isHR: boolean; isLabor: boolean; isAdmin: boolean
}

type NavItem = {
  href: string
  label: string
  icon: React.ElementType
  /** メニュー検索で引っかけたい別名 */
  keywords?: string
  show?: (p: Perm) => boolean
  external?: boolean
}

type NavSection = { id: string; label: string; items: NavItem[] }

/**
 * メニュー構成：「やりたいこと」の単位でまとめる
 * （以前は「社員の機能・基本機能」に 12 項目が並んでいて目的の画面を探しにくかった）
 */
const SECTIONS: NavSection[] = [
  { id: 'home', label: '', items: [
    { href: '/',              label: 'ダッシュボード', icon: Home, keywords: 'ホーム トップ 打刻' },
    { href: '/notifications', label: '通知',           icon: Bell, keywords: 'お知らせ アラート' },
    { href: '/chat',          label: 'チャット',       icon: MessageSquare, keywords: 'メッセージ DM' },
  ]},
  { id: 'work', label: '勤怠・休暇', items: [
    { href: '/attendance', label: '出退勤管理', icon: Clock,    keywords: '打刻 勤怠 残業 作業表' },
    { href: '/leave',      label: '有給・休暇', icon: Calendar, keywords: '休み 休暇申請 代休' },
  ]},
  { id: 'request', label: '申請・承認', items: [
    { href: '/expense',             label: '経費申請',     icon: Receipt,   keywords: '交通費 立替 精算 領収書' },
    { href: '/approval',            label: '電子稟議',     icon: FileText,  keywords: '申請 承認 購買 出張' },
    { href: '/approval/delegation', label: '代理承認設定', icon: UserCheck, keywords: '代理 不在' },
    { href: '/salary',              label: '給与明細',     icon: DollarSign, keywords: '給料 明細 手取り' },
  ]},
  { id: 'daily', label: '日々の業務', items: [
    { href: '/todo',       label: 'TODO／日報',       icon: CheckSquare,      keywords: 'タスク やること 日報' },
    { href: '/project',    label: 'プロジェクト管理', icon: GanttChartSquare, keywords: 'ガント タスク' },
    { href: '/intra',      label: 'イントラ',         icon: Newspaper,        keywords: '社内報 記事 お知らせ' },
    { href: '/documents',  label: 'ドキュメント',     icon: FolderOpen,       keywords: '規程 契約書 ファイル' },
    { href: '/ai',         label: 'AIアシスタント',   icon: Bot,              keywords: 'AI 下書き' },
  ]},
  { id: 'growth', label: '目標・成長', items: [
    { href: '/mbo',        label: '目標管理／月報',   icon: Target,         keywords: 'MBO 目標 月報 評価' },
    { href: '/one-on-one', label: '1on1',             icon: MessagesSquare, keywords: '面談' },
    { href: '/evaluation', label: '360度評価',        icon: Star,           keywords: '評価' },
    { href: '/skills',     label: '取得資格',         icon: Award,          keywords: 'スキル 資格 認定' },
    { href: '/learning',   label: '研修・e-Learning', icon: BookOpen,       keywords: '研修 学習 テスト' },
    { href: '/onboarding', label: 'オンボーディング', icon: ClipboardList,  keywords: '入社 手続き' },
  ]},
  { id: 'health', label: '健康', items: [
    { href: '/stress-check',   label: 'ストレスチェック', icon: HeartPulse,         keywords: 'メンタル' },
    { href: '/health-checkup', label: '健康診断',         icon: Stethoscope,        keywords: '健診' },
    { href: '/pulse',          label: 'パルスサーベイ',   icon: BarChartHorizontal, keywords: 'アンケート サーベイ' },
  ]},
  { id: 'people', label: '社員・組織', items: [
    { href: '/employees',           label: '社員情報', icon: Users,     keywords: '社員一覧 名簿 CSV一括登録',
      show: (p) => p.isHR || p.isManager || p.isSupervisor },
    { href: '/employees/org-chart', label: '組織図',   icon: Building2, keywords: '部署',
      show: (p) => p.isHR || p.isManager || p.isSupervisor },
  ]},
  { id: 'admin', label: '管理部門', items: [
    { href: '/attendance?tab=overtime36', label: '36協定状況',        icon: ShieldAlert,   keywords: '残業 労務 36',
      show: (p) => p.isHR },
    { href: '/leave/obligation',          label: '有給 年5日取得状況', icon: CalendarCheck, keywords: '有給 義務 労務',
      show: (p) => p.isLabor || p.isSupervisor },
    { href: '/compliance',                label: 'コンプライアンス',   icon: ShieldAlert,   keywords: 'チェックリスト 労務',
      show: (p) => p.isHR },
    { href: '/recruitment',               label: '採用管理',           icon: UserPlus,      keywords: '求人 応募 面接',
      show: (p) => p.isHR },
    { href: '/analytics',                 label: '分析ダッシュボード', icon: BarChart2,     keywords: '分析 グラフ',
      show: (p) => p.isHR },
    { href: '/salary/manage',             label: '給与計算',           icon: Calculator,    keywords: '給与 経理',
      show: (p) => p.isAccounting },
    { href: '/assets',                    label: '資産管理',           icon: Package,       keywords: 'PC 備品 貸出',
      show: (p) => p.isManager },
  ]},
  { id: 'system', label: 'システム', items: [
    { href: '/system', label: '通知連携・定期ジョブ', icon: Cog,      keywords: 'Slack Teams Webhook ジョブ',
      show: (p) => p.isHR },
    { href: ADMIN_URL, label: '管理サイト',           icon: Settings, keywords: 'Django admin', external: true,
      show: (p) => p.isAdmin },
  ]},
]

const CUSTOMER_ITEMS: NavItem[] = [
  { href: '/',              label: 'ホーム',   icon: Home },
  { href: '/intra',         label: 'イントラ', icon: Newspaper },
  { href: '/notifications', label: '通知',     icon: Bell },
]

/** href が今の画面に当てはまる度合い（大きいほど具体的。0 は当てはまらない） */
function matchScore(href: string, pathname: string, search: string): number {
  const [path, query] = href.split('?')
  if (path === '/') return pathname === '/' ? 1 : 0
  if (pathname !== path && !pathname.startsWith(path + '/')) return 0
  if (query) return search.includes(query) ? path.length + 1000 : 0
  return path.length
}

export default function Sidebar() {
  const pathname     = usePathname()
  const searchParams = useSearchParams()
  const router       = useRouter()
  const user         = useAuthStore((s) => s.user)
  const role         = user?.role ?? 'employee'
  const isCustomer   = role === 'customer'

  const perm: Perm = {
    isSupervisor: SUPERVISOR_ROLES.includes(role),
    isManager:    MANAGER_ROLES.includes(role),
    isAccounting: ACCOUNTING_ROLES.includes(role),
    isHR:         HR_ROLES.includes(role),
    isLabor:      LABOR_ROLES.includes(role),
    isAdmin:      role === 'admin',
  }

  // 未読通知の件数（レイアウトで先読みしているキャッシュを使う）
  const { data: notifications } = useQuery<{ unread_count?: number }>({
    queryKey: ['notifications'],
    queryFn:  () => api.get('/api/v1/notifications/').then((r) => r.data),
    enabled:  !!user,
  })
  const unread = notifications?.unread_count ?? 0

  const sections = useMemo(() => {
    if (isCustomer) return [{ id: 'home', label: '', items: CUSTOMER_ITEMS }]
    return SECTIONS
      .map((s) => ({ ...s, items: s.items.filter((i) => !i.show || i.show(perm)) }))
      .filter((s) => s.items.length > 0)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [role, isCustomer])

  // いちばん具体的に当てはまる 1 項目だけを選択中にする（/salary と /salary/manage が両方光らないように）
  const search = searchParams?.toString() ?? ''
  const activeHref = useMemo(() => {
    let best = '', bestScore = 0
    for (const s of sections) for (const i of s.items) {
      if (i.external) continue
      const score = matchScore(i.href, pathname, search)
      if (score > bestScore) { best = i.href; bestScore = score }
    }
    return best
  }, [sections, pathname, search])

  // セクションの開閉（ブラウザに記憶。選択中の項目があるセクションは常に開く）
  const [collapsed, setCollapsed] = useState<string[]>([])
  useEffect(() => {
    try { setCollapsed(JSON.parse(localStorage.getItem(COLLAPSE_KEY) ?? '[]')) } catch { /* 記憶なし */ }
  }, [])
  const toggle = (id: string) => {
    setCollapsed((prev) => {
      const next = prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
      try { localStorage.setItem(COLLAPSE_KEY, JSON.stringify(next)) } catch { /* 保存できなくても動く */ }
      return next
    })
  }

  // メニュー検索（「/」キーで検索欄へ）
  const [query, setQuery] = useState('')
  const searchRef = useRef<HTMLInputElement>(null)
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const tag = (e.target as HTMLElement)?.tagName
      if (e.key === '/' && !['INPUT', 'TEXTAREA', 'SELECT'].includes(tag) && !(e.target as HTMLElement)?.isContentEditable) {
        e.preventDefault()
        searchRef.current?.focus()
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [])
  useEffect(() => { setQuery('') }, [pathname])

  const q = query.trim().toLowerCase()
  const results = q
    ? sections.flatMap((s) => s.items).filter((i) =>
        `${i.label} ${i.keywords ?? ''}`.toLowerCase().includes(q))
    : []

  const badgeFor = (href: string) => (href === '/notifications' ? unread : 0)

  return (
    <aside className="w-60 bg-gray-900 text-white flex flex-col h-screen sticky top-0">
      <SidebarHeader user={user} role={role} />

      {!isCustomer && (
        <div className="px-3 pt-3">
          <div className="relative">
            <Search size={14} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-gray-500" />
            <input
              ref={searchRef}
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && results[0]) {
                  if (results[0].external) window.open(results[0].href, '_blank')
                  else router.push(results[0].href)
                }
                if (e.key === 'Escape') { setQuery(''); searchRef.current?.blur() }
              }}
              placeholder="メニューを検索"
              aria-label="メニューを検索"
              className="w-full bg-gray-800 border border-gray-700 rounded-lg pl-8 pr-8 py-1.5 text-sm text-white placeholder-gray-500 focus:border-blue-500"
            />
            {query ? (
              <button onClick={() => setQuery('')} aria-label="検索をクリア"
                className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-500 hover:text-white">
                <X size={14} />
              </button>
            ) : (
              <kbd className="absolute right-2 top-1/2 -translate-y-1/2 text-[10px] text-gray-500 border border-gray-700 rounded px-1">/</kbd>
            )}
          </div>
        </div>
      )}

      <nav className="flex-1 p-2 overflow-y-auto" aria-label="メインメニュー">
        {q ? (
          results.length === 0 ? (
            <p className="text-xs text-gray-500 px-3 py-4">「{query}」に当てはまるメニューはありません</p>
          ) : (
            <div className="space-y-0.5">
              {results.map((i) => (
                <NavLink key={i.href} item={i} active={i.href === activeHref} badge={badgeFor(i.href)} />
              ))}
            </div>
          )
        ) : (
          sections.map((s) => {
            const hasActive = s.items.some((i) => i.href === activeHref)
            const open = !s.label || hasActive || !collapsed.includes(s.id)
            return (
              <div key={s.id} className={s.label ? 'mt-3' : ''}>
                {s.label && (
                  <button
                    onClick={() => toggle(s.id)}
                    aria-expanded={open}
                    disabled={hasActive}
                    className="w-full flex items-center justify-between px-3 py-1 text-xs font-semibold text-gray-500 hover:text-gray-300 disabled:hover:text-gray-500 disabled:cursor-default"
                  >
                    {s.label}
                    {!hasActive && (
                      <ChevronDown size={14} className={clsx('transition-transform', !open && '-rotate-90')} />
                    )}
                  </button>
                )}
                {open && (
                  <div className="space-y-0.5 mt-0.5">
                    {s.items.map((i) => (
                      <NavLink key={i.href} item={i} active={i.href === activeHref} badge={badgeFor(i.href)} />
                    ))}
                  </div>
                )}
              </div>
            )
          })
        )}
      </nav>

      <div className="p-2 border-t border-gray-700 space-y-0.5">
        <NavLink item={{ href: '/settings', label: '設定', icon: Settings }} active={pathname === '/settings'} />
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

function SidebarHeader({ user, role }: { user: any; role: string }) {
  const name = user?.full_name ?? user?.email ?? ''
  return (
    <div className="p-4 border-b border-gray-700">
      <Link href="/" className="block mb-3">
        <span className="text-lg font-bold">HRM</span>
        <span className="text-xs text-gray-400 ml-2">人事管理システム</span>
      </Link>
      <div className="flex items-center gap-2.5">
        <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-sm font-bold shrink-0">
          {name.slice(0, 1) || '?'}
        </div>
        <div className="min-w-0">
          <p className="text-sm font-medium truncate">{name}</p>
          <p className="text-xs text-gray-400">{roleLabel(role)}</p>
        </div>
      </div>
    </div>
  )
}

function NavLink({ item, active, badge = 0 }: { item: NavItem; active: boolean; badge?: number }) {
  const { href, label, icon: Icon, external } = item
  const cls = clsx(
    'flex items-center gap-2 px-3 py-2 rounded-lg transition-colors text-sm',
    active ? 'bg-blue-600 text-white' : 'text-gray-400 hover:text-white hover:bg-gray-700',
  )
  const body = (
    <>
      <Icon size={16} className="shrink-0" />
      <span className="flex-1 truncate">{label}</span>
      {badge > 0 && (
        <span className="min-w-[20px] h-5 px-1.5 rounded-full bg-red-500 text-white text-[11px] font-bold flex items-center justify-center"
          aria-label={`未読 ${badge} 件`}>
          {badge > 99 ? '99+' : badge}
        </span>
      )}
      {external && <ExternalLink size={12} className="shrink-0 opacity-60" />}
    </>
  )
  if (external) {
    return <a href={href} target="_blank" rel="noopener noreferrer" className={cls}>{body}</a>
  }
  return <Link href={href} className={cls} aria-current={active ? 'page' : undefined}>{body}</Link>
}

function roleLabel(role?: string) {
  const map: Record<string, string> = {
    employee:   '社員',
    supervisor: '上司',
    manager:    '管理職',
    hr:         '人事',
    labor:      '労務',
    accounting: '経理',
    admin:      'システム管理者',
    customer:   '顧客',
  }
  return map[role ?? ''] ?? ''
}
