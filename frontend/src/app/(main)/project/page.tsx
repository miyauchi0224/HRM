'use client'
/**
 * プロジェクト管理ページ
 *
 * 機能概要:
 *  - 左カラム: プロジェクト一覧 + 新規作成 / CSV一括登録
 *  - 右カラム: 選択プロジェクトのガントチャート + タスク管理
 *
 * データフロー:
 *  React Query でサーバー状態を管理。
 *  useMutation で作成/更新/削除 → onSuccess で queryKey を invalidate → 自動再取得。
 */
import { useState, useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'
import { useAuthStore } from '@/lib/store'
import {
  GanttChartSquare, Plus, Pencil, Trash2, X,
  Download, Upload, Users, Calendar,
} from 'lucide-react'

// ─── 型定義 ────────────────────────────────────────────────────────────────

/** プロジェクト（APIレスポンス形） */
interface Project {
  id: string
  code: string
  name: string
  description: string
  /** 後方互換: 主管理者1件目のID */
  manager: string | null
  /** 後方互換: 主管理者1件目の名前 */
  manager_name: string | null
  /** 主管理者リスト（M2M） */
  primary_managers: { id: string; full_name: string }[]
  /** 従管理者リスト（M2M） */
  secondary_managers: { id: string; full_name: string }[]
  /** 主管理者IDリスト（フォーム編集用） */
  primary_manager_ids: string[]
  /** 従管理者IDリスト（フォーム編集用） */
  secondary_manager_ids: string[]
  is_active: boolean
  start_date: string | null
  end_date: string | null
  task_count: number
}

/** プロジェクトタスク（ガントチャート行） */
interface ProjectTask {
  id: string
  project: string
  title: string
  description: string
  assignee: string | null
  assignee_name: string | null
  status: string
  status_label: string
  start_date: string | null
  end_date: string | null
  progress: number
  order: number
}

/** プロジェクトフォームの状態 */
interface ProjectFormState {
  code: string
  name: string
  description: string
  primary_manager_ids: string[]
  secondary_manager_ids: string[]
  start_date: string
  end_date: string
  start_undecided: boolean
  end_undecided: boolean
}

// ─── 定数 ──────────────────────────────────────────────────────────────────

/** タスクステータスのガントバー色（Tailwind クラス） */
const STATUS_COLOR: Record<string, string> = {
  todo:        'bg-gray-300',
  in_progress: 'bg-blue-400',
  review:      'bg-yellow-400',
  done:        'bg-green-400',
}

/** タスクステータスの日本語ラベル */
const STATUS_LABEL: Record<string, string> = {
  todo:        '未着手',
  in_progress: '進行中',
  review:      'レビュー中',
  done:        '完了',
}

/** タスクステータスのテキスト色 */
const STATUS_TEXT: Record<string, string> = {
  todo:        'text-gray-600',
  in_progress: 'text-blue-600',
  review:      'text-yellow-600',
  done:        'text-green-600',
}

/** プロジェクトフォームの初期値 */
const BLANK_PROJECT_FORM: ProjectFormState = {
  code: '', name: '', description: '',
  primary_manager_ids: [], secondary_manager_ids: [],
  start_date: '', end_date: '',
  start_undecided: false, end_undecided: false,
}

/** タスクフォームの初期値 */
const BLANK_TASK_FORM = {
  title: '', description: '', assignee: '',
  status: 'todo', progress: 0,
  start_date: '', end_date: '',
}

// ─── ユーティリティ ────────────────────────────────────────────────────────

/**
 * Blob レスポンスをファイルダウンロードとして処理する。
 * <a> タグを一時生成してクリックし、URL を解放する。
 */
function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

// ─── メインページコンポーネント ────────────────────────────────────────────

export default function ProjectPage() {
  const qc      = useQueryClient()
  const user    = useAuthStore((s) => s.user)
  // 顧客ロールは閲覧のみ（作成・編集 UI を非表示）
  const isCustomer = user?.role === 'customer'

  // ── ローカル状態 ──
  const [selectedId,      setSelectedId]      = useState<string | null>(null)
  const [showNewProject,  setShowNewProject]   = useState(false)
  const [projectForm,     setProjectForm]      = useState<ProjectFormState>(BLANK_PROJECT_FORM)
  const [editProjectId,   setEditProjectId]    = useState<string | null>(null)
  const [editProjectForm, setEditProjectForm]  = useState<ProjectFormState>(BLANK_PROJECT_FORM)
  const [showTaskForm,    setShowTaskForm]     = useState(false)
  const [editTask,        setEditTask]         = useState<ProjectTask | null>(null)
  const [taskForm,        setTaskForm]         = useState(BLANK_TASK_FORM)

  // CSV インポート用の非表示 input 参照
  const importRef        = useRef<HTMLInputElement>(null)
  const importProjectRef = useRef<HTMLInputElement>(null)

  // ── サーバーデータ取得（React Query） ──

  /** プロジェクト一覧（常時キャッシュ） */
  const { data: projects = [], isLoading: projectsLoading } = useQuery<Project[]>({
    queryKey: ['projects-all'],
    queryFn: () => api.get('/api/v1/attendance/projects/').then(r => r.data.results ?? r.data),
  })

  /** 社員一覧（プロジェクト管理者選択用: 顧客ロール含む全社員） */
  const { data: allEmployees = [] } = useQuery<any[]>({
    queryKey: ['employees-for-project'],
    queryFn: () => api.get('/api/v1/employees/?for_project=true').then(r => r.data.results ?? r.data),
  })

  /** 社員一覧（タスク担当者選択用: 顧客を除く） */
  const { data: staffEmployees = [] } = useQuery<any[]>({
    queryKey: ['employees-mini'],
    queryFn: () => api.get('/api/v1/employees/').then(r => r.data.results ?? r.data),
  })

  /** 選択中プロジェクトのガントチャートデータ（selectedId が変わるたびに再取得） */
  const { data: ganttData, isLoading: ganttLoading } = useQuery<any>({
    queryKey: ['gantt', selectedId],
    queryFn: () => api.get(`/api/v1/attendance/projects/${selectedId}/gantt/`).then(r => r.data),
    enabled: !!selectedId,  // プロジェクト未選択時はスキップ
  })

  // ── 派生値 ──

  const selectedProject = projects.find(p => p.id === selectedId)
  const tasks: ProjectTask[] = ganttData?.tasks ?? []
  const doneCount      = tasks.filter(t => t.status === 'done').length
  const progressOverall = tasks.length > 0 ? Math.round(doneCount / tasks.length * 100) : 0

  /**
   * ガントバーの左端・幅を % で計算するための日付範囲。
   * タスクの start/end の最小・最大から求める。
   */
  const allDates = tasks.flatMap(t => [t.start_date, t.end_date].filter(Boolean)) as string[]
  const today    = new Date().toISOString().slice(0, 10)
  const minDate  = allDates.length > 0 ? allDates.reduce((a, b) => (a < b ? a : b)) : today
  const maxDate  = allDates.length > 0 ? allDates.reduce((a, b) => (a > b ? a : b)) : today
  const startMs  = new Date(minDate).getTime()
  const endMs    = new Date(maxDate).getTime()
  const totalDays = Math.max(1, Math.ceil((endMs - startMs) / 86400000) + 1)

  // ── API ミューテーション ──

  /** プロジェクト新規作成 */
  const createProjectMut = useMutation({
    mutationFn: (data: any) => api.post('/api/v1/attendance/projects/', data),
    onSuccess: (res) => {
      qc.invalidateQueries({ queryKey: ['projects-all'] })
      setSelectedId(res.data.id)   // 作成直後に選択状態にする
      setShowNewProject(false)
      setProjectForm(BLANK_PROJECT_FORM)
    },
  })

  /** プロジェクト更新（PATCH） */
  const updateProjectMut = useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) =>
      api.patch(`/api/v1/attendance/projects/${id}/`, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['projects-all'] })
      setEditProjectId(null)
    },
  })

  /** タスク新規作成 */
  const createTaskMut = useMutation({
    mutationFn: (data: any) =>
      api.post('/api/v1/attendance/project-tasks/', { ...data, project: selectedId }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['gantt', selectedId] })
      setShowTaskForm(false)
      setTaskForm(BLANK_TASK_FORM)
    },
  })

  /** タスク更新（PATCH） */
  const updateTaskMut = useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) =>
      api.patch(`/api/v1/attendance/project-tasks/${id}/`, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['gantt', selectedId] })
      setEditTask(null)
    },
  })

  /** タスク削除（論理削除） */
  const deleteTaskMut = useMutation({
    mutationFn: (id: string) => api.delete(`/api/v1/attendance/project-tasks/${id}/`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['gantt', selectedId] }),
  })

  /** タスク CSV 一括登録 */
  const importTaskMut = useMutation({
    mutationFn: (fd: FormData) =>
      api.post(`/api/v1/attendance/projects/${selectedId}/import-tasks/`, fd),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['gantt', selectedId] }),
  })

  /** プロジェクト CSV 一括登録 */
  const importProjectMut = useMutation({
    mutationFn: (fd: FormData) =>
      api.post('/api/v1/attendance/projects/import-projects/', fd),
    onSuccess: (res) => {
      qc.invalidateQueries({ queryKey: ['projects-all'] })
      const { created, updated, errors } = res.data
      alert(`登録: ${created}件 / 更新: ${updated}件${errors?.length ? ` / エラー: ${errors.length}件` : ''}`)
    },
  })

  // ── イベントハンドラー ──

  /** タスク編集フォームを開く */
  const startEditTask = (t: ProjectTask) => {
    setEditTask(t)
    setTaskForm({
      title: t.title, description: t.description, assignee: t.assignee ?? '',
      status: t.status, progress: t.progress,
      start_date: t.start_date ?? '', end_date: t.end_date ?? '',
    })
  }

  /** プロジェクト編集フォームを開く（ダブルクリック時） */
  const startEditProject = (p: Project) => {
    setEditProjectId(p.id)
    setEditProjectForm({
      code: p.code, name: p.name, description: p.description,
      primary_manager_ids:   p.primary_manager_ids   ?? [],
      secondary_manager_ids: p.secondary_manager_ids ?? [],
      start_date:      p.start_date ?? '',
      end_date:        p.end_date   ?? '',
      start_undecided: p.start_date === null,
      end_undecided:   p.end_date   === null,
    })
  }

  /** プロジェクト編集を保存 */
  const saveEditProject = () => {
    if (!editProjectId) return
    updateProjectMut.mutate({
      id: editProjectId,
      data: {
        code:                  editProjectForm.code,
        name:                  editProjectForm.name,
        description:           editProjectForm.description,
        primary_manager_ids:   editProjectForm.primary_manager_ids,
        secondary_manager_ids: editProjectForm.secondary_manager_ids,
        start_date: editProjectForm.start_undecided ? null : (editProjectForm.start_date || null),
        end_date:   editProjectForm.end_undecided   ? null : (editProjectForm.end_date   || null),
      },
    })
  }

  /**
   * 管理者チェックボックスのトグル。
   * 汎用にするため key（primary / secondary）と対象フォームを引数で受け取る。
   */
  const handleManagerToggle = (
    empId: string,
    key: 'primary_manager_ids' | 'secondary_manager_ids',
    setForm: React.Dispatch<React.SetStateAction<ProjectFormState>>,
  ) => {
    setForm(f => ({
      ...f,
      [key]: f[key].includes(empId)
        ? f[key].filter(id => id !== empId)
        : [...f[key], empId],
    }))
  }

  /** タスクテンプレート CSV ダウンロード */
  const downloadTaskTemplate = async () => {
    if (!selectedId) return
    const res = await api.get(
      `/api/v1/attendance/projects/${selectedId}/template-csv/`,
      { responseType: 'blob' },
    )
    downloadBlob(res.data, 'tasks_template.csv')
  }

  /** プロジェクトテンプレート CSV ダウンロード */
  const downloadProjectTemplate = async () => {
    const res = await api.get(
      '/api/v1/attendance/projects/projects-template-csv/',
      { responseType: 'blob' },
    )
    downloadBlob(res.data, 'projects_template.csv')
  }

  // ── レンダリング ──────────────────────────────────────────────────────────

  return (
    <div className="flex h-[calc(100vh-4rem)] overflow-hidden">

      {/* ══ 左カラム: プロジェクト一覧 ══ */}
      <div className="w-80 flex-shrink-0 border-r border-gray-200 bg-white flex flex-col">

        {/* ヘッダー: タイトル・新規ボタン・CSV操作 */}
        <div className="p-4 border-b border-gray-200 space-y-2">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold text-gray-700 flex items-center gap-2">
              <GanttChartSquare size={18} className="text-blue-500" />
              プロジェクト管理
            </h2>
            {/* 顧客以外は + ボタンを表示 */}
            {!isCustomer && (
              <button
                onClick={() => setShowNewProject(v => !v)}
                className="p-1 text-blue-600 hover:bg-blue-50 rounded-lg"
                title="新規プロジェクトを作成"
              >
                <Plus size={18} />
              </button>
            )}
          </div>

          {/* CSV 一括操作ボタン */}
          {!isCustomer && (
            <div className="flex gap-1">
              <button
                onClick={downloadProjectTemplate}
                className="flex-1 flex items-center justify-center gap-1 text-xs border border-gray-300 py-1.5 rounded hover:bg-gray-50 text-gray-600"
              >
                <Download size={11} /> テンプレート
              </button>
              <button
                onClick={() => importProjectRef.current?.click()}
                className="flex-1 flex items-center justify-center gap-1 text-xs border border-blue-300 text-blue-600 py-1.5 rounded hover:bg-blue-50"
              >
                <Upload size={11} /> CSV一括登録
              </button>
              {/* ファイル選択はプログラムからクリックするため非表示 */}
              <input
                ref={importProjectRef}
                type="file"
                accept=".csv"
                className="hidden"
                onChange={e => {
                  const f = e.target.files?.[0]
                  if (f) {
                    const fd = new FormData()
                    fd.append('file', f)
                    importProjectMut.mutate(fd)
                  }
                  e.target.value = ''  // 同じファイルを再選択できるようリセット
                }}
              />
            </div>
          )}

          {/* 新規プロジェクト作成フォーム（+ ボタンで展開） */}
          {showNewProject && (
            <ProjectForm
              form={projectForm}
              setForm={setProjectForm}
              employees={allEmployees}
              onSubmit={() => createProjectMut.mutate({
                code:                  projectForm.code,
                name:                  projectForm.name,
                description:           projectForm.description,
                primary_manager_ids:   projectForm.primary_manager_ids,
                secondary_manager_ids: projectForm.secondary_manager_ids,
                start_date: projectForm.start_undecided ? null : (projectForm.start_date || null),
                end_date:   projectForm.end_undecided   ? null : (projectForm.end_date   || null),
              })}
              onCancel={() => { setShowNewProject(false); setProjectForm(BLANK_PROJECT_FORM) }}
              onTogglePrimary={id => handleManagerToggle(id, 'primary_manager_ids', setProjectForm)}
              onToggleSecondary={id => handleManagerToggle(id, 'secondary_manager_ids', setProjectForm)}
              isPending={createProjectMut.isPending}
              error={createProjectMut.error}
            />
          )}
        </div>

        {/* プロジェクト一覧 */}
        <div className="flex-1 overflow-y-auto">
          {projectsLoading ? (
            <p className="text-xs text-gray-400 p-4">読み込み中...</p>
          ) : projects.length === 0 ? (
            <p className="text-xs text-gray-400 p-4 text-center">プロジェクトがありません</p>
          ) : (
            projects.map(p => (
              <div key={p.id}>
                {editProjectId === p.id ? (
                  /* インライン編集フォーム（ダブルクリックで展開） */
                  <div className="p-3 bg-blue-50 border-b border-blue-200">
                    <ProjectForm
                      form={editProjectForm}
                      setForm={setEditProjectForm}
                      employees={allEmployees}
                      onSubmit={saveEditProject}
                      onCancel={() => setEditProjectId(null)}
                      onTogglePrimary={id => handleManagerToggle(id, 'primary_manager_ids', setEditProjectForm)}
                      onToggleSecondary={id => handleManagerToggle(id, 'secondary_manager_ids', setEditProjectForm)}
                      isPending={updateProjectMut.isPending}
                      error={updateProjectMut.error}
                      isEdit
                    />
                  </div>
                ) : (
                  <button
                    onClick={() => setSelectedId(p.id)}
                    onDoubleClick={e => { e.preventDefault(); startEditProject(p) }}
                    title="クリック: 選択 / ダブルクリック: 編集"
                    className={`w-full text-left p-3 border-b border-gray-100 hover:bg-gray-50 transition-colors ${
                      selectedId === p.id ? 'bg-blue-50 border-l-2 border-l-blue-500' : ''
                    }`}
                  >
                    <div className="flex items-center justify-between mb-0.5">
                      <span className="text-xs font-medium text-blue-600">{p.code}</span>
                      <span className="text-xs text-gray-400">{p.task_count}タスク</span>
                    </div>
                    <p className="text-sm font-medium text-gray-800 truncate">{p.name}</p>
                    <div className="text-xs text-gray-400 mt-0.5 space-y-0.5">
                      {/* 管理者表示: 主→従の順 */}
                      {p.primary_managers?.length > 0 && (
                        <p className="flex items-center gap-1">
                          <Users size={10} />
                          {p.primary_managers.map(m => m.full_name).join('・')}（主）
                          {p.secondary_managers?.length > 0 &&
                            ` / ${p.secondary_managers.map(m => m.full_name).join('・')}（従）`}
                        </p>
                      )}
                      <p className="flex items-center gap-1">
                        <Calendar size={10} />
                        {p.start_date ?? '未定'} 〜 {p.end_date ?? '未定'}
                      </p>
                    </div>
                  </button>
                )}
              </div>
            ))
          )}
        </div>
      </div>

      {/* ══ 右カラム: ガントチャート + タスク管理 ══ */}
      <div className="flex-1 overflow-auto bg-gray-50">
        {!selectedId ? (
          /* 未選択時のプレースホルダー */
          <div className="flex items-center justify-center h-full">
            <div className="text-center text-gray-400">
              <GanttChartSquare size={48} className="mx-auto mb-3 opacity-30" />
              <p>プロジェクトを選択してください</p>
              <p className="text-xs mt-1">一覧行をダブルクリックで編集</p>
            </div>
          </div>
        ) : (
          <div className="p-6 space-y-4">

            {/* プロジェクト情報ヘッダー */}
            {selectedProject && (
              <div className="bg-white rounded-xl border border-gray-200 p-4">
                <div className="flex items-start justify-between">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-sm font-medium text-blue-600 bg-blue-50 px-2 py-0.5 rounded">
                        {selectedProject.code}
                      </span>
                      <h1 className="text-lg font-bold text-gray-800">{selectedProject.name}</h1>
                    </div>
                    {selectedProject.description && (
                      <p className="text-sm text-gray-500 mb-2">{selectedProject.description}</p>
                    )}
                    <div className="flex items-center gap-4 text-xs text-gray-400">
                      {selectedProject.primary_managers?.length > 0 && (
                        <span className="flex items-center gap-1">
                          <Users size={12} />
                          主：{selectedProject.primary_managers.map(m => m.full_name).join('・')}
                          {selectedProject.secondary_managers?.length > 0 &&
                            ` / 従：${selectedProject.secondary_managers.map(m => m.full_name).join('・')}`}
                        </span>
                      )}
                      <span className="flex items-center gap-1">
                        <Calendar size={12} />
                        {selectedProject.start_date ?? '開始未定'} 〜 {selectedProject.end_date ?? '終了未定'}
                      </span>
                    </div>
                  </div>
                  {/* 全体進捗率 */}
                  <div className="text-right">
                    <p className="text-2xl font-bold text-blue-600">{progressOverall}%</p>
                    <p className="text-xs text-gray-400">{doneCount}/{tasks.length} 完了</p>
                  </div>
                </div>
                {/* 全体進捗バー */}
                {tasks.length > 0 && (
                  <div className="mt-3">
                    <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-blue-500 rounded-full transition-all"
                        style={{ width: `${progressOverall}%` }}
                      />
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* タスク操作ツールバー */}
            <div className="flex items-center gap-2 flex-wrap">
              <button
                onClick={() => setShowTaskForm(true)}
                className="flex items-center gap-1.5 bg-blue-600 hover:bg-blue-700 text-white px-3 py-1.5 rounded-lg text-sm font-medium"
              >
                <Plus size={14} /> タスク追加
              </button>
              <button
                onClick={downloadTaskTemplate}
                className="flex items-center gap-1.5 border border-gray-300 text-gray-600 px-3 py-1.5 rounded-lg text-sm hover:bg-gray-50"
              >
                <Download size={14} /> タスクテンプレート
              </button>
              <button
                onClick={() => importRef.current?.click()}
                className="flex items-center gap-1.5 border border-blue-300 text-blue-600 px-3 py-1.5 rounded-lg text-sm hover:bg-blue-50"
              >
                <Upload size={14} /> タスクCSV登録
              </button>
              <input
                ref={importRef}
                type="file"
                accept=".csv"
                className="hidden"
                onChange={e => {
                  const f = e.target.files?.[0]
                  if (f) {
                    const fd = new FormData()
                    fd.append('file', f)
                    importTaskMut.mutate(fd)
                  }
                  e.target.value = ''
                }}
              />
            </div>

            {/* タスク追加 / 編集フォーム */}
            {(showTaskForm || editTask) && (
              <TaskForm
                form={taskForm}
                setForm={setTaskForm}
                employees={staffEmployees}
                editTask={editTask}
                onSubmit={() => {
                  const payload = {
                    title:       taskForm.title,
                    description: taskForm.description,
                    start_date:  taskForm.start_date || null,
                    end_date:    taskForm.end_date   || null,
                    status:      taskForm.status,
                    progress:    taskForm.progress,
                    assignee:    taskForm.assignee || null,
                  }
                  editTask
                    ? updateTaskMut.mutate({ id: editTask.id, data: payload })
                    : createTaskMut.mutate(payload)
                }}
                onCancel={() => {
                  setShowTaskForm(false)
                  setEditTask(null)
                  setTaskForm(BLANK_TASK_FORM)
                }}
              />
            )}

            {/* ガントチャート本体 */}
            {ganttLoading ? (
              <div className="bg-white rounded-xl border border-gray-200 p-8 text-center text-gray-400 text-sm">
                読み込み中...
              </div>
            ) : tasks.length === 0 ? (
              <div className="bg-white rounded-xl border border-dashed border-gray-300 p-12 text-center">
                <GanttChartSquare size={32} className="mx-auto text-gray-300 mb-3" />
                <p className="text-gray-400 text-sm">
                  タスクがありません。「タスク追加」から作業項目を登録してください。
                </p>
              </div>
            ) : (
              <GanttTable
                tasks={tasks}
                startMs={startMs}
                endMs={endMs}
                totalDays={totalDays}
                minDate={minDate}
                maxDate={maxDate}
                onEdit={startEditTask}
                onDelete={id => { if (confirm('削除しますか？')) deleteTaskMut.mutate(id) }}
              />
            )}
          </div>
        )}
      </div>
    </div>
  )
}

// ─── サブコンポーネント ─────────────────────────────────────────────────────

// ── 日付フィールド ──

interface DateFieldProps {
  label: string
  value: string
  undecided: boolean
  onChange: (v: string) => void
  onToggleUndecided: () => void
}

/**
 * 「未定」チェックボックス付き日付入力。
 * モジュールレベルで定義することで、親の再レンダリング時に
 * コンポーネントが再マウントされてフォーカスが失われる問題を防ぐ。
 */
function DateField({ label, value, undecided, onChange, onToggleUndecided }: DateFieldProps) {
  return (
    <div>
      <div className="flex items-center justify-between mb-1">
        <label className="text-xs text-gray-500">{label}</label>
        <label className="flex items-center gap-1 text-xs text-gray-400 cursor-pointer">
          <input type="checkbox" checked={undecided} onChange={onToggleUndecided} className="w-3 h-3" />
          未定
        </label>
      </div>
      {undecided ? (
        <div className="w-full px-2 py-1.5 border border-gray-200 rounded text-xs bg-gray-50 text-gray-400">
          未定
        </div>
      ) : (
        <input
          type="date"
          value={value}
          onChange={e => onChange(e.target.value)}
          className="w-full px-2 py-1.5 border border-gray-300 rounded text-xs"
        />
      )}
    </div>
  )
}

// ── プロジェクト作成/編集フォーム ──

interface ProjectFormProps {
  form: ProjectFormState
  setForm: React.Dispatch<React.SetStateAction<ProjectFormState>>
  employees: any[]
  onSubmit: () => void
  onCancel: () => void
  onTogglePrimary: (id: string) => void
  onToggleSecondary: (id: string) => void
  isPending?: boolean
  error?: any
  isEdit?: boolean
}

/** プロジェクトの新規作成・編集共通フォーム */
function ProjectForm({
  form, setForm, employees,
  onSubmit, onCancel,
  onTogglePrimary, onToggleSecondary,
  isPending, error, isEdit,
}: ProjectFormProps) {
  return (
    <div className="bg-white border border-blue-200 rounded-lg p-3 space-y-2">

      {/* 件番・プロジェクト名 */}
      <div className="grid grid-cols-2 gap-2">
        <div>
          <label className="text-xs text-gray-500 block mb-1">件番 *</label>
          <input
            value={form.code}
            onChange={e => setForm(f => ({ ...f, code: e.target.value }))}
            placeholder="PJ001"
            className="w-full px-2 py-1.5 border border-gray-300 rounded text-xs"
          />
        </div>
        <div>
          <label className="text-xs text-gray-500 block mb-1">プロジェクト名 *</label>
          <input
            value={form.name}
            onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
            placeholder="プロジェクト名"
            className="w-full px-2 py-1.5 border border-gray-300 rounded text-xs"
          />
        </div>
      </div>

      {/* 概要 */}
      <div>
        <label className="text-xs text-gray-500 block mb-1">概要</label>
        <textarea
          value={form.description}
          onChange={e => setForm(f => ({ ...f, description: e.target.value }))}
          placeholder="プロジェクトの概要・目的など"
          rows={2}
          className="w-full px-2 py-1.5 border border-gray-300 rounded text-xs resize-none"
        />
      </div>

      {/* 主管理者チェックボックス */}
      <div>
        <label className="text-xs text-gray-500 block mb-1">主管理者（複数選択可）</label>
        <div className="max-h-24 overflow-y-auto border border-gray-200 rounded p-1 space-y-0.5">
          {employees.length === 0 && (
            <p className="text-xs text-gray-400 px-1">読み込み中...</p>
          )}
          {employees.map((emp: any) => (
            <label key={emp.id} className="flex items-center gap-1.5 text-xs cursor-pointer hover:bg-gray-50 px-1 py-0.5 rounded">
              <input
                type="checkbox"
                checked={form.primary_manager_ids.includes(emp.id)}
                onChange={() => onTogglePrimary(emp.id)}
                className="w-3 h-3"
              />
              {emp.full_name}
            </label>
          ))}
        </div>
      </div>

      {/* 従管理者チェックボックス（主管理者に選択済みの社員は除外） */}
      <div>
        <label className="text-xs text-gray-500 block mb-1">従管理者（複数選択可）</label>
        <div className="max-h-24 overflow-y-auto border border-gray-200 rounded p-1 space-y-0.5">
          {employees
            .filter((emp: any) => !form.primary_manager_ids.includes(emp.id))
            .map((emp: any) => (
              <label key={emp.id} className="flex items-center gap-1.5 text-xs cursor-pointer hover:bg-gray-50 px-1 py-0.5 rounded">
                <input
                  type="checkbox"
                  checked={form.secondary_manager_ids.includes(emp.id)}
                  onChange={() => onToggleSecondary(emp.id)}
                  className="w-3 h-3"
                />
                {emp.full_name}
              </label>
            ))}
        </div>
      </div>

      {/* 開始日・終了日（未定チェックボックス付き） */}
      <div className="grid grid-cols-2 gap-2">
        <DateField
          label="開始日"
          value={form.start_date}
          undecided={form.start_undecided}
          onChange={v => setForm(f => ({ ...f, start_date: v }))}
          onToggleUndecided={() => setForm(f => ({ ...f, start_undecided: !f.start_undecided, start_date: '' }))}
        />
        <DateField
          label="終了日"
          value={form.end_date}
          undecided={form.end_undecided}
          onChange={v => setForm(f => ({ ...f, end_date: v }))}
          onToggleUndecided={() => setForm(f => ({ ...f, end_undecided: !f.end_undecided, end_date: '' }))}
        />
      </div>

      {/* API エラーメッセージ */}
      {error && (
        <p className="text-xs text-red-600 bg-red-50 px-2 py-1 rounded">
          {(error as any)?.response?.data?.code?.[0]
            ?? (error as any)?.response?.data?.name?.[0]
            ?? 'エラーが発生しました'}
        </p>
      )}

      {/* 送信・キャンセルボタン */}
      <div className="flex gap-1 pt-1">
        <button
          onClick={onSubmit}
          disabled={!form.code || !form.name || isPending}
          className="flex-1 py-1.5 bg-blue-600 text-white rounded text-xs disabled:opacity-50 font-medium"
        >
          {isPending ? '処理中...' : isEdit ? '更新' : '作成'}
        </button>
        <button
          onClick={onCancel}
          className="px-3 py-1.5 bg-gray-200 hover:bg-gray-300 rounded text-xs"
        >
          <X size={12} />
        </button>
      </div>
    </div>
  )
}

// ── タスク追加/編集フォーム ──

interface TaskFormProps {
  form: typeof BLANK_TASK_FORM
  setForm: React.Dispatch<React.SetStateAction<typeof BLANK_TASK_FORM>>
  employees: any[]
  editTask: ProjectTask | null
  onSubmit: () => void
  onCancel: () => void
}

/** タスクの新規追加・編集共通フォーム */
function TaskForm({ form, setForm, employees, editTask, onSubmit, onCancel }: TaskFormProps) {
  return (
    <div className="bg-white border border-blue-200 rounded-xl p-4">
      <h3 className="font-medium text-gray-700 mb-3 text-sm">
        {editTask ? 'タスク編集' : 'タスク追加'}
      </h3>
      <div className="grid grid-cols-3 gap-3">
        {/* タスク名（全幅） */}
        <div className="col-span-3">
          <label className="text-xs text-gray-500 block mb-1">タスク名 *</label>
          <input
            value={form.title}
            onChange={e => setForm(f => ({ ...f, title: e.target.value }))}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
            placeholder="タスク名を入力"
          />
        </div>
        {/* 担当者 */}
        <div>
          <label className="text-xs text-gray-500 block mb-1">担当者</label>
          <select
            value={form.assignee}
            onChange={e => setForm(f => ({ ...f, assignee: e.target.value }))}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
          >
            <option value="">未割当</option>
            {employees.map((emp: any) => (
              <option key={emp.id} value={emp.id}>{emp.full_name}</option>
            ))}
          </select>
        </div>
        {/* ステータス */}
        <div>
          <label className="text-xs text-gray-500 block mb-1">ステータス</label>
          <select
            value={form.status}
            onChange={e => setForm(f => ({ ...f, status: e.target.value }))}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
          >
            {Object.entries(STATUS_LABEL).map(([k, v]) => (
              <option key={k} value={k}>{v}</option>
            ))}
          </select>
        </div>
        {/* 進捗率スライダー */}
        <div>
          <label className="text-xs text-gray-500 block mb-1">進捗率 ({form.progress}%)</label>
          <input
            type="range"
            min={0} max={100}
            value={form.progress}
            onChange={e => setForm(f => ({ ...f, progress: Number(e.target.value) }))}
            className="w-full mt-2"
          />
        </div>
        {/* 開始予定日 */}
        <div>
          <label className="text-xs text-gray-500 block mb-1">開始予定日</label>
          <input
            type="date"
            value={form.start_date}
            onChange={e => setForm(f => ({ ...f, start_date: e.target.value }))}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
          />
        </div>
        {/* 終了予定日 */}
        <div>
          <label className="text-xs text-gray-500 block mb-1">終了予定日</label>
          <input
            type="date"
            value={form.end_date}
            onChange={e => setForm(f => ({ ...f, end_date: e.target.value }))}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
          />
        </div>
        {/* 詳細メモ */}
        <div>
          <label className="text-xs text-gray-500 block mb-1">詳細メモ</label>
          <input
            value={form.description}
            onChange={e => setForm(f => ({ ...f, description: e.target.value }))}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
          />
        </div>
      </div>
      <div className="flex gap-2 mt-3">
        <button
          disabled={!form.title}
          onClick={onSubmit}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white text-sm rounded-lg font-medium"
        >
          {editTask ? '更新' : '追加'}
        </button>
        <button
          onClick={onCancel}
          className="px-4 py-2 bg-gray-200 hover:bg-gray-300 text-gray-700 text-sm rounded-lg"
        >
          キャンセル
        </button>
      </div>
    </div>
  )
}

// ── ガントチャートテーブル ──

interface GanttTableProps {
  tasks: ProjectTask[]
  startMs: number
  endMs: number
  totalDays: number
  minDate: string
  maxDate: string
  onEdit: (task: ProjectTask) => void
  onDelete: (id: string) => void
}

/**
 * ガントチャートテーブル。
 * 各タスクの start/end を全体の日付範囲に対する % で表現し、
 * 絶対配置バーで期間を視覚化する。
 */
function GanttTable({ tasks, startMs, endMs, totalDays, minDate, maxDate, onEdit, onDelete }: GanttTableProps) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div className="overflow-x-auto">
        <table className="text-xs w-full min-w-[800px]">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="text-left px-4 py-3 font-medium text-gray-600 w-56">タスク名</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600 w-24">担当者</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600 w-20">ステータス</th>
              <th className="text-right px-4 py-3 font-medium text-gray-600 w-16">進捗</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600 w-24">期間</th>
              {/* ガントバーのヘッダーに開始・終了日を表示 */}
              <th className="px-4 py-3 font-medium text-gray-600 min-w-[280px]">
                <div className="flex justify-between text-gray-400 font-normal">
                  {minDate !== maxDate && (
                    <><span>{minDate}</span><span>{maxDate}</span></>
                  )}
                </div>
              </th>
              <th className="w-16" />
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {tasks.map(task => {
              // ガントバーの位置と幅を % で計算
              const taskStart = task.start_date ? new Date(task.start_date).getTime() : startMs
              const taskEnd   = task.end_date   ? new Date(task.end_date).getTime()   : taskStart
              const canCalc   = totalDays > 1 && startMs !== endMs
              const leftPct   = canCalc ? ((taskStart - startMs) / (endMs - startMs)) * 100 : 0
              const widthPct  = canCalc ? Math.max(3, ((taskEnd - taskStart) / (endMs - startMs)) * 100) : 100

              return (
                <tr key={task.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-4 py-3 font-medium text-gray-800">
                    <p className="truncate max-w-[13rem]">{task.title}</p>
                    {task.description && (
                      <p className="text-gray-400 text-xs truncate">{task.description}</p>
                    )}
                  </td>
                  <td className="px-4 py-3 text-gray-500 truncate">
                    {task.assignee_name ?? '—'}
                  </td>
                  <td className="px-4 py-3">
                    <span className={`text-xs font-medium ${STATUS_TEXT[task.status]}`}>
                      {STATUS_LABEL[task.status]}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <div className="flex items-center justify-end gap-1">
                      <div className="w-12 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                        <div
                          className={`h-full ${STATUS_COLOR[task.status]} rounded-full`}
                          style={{ width: `${task.progress}%` }}
                        />
                      </div>
                      <span className="text-gray-500 text-xs">{task.progress}%</span>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-gray-400 text-xs whitespace-nowrap">
                    {task.start_date
                      ? `${task.start_date.slice(5)} 〜 ${task.end_date?.slice(5) ?? '?'}`
                      : '—'}
                  </td>
                  {/* ガントバー: 絶対配置で left/width を % で指定 */}
                  <td className="px-4 py-3">
                    <div className="relative h-5 bg-gray-100 rounded">
                      {task.start_date && (
                        <div
                          className={`absolute h-full rounded ${STATUS_COLOR[task.status]} opacity-80`}
                          style={{
                            left:  `${Math.max(0, Math.min(100, leftPct))}%`,
                            width: `${Math.max(3, Math.min(100 - leftPct, widthPct))}%`,
                          }}
                          title={`${task.start_date} 〜 ${task.end_date ?? '?'}`}
                        />
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-right whitespace-nowrap">
                    <button
                      onClick={() => onEdit(task)}
                      className="p-1 text-gray-400 hover:text-blue-500 transition-colors"
                      title="編集"
                    >
                      <Pencil size={13} />
                    </button>
                    <button
                      onClick={() => onDelete(task.id)}
                      className="p-1 text-gray-400 hover:text-red-500 transition-colors"
                      title="削除"
                    >
                      <Trash2 size={13} />
                    </button>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
