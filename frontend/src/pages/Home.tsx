import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import { Material, Candidate, Experiment } from '../lib/types'
import { formatNumber, getPropertyColor } from '../lib/utils'
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'

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
      setChatResponse('Error connecting to AION. Make sure the backend is running.')
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

  return (
    <div className="p-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold gradient-text">AION Materials Discovery</h1>
        <p className="text-gray-400 mt-2">AI-powered platform for accelerated materials design and discovery</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-3 gap-6 mb-8">
        {[
          { label: 'Materials', value: stats.materials, icon: '⬡', color: 'from-indigo-500 to-purple-600' },
          { label: 'Experiments', value: stats.experiments, icon: '⚗', color: 'from-emerald-500 to-teal-600' },
          { label: 'Predictions', value: stats.predictions || 128, icon: '▦', color: 'from-amber-500 to-orange-600' },
        ].map((stat) => (
          <div key={stat.label} className="glass rounded-xl p-6 hover:border-indigo-500/30 transition-all duration-300">
            <div className="flex items-center justify-between mb-3">
              <p className="text-gray-400 text-sm font-medium">{stat.label}</p>
              <div className={`w-10 h-10 rounded-lg bg-gradient-to-br ${stat.color} flex items-center justify-center text-lg`}>
                {stat.icon}
              </div>
            </div>
            <p className="text-3xl font-bold">{stat.value}</p>
            <div className="mt-2 h-1 bg-gray-800 rounded-full overflow-hidden">
              <div className={`h-full bg-gradient-to-r ${stat.color} rounded-full`} style={{ width: `${Math.min(100, stat.value * 2)}%` }} />
            </div>
          </div>
        ))}
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-3 gap-6 mb-8">
        {/* Activity Chart */}
        <div className="col-span-2 glass rounded-xl p-6">
          <h2 className="text-lg font-semibold mb-4">Discovery Activity</h2>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={chartData}>
              <XAxis dataKey="name" stroke="#6b7280" fontSize={12} />
              <YAxis stroke="#6b7280" fontSize={12} />
              <Tooltip
                contentStyle={{ background: '#1f2937', border: '1px solid #374151', borderRadius: '8px' }}
                labelStyle={{ color: '#f9fafb' }}
              />
              <Line type="monotone" dataKey="materials" stroke="#818cf8" strokeWidth={2} dot={{ fill: '#818cf8' }} />
              <Line type="monotone" dataKey="predictions" stroke="#22c55e" strokeWidth={2} dot={{ fill: '#22c55e' }} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Quick Chat */}
        <div className="glass rounded-xl p-6 flex flex-col">
          <h2 className="text-lg font-semibold mb-4">Ask AION</h2>
          <div className="flex-1 min-h-0">
            {chatResponse && (
              <div className="glass-light rounded-lg p-3 mb-3 text-sm text-gray-300 max-h-32 overflow-y-auto fade-in">
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
                placeholder="Describe a material to discover..."
                className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500"
              />
              <button
                type="submit"
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 rounded-lg text-sm font-medium transition-colors"
              >
                Ask
              </button>
            </div>
          </form>
        </div>
      </div>

      {/* Recent Materials & Experiments */}
      <div className="grid grid-cols-2 gap-6">
        <div className="glass rounded-xl p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold">Recent Materials</h2>
            <button onClick={() => navigate('/materials')} className="text-xs text-indigo-400 hover:text-indigo-300">
              View all →
            </button>
          </div>
          <div className="space-y-2">
            {recentMaterials.length === 0 && loading && (
              <div className="shimmer h-24 rounded-lg" />
            )}
            {recentMaterials.length === 0 && !loading && (
              <p className="text-sm text-gray-500 py-8 text-center">No materials yet. Generate some!</p>
            )}
            {recentMaterials.map((m) => (
              <div
                key={m.id}
                onClick={() => navigate(`/materials`)}
                className="glass-light rounded-lg p-3 cursor-pointer hover:border-indigo-500/30 transition-all"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-mono text-sm font-medium" dangerouslySetInnerHTML={{ __html: m.formula }} />
                    <p className="text-xs text-gray-500 mt-0.5">{m.space_group || '—'}</p>
                  </div>
                  {m.properties?.band_gap && (
                    <span className="text-xs font-mono" style={{ color: getPropertyColor('band_gap') }}>
                      {formatNumber(m.properties.band_gap.value)} eV
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="glass rounded-xl p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold">Recent Experiments</h2>
            <button onClick={() => navigate('/experiments')} className="text-xs text-indigo-400 hover:text-indigo-300">
              View all →
            </button>
          </div>
          <div className="space-y-2">
            {recentExperiments.length === 0 && loading && (
              <div className="shimmer h-24 rounded-lg" />
            )}
            {recentExperiments.length === 0 && !loading && (
              <p className="text-sm text-gray-500 py-8 text-center">No experiments yet. Plan one!</p>
            )}
            {recentExperiments.map((e) => (
              <div key={e.id} className="glass-light rounded-lg p-3">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium">{e.name}</p>
                    <p className="text-xs text-gray-500 mt-0.5">{e.experiment_type}</p>
                  </div>
                  <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                    e.status === 'completed' ? 'bg-green-500/10 text-green-400' :
                    e.status === 'running' ? 'bg-blue-500/10 text-blue-400' :
                    e.status === 'failed' ? 'bg-red-500/10 text-red-400' :
                    'bg-yellow-500/10 text-yellow-400'
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
