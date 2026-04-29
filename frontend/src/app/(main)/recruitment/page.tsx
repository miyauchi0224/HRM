'use client'
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'
import { useAuthStore } from '@/lib/store'
import { UserPlus, Briefcase, ChevronDown, ChevronUp, Plus, CalendarDays, MapPin, DollarSign } from 'lucide-react'

interface JobPosting {
  id: string
  title: string
  department: string
  employment_type: string
  status: string
  open_date: string | null
  close_date: string | null
  candidate_count: number
  description: string
  requirements: string
  preferred: string
  salary_range: string
  location: string
}

interface Candidate {
  id: string
  full_name: string
  email: string
  status: string
  job_posting: string
  applied_at: string
  assigned_to_name: string | null
}

interface Interview {
  id: string
  candidate: string
  scheduled_at: string | null
  result: string | null
}

const JOB_STATUS: Record<string, string> = { draft: '下書き', open: '募集中', closed: '募集終了' }
const CANDIDATE_STATUS: Record<string, { label: string; color: string }> = {
  new: { label: '新規', color: 'bg-blue-100 text-blue-700' },
  screening: { label: '書類選考', color: 'bg-yellow-100 text-yellow-700' },
  interview1: { label: '一次面接', color: 'bg-orange-100 text-orange-700' },
  interview2: { label: '二次面接', color: 'bg-orange-100 text-orange-700' },
  final: { label: '最終面接', color: 'bg-purple-100 text-purple-700' },
  offer: { label: '内定', color: 'bg-green-100 text-green-700' },
  hired: { label: '入社', color: 'bg-green-100 text-green-800' },
  rejected: { label: '不採用', color: 'bg-red-100 text-red-600' },
  withdrawn: { label: '辞退', color: 'bg-gray-100 text-gray-500' },
}
const INTERVIEW_RESULT: Record<string, { label: string; color: string }> = {
  pass: { label: '合格', color: 'text-green-600' },
  fail: { label: '不合格', color: 'text-red-500' },
  pending: { label: '結果待ち', color: 'text-yellow-600' },
}
const EMP_TYPE: Record<string, string> = {
  full_time: '正社員', part_time: 'パートタイム', contract: '契約社員', intern: 'インターン'
}

