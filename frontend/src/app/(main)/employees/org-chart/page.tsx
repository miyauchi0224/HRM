'use client'
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import api from '@/lib/api'
import { Building2, X, Phone, AlertCircle, Mail, Calendar, Briefcase, User } from 'lucide-react'

interface OrgNode {
  id: string
  full_name: string
  department: string
  position: string
  manager_ids: string[]
}

interface EmployeeDetail {
  id: string
  full_name: string
  last_name_kana: string
  first_name_kana: string
  department: string
  position: string
  grade: number
  employment_type: string
  hire_date: string
  retire_date: string | null
  gender: string
  birth_date: string
  email: string
  phone: string
  personal_email: string
  role: string
  emergency_contacts: { id: string; name: string; relationship: string; phone: string }[]
}

const ROLE_LABEL: Record<string, string> = {
  employee: '社員', manager: '管理職', hr: '人事担当', admin: 'システム管理者',
}
const EMPLOYMENT_LABEL: Record<string, string> = {
  full_time: '正社員', part_time: 'パート', contract: '契約社員', dispatch: '派遣社員',
}

export default function OrgChartPage() {
  const [selectedId, setSelectedId] = useState<string | null>(null)

  const { data: nodes = [], isLoading } = useQuery<OrgNode[]>({
    queryKey: ['org-chart'],
    queryFn: () => api.get('/api/v1/employees/org-chart/').then((r) => r.data),
  })

  const { data: detail, isLoading: detailLoading } = useQuery<EmployeeDetail>({
    queryKey: ['employee', selectedId],
    queryFn: () => api.get(`/api/v1/employees/${selectedId}/`).then((r) => r.data),
    enabled: !!selectedId,
  })

  const byDept  = nodes.reduce<Record<string, OrgNode[]>>((acc, n) => {
    if (!acc[n.department]) acc[n.department] = []
    acc[n.department].push(n)
    return acc
  }, {})

  const roots = nodes.filter((n) => n.manager_ids.length === 0)

  const select = (id: string) => setSelectedId((prev) => (prev === id ? null : id))

  if (isLoading) return (
    <div>
      <h1 className="text-2xl font-bold text-gray-800 mb-6 flex items-center gap-2">
        <Building2 size={22} /> 組織図
      </h1>
      <p className="text-gray-400 text-sm">読み込み中...</p>
    </div>
  )

  return (
    <div className="flex gap-5 h-[calc(100vh-96px)]">
      {/* 左: 組織図本体 */}
      <div className={`flex-1 overflow-y-auto transition-all ${selectedId ? 'min-w-0' : ''}`}>
        <h1 className="text-2xl font-bold text-gray-800 mb-6 flex items-center gap-2">
          <Building2 size={22} /> 組織図
        </h1>

        {nodes.length === 0 ? (
          <div className="bg-white rounded-xl border border-dashed border-gray-300 p-12 text-center">
            <Building2 size={32} className="mx-auto text-gray-300 mb-3" />
            <p className="text-gray-400 text-sm">社員情報がありません</p>
          </div>
        ) : (
          <div className="space-y-6">
            {/* 部署ごとカード */}
            {Object.entries(byDept).map(([dept, members]) => (
              <div key={dept} className="bg-white rounded-xl border border-gray-200 overflow-hidden">
                <div className="px-5 py-3 bg-blue-600 text-white flex items-center justify-between">
                  <h2 className="font-semibold text-sm">{dept}</h2>
                  <p className="text-xs text-blue-200">{members.length} 名</p>
                </div>
                <div className="p-4 grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3">
                  {members.map((m) => {
                    const isManager  = nodes.some((n) => n.manager_ids.includes(m.id))
                    const isSelected = selectedId === m.id
                    return (
                      <button
                        key={m.id}
                        onClick={() => select(m.id)}
                        className={`rounded-lg border p-3 text-center transition-all hover:shadow-md cursor-pointer ${
                          isSelected
                            ? 'border-blue-500 bg-blue-50 shadow-md ring-2 ring-blue-300'
                            : isManager
                              ? 'border-blue-200 bg-blue-50 hover:border-blue-400'
                              : 'border-gray-200 hover:border-gray-400'
                        }`}
                      >
                        <div className={`w-10 h-10 rounded-full mx-auto mb-2 flex items-center justify-center text-base font-bold ${
                          isSelected ? 'bg-blue-500 text-white' : isManager ? 'bg-blue-200 text-blue-800' : 'bg-gray-100 text-gray-600'
                        }`}>
                          {m.full_name.slice(0, 1)}
                        </div>
                        <p className="text-xs font-medium text-gray-800">{m.full_name}</p>
                        <p className="text-xs text-gray-400 mt-0.5">{m.position}</p>
                        {isManager && (
                          <span className="mt-1 inline-block text-xs bg-blue-100 text-blue-700 px-1.5 py-0.5 rounded">
                            管理職
                          </span>
                        )}
                      </button>
                    )
                  })}
                </div>
              </div>
            ))}

            {/* レポートライン */}
            {roots.length > 0 && (
              <div className="bg-white rounded-xl border border-gray-200 p-5">
                <h2 className="font-semibold text-gray-700 mb-4 text-sm">レポートライン</h2>
                <div className="space-y-1">
                  {roots.map((root) => (
                    <TreeNode
                      key={root.id}
                      node={root}
                      all={nodes}
                      depth={0}
                      selectedId={selectedId}
                      onSelect={select}
                    />
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* 右: 社員情報パネル（スライドイン） */}
      <div className={`transition-all duration-300 overflow-hidden shrink-0 ${
        selectedId ? 'w-80' : 'w-0'
      }`}>
        {selectedId && (
          <div className="w-80 h-full overflow-y-auto">
            <div className="bg-white rounded-xl border border-gray-200 overflow-hidden h-full">
              {/* パネルヘッダー */}
              <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100 bg-gray-50">
                <p className="text-sm font-semibold text-gray-700">社員情報</p>
                <button
                  onClick={() => setSelectedId(null)}
                  className="text-gray-400 hover:text-gray-600 transition-colors"
                >
                  <X size={16} />
                </button>
              </div>

              {detailLoading ? (
                <div className="p-6 text-center text-gray-400 text-sm">読み込み中...</div>
              ) : detail ? (
                <EmployeePanel detail={detail} />
              ) : null}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

// ===== ツリーノード =====
function TreeNode({
  node, all, depth, selectedId, onSelect,
}: {
  node: OrgNode; all: OrgNode[]; depth: number
  selectedId: string | null; onSelect: (id: string) => void
}) {
  const subordinates = all.filter((n) => n.manager_ids.includes(node.id))
  const isSelected   = selectedId === node.id

  return (
    <div style={{ marginLeft: depth * 20 }}>
      <button
        onClick={() => onSelect(node.id)}
        className={`flex items-center gap-2 py-1.5 px-2 rounded-lg w-full text-left transition-colors ${
          isSelected ? 'bg-blue-50 text-blue-700' : 'hover:bg-gray-50'
        }`}
      >
        {depth > 0 && <span className="text-gray-300 text-sm shrink-0">└</span>}
        <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold shrink-0 ${
          isSelected ? 'bg-blue-500 text-white' : 'bg-blue-100 text-blue-700'
        }`}>
          {node.full_name.slice(0, 1)}
        </div>
        <div className="min-w-0">
          <span className="text-sm font-medium text-gray-800 block truncate">{node.full_name}</span>
          <span className="text-xs text-gray-400 truncate">{node.department} · {node.position}</span>
        </div>
      </button>
      {subordinates.map((sub) => (
        <TreeNode
          key={sub.id} node={sub} all={all} depth={depth + 1}
          selectedId={selectedId} onSelect={onSelect}
        />
      ))}
    </div>
  )
}

// ===== 社員情報パネル =====
function EmployeePanel({ detail }: { detail: EmployeeDetail }) {
  const isActive = !detail.retire_date

  return (
    <div className="p-5 space-y-5">
      {/* アバター・名前 */}
      <div className="text-center pb-4 border-b border-gray-100">
        <div className="w-16 h-16 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center text-2xl font-bold mx-auto mb-3">
          {detail.full_name.slice(0, 1)}
        </div>
        <p className="text-lg font-bold text-gray-800">{detail.full_name}</p>
        {detail.last_name_kana && (
          <p className="text-xs text-gray-400 mt-0.5">{detail.last_name_kana} {detail.first_name_kana}</p>
        )}
        <span className={`mt-2 inline-block text-xs px-2.5 py-0.5 rounded-full font-medium ${
          isActive ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'
        }`}>
          {isActive ? '在職中' : '退職済'}
        </span>
      </div>

      {/* 所属・役職 */}
      <section className="space-y-2">
        <Row icon={<Briefcase size={13} />} label="部署" value={detail.department} />
        <Row icon={<User size={13} />}      label="役職" value={detail.position} />
        <Row icon={<User size={13} />}      label="等級" value={`${detail.grade} 級`} />
        <Row icon={<User size={13} />}      label="ロール" value={ROLE_LABEL[detail.role] ?? detail.role} />
        <Row icon={<Briefcase size={13} />} label="雇用形態" value={EMPLOYMENT_LABEL[detail.employment_type] ?? '—'} />
      </section>

      {/* 入退社 */}
      <section className="space-y-2 pt-2 border-t border-gray-100">
        <Row icon={<Calendar size={13} />} label="入社日" value={detail.hire_date} />
        {detail.retire_date && (
          <Row icon={<Calendar size={13} />} label="退職日" value={detail.retire_date} />
        )}
      </section>

      {/* 連絡先 */}
      <section className="space-y-2 pt-2 border-t border-gray-100">
        <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide">連絡先</p>
        {detail.email && (
          <Row icon={<Mail size={13} />} label="メール" value={detail.email} />
        )}
        <Row
          icon={<Phone size={13} />}
          label="電話番号"
          value={detail.phone || '未登録'}
          muted={!detail.phone}
        />
      </section>

      {/* 緊急連絡先 */}
      <section className="pt-2 border-t border-gray-100">
        <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2 flex items-center gap-1">
          <AlertCircle size={11} /> 緊急連絡先
        </p>
        {!detail.emergency_contacts || detail.emergency_contacts.length === 0 ? (
          <p className="text-xs text-gray-400">登録なし</p>
        ) : (
          <div className="space-y-2">
            {detail.emergency_contacts.map((c) => (
              <div key={c.id} className="bg-gray-50 rounded-lg px-3 py-2.5 text-xs space-y-0.5">
                <div className="flex items-center justify-between">
                  <span className="font-medium text-gray-800">{c.name}</span>
                  {c.relationship && (
                    <span className="text-gray-400 bg-white border border-gray-200 rounded px-1.5 py-0.5">
                      {c.relationship}
                    </span>
                  )}
                </div>
                <p className="text-gray-600 font-mono">{c.phone}</p>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  )
}

// ===== 汎用行コンポーネント =====
function Row({
  icon, label, value, muted = false,
}: { icon: React.ReactNode; label: string; value: string; muted?: boolean }) {
  return (
    <div className="flex items-start gap-2 text-xs">
      <span className="text-gray-400 mt-0.5 shrink-0">{icon}</span>
      <span className="text-gray-400 shrink-0 w-16">{label}</span>
      <span className={`font-medium ${muted ? 'text-gray-400' : 'text-gray-700'}`}>{value}</span>
    </div>
  )
}
