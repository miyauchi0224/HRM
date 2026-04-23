'use client'
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'
import { useAuthStore } from '@/lib/store'
import { CheckCircle2, Circle, ClipboardList, Plus } from 'lucide-react'

// ===== 型定義 =====
interface TaskItem {
  id: string
  task_title: string
  task_description: string
  task_category: string
  task_category_label: string
  due_days_from_hire: number
  is_completed: boolean
  completed_at: string | null
}

interface Assignment {
  id: string
  template: string
  template_name: string
  employee: string
  employee_name: string
  assigned_by_name: string | null
  assigned_at: string
  progress_percent: number
  task_items: TaskItem[]
}

interface Template {
  id: string
  name: string
  description: string
  is_active: boolean
  task_count: number
  tasks: TemplateTask[]
  created_at: string
}

interface TemplateTask {
  id: string
  title: string
  description: string
  category: string
  category_label: string
  due_days_from_hire: number
  order: number
}

interface Employee {
  id: string
  full_name: string
}

// カテゴリごとの色設定
const CATEGORY_COLOR: Record<string, { bg: string; text: string; border: string }> = {
  document: { bg: 'bg-blue-50',   text: 'text-blue-700',   border: 'border-blue-200' },
  it:       { bg: 'bg-purple-50', text: 'text-purple-700', border: 'border-purple-200' },
  training: { bg: 'bg-green-50',  text: 'text-green-700',  border: 'border-green-200' },
  facility: { bg: 'bg-orange-50', text: 'text-orange-700', border: 'border-orange-200' },
  other:    { bg: 'bg-gray-50',   text: 'text-gray-700',   border: 'border-gray-200' },
}

// ===== 進捗バーコンポーネント =====
function ProgressBar({ percent }: { percent: number }) {
  const color =
    percent === 100
      ? 'bg-green-500'
      : percent >= 50
      ? 'bg-blue-500'
      : 'bg-yellow-400'

  return (
    <div className="w-full bg-gray-200 rounded-full h-2">
      <div
        className={`${color} h-2 rounded-full transition-all duration-300`}
        style={{ width: `${percent}%` }}
      />
    </div>
  )
}

// ===== 一般社員向け: タスクカードグループ =====
function EmployeeView() {
  const qc = useQueryClient()

  const { data: assignments = [], isLoading } = useQuery<Assignment[]>({
    queryKey: ['onboarding-assignments'],
    queryFn: () =>
      api.get('/api/v1/onboarding/assignments/').then((r) => r.data.results ?? r.data),
  })

  const completeMut = useMutation({
    mutationFn: (id: string) =>
      api.patch(`/api/v1/onboarding/task-items/${id}/complete/`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['onboarding-assignments'] }),
  })

  const uncompleteMut = useMutation({
    mutationFn: (id: string) =>
      api.patch(`/api/v1/onboarding/task-items/${id}/uncomplete/`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['onboarding-assignments'] }),
  })

  const toggleTask = (item: TaskItem) => {
    if (item.is_completed) {
      uncompleteMut.mutate(item.id)
    } else {
      completeMut.mutate(item.id)
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-40 text-gray-400">
        読み込み中...
      </div>
    )
  }

  if (assignments.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-40 text-gray-400 gap-2">
        <ClipboardList size={40} className="opacity-40" />
        <p>割り当てられたオンボーディングはありません</p>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      {assignments.map((assignment) => {
        // カテゴリごとにタスクをグループ化
        const grouped = assignment.task_items.reduce<Record<string, TaskItem[]>>(
          (acc, item) => {
            const key = item.task_category || 'other'
            if (!acc[key]) acc[key] = []
            acc[key].push(item)
            return acc
          },
          {},
        )

        return (
          <div key={assignment.id} className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            {/* ヘッダー */}
            <div className="flex items-start justify-between mb-4">
              <div>
                <h2 className="text-lg font-bold text-gray-800">{assignment.template_name}</h2>
                {assignment.assigned_by_name && (
                  <p className="text-sm text-gray-500 mt-0.5">
                    担当: {assignment.assigned_by_name}
                  </p>
                )}
              </div>
              <div className="text-right">
                <span className="text-2xl font-bold text-blue-600">
                  {assignment.progress_percent}%
                </span>
                <p className="text-xs text-gray-400">完了</p>
              </div>
            </div>

            {/* 進捗バー */}
            <div className="mb-6">
              <ProgressBar percent={assignment.progress_percent} />
            </div>

            {/* カテゴリ別タスクカード */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {Object.entries(grouped).map(([category, items]) => {
                const colors = CATEGORY_COLOR[category] ?? CATEGORY_COLOR.other
                const categoryLabel = items[0]?.task_category_label ?? category

                return (
                  <div
                    key={category}
                    className={`${colors.bg} ${colors.border} border rounded-lg p-4`}
                  >
                    <h3 className={`text-sm font-semibold ${colors.text} mb-3`}>
                      {categoryLabel}
                    </h3>
                    <ul className="space-y-2">
                      {items.map((item) => (
                        <li key={item.id}>
                          <button
                            onClick={() => toggleTask(item)}
                            disabled={completeMut.isPending || uncompleteMut.isPending}
                            className="flex items-start gap-2 w-full text-left group"
                          >
                            {item.is_completed ? (
                              <CheckCircle2
                                size={18}
                                className="text-green-500 mt-0.5 flex-shrink-0"
                              />
                            ) : (
                              <Circle
                                size={18}
                                className="text-gray-400 mt-0.5 flex-shrink-0 group-hover:text-blue-400 transition-colors"
                              />
                            )}
                            <div>
                              <p
                                className={`text-sm font-medium ${
                                  item.is_completed
                                    ? 'line-through text-gray-400'
                                    : 'text-gray-700'
                                }`}
                              >
                                {item.task_title}
                              </p>
                              {item.task_description && (
                                <p className="text-xs text-gray-400 mt-0.5 line-clamp-2">
                                  {item.task_description}
                                </p>
                              )}
                              <p className="text-xs text-gray-400 mt-0.5">
                                入社後 {item.due_days_from_hire} 日以内
                              </p>
                            </div>
                          </button>
                        </li>
                      ))}
                    </ul>
                  </div>
                )
              })}
            </div>
          </div>
        )
      })}
    </div>
  )
}

