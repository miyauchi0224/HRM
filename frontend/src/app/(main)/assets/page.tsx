'use client'
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'
import { useAuthStore } from '@/lib/store'
import { Package, Plus, ArrowRightLeft } from 'lucide-react'

interface Asset {
  id: string; asset_number: string; name: string; category_name: string | null
  serial_number: string; model: string; manufacturer: string
  status: string; condition: string; assigned_to_name: string | null
  assigned_at: string | null; purchase_date: string | null; purchase_price: number | null
  warranty_expiry: string | null; location: string; note: string
}

const STATUS_CONFIG: Record<string, { label: string; color: string }> = {
  available: { label: '利用可能', color: 'bg-green-100 text-green-700' },
  in_use: { label: '使用中', color: 'bg-blue-100 text-blue-700' },
  maintenance: { label: '修理中', color: 'bg-yellow-100 text-yellow-700' },
  disposed: { label: '廃棄済', color: 'bg-gray-100 text-gray-500' },
}

export default function AssetsPage() {
  const user = useAuthStore((s) => s.user)
  const qc = useQueryClient()
  const [showNew, setShowNew] = useState(false)
  const [assignTarget, setAssignTarget] = useState<Asset | null>(null)
  const [empId, setEmpId] = useState('')
  const [form, setForm] = useState({
    asset_number: '', name: '', serial_number: '', model: '',
    manufacturer: '', location: '', purchase_price: '', note: ''
  })

  const { data: assets = [], isLoading } = useQuery<Asset[]>({
    queryKey: ['assets'],
    queryFn: () => api.get('/api/v1/assets/items/').then((r) => r.data.results ?? r.data),
  })

  const { data: employees = [] } = useQuery({
    queryKey: ['employees-mini'],
    queryFn: () => api.get('/api/v1/employees/').then((r) => r.data.results ?? r.data),
  })

  const createMut = useMutation({
    mutationFn: (data: any) => api.post('/api/v1/assets/items/', data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['assets'] }); setShowNew(false) },
  })

  const assignMut = useMutation({
    mutationFn: ({ id, employee_id }: any) =>
      api.post(`/api/v1/assets/items/${id}/assign/`, { employee_id }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['assets'] }); setAssignTarget(null) },
  })

  const returnMut = useMutation({
    mutationFn: (id: string) => api.post(`/api/v1/assets/items/${id}/return/`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['assets'] }),
  })

  const totalValue = assets.reduce((s, a) => s + (a.purchase_price ?? 0), 0)

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <Package className="text-indigo-600" size={28} />
          <div>
            <h1 className="text-2xl font-bold text-gray-800">資産管理</h1>
            <p className="text-sm text-gray-500">PC・スマホ・備品などの台帳管理</p>
          </div>
        </div>
        {user?.role && ['hr', 'admin'].includes(user.role) && (
          <button
            onClick={() => setShowNew(true)}
            className="flex items-center gap-2 bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 text-sm"
          >
            <Plus size={16} /> 資産登録
          </button>
        )}
      </div>

      <div className="grid grid-cols-4 gap-4 mb-6">
        {[
          { label: '総資産数', value: assets.length, suffix: '件' },
          { label: '使用中', value: assets.filter((a) => a.status === 'in_use').length, suffix: '件' },
          { label: '利用可能', value: assets.filter((a) => a.status === 'available').length, suffix: '件' },
          { label: '資産総額', value: `¥${totalValue.toLocaleString()}`, suffix: '' },
        ].map((item) => (
          <div key={item.label} className="bg-white rounded-xl border shadow-sm p-4 text-center">
            <p className="text-2xl font-bold text-gray-800">{item.value}{item.suffix}</p>
            <p className="text-sm text-gray-500 mt-1">{item.label}</p>
          </div>
        ))}
      </div>

      <div className="bg-white rounded-xl border shadow-sm overflow-hidden">
        {isLoading ? (
          <div className="p-8 text-center text-gray-400">読み込み中...</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 text-xs text-gray-500 uppercase">
                <tr>
                  <th className="px-4 py-3 text-left">資産番号</th>
                  <th className="px-4 py-3 text-left">資産名</th>
                  <th className="px-4 py-3 text-left">型番</th>
                  <th className="px-4 py-3 text-center">ステータス</th>
                  <th className="px-4 py-3 text-left">使用者</th>
                  <th className="px-4 py-3 text-right">購入金額</th>
                  <th className="px-4 py-3 text-center">操作</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {assets.map((asset) => {
                  const cfg = STATUS_CONFIG[asset.status] ?? { label: asset.status, color: 'bg-gray-100 text-gray-600' }
                  return (
                    <tr key={asset.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3 font-mono text-xs text-gray-600">{asset.asset_number}</td>
                      <td className="px-4 py-3 font-medium text-gray-800">{asset.name}</td>
                      <td className="px-4 py-3 text-gray-500 text-xs">{asset.model || '-'}</td>
                      <td className="px-4 py-3 text-center">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${cfg.color}`}>{cfg.label}</span>
                      </td>
                      <td className="px-4 py-3 text-gray-600">{asset.assigned_to_name || '-'}</td>
                      <td className="px-4 py-3 text-right text-gray-700">
                        {asset.purchase_price ? `¥${asset.purchase_price.toLocaleString()}` : '-'}
                      </td>
                      <td className="px-4 py-3 text-center">
                        {user?.role && ['hr', 'admin'].includes(user.role) && (
                          <div className="flex items-center justify-center gap-1">
                            {asset.status === 'available' && (
                              <button
                                onClick={() => setAssignTarget(asset)}
                                className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded hover:bg-blue-200"
                              >貸出</button>
                            )}
                            {asset.status === 'in_use' && (
                              <button
                                onClick={() => returnMut.mutate(asset.id)}
                                className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded hover:bg-gray-200"
                              >返却</button>
                            )}
                          </div>
                        )}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* 資産登録モーダル */}
      {showNew && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg p-6">
            <h2 className="text-lg font-bold text-gray-800 mb-4">資産登録</h2>
            <div className="grid grid-cols-2 gap-3">
              <input className="border rounded-lg px-3 py-2 text-sm" placeholder="資産番号 *" value={form.asset_number} onChange={(e) => setForm({ ...form, asset_number: e.target.value })} />
              <input className="border rounded-lg px-3 py-2 text-sm" placeholder="資産名 *" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
              <input className="border rounded-lg px-3 py-2 text-sm" placeholder="型番" value={form.model} onChange={(e) => setForm({ ...form, model: e.target.value })} />
              <input className="border rounded-lg px-3 py-2 text-sm" placeholder="メーカー" value={form.manufacturer} onChange={(e) => setForm({ ...form, manufacturer: e.target.value })} />
              <input className="border rounded-lg px-3 py-2 text-sm" placeholder="シリアル番号" value={form.serial_number} onChange={(e) => setForm({ ...form, serial_number: e.target.value })} />
              <input type="number" className="border rounded-lg px-3 py-2 text-sm" placeholder="購入金額（円）" value={form.purchase_price} onChange={(e) => setForm({ ...form, purchase_price: e.target.value })} />
              <input className="border rounded-lg px-3 py-2 text-sm col-span-2" placeholder="保管場所" value={form.location} onChange={(e) => setForm({ ...form, location: e.target.value })} />
              <textarea className="border rounded-lg px-3 py-2 text-sm col-span-2 resize-none h-16" placeholder="備考" value={form.note} onChange={(e) => setForm({ ...form, note: e.target.value })} />
            </div>
            <div className="flex gap-3 mt-4">
              <button onClick={() => setShowNew(false)} className="flex-1 border text-gray-700 py-2 rounded-lg text-sm">キャンセル</button>
              <button
                onClick={() => createMut.mutate({ ...form, purchase_price: form.purchase_price || null })}
                disabled={!form.asset_number || !form.name}
                className="flex-1 bg-indigo-600 text-white py-2 rounded-lg text-sm hover:bg-indigo-700 disabled:opacity-50"
              >登録</button>
            </div>
          </div>
        </div>
      )}

      {/* 貸出モーダル */}
      {assignTarget && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-sm p-6">
            <h2 className="text-lg font-bold text-gray-800 mb-1">貸出: {assignTarget.name}</h2>
            <p className="text-sm text-gray-500 mb-4">貸出先の社員を選択してください</p>
            <select
              className="w-full border rounded-lg px-3 py-2 text-sm mb-4"
              value={empId}
              onChange={(e) => setEmpId(e.target.value)}
            >
              <option value="">社員を選択</option>
              {employees.map((e: any) => (
                <option key={e.id} value={e.id}>{e.full_name}</option>
              ))}
            </select>
            <div className="flex gap-3">
              <button onClick={() => setAssignTarget(null)} className="flex-1 border text-gray-700 py-2 rounded-lg text-sm">キャンセル</button>
              <button
                onClick={() => assignMut.mutate({ id: assignTarget.id, employee_id: empId })}
                disabled={!empId}
                className="flex-1 bg-indigo-600 text-white py-2 rounded-lg text-sm hover:bg-indigo-700 disabled:opacity-50"
              >貸出</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
