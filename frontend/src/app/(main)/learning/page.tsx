'use client'
import { useState, useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'
import { useAuthStore } from '@/lib/store'
import {
  BookOpen, Plus, Play, CheckCircle, Clock, Paperclip, X,
  FileText, ClipboardList, ChevronRight, AlertCircle
} from 'lucide-react'

interface LearningCourse {
  id: string; title: string; description: string; course_type: string
  duration_minutes: number; is_required: boolean; status: string
  enrollment_count: number; has_quiz: boolean
  attachments: CourseAttachment[]
  my_enrollment: {
    id: string; status: string; progress_pct: number; completed_at: string | null; score: number | null
  } | null
}

interface CourseAttachment {
  id: string; file_name: string; file_size: number; content_type: string; is_image: boolean; url: string
}

interface Quiz {
  id: string; title: string; description: string; pass_score: number
  time_limit_minutes: number | null; question_count: number
  questions: QuizQuestion[]
}

interface QuizQuestion {
  id: string; question_text: string; question_type: 'choice' | 'free_text'
  order: number; points: number; choices: QuizChoice[]
}

interface QuizChoice { id: string; choice_text: string; order: number }

interface QuizAttempt {
  id: string; score: number | null; is_passed: boolean | null
  started_at: string; submitted_at: string | null
  answers: QuizAnswer[]
}

interface QuizAnswer {
  question: string; selected_choice: string | null; free_text_answer: string; is_correct: boolean | null
}

const COURSE_TYPE: Record<string, { label: string; color: string }> = {
  elearning: { label: 'eラーニング', color: 'bg-blue-100 text-blue-700' },
  classroom: { label: '集合研修', color: 'bg-green-100 text-green-700' },
  ojt: { label: 'OJT', color: 'bg-orange-100 text-orange-700' },
  external: { label: '外部研修', color: 'bg-purple-100 text-purple-700' },
}

const formatSize = (b: number) => b < 1024 * 1024 ? `${(b / 1024).toFixed(1)}KB` : `${(b / 1024 / 1024).toFixed(1)}MB`

export default function LearningPage() {
  const user = useAuthStore((s) => s.user)
  const qc = useQueryClient()
  const isHR = ['hr', 'admin'].includes(user?.role ?? '')
  const [showNew, setShowNew] = useState(false)
  const [quizCourseId, setQuizCourseId] = useState<string | null>(null)
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

  const filtered = courses.filter((c) => {
    if (filterStatus === 'enrolled') return c.my_enrollment && c.my_enrollment.status !== 'completed'
    if (filterStatus === 'completed') return c.my_enrollment?.status === 'completed'
    return true
  })

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
          <button onClick={() => setShowNew(true)}
            className="flex items-center gap-2 bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 text-sm">
            <Plus size={16} /> コース作成
          </button>
        )}
      </div>

      <div className="grid grid-cols-4 gap-4 mb-6">
        {[
          { label: '全コース', value: courses.length },
          { label: '必須研修', value: courses.filter((c) => c.is_required).length },
          { label: '受講中', value: courses.filter((c) => c.my_enrollment?.status === 'in_progress').length },
          { label: '修了', value: courses.filter((c) => c.my_enrollment?.status === 'completed').length },
        ].map((item) => (
          <div key={item.label} className="bg-white rounded-xl border shadow-sm p-4 text-center">
            <p className="text-3xl font-bold text-gray-800">{item.value}</p>
            <p className="text-sm text-gray-500 mt-1">{item.label}</p>
          </div>
        ))}
      </div>

      <div className="flex gap-2 mb-4">
        {[{ key: 'all', label: 'すべて' }, { key: 'enrolled', label: '受講中' }, { key: 'completed', label: '修了' }].map((f) => (
          <button key={f.key} onClick={() => setFilterStatus(f.key as any)}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
              filterStatus === f.key ? 'bg-indigo-600 text-white' : 'bg-white border text-gray-600 hover:bg-gray-50'
            }`}>{f.label}</button>
        ))}
      </div>

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
                    <div className="flex items-center gap-2 mb-2 flex-wrap">
                      <span className={`text-xs px-2 py-0.5 rounded-full ${typeConfig.color}`}>{typeConfig.label}</span>
                      {course.is_required && <span className="text-xs bg-red-100 text-red-600 px-2 py-0.5 rounded-full">必須</span>}
                      {isCompleted && (
                        <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full flex items-center gap-1">
                          <CheckCircle size={10} /> 修了
                        </span>
                      )}
                      {course.has_quiz && (
                        <span className="text-xs bg-amber-100 text-amber-700 px-2 py-0.5 rounded-full flex items-center gap-1">
                          <ClipboardList size={10} /> テストあり
                        </span>
                      )}
                    </div>
                    <h3 className="font-bold text-gray-800 mb-1">{course.title}</h3>
                    <p className="text-sm text-gray-500 line-clamp-2">{course.description}</p>
                    <div className="flex items-center gap-4 mt-2 text-xs text-gray-400">
                      <span className="flex items-center gap-1"><Clock size={12} /> {course.duration_minutes}分</span>
                      <span>{course.enrollment_count}名受講</span>
                      {enrollment?.score != null && (
                        <span className="text-indigo-600 font-medium">テスト: {enrollment.score}点</span>
                      )}
                    </div>

                    {/* 添付ファイル一覧 */}
                    {course.attachments.length > 0 && (
                      <div className="mt-3 flex flex-wrap gap-2">
                        {course.attachments.map((att) => (
                          <a key={att.id} href={att.url} target="_blank" rel="noopener noreferrer"
                            className="flex items-center gap-1.5 bg-gray-50 border rounded-lg px-2.5 py-1.5 text-xs text-gray-600 hover:bg-gray-100">
                            {att.is_image ? <FileText size={12} /> : <Paperclip size={12} />}
                            <span className="truncate max-w-[120px]">{att.file_name}</span>
                            <span className="text-gray-400">{formatSize(att.file_size)}</span>
                          </a>
                        ))}
                      </div>
                    )}

                    {isEnrolled && !isCompleted && (
                      <div className="mt-3">
                        <div className="flex justify-between text-xs text-gray-500 mb-1">
                          <span>進捗</span><span>{enrollment.progress_pct}%</span>
                        </div>
                        <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                          <div className="h-full bg-indigo-500 rounded-full transition-all" style={{ width: `${enrollment.progress_pct}%` }} />
                        </div>
                      </div>
                    )}
                  </div>

                  <div className="flex flex-col gap-2 shrink-0">
                    {!isEnrolled ? (
                      <button onClick={() => enrollMut.mutate(course.id)}
                        className="text-sm bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 flex items-center gap-2">
                        <Play size={14} /> 受講開始
                      </button>
                    ) : !isCompleted ? (
                      <div className="flex flex-col gap-2">
                        <div className="flex gap-2">
                          <button onClick={() => progressMut.mutate({ enrollmentId: enrollment!.id, pct: Math.min(100, (enrollment!.progress_pct ?? 0) + 25) })}
                            className="text-sm bg-indigo-100 text-indigo-700 px-3 py-2 rounded-lg hover:bg-indigo-200">+25%</button>
                          <button onClick={() => progressMut.mutate({ enrollmentId: enrollment!.id, pct: 100 })}
                            className="text-sm bg-green-100 text-green-700 px-3 py-2 rounded-lg hover:bg-green-200">修了</button>
                        </div>
                        {course.has_quiz && (
                          <button onClick={() => setQuizCourseId(course.id)}
                            className="text-sm bg-amber-100 text-amber-700 px-3 py-2 rounded-lg hover:bg-amber-200 flex items-center gap-1.5 justify-center">
                            <ClipboardList size={14} /> テスト受験
                          </button>
                        )}
                      </div>
                    ) : (
                      <div className="flex flex-col gap-2">
                        <div className="flex items-center gap-2 text-green-600">
                          <CheckCircle size={20} />
                          <span className="text-sm font-medium">修了済</span>
                        </div>
                        {course.has_quiz && (
                          <button onClick={() => setQuizCourseId(course.id)}
                            className="text-xs bg-gray-100 text-gray-600 px-2 py-1.5 rounded-lg hover:bg-gray-200 flex items-center gap-1 justify-center">
                            <ClipboardList size={12} /> テスト確認
                          </button>
                        )}
                      </div>
                    )}
                    {isHR && (
                      <button onClick={() => setQuizCourseId(course.id)}
                        className="text-xs text-gray-400 hover:text-indigo-600 flex items-center gap-1 justify-end mt-1">
                        <ClipboardList size={12} /> テスト管理
                      </button>
                    )}
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}

      {showNew && <CourseCreateModal onClose={() => setShowNew(false)} onCreated={() => {
        qc.invalidateQueries({ queryKey: ['learning-courses'] })
        setShowNew(false)
      }} isHR={isHR} />}

      {quizCourseId && (
        <QuizModal
          courseId={quizCourseId}
          isHR={isHR}
          onClose={() => setQuizCourseId(null)}
        />
      )}
    </div>
  )
}

// ---- コース作成モーダル（ファイル添付対応）----
function CourseCreateModal({ onClose, onCreated, isHR }: { onClose: () => void; onCreated: () => void; isHR: boolean }) {
  const [form, setForm] = useState({ title: '', description: '', course_type: 'elearning', duration_minutes: '', is_required: false })
  const [files, setFiles] = useState<File[]>([])
  const fileRef = useRef<HTMLInputElement | null>(null)

  const createMut = useMutation({
    mutationFn: () => {
      const fd = new FormData()
      fd.append('title', form.title)
      fd.append('description', form.description)
      fd.append('course_type', form.course_type)
      fd.append('duration_minutes', String(Number(form.duration_minutes) || 0))
      fd.append('is_required', String(form.is_required))
      fd.append('status', 'published')
      files.forEach((f) => fd.append('files', f))
      return api.post('/api/v1/learning/courses/', fd, { headers: { 'Content-Type': 'multipart/form-data' } })
    },
    onSuccess: onCreated,
  })

  const removeFile = (i: number) => setFiles(files.filter((_, idx) => idx !== i))

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg p-6 max-h-[90vh] overflow-y-auto">
        <h2 className="text-lg font-bold text-gray-800 mb-4">コース作成</h2>
        <div className="space-y-3">
          <input className="w-full border rounded-lg px-3 py-2 text-sm" placeholder="コースタイトル *"
            value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} />
          <textarea className="w-full border rounded-lg px-3 py-2 text-sm h-20 resize-none" placeholder="コース説明 *"
            value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
          <div className="grid grid-cols-2 gap-3">
            <select className="border rounded-lg px-3 py-2 text-sm" value={form.course_type}
              onChange={(e) => setForm({ ...form, course_type: e.target.value })}>
              {Object.entries(COURSE_TYPE).map(([k, v]) => <option key={k} value={k}>{v.label}</option>)}
            </select>
            <input type="number" className="border rounded-lg px-3 py-2 text-sm" placeholder="所要時間（分）"
              value={form.duration_minutes} onChange={(e) => setForm({ ...form, duration_minutes: e.target.value })} />
          </div>
          <label className="flex items-center gap-2 text-sm text-gray-700">
            <input type="checkbox" checked={form.is_required} onChange={(e) => setForm({ ...form, is_required: e.target.checked })} />
            必須研修として設定
          </label>

          {/* ファイル添付 */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-700">添付ファイル</span>
              <button onClick={() => fileRef.current?.click()}
                className="flex items-center gap-1 text-xs text-indigo-600 hover:text-indigo-800">
                <Paperclip size={12} /> ファイルを追加
              </button>
            </div>
            <input ref={fileRef} type="file" multiple className="hidden"
              onChange={(e) => setFiles([...files, ...Array.from(e.target.files ?? [])])} />
            {files.length > 0 && (
              <div className="space-y-1.5">
                {files.map((f, i) => (
                  <div key={i} className="flex items-center justify-between bg-gray-50 rounded-lg px-3 py-1.5 text-xs">
                    <span className="text-gray-600 truncate max-w-[280px]">{f.name}</span>
                    <div className="flex items-center gap-2">
                      <span className="text-gray-400">{formatSize(f.size)}</span>
                      <button onClick={() => removeFile(i)} className="text-gray-400 hover:text-red-500"><X size={12} /></button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
        <div className="flex gap-3 mt-4">
          <button onClick={onClose} className="flex-1 border text-gray-700 py-2 rounded-lg text-sm">キャンセル</button>
          <button onClick={() => createMut.mutate()} disabled={!form.title || !form.description}
            className="flex-1 bg-indigo-600 text-white py-2 rounded-lg text-sm hover:bg-indigo-700 disabled:opacity-50">
            作成・公開
          </button>
        </div>
      </div>
    </div>
  )
}

// ---- テスト管理・受験モーダル ----
function QuizModal({ courseId, isHR, onClose }: { courseId: string; isHR: boolean; onClose: () => void }) {
  const qc = useQueryClient()
  const [tab, setTab] = useState<'take' | 'manage'>(isHR ? 'manage' : 'take')
  const [attempt, setAttempt] = useState<QuizAttempt | null>(null)
  const [answers, setAnswers] = useState<Record<string, { selected_choice?: string; free_text_answer?: string }>>({})
  const [submitted, setSubmitted] = useState(false)
  const [result, setResult] = useState<QuizAttempt | null>(null)
  const [showAddQuestion, setShowAddQuestion] = useState(false)

  const { data: quiz, isLoading, refetch } = useQuery<Quiz>({
    queryKey: ['quiz', courseId],
    queryFn: () => api.get(`/api/v1/learning/courses/${courseId}/quiz/`).then((r) => r.data),
  })

  const createQuizMut = useMutation({
    mutationFn: () => api.post(`/api/v1/learning/courses/${courseId}/quiz/create/`, { title: '理解度確認テスト', pass_score: 70 }),
    onSuccess: () => refetch(),
  })

  const startMut = useMutation({
    mutationFn: () => api.post(`/api/v1/learning/quizzes/${quiz!.id}/start/`),
    onSuccess: (res) => setAttempt(res.data),
  })

  const submitMut = useMutation({
    mutationFn: () => api.post(`/api/v1/learning/quizzes/${quiz!.id}/submit/${attempt!.id}/`, {
      answers: Object.entries(answers).map(([qid, ans]) => ({
        question: qid,
        selected_choice: ans.selected_choice || null,
        free_text_answer: ans.free_text_answer || '',
      }))
    }),
    onSuccess: (res) => {
      setResult(res.data)
      setSubmitted(true)
      qc.invalidateQueries({ queryKey: ['learning-courses'] })
    },
  })

  const deleteQuestionMut = useMutation({
    mutationFn: (qId: string) => api.delete(`/api/v1/learning/quizzes/${quiz!.id}/questions/${qId}/`),
    onSuccess: () => refetch(),
  })

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-2xl max-h-[90vh] flex flex-col">
        <div className="flex items-center justify-between p-5 border-b">
          <div className="flex items-center gap-3">
            <ClipboardList className="text-amber-600" size={20} />
            <h2 className="text-lg font-bold text-gray-800">
              {quiz?.title ?? '理解度確認テスト'}
            </h2>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600"><X size={20} /></button>
        </div>

        {isHR && (
          <div className="flex border-b">
            {[{ key: 'take', label: '受験' }, { key: 'manage', label: '問題管理' }].map((t) => (
              <button key={t.key} onClick={() => setTab(t.key as any)}
                className={`px-5 py-2.5 text-sm font-medium border-b-2 transition-colors ${
                  tab === t.key ? 'border-indigo-500 text-indigo-600' : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}>{t.label}</button>
            ))}
          </div>
        )}

        <div className="flex-1 overflow-y-auto p-5">
          {isLoading ? (
            <div className="text-center text-gray-400 py-8">読み込み中...</div>
          ) : !quiz ? (
            <div className="text-center py-8">
              <AlertCircle size={40} className="mx-auto text-gray-300 mb-3" />
              <p className="text-gray-500 mb-4">テストが設定されていません</p>
              {isHR && (
                <button onClick={() => createQuizMut.mutate()}
                  className="bg-amber-500 text-white px-4 py-2 rounded-lg text-sm hover:bg-amber-600">
                  テストを作成する
                </button>
              )}
            </div>
          ) : tab === 'take' ? (
            /* --- 受験タブ --- */
            <div>
              {!attempt && !submitted && (
                <div className="text-center py-8">
                  <ClipboardList size={40} className="mx-auto text-amber-400 mb-3" />
                  <p className="text-gray-600 mb-2 font-medium">{quiz.title}</p>
                  <p className="text-sm text-gray-400 mb-1">問題数: {quiz.question_count}問</p>
                  {quiz.time_limit_minutes && <p className="text-sm text-gray-400 mb-1">制限時間: {quiz.time_limit_minutes}分</p>}
                  <p className="text-sm text-gray-400 mb-5">合格点: {quiz.pass_score}%</p>
                  <button onClick={() => startMut.mutate()}
                    className="bg-amber-500 text-white px-6 py-2.5 rounded-lg hover:bg-amber-600">
                    テスト開始
                  </button>
                </div>
              )}

              {attempt && !submitted && (
                <div className="space-y-6">
                  {quiz.questions.map((q, qi) => (
                    <div key={q.id} className="border rounded-xl p-4">
                      <p className="font-medium text-gray-800 mb-3">
                        <span className="text-indigo-600 mr-2">Q{qi + 1}.</span>{q.question_text}
                      </p>
                      {q.question_type === 'choice' ? (
                        <div className="space-y-2">
                          {q.choices.map((c) => (
                            <label key={c.id} className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-colors ${
                              answers[q.id]?.selected_choice === c.id ? 'bg-indigo-50 border-indigo-300' : 'hover:bg-gray-50'
                            }`}>
                              <input type="radio" name={`q-${q.id}`} value={c.id}
                                checked={answers[q.id]?.selected_choice === c.id}
                                onChange={() => setAnswers({ ...answers, [q.id]: { selected_choice: c.id } })}
                                className="text-indigo-600" />
                              <span className="text-sm text-gray-700">{c.choice_text}</span>
                            </label>
                          ))}
                        </div>
                      ) : (
                        <textarea
                          className="w-full border rounded-lg px-3 py-2 text-sm resize-none h-24 focus:outline-none focus:ring-2 focus:ring-indigo-300"
                          placeholder="回答を入力してください..."
                          value={answers[q.id]?.free_text_answer ?? ''}
                          onChange={(e) => setAnswers({ ...answers, [q.id]: { free_text_answer: e.target.value } })}
                        />
                      )}
                    </div>
                  ))}
                  <button onClick={() => submitMut.mutate()}
                    className="w-full bg-amber-500 text-white py-3 rounded-xl hover:bg-amber-600 font-medium">
                    回答を提出する
                  </button>
                </div>
              )}

              {submitted && result && (
                <div className="text-center py-6">
                  <div className={`w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-4 ${
                    result.is_passed ? 'bg-green-100' : 'bg-red-100'
                  }`}>
                    {result.is_passed
                      ? <CheckCircle size={40} className="text-green-500" />
                      : <AlertCircle size={40} className="text-red-500" />
                    }
                  </div>
                  <p className="text-3xl font-bold text-gray-800 mb-1">{result.score}点</p>
                  <p className={`text-lg font-medium mb-4 ${result.is_passed ? 'text-green-600' : 'text-red-500'}`}>
                    {result.is_passed ? '合格' : '不合格'}
                  </p>
                  <p className="text-sm text-gray-500">合格点: {quiz.pass_score}%</p>
                  <button onClick={() => { setAttempt(null); setSubmitted(false); setAnswers({}); setResult(null) }}
                    className="mt-4 text-sm text-indigo-600 hover:underline">再受験する</button>
                </div>
              )}
            </div>
          ) : (
            /* --- 問題管理タブ（HR） --- */
            <div>
              <div className="flex justify-between items-center mb-4">
                <p className="text-sm text-gray-600">問題数: {quiz.questions.length}問</p>
                <button onClick={() => setShowAddQuestion(true)}
                  className="flex items-center gap-1.5 bg-indigo-600 text-white px-3 py-1.5 rounded-lg text-sm hover:bg-indigo-700">
                  <Plus size={14} /> 問題を追加
                </button>
              </div>
              {quiz.questions.length === 0 ? (
                <div className="text-center py-8 text-gray-400">問題がありません。追加してください。</div>
              ) : (
                <div className="space-y-3">
                  {quiz.questions.map((q, i) => (
                    <div key={q.id} className="border rounded-xl p-4">
                      <div className="flex justify-between items-start">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="text-xs bg-indigo-100 text-indigo-700 px-2 py-0.5 rounded-full">Q{i + 1}</span>
                            <span className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full">
                              {q.question_type === 'choice' ? '選択式' : '自由記述'}
                            </span>
                          </div>
                          <p className="text-sm text-gray-800">{q.question_text}</p>
                          {q.question_type === 'choice' && (
                            <div className="mt-2 space-y-1">
                              {q.choices.map((c) => (
                                <div key={c.id} className={`text-xs px-2 py-1 rounded ${(c as any).is_correct ? 'bg-green-50 text-green-700' : 'text-gray-500'}`}>
                                  {(c as any).is_correct ? '✓ ' : '　'}{c.choice_text}
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                        <button onClick={() => deleteQuestionMut.mutate(q.id)}
                          className="text-gray-300 hover:text-red-500 ml-3">
                          <X size={16} />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
              {showAddQuestion && (
                <AddQuestionForm quizId={quiz.id} onAdded={() => { refetch(); setShowAddQuestion(false) }} onCancel={() => setShowAddQuestion(false)} />
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

// ---- 問題追加フォーム ----
function AddQuestionForm({ quizId, onAdded, onCancel }: { quizId: string; onAdded: () => void; onCancel: () => void }) {
  const [questionText, setQuestionText] = useState('')
  const [type, setType] = useState<'choice' | 'free_text'>('choice')
  const [choices, setChoices] = useState([
    { choice_text: '', is_correct: false },
    { choice_text: '', is_correct: false },
    { choice_text: '', is_correct: false },
    { choice_text: '', is_correct: false },
  ])

  const addMut = useMutation({
    mutationFn: () => api.post(`/api/v1/learning/quizzes/${quizId}/questions/`, {
      question_text: questionText,
      question_type: type,
      choices: type === 'choice' ? choices.filter((c) => c.choice_text.trim()) : [],
    }),
    onSuccess: onAdded,
  })

  const updateChoice = (i: number, field: 'choice_text' | 'is_correct', val: string | boolean) => {
    const updated = [...choices]
    if (field === 'is_correct') {
      // 単一選択: 他をオフにする
      updated.forEach((c, j) => { c.is_correct = j === i ? (val as boolean) : false })
    } else {
      updated[i] = { ...updated[i], [field]: val }
    }
    setChoices(updated)
  }

  return (
    <div className="mt-4 border-t pt-4">
      <h3 className="font-medium text-gray-700 mb-3">問題を追加</h3>
      <div className="space-y-3">
        <textarea className="w-full border rounded-lg px-3 py-2 text-sm resize-none h-20" placeholder="問題文を入力 *"
          value={questionText} onChange={(e) => setQuestionText(e.target.value)} />
        <div className="flex gap-3">
          <label className="flex items-center gap-2 text-sm cursor-pointer">
            <input type="radio" checked={type === 'choice'} onChange={() => setType('choice')} /> 選択式
          </label>
          <label className="flex items-center gap-2 text-sm cursor-pointer">
            <input type="radio" checked={type === 'free_text'} onChange={() => setType('free_text')} /> 自由記述
          </label>
        </div>
        {type === 'choice' && (
          <div className="space-y-2">
            <p className="text-xs text-gray-500">選択肢を入力し、正解にチェックを付けてください</p>
            {choices.map((c, i) => (
              <div key={i} className="flex items-center gap-2">
                <input type="radio" name="correct" checked={c.is_correct} onChange={(e) => updateChoice(i, 'is_correct', e.target.checked)}
                  className="text-green-600 shrink-0" title="正解" />
                <input className="flex-1 border rounded-lg px-3 py-1.5 text-sm" placeholder={`選択肢 ${i + 1}`}
                  value={c.choice_text} onChange={(e) => updateChoice(i, 'choice_text', e.target.value)} />
              </div>
            ))}
          </div>
        )}
        {type === 'free_text' && (
          <p className="text-xs text-gray-400 bg-gray-50 rounded-lg p-3">
            自由記述は手動採点となります。スコアには含まれません。
          </p>
        )}
      </div>
      <div className="flex gap-2 mt-3">
        <button onClick={onCancel} className="flex-1 border text-gray-600 py-2 rounded-lg text-sm">キャンセル</button>
        <button onClick={() => addMut.mutate()} disabled={!questionText.trim()}
          className="flex-1 bg-indigo-600 text-white py-2 rounded-lg text-sm hover:bg-indigo-700 disabled:opacity-50">
          追加
        </button>
      </div>
    </div>
  )
}

