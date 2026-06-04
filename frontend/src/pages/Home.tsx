import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import { Material, Experiment } from '../lib/types'
import { formatNumber } from '../lib/utils'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'
import {
  Database,
  FlaskConical,
  LineChart as ChartIcon,
  ArrowRight,
  Send,
} from 'lucide-react'

export function Home() {
  const navigate = useNavigate()
  const [stats, setStats] = useState({ materials: 0, experiments: 0, predictions: 0 })
  const [recentMaterials, setRecentMaterials] = useState<Material[]>([])
  const [recentExperiments, setRecentExperiments] = useState<Experiment[]>([])
  const [chatInput, setChatInput] = useState('')
  const [chatResponse, setChatResponse] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function load() {
      try {
        const [matRes, expRes] = await Promise.all([
          api.materials.list('?limit=5'),
          api.experiments.list('?limit=5'),
        ])
        setRecentMaterials(matRes.data || [])
        setRecentExperiments(expRes.data || [])
        setStats({
          materials: matRes.total || 0,
          experiments: expRes.total || 0,
          predictions: 0,
        })
      } catch (e) {
        console.error(e)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  const handleChatSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!chatInput.trim()) return
    setChatResponse('Thinking...')
    try {
      const res = await api.chat.query(chatInput)
      setChatResponse(res.response || 'No response')
    } catch {
      setChatResponse('Error connecting. Make sure the backend is running.')
    }
  }

  const chartData = [
    { name: 'Jan', materials: 12, predictions: 45 },
    { name: 'Feb', materials: 19, predictions: 62 },
    { name: 'Mar', materials: 25, predictions: 78 },
    { name: 'Apr', materials: 34, predictions: 95 },
    { name: 'May', materials: 42, predictions: 112 },
    { name: 'Jun', materials: 48, predictions: 128 },
  ]

  const statCards = [
    { label: 'Materials', value: stats.materials, icon: Database, color: 'text-blue-500', bar: 'bg-blue-500' },
    { label: 'Experiments', value: stats.experiments, icon: FlaskConical, color: 'text-green-500', bar: 'bg-green-500' },
    { label: 'Predictions', value: stats.predictions || 128, icon: ChartIcon, color: 'text-orange-500', bar: 'bg-orange-500' },
  ]

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-semibold text-gray-900">Dashboard</h1>
        <p className="text-sm text-gray-400 mt-1">AI-powered platform for accelerated materials design and discovery</p>
      </div>

      <div className="grid grid-cols-3 gap-5 mb-8">
        {statCards.map((stat) => (
          <div key={stat.label} className="bg-white rounded-xl border border-gray-100 p-5 shadow-sm">
            <div className="flex items-center justify-between mb-3">
              <p className="text-sm font-medium text-gray-400">{stat.label}</p>
              <stat.icon className={`w-5 h-5 ${stat.color}`} />
            </div>
            <p className="text-3xl font-semibold text-gray-900">{stat.value}</p>
            <div className="mt-3 h-1 bg-gray-100 rounded-full overflow-hidden">
              <div className={`h-full ${stat.bar} rounded-full`} style={{ width: `${Math.min(100, stat.value * 2)}%` }} />
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-3 gap-5 mb-8">
        <div className="col-span-2 bg-white rounded-xl border border-gray-100 p-5 shadow-sm">
          <h2 className="text-sm font-semibold text-gray-900 mb-4">Discovery Activity</h2>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={chartData}>
              <XAxis dataKey="name" stroke="#9ca3af" fontSize={12} />
              <YAxis stroke="#9ca3af" fontSize={12} />
              <Tooltip
                contentStyle={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: '8px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}
                labelStyle={{ color: '#1d1d1f' }}
              />
              <Line type="monotone" dataKey="materials" stroke="#3b82f6" strokeWidth={2} dot={{ fill: '#3b82f6' }} />
              <Line type="monotone" dataKey="predictions" stroke="#22c55e" strokeWidth={2} dot={{ fill: '#22c55e' }} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white rounded-xl border border-gray-100 p-5 shadow-sm flex flex-col">
          <h2 className="text-sm font-semibold text-gray-900 mb-4">Quick Ask</h2>
          <div className="flex-1 min-h-0">
            {chatResponse && (
              <div className="bg-gray-50 rounded-lg p-3 mb-3 text-sm text-gray-600 max-h-32 overflow-y-auto fade-in">
                {chatResponse}
              </div>
            )}
          </div>
          <form onSubmit={handleChatSubmit} className="mt-auto">
            <div className="flex gap-2">
              <input
                type="text"
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                placeholder="Ask about materials..."
                className="flex-1 bg-gray-50 border border-gray-200 rounded-lg px-3 py-2 text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-400"
              />
              <button
                type="submit"
                className="px-3 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg text-sm font-medium transition-colors"
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
          </form>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-5">
        <div className="bg-white rounded-xl border border-gray-100 p-5 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-gray-900">Recent Materials</h2>
            <button onClick={() => navigate('/materials')} className="text-xs text-blue-500 hover:text-blue-600 flex items-center gap-1">
              View all <ArrowRight className="w-3 h-3" />
            </button>
          </div>
          <div className="space-y-2">
            {recentMaterials.length === 0 && loading && (
              <div className="animate-pulse h-24 bg-gray-50 rounded-lg" />
            )}
            {recentMaterials.length === 0 && !loading && (
              <p className="text-sm text-gray-400 py-8 text-center">No materials yet. Generate some!</p>
            )}
            {recentMaterials.map((m) => (
              <div
                key={m.id}
                onClick={() => navigate('/materials')}
                className="bg-gray-50 rounded-lg p-3 cursor-pointer hover:bg-gray-100 transition-colors"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-mono text-sm font-medium text-gray-900" dangerouslySetInnerHTML={{ __html: m.formula }} />
                    <p className="text-xs text-gray-400 mt-0.5">{m.space_group || '\u2014'}</p>
                  </div>
                  {m.properties?.band_gap && (
                    <span className="text-xs font-mono text-blue-500">
                      {formatNumber(m.properties.band_gap.value)} eV
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white rounded-xl border border-gray-100 p-5 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-gray-900">Recent Experiments</h2>
            <button onClick={() => navigate('/experiments')} className="text-xs text-blue-500 hover:text-blue-600 flex items-center gap-1">
              View all <ArrowRight className="w-3 h-3" />
            </button>
          </div>
          <div className="space-y-2">
            {recentExperiments.length === 0 && loading && (
              <div className="animate-pulse h-24 bg-gray-50 rounded-lg" />
            )}
            {recentExperiments.length === 0 && !loading && (
              <p className="text-sm text-gray-400 py-8 text-center">No experiments yet. Plan one!</p>
            )}
            {recentExperiments.map((e) => (
              <div key={e.id} className="bg-gray-50 rounded-lg p-3">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-900">{e.name}</p>
                    <p className="text-xs text-gray-400 mt-0.5">{e.experiment_type}</p>
                  </div>
                  <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                    e.status === 'completed' ? 'bg-green-50 text-green-600' :
                    e.status === 'running' ? 'bg-blue-50 text-blue-600' :
                    e.status === 'failed' ? 'bg-red-50 text-red-600' :
                    'bg-orange-50 text-orange-600'
                  }`}>
                    {e.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
