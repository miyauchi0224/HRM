'use client'
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'
import { useAuthStore } from '@/lib/store'
import { BookOpen, Plus, Play, CheckCircle, Clock } from 'lucide-react'

interface LearningCourse {
  id: string; title: string; description: string; course_type: string
  duration_minutes: number; is_required: boolean; status: string
  enrollment_count: number
  my_enrollment: {
    id: string; status: string; progress_pct: number; completed_at: string | null
  } | null
}

const COURSE_TYPE: Record<string, { label: string; color: string }> = {
  elearning: { label: 'eラーニング', color: 'bg-blue-100 text-blue-700' },
  classroom: { label: '集合研修', color: 'bg-green-100 text-green-700' },
  ojt: { label: 'OJT', color: 'bg-orange-100 text-orange-700' },
  external: { label: '外部研修', color: 'bg-purple-100 text-purple-700' },
}

export default function LearningPage() {
  const user = useAuthStore((s) => s.user)
  const qc = useQueryClient()
  const isHR = ['hr', 'admin'].includes(user?.role ?? '')
  const [showNew, setShowNew] = useState(false)
  const [form, setForm] = useState({
    title: '', description: '', course_type: 'elearning',
    duration_minutes: '', is_required: false
  })
  const [filterStatus, setFilterStatus] = useState<'all' | 'enrolled' | 'completed'>('all')

  const { data: courses = [], isLoading } = useQuery<LearningCourse[]>({
    queryKey: ['learning-courses'],
    queryFn: () => api.get('/api/v1/learning/courses/').then((r) => r.data.results ?? r.data),
  })

  const enrollMut = useMutation({
    mutationFn: (courseId: string) => api.post(`/api/v1/learning/courses/${courseId}/enroll/`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['learning-courses'] }),
  })

  const progressMut = useMutation({
    mutationFn: ({ enrollmentId, pct }: { enrollmentId: string; pct: number }) =>
      api.patch(`/api/v1/learning/enrollments/${enrollmentId}/progress/`, { progress_pct: pct }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['learning-courses'] }),
  })

  const createMut = useMutation({
    mutationFn: (data: any) => api.post('/api/v1/learning/courses/', data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['learning-courses'] }); setShowNew(false) },
  })

  const filtered = courses.filter((c) => {
    if (filterStatus === 'enrolled') return c.my_enrollment && c.my_enrollment.status !== 'completed'
    if (filterStatus === 'completed') return c.my_enrollment?.status === 'completed'
    return true
  })

  const completed = courses.filter((c) => c.my_enrollment?.status === 'completed').length
  const required = courses.filter((c) => c.is_required).length

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <BookOpen className="text-indigo-600" size={28} />
          <div>
            <h1 className="text-2xl font-bold text-gray-800">e-Learning / 研修</h1>
            <p className="text-sm text-gray-500">社内研修・eラーニングの受講管理</p>
          </div>
        </div>
        {isHR && (
          <button
            onClick={() => setShowNew(true)}
            className="flex items-center gap-2 bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 text-sm"
          >
            <Plus size={16} /> コース作成
          </button>
        )}
      </div>

      <div className="grid grid-cols-4 gap-4 mb-6">
        {[
          { label: '全コース', value: courses.length },
          { label: '必須研修', value: required },
          { label: '受講中', value: courses.filter((c) => c.my_enrollment?.status === 'in_progress').length },
          { label: '修了', value: completed },
        ].map((item) => (
          <div key={item.label} className="bg-white rounded-xl border shadow-sm p-4 text-center">
            <p className="text-3xl font-bold text-gray-800">{item.value}</p>
            <p className="text-sm text-gray-500 mt-1">{item.label}</p>
          </div>
        ))}
      </div>

      {/* フィルター */}
      <div className="flex gap-2 mb-4">
        {[
          { key: 'all', label: 'すべて' },
          { key: 'enrolled', label: '受講中' },
          { key: 'completed', label: '修了' },
        ].map((f) => (
          <button
            key={f.key}
            onClick={() => setFilterStatus(f.key as any)}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
              filterStatus === f.key
                ? 'bg-indigo-600 text-white'
                : 'bg-white border text-gray-600 hover:bg-gray-50'
            }`}
          >{f.label}</button>
        ))}
      </div>

      {/* コース一覧 */}
      {isLoading ? (
        <div className="p-8 text-center text-gray-400">読み込み中...</div>
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {filtered.map((course) => {
            const typeConfig = COURSE_TYPE[course.course_type] ?? { label: course.course_type, color: 'bg-gray-100 text-gray-600' }
            const enrollment = course.my_enrollment
            const isCompleted = enrollment?.status === 'completed'
            const isEnrolled = !!enrollment

            return (
              <div key={course.id} className="bg-white rounded-xl border shadow-sm p-5">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <span className={`text-xs px-2 py-0.5 rounded-full ${typeConfig.color}`}>
                        {typeConfig.label}
                      </span>
                      {course.is_required && (
                        <span className="text-xs bg-red-100 text-red-600 px-2 py-0.5 rounded-full">必須</span>
                      )}
                      {isCompleted && (
                        <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full flex items-center gap-1">
                          <CheckCircle size={10} /> 修了
                        </span>
                      )}
                    </div>
                    <h3 className="font-bold text-gray-800 mb-1">{course.title}</h3>
                    <p className="text-sm text-gray-500 line-clamp-2">{course.description}</p>
                    <div className="flex items-center gap-4 mt-2 text-xs text-gray-400">
                      <span className="flex items-center gap-1"><Clock size={12} /> {course.duration_minutes}分</span>
                      <span>{course.enrollment_count}名受講</span>
                    </div>
                    {isEnrolled && !isCompleted && (
                      <div className="mt-3">
                        <div className="flex justify-between text-xs text-gray-500 mb-1">
                          <span>進捗</span>
                          <span>{enrollment.progress_pct}%</span>
                        </div>
                        <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                          <div
                            className="h-full bg-indigo-500 rounded-full transition-all"
                            style={{ width: `${enrollment.progress_pct}%` }}
                          />
                        </div>
                      </div>
                    )}
                  </div>
                  <div className="flex flex-col gap-2 shrink-0">
                    {!isEnrolled ? (
                      <button
                        onClick={() => enrollMut.mutate(course.id)}
                        className="text-sm bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 flex items-center gap-2"
                      >
                        <Play size={14} /> 受講開始
                      </button>
                    ) : !isCompleted ? (
                      <div className="flex gap-2">
                        <button
                          onClick={() => progressMut.mutate({ enrollmentId: enrollment!.id, pct: Math.min(100, (enrollment!.progress_pct ?? 0) + 25) })}
                          className="text-sm bg-indigo-100 text-indigo-700 px-3 py-2 rounded-lg hover:bg-indigo-200"
                        >+25%</button>
                        <button
                          onClick={() => progressMut.mutate({ enrollmentId: enrollment!.id, pct: 100 })}
                          className="text-sm bg-green-100 text-green-700 px-3 py-2 rounded-lg hover:bg-green-200"
                        >修了</button>
                      </div>
                    ) : (
                      <div className="flex items-center gap-2 text-green-600">
                        <CheckCircle size={20} />
                        <span className="text-sm font-medium">修了済</span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* コース作成モーダル */}
      {showNew && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg p-6">
            <h2 className="text-lg font-bold text-gray-800 mb-4">コース作成</h2>
            <div className="space-y-3">
              <input
                className="w-full border rounded-lg px-3 py-2 text-sm"
                placeholder="コースタイトル *"
                value={form.title}
                onChange={(e) => setForm({ ...form, title: e.target.value })}
              />
              <textarea
                className="w-full border rounded-lg px-3 py-2 text-sm h-20 resize-none"
                placeholder="コース説明 *"
                value={form.description}
                onChange={(e) => setForm({ ...form, description: e.target.value })}
              />
              <div className="grid grid-cols-2 gap-3">
                <select
                  className="border rounded-lg px-3 py-2 text-sm"
                  value={form.course_type}
                  onChange={(e) => setForm({ ...form, course_type: e.target.value })}
                >
                  {Object.entries(COURSE_TYPE).map(([k, v]) => (
                    <option key={k} value={k}>{v.label}</option>
                  ))}
                </select>
                <input
                  type="number"
                  className="border rounded-lg px-3 py-2 text-sm"
                  placeholder="所要時間（分）"
                  value={form.duration_minutes}
                  onChange={(e) => setForm({ ...form, duration_minutes: e.target.value })}
                />
              </div>
              <label className="flex items-center gap-2 text-sm text-gray-700">
                <input
                  type="checkbox"
                  checked={form.is_required}
                  onChange={(e) => setForm({ ...form, is_required: e.target.checked })}
                />
                必須研修として設定
              </label>
            </div>
            <div className="flex gap-3 mt-4">
              <button onClick={() => setShowNew(false)} className="flex-1 border text-gray-700 py-2 rounded-lg text-sm">キャンセル</button>
              <button
                onClick={() => createMut.mutate({ ...form, duration_minutes: Number(form.duration_minutes) || 0, status: 'published' })}
                disabled={!form.title || !form.description}
                className="flex-1 bg-indigo-600 text-white py-2 rounded-lg text-sm hover:bg-indigo-700 disabled:opacity-50"
              >作成・公開</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