// 求人詳細アコーディオンコンポーネント
function JobDetailAccordion({ job }: { job: JobPosting }) {
  const [open, setOpen] = useState(false)

  const hasDetails = job.description || job.requirements || job.preferred || job.salary_range || job.location || job.close_date

  if (!hasDetails) return null

  return (
    <div className="border rounded-xl overflow-hidden mb-4">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-4 py-3 bg-indigo-50 hover:bg-indigo-100 transition-colors"
      >
        <span className="text-sm font-semibold text-indigo-700">求人詳細情報</span>
        {open ? <ChevronUp size={16} className="text-indigo-600" /> : <ChevronDown size={16} className="text-indigo-600" />}
      </button>

      {open && (
        <div className="p-4 bg-white space-y-4 text-sm">
          {/* メタ情報バッジ行 */}
          <div className="flex flex-wrap gap-3">
            {job.status && (
              <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                job.status === 'open' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'
              }`}>
                {JOB_STATUS[job.status] ?? job.status}
              </span>
            )}
            {job.location && (
              <span className="flex items-center gap-1 text-xs text-gray-600">
                <MapPin size={12} className="text-gray-400" />
                {job.location}
              </span>
            )}
            {job.salary_range && (
              <span className="flex items-center gap-1 text-xs text-gray-600">
                <DollarSign size={12} className="text-gray-400" />
                {job.salary_range}
              </span>
            )}
            {job.close_date && (
              <span className="flex items-center gap-1 text-xs text-gray-600">
                <CalendarDays size={12} className="text-gray-400" />
                締切: {new Date(job.close_date).toLocaleDateString('ja-JP')}
              </span>
            )}
          </div>

          {job.description && (
            <div>
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">職務内容</p>
              <p className="text-gray-700 leading-relaxed whitespace-pre-line">{job.description}</p>
            </div>
          )}
          {job.requirements && (
            <div>
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">必須要件</p>
              <p className="text-gray-700 leading-relaxed whitespace-pre-line">{job.requirements}</p>
            </div>
          )}
          {job.preferred && (
            <div>
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">歓迎要件</p>
              <p className="text-gray-700 leading-relaxed whitespace-pre-line">{job.preferred}</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// 応募者行コンポーネント（面接情報付き）
function CandidateRow({
  candidate,
  onStatusChange,
}: {
  candidate: Candidate
  onStatusChange: (id: string, status: string) => void
}) {
  const { data: interviews = [] } = useQuery<Interview[]>({
    queryKey: ['interviews', candidate.id],
    queryFn: () =>
      api.get(`/api/v1/recruitment/interviews/?candidate=${candidate.id}`)
        .then((r) => r.data.results ?? r.data),
  })

  const cfg = CANDIDATE_STATUS[candidate.status] ?? { label: candidate.status, color: 'bg-gray-100 text-gray-600' }

  // 最新の面接情報を取得
  const latestInterview = interviews.length > 0
    ? interviews.sort((a, b) => {
        if (!a.scheduled_at) return 1
        if (!b.scheduled_at) return -1
        return new Date(b.scheduled_at).getTime() - new Date(a.scheduled_at).getTime()
      })[0]
    : null

  return (
    <tr className="hover:bg-gray-50">
      <td className="px-4 py-3 font-medium text-gray-800">{candidate.full_name}</td>
      <td className="px-4 py-3 text-gray-500 text-xs">{candidate.email}</td>
      <td className="px-4 py-3 text-center">
        <span className={`px-2 py-1 rounded-full text-xs ${cfg.color}`}>{cfg.label}</span>
      </td>
      <td className="px-4 py-3 text-xs text-gray-500">
        {latestInterview ? (
          <div>
            {latestInterview.scheduled_at && (
              <p>{new Date(latestInterview.scheduled_at).toLocaleDateString('ja-JP')}</p>
            )}
            {latestInterview.result && (
              <p className={`font-medium ${INTERVIEW_RESULT[latestInterview.result]?.color ?? 'text-gray-600'}`}>
                {INTERVIEW_RESULT[latestInterview.result]?.label ?? latestInterview.result}
              </p>
            )}
          </div>
        ) : (
          <span className="text-gray-300">—</span>
        )}
      </td>
      <td className="px-4 py-3 text-center">
        <select
          className="text-xs border rounded px-2 py-1"
          value={candidate.status}
          onChange={(e) => onStatusChange(candidate.id, e.target.value)}
        >
          {Object.entries(CANDIDATE_STATUS).map(([k, v]) => (
            <option key={k} value={k}>{v.label}</option>
          ))}
        </select>
      </td>
    </tr>
  )
}

export default function RecruitmentPage() {
  const user = useAuthStore((s) => s.user)
  const qc = useQueryClient()
  const [selectedJob, setSelectedJob] = useState<JobPosting | null>(null)
  const [showNewJob, setShowNewJob] = useState(false)
  const [jobForm, setJobForm] = useState({
    title: '',
    department: '',
    employment_type: 'full_time',
    status: 'open',
    description: '',
    requirements: '',
    preferred: '',
    salary_range: '',
    location: '',
  })

  const { data: jobs = [], isLoading } = useQuery<JobPosting[]>({
    queryKey: ['jobs'],
    queryFn: () => api.get('/api/v1/recruitment/jobs/').then((r) => r.data.results ?? r.data),
  })

  const { data: candidates = [] } = useQuery<Candidate[]>({
    queryKey: ['candidates', selectedJob?.id],
    queryFn: () =>
      selectedJob
        ? api.get(`/api/v1/recruitment/candidates/?job=${selectedJob.id}`).then((r) => r.data.results ?? r.data)
        : Promise.resolve([]),
    enabled: !!selectedJob,
  })

  const createJobMut = useMutation({
    mutationFn: (data: any) => api.post('/api/v1/recruitment/jobs/', data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['jobs'] })
      setShowNewJob(false)
      setJobForm({
        title: '', department: '', employment_type: 'full_time', status: 'open',
        description: '', requirements: '', preferred: '', salary_range: '', location: '',
      })
    },
  })

  const updateStatusMut = useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) =>
      api.patch(`/api/v1/recruitment/candidates/${id}/`, { status }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['candidates', selectedJob?.id] }),
  })

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <UserPlus className="text-indigo-600" size={28} />
          <div>
            <h1 className="text-2xl font-bold text-gray-800">採用管理</h1>
            <p className="text-sm text-gray-500">求人・応募者の管理</p>
          </div>
        </div>
        <button
          onClick={() => setShowNewJob(true)}
          className="flex items-center gap-2 bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 text-sm"
        >
          <Plus size={16} /> 求人作成
        </button>
      </div>

      <div className="grid grid-cols-3 gap-4 mb-6">
        {[
          { label: '求人数', value: jobs.length },
          { label: '募集中', value: jobs.filter((j) => j.status === 'open').length },
          { label: '総応募者', value: jobs.reduce((s, j) => s + j.candidate_count, 0) },
        ].map((item) => (
          <div key={item.label} className="bg-white rounded-xl border shadow-sm p-4 text-center">
            <p className="text-3xl font-bold text-gray-800">{item.value}</p>
            <p className="text-sm text-gray-500 mt-1">{item.label}</p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-5 gap-6">
        {/* 求人一覧 */}
        <div className="col-span-2 bg-white rounded-xl border shadow-sm overflow-hidden">
          <div className="px-4 py-3 border-b bg-gray-50">
            <h2 className="font-semibold text-gray-700 text-sm">求人一覧</h2>
          </div>
          {isLoading ? (
            <div className="p-6 text-center text-gray-400">読み込み中...</div>
          ) : (
            <div className="divide-y">
              {jobs.map((job) => (
                <button
                  key={job.id}
                  onClick={() => setSelectedJob(job)}
                  className={`w-full text-left px-4 py-3 hover:bg-gray-50 transition-colors ${
                    selectedJob?.id === job.id ? 'bg-indigo-50 border-l-4 border-indigo-500' : ''
                  }`}
                >
                  <div className="flex justify-between items-start">
                    <div>
                      <p className="font-medium text-gray-800 text-sm">{job.title}</p>
                      <p className="text-xs text-gray-500 mt-0.5">{job.department || '部署未設定'} ・ {EMP_TYPE[job.employment_type]}</p>
                      {job.location && <p className="text-xs text-gray-400 mt-0.5 flex items-center gap-1"><MapPin size={10} />{job.location}</p>}
                    </div>
                    <div className="text-right">
                      <span className={`text-xs px-2 py-0.5 rounded-full ${job.status === 'open' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
                        {JOB_STATUS[job.status]}
                      </span>
                      <p className="text-xs text-gray-400 mt-1">{job.candidate_count}名</p>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* 応募者エリア */}
        <div className="col-span-3">
          {!selectedJob ? (
            <div className="bg-white rounded-xl border shadow-sm p-12 text-center text-gray-400">
              <Briefcase size={36} className="mx-auto mb-2 opacity-30" />
              <p className="text-sm">左の求人を選択してください</p>
            </div>
          ) : (
            <>
              {/* 求人詳細アコーディオン */}
              <JobDetailAccordion job={selectedJob} />

              {/* 応募者一覧 */}
              <div className="bg-white rounded-xl border shadow-sm overflow-hidden">
                <div className="px-4 py-3 border-b bg-gray-50">
                  <h2 className="font-semibold text-gray-700 text-sm">
                    応募者: {selectedJob.title}（{candidates.length}名）
                  </h2>
                </div>
                {candidates.length === 0 ? (
                  <div className="p-12 text-center text-gray-400 text-sm">応募者がいません</div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead className="bg-gray-50 text-xs text-gray-500 uppercase">
                        <tr>
                          <th className="px-4 py-3 text-left">氏名</th>
                          <th className="px-4 py-3 text-left">メール</th>
                          <th className="px-4 py-3 text-center">ステータス</th>
                          <th className="px-4 py-3 text-center">面接情報</th>
                          <th className="px-4 py-3 text-center">変更</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-100">
                        {candidates.map((c) => (
                          <CandidateRow
                            key={c.id}
                            candidate={c}
                            onStatusChange={(id, status) => updateStatusMut.mutate({ id, status })}
                          />
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </>
          )}
        </div>
      </div>

      {/* 求人作成モーダル */}
      {showNewJob && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg p-6 max-h-[90vh] overflow-y-auto">
            <h2 className="text-lg font-bold text-gray-800 mb-4">求人作成</h2>
            <div className="space-y-3">
              {/* タイトル */}
              <input
                className="w-full border rounded-lg px-3 py-2 text-sm"
                placeholder="求人タイトル *"
                value={jobForm.title}
                onChange={(e) => setJobForm({ ...jobForm, title: e.target.value })}
              />

              {/* 部署・雇用形態 */}
              <div className="grid grid-cols-2 gap-3">
                <input
                  className="border rounded-lg px-3 py-2 text-sm"
                  placeholder="部署"
                  value={jobForm.department}
                  onChange={(e) => setJobForm({ ...jobForm, department: e.target.value })}
                />
                <select
                  className="border rounded-lg px-3 py-2 text-sm"
                  value={jobForm.employment_type}
                  onChange={(e) => setJobForm({ ...jobForm, employment_type: e.target.value })}
                >
                  {Object.entries(EMP_TYPE).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
                </select>
              </div>

              {/* ステータス・勤務地 */}
              <div className="grid grid-cols-2 gap-3">
                <select
                  className="border rounded-lg px-3 py-2 text-sm"
                  value={jobForm.status}
                  onChange={(e) => setJobForm({ ...jobForm, status: e.target.value })}
                >
                  {Object.entries(JOB_STATUS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
                </select>
                <input
                  className="border rounded-lg px-3 py-2 text-sm"
                  placeholder="勤務地（例: 東京・リモート）"
                  value={jobForm.location}
                  onChange={(e) => setJobForm({ ...jobForm, location: e.target.value })}
                />
              </div>

              {/* 給与レンジ */}
              <input
                className="w-full border rounded-lg px-3 py-2 text-sm"
                placeholder="給与レンジ（例: 400〜600万円）"
                value={jobForm.salary_range}
                onChange={(e) => setJobForm({ ...jobForm, salary_range: e.target.value })}
              />

              {/* 職務内容 */}
              <div>
                <label className="block text-xs font-medium text-gray-500 mb-1">職務内容 *</label>
                <textarea
                  className="w-full border rounded-lg px-3 py-2 text-sm h-24 resize-none"
                  placeholder="担当業務や役割を記入してください"
                  value={jobForm.description}
                  onChange={(e) => setJobForm({ ...jobForm, description: e.target.value })}
                />
              </div>

              {/* 必須要件 */}
              <div>
                <label className="block text-xs font-medium text-gray-500 mb-1">必須要件 *</label>
                <textarea
                  className="w-full border rounded-lg px-3 py-2 text-sm h-20 resize-none"
                  placeholder="応募に必要なスキル・経験を記入してください"
                  value={jobForm.requirements}
                  onChange={(e) => setJobForm({ ...jobForm, requirements: e.target.value })}
                />
              </div>

              {/* 歓迎要件 */}
              <div>
                <label className="block text-xs font-medium text-gray-500 mb-1">歓迎要件</label>
                <textarea
                  className="w-full border rounded-lg px-3 py-2 text-sm h-20 resize-none"
                  placeholder="あれば尚可なスキル・経験を記入してください"
                  value={jobForm.preferred}
                  onChange={(e) => setJobForm({ ...jobForm, preferred: e.target.value })}
                />
              </div>
            </div>

            <div className="flex gap-3 mt-4">
              <button onClick={() => setShowNewJob(false)} className="flex-1 border text-gray-700 py-2 rounded-lg text-sm">
                キャンセル
              </button>
              <button
                onClick={() => createJobMut.mutate(jobForm)}
                disabled={!jobForm.title || !jobForm.description || !jobForm.requirements || createJobMut.isPending}
                className="flex-1 bg-indigo-600 text-white py-2 rounded-lg text-sm hover:bg-indigo-700 disabled:opacity-50"
              >
                {createJobMut.isPending ? '作成中...' : '作成'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
