'use client'
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'
import { ChevronDown, Check, AlertCircle } from 'lucide-react'

interface ChecklistItem {
  id: string
  title: string
  order: number
  is_critical: boolean
  is_completed?: boolean
  completed_at?: string | null
  notes?: string
}

interface ChecklistSection {
  id: string
  title: string
  order: number
  item_count: number
  completed_count: number
  progress_rate: number
  items?: ChecklistItem[]
}

interface SummaryData {
  overall_progress: number
  total_items: number
  completed_items: number
  sections: ChecklistSection[]
}

export default function ComplianceChecklist() {
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set())
  const [sectionDetails, setSectionDetails] = useState<Record<string, ChecklistSection>>({})
  const qc = useQueryClient()

  // 全体進捗サマリー取得
  const { data: summary } = useQuery<SummaryData>({
    queryKey: ['compliance-summary'],
    queryFn: () => api.get('/api/v1/compliance/checklists/summary/').then((r) => r.data),
  })

  // チェックリストセクション一覧取得
  const { data: sections = [] } = useQuery<ChecklistSection[]>({
    queryKey: ['compliance-checklists'],
    queryFn: () => api.get('/api/v1/compliance/checklists/').then((r) => r.data.results ?? r.data),
  })

  // 項目完了状況を更新
  const updateItemMutation = useMutation({
    mutationFn: (payload: { item_id: string; is_completed: boolean; notes?: string }) =>
      api.post('/api/v1/compliance/checklists/update_item_progress/', payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['compliance-summary'] })
      qc.invalidateQueries({ queryKey: ['compliance-checklists'] })
    },
  })

  const toggleSection = async (sectionId: string) => {
    const newExpanded = new Set(expandedSections)
    if (newExpanded.has(sectionId)) {
      newExpanded.delete(sectionId)
    } else {
      newExpanded.add(sectionId)
      // セクション詳細を取得（まだ取得していない場合）
      if (!sectionDetails[sectionId]) {
        try {
          const response = await api.get(`/api/v1/compliance/checklists/${sectionId}/`)
          setSectionDetails((prev) => ({
            ...prev,
            [sectionId]: response.data,
          }))
        } catch (error) {
          console.error('Failed to fetch section details:', error)
        }
      }
    }
    setExpandedSections(newExpanded)
  }

  const handleItemCheck = (itemId: string, isCompleted: boolean) => {
    updateItemMutation.mutate({
      item_id: itemId,
      is_completed: !isCompleted,
    })
  }

  if (!summary) {
    return <div className="text-center text-gray-400">読み込み中...</div>
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6 mb-8">
      {/* ヘッダー */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-lg font-bold text-gray-800">コンプライアンスチェックリスト</h2>
          <p className="text-sm text-gray-500 mt-1">労働管理・安全衛生チェック</p>
        </div>
      </div>

      {/* 全体進捗バー */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-gray-700">全体進捗</span>
          <span className="text-sm font-semibold text-gray-800">
            {summary.completed_items}/{summary.total_items}
          </span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
          <div
            className={`h-full transition-all ${
              summary.overall_progress >= 70
                ? 'bg-green-500'
                : summary.overall_progress >= 40
                ? 'bg-yellow-500'
                : 'bg-red-500'
            }`}
            style={{ width: `${summary.overall_progress}%` }}
          />
        </div>
        <p className="text-xs text-gray-500 mt-1">{summary.overall_progress}% 完了</p>
      </div>

      {/* セクション一覧 */}
      <div className="space-y-3">
        {sections.map((section) => (
          <div key={section.id} className="border border-gray-200 rounded-lg overflow-hidden">
            {/* セクションヘッダー */}
            <button
              onClick={() => toggleSection(section.id)}
              className="w-full px-4 py-3 flex items-center justify-between hover:bg-gray-50 transition-colors"
            >
              <div className="flex items-center gap-3 flex-1 text-left">
                <ChevronDown
                  size={18}
                  className={`text-gray-600 transition-transform ${
                    expandedSections.has(section.id) ? 'rotate-180' : ''
                  }`}
                />
                <div className="flex-1">
                  <p className="font-medium text-gray-800">{section.title}</p>
                  <p className="text-xs text-gray-500">
                    {section.completed_count}/{section.item_count}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <div className="w-16 h-2 bg-gray-200 rounded-full overflow-hidden">
                  <div
                    className={`h-full transition-all ${
                      section.progress_rate >= 70
                        ? 'bg-green-500'
                        : section.progress_rate >= 40
                        ? 'bg-yellow-500'
                        : 'bg-red-500'
                    }`}
                    style={{ width: `${section.progress_rate}%` }}
                  />
                </div>
                <span className="text-sm font-semibold text-gray-700 w-12 text-right">
                  {section.progress_rate}%
                </span>
              </div>
            </button>

            {/* セクション内容（展開時） */}
            {expandedSections.has(section.id) && (
              <div className="bg-gray-50 border-t border-gray-200 px-4 py-3 space-y-3">
                {(() => {
                  const details = sectionDetails[section.id]
                  const items = details?.items ?? []
                  return items.length > 0 ? (
                    items.map((item: ChecklistItem) => (
                      <label key={item.id} className="flex items-start gap-3 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={item.is_completed ?? false}
                          onChange={() => handleItemCheck(item.id, item.is_completed ?? false)}
                          disabled={updateItemMutation.isPending}
                          className="mt-1 w-4 h-4 rounded border-gray-300 cursor-pointer"
                        />
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <p
                              className={`text-sm ${
                                item.is_completed ? 'text-gray-500 line-through' : 'text-gray-800'
                              }`}
                            >
                              {item.title}
                            </p>
                            {item.is_critical && (
                              <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-red-100 text-red-700 text-xs rounded font-medium">
                                <AlertCircle size={12} /> 重要
                              </span>
                            )}
                          </div>
                          {item.is_completed && (
                            <p className="text-xs text-gray-400 mt-1">
                              完了: {item.completed_at ? new Date(item.completed_at).toLocaleDateString('ja-JP') : '—'}
                            </p>
                          )}
                        </div>
                        {item.is_completed && <Check size={16} className="text-green-500 shrink-0 mt-0.5" />}
                      </label>
                    ))
                  ) : (
                    <p className="text-sm text-gray-500 text-center py-4">項目が見つかりません</p>
                  )
                })()}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* リスク警告（80%未満） */}
      {summary.overall_progress < 80 && (
        <div className="mt-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg flex gap-3">
          <AlertCircle size={18} className="text-yellow-600 shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="text-sm font-medium text-yellow-800">
              コンプライアンス対応が未完了です
            </p>
            <p className="text-xs text-yellow-700 mt-1">
              {100 - summary.overall_progress}% の項目が未完了です。定期的に確認してください。
            </p>
          </div>
        </div>
      )}
    </div>
  )
}