// ===== HR/管理者向け: テンプレート一覧 + アサイン管理 =====
function HRView() {
  const qc = useQueryClient()
  const [showAssignModal, setShowAssignModal] = useState(false)
  const [selectedTemplateId, setSelectedTemplateId] = useState<string>('')
  const [selectedEmployeeId, setSelectedEmployeeId] = useState<string>('')

  const { data: templates = [], isLoading: loadingTemplates } = useQuery<Template[]>({
    queryKey: ['onboarding-templates'],
    queryFn: () =>
      api.get('/api/v1/onboarding/templates/').then((r) => r.data.results ?? r.data),
  })

  const { data: assignments = [], isLoading: loadingAssignments } = useQuery<Assignment[]>({
    queryKey: ['onboarding-assignments'],
    queryFn: () =>
      api.get('/api/v1/onboarding/assignments/').then((r) => r.data.results ?? r.data),
  })

  const { data: employees = [] } = useQuery<Employee[]>({
    queryKey: ['employees-simple'],
    queryFn: () =>
      api.get('/api/v1/employees/').then((r) => r.data.results ?? r.data),
  })

  const assignMut = useMutation({
    mutationFn: ({ template_id, employee_id }: { template_id: string; employee_id: string }) =>
      api.post('/api/v1/onboarding/assignments/assign/', {
        template_id,
        employee_id,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['onboarding-assignments'] })
      setShowAssignModal(false)
      setSelectedTemplateId('')
      setSelectedEmployeeId('')
    },
  })

  const handleAssign = () => {
    if (!selectedTemplateId || !selectedEmployeeId) return
    assignMut.mutate({
      template_id: selectedTemplateId,
      employee_id: selectedEmployeeId,
    })
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* 左カラム: テンプレート一覧 */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-base font-bold text-gray-700">テンプレート一覧</h2>
        </div>

        {loadingTemplates ? (
          <p className="text-sm text-gray-400">読み込み中...</p>
        ) : templates.length === 0 ? (
          <p className="text-sm text-gray-400">テンプレートがありません</p>
        ) : (
          <div className="space-y-3">
            {templates.map((t) => (
              <div
                key={t.id}
                className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm"
              >
                <div className="flex items-start justify-between">
                  <div>
                    <p className="font-semibold text-gray-800">{t.name}</p>
                    {t.description && (
                      <p className="text-xs text-gray-500 mt-0.5 line-clamp-2">
                        {t.description}
                      </p>
                    )}
                  </div>
                  <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full whitespace-nowrap ml-2">
                    {t.task_count} タスク
                  </span>
                </div>
                {t.tasks.length > 0 && (
                  <ul className="mt-3 space-y-1">
                    {t.tasks.slice(0, 4).map((task) => (
                      <li key={task.id} className="flex items-center gap-1.5 text-xs text-gray-500">
                        <span className="w-1.5 h-1.5 rounded-full bg-gray-300 flex-shrink-0" />
                        {task.title}
                        <span className="text-gray-400">({task.due_days_from_hire}日以内)</span>
                      </li>
                    ))}
                    {t.tasks.length > 4 && (
                      <li className="text-xs text-gray-400 pl-3">
                        他 {t.tasks.length - 4} 件...
                      </li>
                    )}
                  </ul>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 右カラム: アサイン一覧 + アサインボタン */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-base font-bold text-gray-700">アサイン一覧</h2>
          <button
            onClick={() => setShowAssignModal(true)}
            className="flex items-center gap-1.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium px-3 py-1.5 rounded-lg transition-colors"
          >
            <Plus size={15} />
            アサイン
          </button>
        </div>

        {loadingAssignments ? (
          <p className="text-sm text-gray-400">読み込み中...</p>
        ) : assignments.length === 0 ? (
          <p className="text-sm text-gray-400">アサインがありません</p>
        ) : (
          <div className="space-y-3">
            {assignments.map((a) => (
              <div
                key={a.id}
                className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm"
              >
                <div className="flex items-start justify-between mb-2">
                  <div>
                    <p className="font-semibold text-gray-800 text-sm">{a.employee_name}</p>
                    <p className="text-xs text-gray-500">{a.template_name}</p>
                  </div>
                  <span
                    className={`text-sm font-bold ${
                      a.progress_percent === 100 ? 'text-green-600' : 'text-blue-600'
                    }`}
                  >
                    {a.progress_percent}%
                  </span>
                </div>
                <ProgressBar percent={a.progress_percent} />
                <p className="text-xs text-gray-400 mt-2">
                  {a.task_items.filter((t) => t.is_completed).length} /{' '}
                  {a.task_items.length} タスク完了
                </p>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* アサインモーダル */}
      {showAssignModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-6">
            <h3 className="text-lg font-bold text-gray-800 mb-4">
              オンボーディングをアサイン
            </h3>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  テンプレート
                </label>
                <select
                  value={selectedTemplateId}
                  onChange={(e) => setSelectedTemplateId(e.target.value)}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">選択してください</option>
                  {templates
                    .filter((t) => t.is_active)
                    .map((t) => (
                      <option key={t.id} value={t.id}>
                        {t.name} ({t.task_count} タスク)
                      </option>
                    ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  対象社員
                </label>
                <select
                  value={selectedEmployeeId}
                  onChange={(e) => setSelectedEmployeeId(e.target.value)}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">選択してください</option>
                  {employees.map((emp) => (
                    <option key={emp.id} value={emp.id}>
                      {emp.full_name}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {assignMut.isError && (
              <p className="text-sm text-red-500 mt-3">
                アサインに失敗しました。既にアサイン済みの可能性があります。
              </p>
            )}

            <div className="flex justify-end gap-3 mt-6">
              <button
                onClick={() => {
                  setShowAssignModal(false)
                  setSelectedTemplateId('')
                  setSelectedEmployeeId('')
                }}
                className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800 transition-colors"
              >
                キャンセル
              </button>
              <button
                onClick={handleAssign}
                disabled={
                  !selectedTemplateId ||
                  !selectedEmployeeId ||
                  assignMut.isPending
                }
                className="px-4 py-2 text-sm bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white rounded-lg transition-colors"
              >
                {assignMut.isPending ? 'アサイン中...' : 'アサインする'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

// ===== メインページ =====
export default function OnboardingPage() {
  const user = useAuthStore((s) => s.user)
  const isHR = ['hr', 'admin'].includes(user?.role ?? '')

  return (
    <div>
      {/* ページヘッダー */}
      <div className="flex items-center gap-3 mb-6">
        <ClipboardList size={22} className="text-blue-600" />
        <div>
          <h1 className="text-2xl font-bold text-gray-800">オンボーディング管理</h1>
          <p className="text-sm text-gray-500 mt-0.5">
            {isHR
              ? 'テンプレートの管理とオンボーディングのアサインを行います'
              : '割り当てられたオンボーディングタスクを確認・完了マークできます'}
          </p>
        </div>
      </div>

      {/* ロール別ビュー切り替え */}
      {isHR ? <HRView /> : <EmployeeView />}
    </div>
  )
}
