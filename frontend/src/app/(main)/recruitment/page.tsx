'use client'
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'
import { useAuthStore } from '@/lib/store'
import { UserPlus, Briefcase, ChevronRight, Plus } from 'lucide-react'

interface JobPosting {
  id: string; title: string; department: string; employment_type: string
  status: string; open_date: string | null; close_date: string | null; candidate_count: number
}
interface Candidate {
  id: string; full_name: string; email: string; status: string
  job_posting: string; applied_at: string; assigned_to_name: string | null
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
const EMP_TYPE: Record<string, string> = {
  full_time: '正社員', part_time: 'パートタイム', contract: '契約社員', intern: 'インターン'
}

export default function RecruitmentPage() {
  const user = useAuthStore((s) => s.user)
  const qc = useQueryClient()
  const [selectedJob, setSelectedJob] = useState<JobPosting | null>(null)
  const [showNewJob, setShowNewJob] = useState(false)
  const [jobForm, setJobForm] = useState({
    title: '', department: '', employment_type: 'full_time', description: '', requirements: ''
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
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['jobs'] }); setShowNewJob(false) },
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

        {/* 応募者一覧 */}
        <div className="col-span-3 bg-white rounded-xl border shadow-sm overflow-hidden">
          <div className="px-4 py-3 border-b bg-gray-50">
            <h2 className="font-semibold text-gray-700 text-sm">
              {selectedJob ? `応募者: ${selectedJob.title}` : '求人を選択してください'}
            </h2>
          </div>
          {!selectedJob ? (
            <div className="p-12 text-center text-gray-400">
              <Briefcase size={36} className="mx-auto mb-2 opacity-30" />
              <p className="text-sm">左の求人を選択してください</p>
            </div>
          ) : candidates.length === 0 ? (
            <div className="p-12 text-center text-gray-400 text-sm">応募者がいません</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 text-xs text-gray-500 uppercase">
                  <tr>
                    <th className="px-4 py-3 text-left">氏名</th>
                    <th className="px-4 py-3 text-left">メール</th>
                    <th className="px-4 py-3 text-center">選考ステータス</th>
                    <th className="px-4 py-3 text-center">変更</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {candidates.map((c) => {
                    const cfg = CANDIDATE_STATUS[c.status] ?? { label: c.status, color: 'bg-gray-100 text-gray-600' }
                    return (
                      <tr key={c.id} className="hover:bg-gray-50">
                        <td className="px-4 py-3 font-medium text-gray-800">{c.full_name}</td>
                        <td className="px-4 py-3 text-gray-500">{c.email}</td>
                        <td className="px-4 py-3 text-center">
                          <span className={`px-2 py-1 rounded-full text-xs ${cfg.color}`}>{cfg.label}</span>
                        </td>
                        <td className="px-4 py-3 text-center">
                          <select
                            className="text-xs border rounded px-2 py-1"
                            value={c.status}
                            onChange={(e) => updateStatusMut.mutate({ id: c.id, status: e.target.value })}
                          >
                            {Object.entries(CANDIDATE_STATUS).map(([k, v]) => (
                              <option key={k} value={k}>{v.label}</option>
                            ))}
                          </select>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* 求人作成モーダル */}
      {showNewJob && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg p-6">
            <h2 className="text-lg font-bold text-gray-800 mb-4">求人作成</h2>
            <div className="space-y-3">
              <input
                className="w-full border rounded-lg px-3 py-2 text-sm"
                placeholder="求人タイトル *"
                value={jobForm.title}
                onChange={(e) => setJobForm({ ...jobForm, title: e.target.value })}
              />
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
              <textarea
                className="w-full border rounded-lg px-3 py-2 text-sm h-24 resize-none"
                placeholder="仕事内容 *"
                value={jobForm.description}
                onChange={(e) => setJobForm({ ...jobForm, description: e.target.value })}
              />
              <textarea
                className="w-full border rounded-lg px-3 py-2 text-sm h-20 resize-none"
                placeholder="応募要件 *"
                value={jobForm.requirements}
                onChange={(e) => setJobForm({ ...jobForm, requirements: e.target.value })}
              />
            </div>
            <div className="flex gap-3 mt-4">
              <button onClick={() => setShowNewJob(false)} className="flex-1 border text-gray-700 py-2 rounded-lg text-sm">キャンセル</button>
              <button
                onClick={() => createJobMut.mutate(jobForm)}
                disabled={!jobForm.title || !jobForm.description || !jobForm.requirements}
                className="flex-1 bg-indigo-600 text-white py-2 rounded-lg text-sm hover:bg-indigo-700 disabled:opacity-50"
              >作成</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
