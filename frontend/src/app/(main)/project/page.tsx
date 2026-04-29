'use client'
import { useState, useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'
import { useAuthStore } from '@/lib/store'
import {
  GanttChartSquare, Plus, Pencil, Trash2, X, Check,
  Download, Upload, Users, Calendar,
} from 'lucide-react'

interface Project {
  id: string; code: string; name: string; description: string
  manager: string | null; manager_name: string | null
  sub_manager_ids: string[]; sub_manager_names: string[]
  is_active: boolean; start_date: string | null; end_date: string | null
  task_count: number
}

interface ProjectTask {
  id: string; project: string; title: string; description: string
  assignee: string | null; assignee_name: string | null
  status: string; status_label: string
  start_date: string | null; end_date: string | null
  progress: number; order: number
}

const STATUS_COLOR: Record<string, string> = {
  todo: 'bg-gray-300', in_progress: 'bg-blue-400', review: 'bg-yellow-400', done: 'bg-green-400',
}
const STATUS_LABEL: Record<string, string> = {
  todo: '未着手', in_progress: '進行中', review: 'レビュー中', done: '完了',
}
const STATUS_TEXT: Record<string, string> = {
  todo: 'text-gray-600', in_progress: 'text-blue-600', review: 'text-yellow-600', done: 'text-green-600',
}

const BLANK_PROJECT_FORM = { code: '', name: '', description: '', manager: '', sub_manager_ids: [] as string[], start_date: '', end_date: '', start_undecided: false, end_undecided: false }

export default function ProjectPage() {
  const qc = useQueryClient()
  const user = useAuthStore((s) => s.user)
  const isManager = user?.role && ['supervisor', 'manager', 'hr', 'accounting', 'admin'].includes(user.role)

  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [showNewProject, setShowNewProject] = useState(false)
  const [projectForm, setProjectForm] = useState(BLANK_PROJECT_FORM)
  const [editProjectId, setEditProjectId] = useState<string | null>(null)
  const [editProjectForm, setEditProjectForm] = useState(BLANK_PROJECT_FORM)
  const [showTaskForm, setShowTaskForm] = useState(false)
  const [editTask, setEditTask] = useState<ProjectTask | null>(null)
  const [taskForm, setTaskForm] = useState({ title: '', description: '', start_date: '', end_date: '', status: 'todo', progress: 0, assignee: '' })
  const importRef = useRef<HTMLInputElement>(null)
  const importProjectRef = useRef<HTMLInputElement>(null)

  // データ取得
  const { data: projects = [], isLoading: projectsLoading } = useQuery<Project[]>({
    queryKey: ['projects-all'],
    queryFn: () => api.get('/api/v1/attendance/projects/').then(r => r.data.results ?? r.data),
  })
  const { data: employees = [] } = useQuery<any[]>({
    queryKey: ['employees-mini'],
    queryFn: () => api.get('/api/v1/employees/').then(r => r.data.results ?? r.data),
  })
  const { data: ganttData, isLoading: ganttLoading } = useQuery<any>({
    queryKey: ['gantt', selectedId],
    queryFn: () => api.get(`/api/v1/attendance/projects/${selectedId}/gantt/`).then(r => r.data),
    enabled: !!selectedId,
  })

  const selectedProject: Project | undefined = projects.find(p => p.id === selectedId)
  const tasks: ProjectTask[] = ganttData?.tasks ?? []

  // ガントチャート日付範囲
  const allDates = tasks.flatMap(t => [t.start_date, t.end_date].filter(Boolean)) as string[]
  const minDate = allDates.length > 0 ? allDates.reduce((a, b) => a < b ? a : b) : new Date().toISOString().slice(0, 10)
  const maxDate = allDates.length > 0 ? allDates.reduce((a, b) => a > b ? a : b) : new Date().toISOString().slice(0, 10)
  const startMs = new Date(minDate).getTime()
  const endMs   = new Date(maxDate).getTime()
  const totalDays = Math.max(1, Math.ceil((endMs - startMs) / 86400000) + 1)

  // ミューテーション
  const createProjectMut = useMutation({
    mutationFn: (data: any) => api.post('/api/v1/attendance/projects/', data),
    onSuccess: (res) => {
      qc.invalidateQueries({ queryKey: ['projects-all'] })
      setSelectedId(res.data.id)
      setShowNewProject(false)
      setProjectForm(BLANK_PROJECT_FORM)
    },
  })
  const updateProjectMut = useMutation({
    mutationFn: ({ id, data }: any) => api.patch(`/api/v1/attendance/projects/${id}/`, data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['projects-all'] }); setEditProjectId(null) },
  })
  const createTaskMut = useMutation({
    mutationFn: (data: any) => api.post('/api/v1/attendance/project-tasks/', { ...data, project: selectedId }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['gantt', selectedId] }); setShowTaskForm(false); resetTaskForm() },
  })
  const updateTaskMut = useMutation({
    mutationFn: ({ id, data }: any) => api.patch(`/api/v1/attendance/project-tasks/${id}/`, data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['gantt', selectedId] }); setEditTask(null) },
  })
  const deleteTaskMut = useMutation({
    mutationFn: (id: string) => api.delete(`/api/v1/attendance/project-tasks/${id}/`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['gantt', selectedId] }),
  })
  const importTaskMut = useMutation({
    mutationFn: (fd: FormData) => api.post(`/api/v1/attendance/projects/${selectedId}/import-tasks/`, fd),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['gantt', selectedId] }),
  })
  const importProjectMut = useMutation({
    mutationFn: (fd: FormData) => api.post('/api/v1/attendance/projects/import-projects/', fd),
    onSuccess: (res) => {
      qc.invalidateQueries({ queryKey: ['projects-all'] })
      const { created, updated, errors } = res.data
      alert(`登録: ${created}件 / 更新: ${updated}件${errors?.length ? ` / エラー: ${errors.length}件` : ''}`)
    },
  })

  const resetTaskForm = () => setTaskForm({ title: '', description: '', start_date: '', end_date: '', status: 'todo', progress: 0, assignee: '' })
  const startEditTask = (t: ProjectTask) => {
    setEditTask(t)
    setTaskForm({ title: t.title, description: t.description, start_date: t.start_date ?? '', end_date: t.end_date ?? '', status: t.status, progress: t.progress, assignee: t.assignee ?? '' })
  }

  const startEditProject = (p: Project) => {
    setEditProjectId(p.id)
    setEditProjectForm({
      code: p.code, name: p.name, description: p.description,
      manager: p.manager ?? '', sub_manager_ids: p.sub_manager_ids ?? [],
      start_date: p.start_date ?? '', end_date: p.end_date ?? '',
      start_undecided: p.start_date === null,
      end_undecided: p.end_date === null,
    })
  }

  const saveEditProject = () => {
    if (!editProjectId) return
    updateProjectMut.mutate({
      id: editProjectId,
      data: {
        code: editProjectForm.code,
        name: editProjectForm.name,
        description: editProjectForm.description,
        manager: editProjectForm.manager || null,
        sub_manager_ids: editProjectForm.sub_manager_ids,
        start_date: editProjectForm.start_undecided ? null : (editProjectForm.start_date || null),
        end_date: editProjectForm.end_undecided ? null : (editProjectForm.end_date || null),
      },
    })
  }

  const handleSubManagerToggle = (empId: string, form: typeof BLANK_PROJECT_FORM, setForm: any) => {
    setForm((f: any) => ({
      ...f,
      sub_manager_ids: f.sub_manager_ids.includes(empId)
        ? f.sub_manager_ids.filter((id: string) => id !== empId)
        : [...f.sub_manager_ids, empId],
    }))
  }

  const downloadTaskTemplate = async () => {
    if (!selectedId) return
    const res = await api.get(`/api/v1/attendance/projects/${selectedId}/template-csv/`, { responseType: 'blob' })
    const url = URL.createObjectURL(res.data)
    const a = document.createElement('a'); a.href = url; a.download = 'tasks_template.csv'; a.click()
    URL.revokeObjectURL(url)
  }
  const downloadProjectTemplate = async () => {
    const res = await api.get('/api/v1/attendance/projects/projects-template-csv/', { responseType: 'blob' })
    const url = URL.createObjectURL(res.data)
    const a = document.createElement('a'); a.href = url; a.download = 'projects_template.csv'; a.click()
    URL.revokeObjectURL(url)
  }

  const doneCount = tasks.filter(t => t.status === 'done').length
  const progressOverall = tasks.length > 0 ? Math.round(doneCount / tasks.length * 100) : 0

  // フォーム部品
  const DateField = ({ label, value, undecided, onChange, onToggleUndecided }: any) => (
    <div>
      <div className="flex items-center justify-between mb-1">
        <label className="text-xs text-gray-500">{label}</label>
        <label className="flex items-center gap-1 text-xs text-gray-400 cursor-pointer">
          <input type="checkbox" checked={undecided} onChange={onToggleUndecided} className="w-3 h-3" />
          未定
        </label>
      </div>
      {undecided ? (
        <div className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm bg-gray-50 text-gray-400">未定</div>
      ) : (
        <input type="date" value={value} onChange={e => onChange(e.target.value)} className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm" />
      )}
    </div>
  )

  return (
    <div className="flex h-[calc(100vh-4rem)] overflow-hidden">
      {/* 左: プロジェクト一覧 */}
      <div className="w-80 flex-shrink-0 border-r border-gray-200 bg-white flex flex-col">
        <div className="p-4 border-b border-gray-200 space-y-2">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold text-gray-700 flex items-center gap-2">
              <GanttChartSquare size={18} className="text-blue-500" />
              プロジェクト管理
            </h2>
            {isManager && (
              <button onClick={() => setShowNewProject(v => !v)} className="p-1 text-blue-600 hover:bg-blue-50 rounded-lg">
                <Plus size={18} />
              </button>
            )}
          </div>

          {/* CSV一括登録ボタン */}
          {isManager && (
            <div className="flex gap-1">
              <button onClick={downloadProjectTemplate} className="flex-1 flex items-center justify-center gap-1 text-xs border border-gray-300 py-1.5 rounded hover:bg-gray-50 text-gray-600">
                <Download size={11} /> テンプレート
              </button>
              <button onClick={() => importProjectRef.current?.click()} className="flex-1 flex items-center justify-center gap-1 text-xs border border-blue-300 text-blue-600 py-1.5 rounded hover:bg-blue-50">
                <Upload size={11} /> CSV一括登録
              </button>
              <input ref={importProjectRef} type="file" accept=".csv" className="hidden"
                onChange={e => { const f = e.target.files?.[0]; if (f) { const fd = new FormData(); fd.append('file', f); importProjectMut.mutate(fd) } e.target.value = '' }} />
            </div>
          )}

          {/* 新規プロジェクトフォーム */}
          {showNewProject && (
            <ProjectForm
              form={projectForm}
              setForm={setProjectForm}
              employees={employees}
              onSubmit={() => createProjectMut.mutate({
                code: projectForm.code, name: projectForm.name,
                description: projectForm.description,
                manager: projectForm.manager || null,
                sub_manager_ids: projectForm.sub_manager_ids,
                start_date: projectForm.start_undecided ? null : (projectForm.start_date || null),
                end_date: projectForm.end_undecided ? null : (projectForm.end_date || null),
              })}
              onCancel={() => setShowNewProject(false)}
              onToggleSub={(id: string) => handleSubManagerToggle(id, projectForm, setProjectForm)}
              DateField={DateField}
            />
          )}
        </div>

        {/* プロジェクト一覧 */}
        <div className="flex-1 overflow-y-auto">
          {projectsLoading ? (
            <p className="text-xs text-gray-400 p-4">読み込み中...</p>
          ) : projects.length === 0 ? (
            <p className="text-xs text-gray-400 p-4 text-center">プロジェクトがありません</p>
          ) : projects.map(p => (
            <div key={p.id}>
              {editProjectId === p.id ? (
                /* インライン編集フォーム */
                <div className="p-3 bg-blue-50 border-b border-blue-200">
                  <ProjectForm
                    form={editProjectForm}
                    setForm={setEditProjectForm}
                    employees={employees}
                    onSubmit={saveEditProject}
                    onCancel={() => setEditProjectId(null)}
                    onToggleSub={(id: string) => handleSubManagerToggle(id, editProjectForm, setEditProjectForm)}
                    DateField={DateField}
                    isEdit
                  />
                </div>
              ) : (
                <button
                  key={p.id}
                  onClick={() => setSelectedId(p.id)}
                  onDoubleClick={(e) => { e.preventDefault(); startEditProject(p) }}
                  title="ダブルクリックで編集"
                  className={`w-full text-left p-3 border-b border-gray-100 hover:bg-gray-50 transition-colors ${selectedId === p.id ? 'bg-blue-50 border-l-2 border-l-blue-500' : ''}`}
                >
                  <div className="flex items-center justify-between mb-0.5">
                    <span className="text-xs font-medium text-blue-600">{p.code}</span>
                    <span className="text-xs text-gray-400">{p.task_count}タスク</span>
                  </div>
                  <p className="text-sm font-medium text-gray-800 truncate">{p.name}</p>
                  <div className="text-xs text-gray-400 mt-0.5 space-y-0.5">
                    {p.manager_name && <p className="flex items-center gap-1"><Users size={10} /> {p.manager_name}（主）{p.sub_manager_names?.length > 0 && ` / ${p.sub_manager_names.join('・')}（従）`}</p>}
                    <p className="flex items-center gap-1">
                      <Calendar size={10} />
                      {p.start_date ?? '未定'} 〜 {p.end_date ?? '未定'}
                    </p>
                  </div>
                </button>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* 右: ガントチャート + タスク管理 */}
      <div className="flex-1 overflow-auto bg-gray-50">
        {!selectedId ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center text-gray-400">
              <GanttChartSquare size={48} className="mx-auto mb-3 opacity-30" />
              <p>プロジェクトを選択してください</p>
              <p className="text-xs mt-1">一覧行をダブルクリックで編集</p>
            </div>
          </div>
        ) : (
          <div className="p-6 space-y-4">
            {/* プロジェクトヘッダー */}
            {selectedProject && (
              <div className="bg-white rounded-xl border border-gray-200 p-4">
                <div className="flex items-start justify-between">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-sm font-medium text-blue-600 bg-blue-50 px-2 py-0.5 rounded">{selectedProject.code}</span>
                      <h1 className="text-lg font-bold text-gray-800">{selectedProject.name}</h1>
                    </div>
                    {selectedProject.description && <p className="text-sm text-gray-500 mb-2">{selectedProject.description}</p>}
                    <div className="flex items-center gap-4 text-xs text-gray-400">
                      {selectedProject.manager_name && (
                        <span className="flex items-center gap-1">
                          <Users size={12} />
                          主：{selectedProject.manager_name}
                          {selectedProject.sub_manager_names?.length > 0 && ` / 従：${selectedProject.sub_manager_names.join('・')}`}
                        </span>
                      )}
                      <span className="flex items-center gap-1">
                        <Calendar size={12} />
                        {selectedProject.start_date ?? '開始未定'} 〜 {selectedProject.end_date ?? '終了未定'}
                      </span>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-2xl font-bold text-blue-600">{progressOverall}%</p>
                    <p className="text-xs text-gray-400">{doneCount}/{tasks.length} 完了</p>
                  </div>
                </div>
                {tasks.length > 0 && (
                  <div className="mt-3">
                    <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
                      <div className="h-full bg-blue-500 rounded-full transition-all" style={{ width: `${progressOverall}%` }} />
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* ツールバー */}
            <div className="flex items-center gap-2 flex-wrap">
              <button onClick={() => setShowTaskForm(true)} className="flex items-center gap-1.5 bg-blue-600 hover:bg-blue-700 text-white px-3 py-1.5 rounded-lg text-sm font-medium">
                <Plus size={14} /> タスク追加
              </button>
              <button onClick={downloadTaskTemplate} className="flex items-center gap-1.5 border border-gray-300 text-gray-600 px-3 py-1.5 rounded-lg text-sm hover:bg-gray-50">
                <Download size={14} /> タスクテンプレート
              </button>
              <button onClick={() => importRef.current?.click()} className="flex items-center gap-1.5 border border-blue-300 text-blue-600 px-3 py-1.5 rounded-lg text-sm hover:bg-blue-50">
                <Upload size={14} /> タスクCSV登録
              </button>
              <input ref={importRef} type="file" accept=".csv" className="hidden"
                onChange={e => {
                  const f = e.target.files?.[0]
                  if (f) { const fd = new FormData(); fd.append('file', f); importTaskMut.mutate(fd) }
                  e.target.value = ''
                }} />
            </div>

            {/* タスク追加/編集フォーム */}
            {(showTaskForm || editTask) && (
              <div className="bg-white border border-blue-200 rounded-xl p-4">
                <h3 className="font-medium text-gray-700 mb-3 text-sm">{editTask ? 'タスク編集' : 'タスク追加'}</h3>
                <div className="grid grid-cols-3 gap-3">
                  <div className="col-span-3">
                    <label className="text-xs text-gray-500 block mb-1">タスク名 *</label>
                    <input value={taskForm.title} onChange={e => setTaskForm(f => ({...f, title: e.target.value}))} className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm" placeholder="タスク名を入力" />
                  </div>
                  <div>
                    <label className="text-xs text-gray-500 block mb-1">担当者</label>
                    <select value={taskForm.assignee} onChange={e => setTaskForm(f => ({...f, assignee: e.target.value}))} className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm">
                      <option value="">未割当</option>
                      {employees.map((emp: any) => <option key={emp.id} value={emp.id}>{emp.full_name}</option>)}
                    </select>
                  </div>
                  <div>
                    <label className="text-xs text-gray-500 block mb-1">ステータス</label>
                    <select value={taskForm.status} onChange={e => setTaskForm(f => ({...f, status: e.target.value}))} className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm">
                      {Object.entries(STATUS_LABEL).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
                    </select>
                  </div>
                  <div>
                    <label className="text-xs text-gray-500 block mb-1">進捗率 ({taskForm.progress}%)</label>
                    <input type="range" min={0} max={100} value={taskForm.progress} onChange={e => setTaskForm(f => ({...f, progress: Number(e.target.value)}))} className="w-full mt-2" />
                  </div>
                  <div>
                    <label className="text-xs text-gray-500 block mb-1">開始予定日</label>
                    <input type="date" value={taskForm.start_date} onChange={e => setTaskForm(f => ({...f, start_date: e.target.value}))} className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm" />
                  </div>
                  <div>
                    <label className="text-xs text-gray-500 block mb-1">終了予定日</label>
                    <input type="date" value={taskForm.end_date} onChange={e => setTaskForm(f => ({...f, end_date: e.target.value}))} className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm" />
                  </div>
                  <div>
                    <label className="text-xs text-gray-500 block mb-1">詳細メモ</label>
                    <input value={taskForm.description} onChange={e => setTaskForm(f => ({...f, description: e.target.value}))} className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm" />
                  </div>
                </div>
                <div className="flex gap-2 mt-3">
                  <button
                    disabled={!taskForm.title}
                    onClick={() => {
                      const payload = { title: taskForm.title, description: taskForm.description, start_date: taskForm.start_date || null, end_date: taskForm.end_date || null, status: taskForm.status, progress: taskForm.progress, assignee: taskForm.assignee || null }
                      editTask ? updateTaskMut.mutate({ id: editTask.id, data: payload }) : createTaskMut.mutate(payload)
                    }}
                    className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white text-sm rounded-lg font-medium"
                  >
                    {editTask ? '更新' : '追加'}
                  </button>
                  <button onClick={() => { setShowTaskForm(false); setEditTask(null); resetTaskForm() }} className="px-4 py-2 bg-gray-200 hover:bg-gray-300 text-gray-700 text-sm rounded-lg">キャンセル</button>
                </div>
              </div>
            )}

            {/* ガントチャート */}
            {ganttLoading ? (
              <div className="bg-white rounded-xl border border-gray-200 p-8 text-center text-gray-400 text-sm">読み込み中...</div>
            ) : tasks.length === 0 ? (
              <div className="bg-white rounded-xl border border-dashed border-gray-300 p-12 text-center">
                <GanttChartSquare size={32} className="mx-auto text-gray-300 mb-3" />
                <p className="text-gray-400 text-sm">タスクがありません。「タスク追加」から作業項目を登録してください。</p>
              </div>
            ) : (
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
                        <th className="px-4 py-3 font-medium text-gray-600 min-w-[280px]">
                          <div className="flex justify-between text-gray-400 font-normal">{minDate !== maxDate && (<><span>{minDate}</span><span>{maxDate}</span></>)}</div>
                        </th>
                        <th className="w-16" />
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                      {tasks.map(task => {
                        const taskStart = task.start_date ? new Date(task.start_date).getTime() : startMs
                        const taskEnd   = task.end_date   ? new Date(task.end_date).getTime()   : taskStart
                        const leftPct   = totalDays > 1 && startMs !== endMs ? ((taskStart - startMs) / (endMs - startMs)) * 100 : 0
                        const widthPct  = totalDays > 1 && startMs !== endMs ? Math.max(3, ((taskEnd - taskStart) / (endMs - startMs)) * 100) : 100
                        return (
                          <tr key={task.id} className="hover:bg-gray-50 transition-colors">
                            <td className="px-4 py-3 font-medium text-gray-800">
                              <p className="truncate max-w-[13rem]">{task.title}</p>
                              {task.description && <p className="text-gray-400 text-xs truncate">{task.description}</p>}
                            </td>
                            <td className="px-4 py-3 text-gray-500 truncate">{task.assignee_name ?? '—'}</td>
                            <td className="px-4 py-3">
                              <span className={`text-xs font-medium ${STATUS_TEXT[task.status]}`}>{STATUS_LABEL[task.status]}</span>
                            </td>
                            <td className="px-4 py-3 text-right">
                              <div className="flex items-center justify-end gap-1">
                                <div className="w-12 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                                  <div className={`h-full ${STATUS_COLOR[task.status]} rounded-full`} style={{ width: `${task.progress}%` }} />
                                </div>
                                <span className="text-gray-500 text-xs">{task.progress}%</span>
                              </div>
                            </td>
                            <td className="px-4 py-3 text-gray-400 text-xs whitespace-nowrap">
                              {task.start_date ? `${task.start_date.slice(5)} 〜 ${task.end_date?.slice(5) ?? '?'}` : '—'}
                            </td>
                            <td className="px-4 py-3">
                              <div className="relative h-5 bg-gray-100 rounded">
                                {task.start_date && (
                                  <div
                                    className={`absolute h-full rounded ${STATUS_COLOR[task.status]} opacity-80`}
                                    style={{ left: `${Math.max(0, Math.min(100, leftPct))}%`, width: `${Math.max(3, Math.min(100 - leftPct, widthPct))}%` }}
                                    title={`${task.start_date} 〜 ${task.end_date ?? '?'}`}
                                  />
                                )}
                              </div>
                            </td>
                            <td className="px-4 py-3 text-right whitespace-nowrap">
                              <button onClick={() => startEditTask(task)} className="p-1 text-gray-400 hover:text-blue-500 transition-colors"><Pencil size={13} /></button>
                              <button onClick={() => { if (confirm('削除しますか？')) deleteTaskMut.mutate(task.id) }} className="p-1 text-gray-400 hover:text-red-500 transition-colors"><Trash2 size={13} /></button>
                            </td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

// ===== プロジェクト作成/編集フォーム =====
function ProjectForm({ form, setForm, employees, onSubmit, onCancel, onToggleSub, DateField, isEdit }: any) {
  return (
    <div className="bg-white border border-blue-200 rounded-lg p-3 space-y-2">
      <div className="grid grid-cols-2 gap-2">
        <div>
          <label className="text-xs text-gray-500 block mb-1">件番 *</label>
          <input value={form.code} onChange={e => setForm((f: any) => ({...f, code: e.target.value}))} placeholder="PJ001" className="w-full px-2 py-1.5 border border-gray-300 rounded text-xs" />
        </div>
        <div>
          <label className="text-xs text-gray-500 block mb-1">プロジェクト名 *</label>
          <input value={form.name} onChange={e => setForm((f: any) => ({...f, name: e.target.value}))} placeholder="プロジェクト名" className="w-full px-2 py-1.5 border border-gray-300 rounded text-xs" />
        </div>
      </div>
      <div>
        <label className="text-xs text-gray-500 block mb-1">主管理者</label>
        <select value={form.manager} onChange={e => setForm((f: any) => ({...f, manager: e.target.value}))} className="w-full px-2 py-1.5 border border-gray-300 rounded text-xs">
          <option value="">未設定</option>
          {employees.map((emp: any) => <option key={emp.id} value={emp.id}>{emp.full_name}</option>)}
        </select>
      </div>
      <div>
        <label className="text-xs text-gray-500 block mb-1">従管理者（複数選択可）</label>
        <div className="max-h-24 overflow-y-auto border border-gray-200 rounded p-1 space-y-0.5">
          {employees.filter((emp: any) => emp.id !== form.manager).map((emp: any) => (
            <label key={emp.id} className="flex items-center gap-1.5 text-xs cursor-pointer hover:bg-gray-50 px-1 py-0.5 rounded">
              <input
                type="checkbox"
                checked={form.sub_manager_ids.includes(emp.id)}
                onChange={() => onToggleSub(emp.id)}
                className="w-3 h-3"
              />
              {emp.full_name}
            </label>
          ))}
        </div>
      </div>
      <div className="grid grid-cols-2 gap-2">
        <DateField
          label="開始日"
          value={form.start_date}
          undecided={form.start_undecided}
          onChange={(v: string) => setForm((f: any) => ({...f, start_date: v}))}
          onToggleUndecided={() => setForm((f: any) => ({...f, start_undecided: !f.start_undecided, start_date: ''}))}
        />
        <DateField
          label="終了日"
          value={form.end_date}
          undecided={form.end_undecided}
          onChange={(v: string) => setForm((f: any) => ({...f, end_date: v}))}
          onToggleUndecided={() => setForm((f: any) => ({...f, end_undecided: !f.end_undecided, end_date: ''}))}
        />
      </div>
      <div className="flex gap-1">
        <button
          onClick={onSubmit}
          disabled={!form.code || !form.name}
          className="flex-1 py-1.5 bg-blue-600 text-white rounded text-xs disabled:bg-blue-300 font-medium"
        >
          {isEdit ? '更新' : '作成'}
        </button>
        <button onClick={onCancel} className="px-3 py-1.5 bg-gray-200 rounded text-xs"><X size={12} /></button>
      </div>
    </div>
  )
}
