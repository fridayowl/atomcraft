import { useState } from 'react'
import { api } from '../api/client'
import { formatNumber } from '../lib/utils'
import CrystalViewer from '../components/CrystalViewer'
import {
  Beaker,
  Search,
  Filter,
  Atom,
  Ruler,
  FlaskConical,
  Layers,
  ChevronDown,
  ChevronRight,
  Award,
  AlertTriangle,
  Battery,
  Cpu,
  Zap,
} from 'lucide-react'

interface DiscoverCandidate {
  rank: number
  formula: string
  elements: string[]
  space_group: string
  crystal_system: string
  lattice_parameters: Record<string, number>
  predictions: {
    band_gap: number
    formation_energy: number
    density: number
  }
  synthesis: {
    feasibility_score: number
    recommended_methods: { method: string; difficulty: string }[]
    risks: string[]
  }
  battery: Record<string, { score: number; assessment: string }> | null
  xrd: { num_peaks: number; peaks: { two_theta: number; intensity: number }[] } | null
  overall_score: number
}

export function Discover() {
  const [elements, setElements] = useState('Li, Co, O')
  const [numCandidates, setNumCandidates] = useState(50)
  const [topK, setTopK] = useState(10)
  const [application, setApplication] = useState('battery')
  const [bgMin, setBgMin] = useState('')
  const [bgMax, setBgMax] = useState('')
  const [feMax, setFeMax] = useState('')
  const [loading, setLoading] = useState(false)
  const [candidates, setCandidates] = useState<DiscoverCandidate[]>([])
  const [totalGen, setTotalGen] = useState(0)
  const [expandedIdx, setExpandedIdx] = useState<number | null>(null)

  async function handleDiscover() {
    setLoading(true)
    setCandidates([])
    try {
      const constraints: Record<string, number> = {}
      if (bgMin) constraints.band_gap_min = parseFloat(bgMin)
      if (bgMax) constraints.band_gap_max = parseFloat(bgMax)
      if (feMax) constraints.formation_energy_max = parseFloat(feMax)

      const res = await fetch('/api/discover/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          elements: elements.split(',').map(e => e.trim()).filter(Boolean),
          num_candidates: numCandidates,
          top_k: topK,
          application: application || undefined,
          constraints: Object.keys(constraints).length ? constraints : undefined,
        }),
      })
      const data = await res.json()
      setCandidates(data.candidates || [])
      setTotalGen(data.total_generated || 0)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  function getApplicationLabel(app: string | null) {
    if (!app) return ''
    return { battery: 'Battery', solar: 'Solar', thermoelectric: 'Thermoelectric' }[app] || app
  }

  function structureFromCandidate(c: DiscoverCandidate) {
    const atoms = c.elements.map((el, i) => ({
      element: el,
      x: 0.5,
      y: 0.5,
      z: 0.5 + (i - (c.elements.length - 1) / 2) * 0.15,
    }))
    return {
      atoms,
      lattice: {
        a: c.lattice_parameters.a || 5,
        b: c.lattice_parameters.b || 5,
        c: c.lattice_parameters.c || 5,
      },
    }
  }

  return (
    <div className="p-6 h-full">
      <div className="mb-6">
        <h1 className="text-2xl font-semibold text-gray-900">Discover Materials</h1>
        <p className="text-sm text-gray-400 mt-1">Generate, predict, screen, and rank novel materials in one pipeline</p>
      </div>

      <div className="flex gap-6 h-[calc(100%-5rem)]">
        <div className="w-72 shrink-0 bg-white rounded-xl border border-gray-100 shadow-sm p-5 space-y-4 overflow-y-auto scrollbar-thin">
          <div>
            <label className="text-xs font-medium text-gray-500 uppercase tracking-wider flex items-center gap-1">
              <Atom className="w-3 h-3" /> Elements
            </label>
            <input
              className="w-full mt-1 px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-400"
              value={elements}
              onChange={e => setElements(e.target.value)}
              placeholder="Li, Co, O, ..."
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">Generate</label>
              <input
                type="number"
                className="w-full mt-1 px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-400"
                value={numCandidates}
                onChange={e => setNumCandidates(Number(e.target.value))}
                min={10}
                max={500}
              />
            </div>
            <div>
              <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">Show Top</label>
              <input
                type="number"
                className="w-full mt-1 px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-400"
                value={topK}
                onChange={e => setTopK(Number(e.target.value))}
                min={1}
                max={50}
              />
            </div>
          </div>

          <div>
            <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">Application</label>
            <select
              className="w-full mt-1 px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-400"
              value={application}
              onChange={e => setApplication(e.target.value)}
            >
              <option value="">None</option>
              <option value="battery">Battery</option>
            </select>
          </div>

          <div>
            <label className="text-xs font-medium text-gray-500 uppercase tracking-wider flex items-center gap-1">
              <Filter className="w-3 h-3" /> Constraints
            </label>
            <div className="mt-1 space-y-2">
              <div className="flex gap-2">
                <input
                  placeholder="Band gap min"
                  className="w-1/2 px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-400"
                  value={bgMin}
                  onChange={e => setBgMin(e.target.value)}
                />
                <input
                  placeholder="Band gap max"
                  className="w-1/2 px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-400"
                  value={bgMax}
                  onChange={e => setBgMax(e.target.value)}
                />
              </div>
              <input
                placeholder="Formation energy max (eV/atom)"
                className="w-full px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-400"
                value={feMax}
                onChange={e => setFeMax(e.target.value)}
              />
            </div>
          </div>

          <button
            onClick={handleDiscover}
            disabled={loading}
            className="w-full py-3 rounded-xl font-semibold text-sm bg-blue-500 hover:bg-blue-600 text-white disabled:opacity-50 transition-all flex items-center justify-center gap-2"
          >
            <Search className="w-4 h-4" />
            {loading ? 'Running pipeline...' : 'Discover'}
          </button>
        </div>

        <div className="flex-1 overflow-y-auto scrollbar-thin">
          {loading && (
            <div className="flex items-center justify-center h-64">
              <div className="flex gap-2">
                <div className="w-3 h-3 rounded-full bg-blue-400 animate-bounce" style={{ animationDelay: '0ms' }} />
                <div className="w-3 h-3 rounded-full bg-blue-400 animate-bounce" style={{ animationDelay: '150ms' }} />
                <div className="w-3 h-3 rounded-full bg-blue-400 animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          )}

          {!loading && candidates.length === 0 && (
            <div className="flex flex-col items-center justify-center h-64 text-gray-400">
              <Beaker className="w-8 h-8 mb-3 text-gray-300" />
              <p className="text-sm">Set constraints and click Discover to find novel materials</p>
            </div>
          )}

          {!loading && candidates.length > 0 && (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <p className="text-sm text-gray-500">
                  Generated <span className="text-blue-600 font-semibold">{totalGen}</span> candidates, showing top <span className="text-blue-600 font-semibold">{candidates.length}</span>
                  {application && <span className="ml-2">· screened for <span className="text-purple-600">{getApplicationLabel(application)}</span></span>}
                </p>
              </div>

              {candidates.map((c, idx) => (
                <div
                  key={c.formula}
                  className="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden hover:border-gray-200 transition-all"
                >
                  <button
                    onClick={() => setExpandedIdx(expandedIdx === idx ? null : idx)}
                    className="w-full flex items-center gap-4 p-4 text-left"
                  >
                    <div className="w-8 h-8 rounded-lg bg-blue-50 border border-blue-100 flex items-center justify-center text-sm font-semibold text-blue-600 shrink-0">
                      {c.rank}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="font-semibold text-sm text-gray-900">{c.formula}</div>
                      <div className="text-xs text-gray-400 mt-0.5">
                        {c.crystal_system} · {c.space_group} · {c.elements.join(', ')}
                      </div>
                    </div>
                    <div className="flex items-center gap-4 text-xs">
                      <div className="text-center">
                        <div className="font-medium text-gray-900">{c.predictions.band_gap.toFixed(2)}</div>
                        <div className="text-gray-400">Band gap</div>
                      </div>
                      <div className="text-center">
                        <div className={c.predictions.formation_energy < 0 ? 'text-green-600' : 'text-red-600'}>
                          {c.predictions.formation_energy.toFixed(2)}
                        </div>
                        <div className="text-gray-400">Form. E</div>
                      </div>
                      <div className="text-center">
                        <div className={c.synthesis.feasibility_score > 0.6 ? 'text-green-600' : 'text-orange-500'}>
                          {(c.synthesis.feasibility_score * 100).toFixed(0)}
                        </div>
                        <div className="text-gray-400">Synth</div>
                      </div>
                      <div className="text-center">
                        <div className="text-blue-600 font-semibold">{(c.overall_score * 100).toFixed(0)}</div>
                        <div className="text-gray-400">Score</div>
                      </div>
                    </div>
                    <span className="text-gray-300">
                      {expandedIdx === idx ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                    </span>
                  </button>

                  {expandedIdx === idx && (
                    <div className="border-t border-gray-100 p-4 grid grid-cols-2 gap-4 text-sm">
                      <div className="bg-gray-50 rounded-lg p-3">
                        <div className="text-xs text-gray-500 uppercase tracking-wider mb-2">Predictions</div>
                        <div className="space-y-2">
                          {Object.entries(c.predictions).map(([k, v]) => (
                            <div key={k} className="flex justify-between">
                              <span className="text-gray-400 capitalize">{k.replace(/_/g, ' ')}</span>
                              <span className="font-mono text-gray-700">{typeof v === 'number' ? v.toFixed(3) : v}</span>
                            </div>
                          ))}
                        </div>
                      </div>

                      <div className="bg-gray-50 rounded-lg p-3">
                        <div className="text-xs text-gray-500 uppercase tracking-wider mb-2">Lattice</div>
                        <div className="space-y-2">
                          {Object.entries(c.lattice_parameters).map(([k, v]) => (
                            <div key={k} className="flex justify-between">
                              <span className="text-gray-400">{k}</span>
                              <span className="font-mono text-gray-700">{typeof v === 'number' ? v.toFixed(3) : v}</span>
                            </div>
                          ))}
                        </div>
                      </div>

                      <div className="bg-gray-50 rounded-lg p-3">
                        <div className="text-xs text-gray-500 uppercase tracking-wider mb-2">Synthesis</div>
                        <div className="mb-2">
                          <span className="font-medium text-gray-700">Score:</span> {(c.synthesis.feasibility_score * 100).toFixed(0)}%
                        </div>
                        {c.synthesis.recommended_methods.length > 0 && (
                          <div className="mb-2">
                            <span className="text-gray-400">Methods:</span>
                            <div className="flex flex-wrap gap-1 mt-1">
                              {c.synthesis.recommended_methods.map((m: any) => (
                                <span key={m.method} className="px-2 py-0.5 rounded bg-white border border-gray-100 text-xs text-gray-500">
                                  {m.method} ({m.difficulty})
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                        {c.synthesis.risks.length > 0 && (
                          <div>
                            <span className="text-gray-400">Risks:</span>
                            <ul className="list-disc list-inside text-xs text-gray-500 mt-1">
                              {c.synthesis.risks.map((r, i) => <li key={i}>{r}</li>)}
                            </ul>
                          </div>
                        )}
                      </div>

                      <div className="bg-gray-50 rounded-lg p-3">
                        <div className="text-xs text-gray-500 uppercase tracking-wider mb-2">Battery</div>
                        {c.battery ? (
                          <div className="space-y-2">
                            {Object.entries(c.battery).map(([app, info]: [string, any]) => (
                              <div key={app} className="flex justify-between items-center">
                                <span className="text-gray-400 capitalize">{app}</span>
                                <div className="text-right">
                                  <div className="font-medium text-gray-700">{(info.score * 100).toFixed(0)}%</div>
                                  <div className="text-xs text-gray-400">{info.assessment}</div>
                                </div>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <p className="text-gray-400 text-xs">Not assessed</p>
                        )}
                      </div>

                      <div className="bg-gray-50 rounded-lg p-3 col-span-2">
                        <div className="flex items-center justify-between mb-3">
                          <div className="text-xs text-gray-500 uppercase tracking-wider">Structure</div>
                          {c.xrd && (
                            <span className="text-xs text-gray-400">{c.xrd.num_peaks} XRD peaks simulated</span>
                          )}
                        </div>
                        <div className="h-48 rounded-lg overflow-hidden bg-white">
                          <CrystalViewer structure={structureFromCandidate(c)} />
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
