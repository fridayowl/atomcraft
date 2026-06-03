import { useState, useEffect } from 'react'
import { api } from '../api/client'
import { Experiment, ExperimentDesign } from '../lib/types'
import { formatNumber, getStatusColor } from '../lib/utils'

export function Experiments() {
  const [experiments, setExperiments] = useState<Experiment[]>([])
  const [loading, setLoading] = useState(true)
  const [selected, setSelected] = useState<Experiment | null>(null)
  const [showDesigner, setShowDesigner] = useState(false)
  const [designFormula, setDesignFormula] = useState('')
  const [designMethod, setDesignMethod] = useState('solid_state')
  const [designedExperiment, setDesignedExperiment] = useState<ExperimentDesign | null>(null)

  useEffect(() => {
    loadExperiments()
  }, [])

  async function loadExperiments() {
    try {
      const res = await api.experiments.list('?limit=50')
      setExperiments(res.data || [])
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  async function loadDetail(id: number) {
    try {
      const res = await api.experiments.get(id)
      setSelected(res)
    } catch (e) {
      console.error(e)
    }
  }

  async function handleDesignExperiment() {
    if (!designFormula.trim()) return
    try {
      const res = await api.synthesis.designExperiment(designFormula, designMethod)
      setDesignedExperiment(res)
    } catch (e) {
      console.error(e)
    }
  }

  async function handleCreateFromDesign() {
    if (!designedExperiment) return
    try {
      const res = await api.experiments.create({
        material_id: 0,
        name: `Synthesis of ${designedExperiment.formula} (${designedExperiment.method})`,
        experiment_type: 'synthesis',
        description: `Auto-designed experiment for ${designedExperiment.formula} via ${designedExperiment.method}`,
        synthesis_method: designedExperiment.method,
        synthesis_conditions: designedExperiment.parameters,
      })
      setShowDesigner(false)
      setDesignedExperiment(null)
      setDesignFormula('')
      loadExperiments()
    } catch (e) {
      console.error(e)
    }
  }

  async function handleUpdateStatus(id: number, status: string, successful?: boolean) {
    try {
      await api.experiments.updateStatus(id, status, successful)
      loadDetail(id)
      loadExperiments()
    } catch (e) {
      console.error(e)
    }
  }

  const methods = [
    { id: 'solid_state', label: 'Solid State' },
    { id: 'sol_gel', label: 'Sol-Gel' },
    { id: 'hydrothermal', label: 'Hydrothermal' },
    { id: 'cvd', label: 'CVD' },
    { id: 'mechanochemical', label: 'Mechanochemical' },
  ]

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold gradient-text">Experiments</h1>
          <p className="text-sm text-gray-400 mt-1">Plan, track, and learn from synthesis experiments</p>
        </div>
        <button
          onClick={() => setShowDesigner(!showDesigner)}
          className="px-4 py-2 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 rounded-lg text-sm font-medium transition-all"
        >
          {showDesigner ? 'Close Designer' : 'Design Experiment'}
        </button>
      </div>

      {/* Experiment Designer */}
      {showDesigner && (
        <div className="glass rounded-xl p-6 mb-8 fade-in">
          <h2 className="text-lg font-semibold mb-4">Experiment Designer</h2>
          <div className="flex gap-3 mb-4">
            <input
              type="text"
              value={designFormula}
              onChange={(e) => setDesignFormula(e.target.value)}
              placeholder="Formula (e.g., LiCoO2)"
              className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500 font-mono"
            />
            <select
              value={designMethod}
              onChange={(e) => setDesignMethod(e.target.value)}
              className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
            >
              {methods.map((m) => (
                <option key={m.id} value={m.id}>{m.label}</option>
              ))}
            </select>
            <button
              onClick={handleDesignExperiment}
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 rounded-lg text-sm font-medium transition-colors"
            >
              Design
            </button>
          </div>

          {designedExperiment && (
            <div className="glass-light rounded-lg p-4 fade-in">
              <h3 className="font-semibold text-sm mb-3">{designedExperiment.formula} — {designedExperiment.method}</h3>
              <div className="grid grid-cols-2 gap-6">
                <div>
                  <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Parameters</h4>
                  <div className="space-y-1 text-sm">
                    {Object.entries(designedExperiment.parameters).map(([k, v]) => (
                      <div key={k} className="flex justify-between">
                        <span className="text-gray-400 capitalize">{k.replace(/_/g, ' ')}</span>
                        <span className="font-mono">{String(v)}</span>
                      </div>
                    ))}
                  </div>
                </div>
                <div>
                  <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Steps</h4>
                  <div className="space-y-1 text-sm">
                    {designedExperiment.steps.map((s) => (
                      <p key={s.step} className="text-gray-400">
                        <span className="text-gray-600">{s.step}.</span> {s.action}
                      </p>
                    ))}
                  </div>
                </div>
              </div>
              <div className="flex items-center justify-between mt-4 pt-3 border-t border-gray-800">
                <div className="flex gap-4 text-xs text-gray-500">
                  <span>Characterization: {designedExperiment.characterization.join(', ')}</span>
                  <span>Est. time: {designedExperiment.estimated_total_time_hours}h</span>
                  <span>Est. cost: ${designedExperiment.estimated_cost_usd}</span>
                </div>
                <button
                  onClick={handleCreateFromDesign}
                  className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 rounded-lg text-sm font-medium transition-colors"
                >
                  Create Experiment
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* List & Detail */}
      <div className="grid grid-cols-3 gap-6">
        <div className="col-span-1 glass rounded-xl p-4 max-h-[65vh] overflow-y-auto scrollbar-thin">
          {loading ? (
            <div className="shimmer h-64 rounded-lg" />
          ) : experiments.length === 0 ? (
            <p className="text-sm text-gray-500 py-8 text-center">No experiments yet</p>
          ) : (
            <div className="space-y-1">
              {experiments.map((e) => (
                <div
                  key={e.id}
                  onClick={() => loadDetail(e.id)}
                  className={`p-3 rounded-lg cursor-pointer transition-all ${
                    selected?.id === e.id ? 'bg-indigo-500/10 border border-indigo-500/20' : 'hover:bg-white/5'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <p className="text-sm font-medium truncate mr-2">{e.name}</p>
                    <span className="shrink-0 px-2 py-0.5 rounded text-[10px] font-medium"
                      style={{ background: `${getStatusColor(e.status)}15`, color: getStatusColor(e.status) }}>
                      {e.status}
                    </span>
                  </div>
                   <p className="text-xs text-gray-500">{e.experiment_type} · {(e as any).step_count || 0} steps</p>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="col-span-2 glass rounded-xl p-6 min-h-[400px]">
          {!selected ? (
            <div className="flex items-center justify-center h-full text-gray-500 text-sm">
              Select an experiment to view details
            </div>
          ) : (
            <div className="fade-in">
              <div className="flex items-start justify-between mb-6">
                <div>
                  <h2 className="text-xl font-bold">{selected.name}</h2>
                  <p className="text-sm text-gray-400 mt-1">{selected.experiment_type} · {selected.synthesis_method || 'N/A'}</p>
                </div>
                <div className="flex gap-2">
                  {selected.status === 'planned' && (
                    <button onClick={() => handleUpdateStatus(selected.id, 'running')} className="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 rounded-lg text-xs transition-colors">
                      Start
                    </button>
                  )}
                  {selected.status === 'running' && (
                    <>
                      <button onClick={() => handleUpdateStatus(selected.id, 'completed', true)} className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 rounded-lg text-xs transition-colors">
                        Complete ✓
                      </button>
                      <button onClick={() => handleUpdateStatus(selected.id, 'failed', false)} className="px-3 py-1.5 bg-red-600 hover:bg-red-500 rounded-lg text-xs transition-colors">
                        Failed ✗
                      </button>
                    </>
                  )}
                </div>
              </div>

              {selected.description && (
                <p className="text-sm text-gray-400 mb-6">{selected.description}</p>
              )}

              <div className="grid grid-cols-2 gap-6">
                {/* Steps */}
                <div className="glass-light rounded-lg p-4">
                  <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Steps</h3>
                  {selected.steps.length === 0 ? (
                    <p className="text-xs text-gray-600">No steps recorded</p>
                  ) : (
                    <div className="space-y-3">
                      {selected.steps.map((s) => (
                        <div key={s.id} className="flex items-start gap-3">
                          <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium shrink-0 ${
                            s.completed ? 'bg-emerald-500/20 text-emerald-400' : 'bg-gray-800 text-gray-500'
                          }`}>
                            {s.step_number}
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="text-sm">{s.description}</p>
                            <div className="flex gap-2 text-xs text-gray-500 mt-0.5">
                              {s.temperature && <span>{s.temperature}°C</span>}
                              {s.duration_minutes && <span>{s.duration_minutes} min</span>}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Results */}
                <div className="glass-light rounded-lg p-4">
                  <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Results</h3>
                  {selected.results.length === 0 ? (
                    <p className="text-xs text-gray-600">No results yet</p>
                  ) : (
                    <div className="space-y-2">
                      {selected.results.map((r) => (
                        <div key={r.id} className="flex items-center justify-between py-2 border-b border-gray-800 last:border-0">
                          <div>
                            <p className="text-sm font-medium capitalize">{r.result_type.replace(/_/g, ' ')}</p>
                            <p className="text-xs text-gray-500">{r.characterization_method}</p>
                          </div>
                          {r.value !== null && (
                            <span className="font-mono text-sm">{formatNumber(r.value)} {r.unit}</span>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>

              {/* Failed Data Note */}
              {selected.status === 'failed' && (
                <div className="mt-4 p-4 rounded-lg bg-amber-500/5 border border-amber-500/20">
                  <p className="text-xs font-medium text-amber-400">⚠ Failed experiment recorded</p>
                  <p className="text-xs text-gray-400 mt-1">This negative result improves AION's models. No data goes to waste.</p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
