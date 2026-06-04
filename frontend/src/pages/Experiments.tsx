import { useState, useEffect } from 'react'
import { api } from '../api/client'
import { Experiment, ExperimentDesign } from '../lib/types'
import { formatNumber } from '../lib/utils'
import {
  FlaskConical,
  Plus,
  Play,
  CheckCircle2,
  XCircle,
  Beaker,
  Clock,
  DollarSign,
  ChevronDown,
  ChevronRight,
} from 'lucide-react'

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
      await api.experiments.create({
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
          <h1 className="text-2xl font-semibold text-gray-900">Experiments</h1>
          <p className="text-sm text-gray-400 mt-1">Plan, track, and learn from synthesis experiments</p>
        </div>
        <button
          onClick={() => setShowDesigner(!showDesigner)}
          className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg text-sm font-medium transition-all flex items-center gap-1"
        >
          <Plus className="w-4 h-4" />
          {showDesigner ? 'Close Designer' : 'Design Experiment'}
        </button>
      </div>

      {showDesigner && (
        <div className="bg-white rounded-xl border border-gray-100 p-6 shadow-sm mb-8 fade-in">
          <h2 className="text-sm font-semibold text-gray-900 mb-4">Experiment Designer</h2>
          <div className="flex gap-3 mb-4">
            <input
              type="text"
              value={designFormula}
              onChange={(e) => setDesignFormula(e.target.value)}
              placeholder="Formula (e.g., LiCoO2)"
              className="flex-1 bg-gray-50 border border-gray-200 rounded-lg px-3 py-2 text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-400 font-mono"
            />
            <select
              value={designMethod}
              onChange={(e) => setDesignMethod(e.target.value)}
              className="bg-gray-50 border border-gray-200 rounded-lg px-3 py-2 text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-400"
            >
              {methods.map((m) => (
                <option key={m.id} value={m.id}>{m.label}</option>
              ))}
            </select>
            <button
              onClick={handleDesignExperiment}
              className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg text-sm font-medium transition-colors"
            >
              Design
            </button>
          </div>

          {designedExperiment && (
            <div className="bg-gray-50 rounded-lg p-4 fade-in">
              <h3 className="font-semibold text-sm text-gray-900 mb-3">{designedExperiment.formula} &mdash; {designedExperiment.method}</h3>
              <div className="grid grid-cols-2 gap-6">
                <div>
                  <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Parameters</h4>
                  <div className="space-y-1 text-sm">
                    {Object.entries(designedExperiment.parameters).map(([k, v]) => (
                      <div key={k} className="flex justify-between">
                        <span className="text-gray-400 capitalize">{k.replace(/_/g, ' ')}</span>
                        <span className="font-mono text-gray-700">{String(v)}</span>
                      </div>
                    ))}
                  </div>
                </div>
                <div>
                  <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Steps</h4>
                  <div className="space-y-1 text-sm">
                    {designedExperiment.steps.map((s) => (
                      <p key={s.step} className="text-gray-500">
                        <span className="text-gray-400">{s.step}.</span> {s.action}
                      </p>
                    ))}
                  </div>
                </div>
              </div>
              <div className="flex items-center justify-between mt-4 pt-3 border-t border-gray-100">
                <div className="flex gap-4 text-xs text-gray-500">
                  <span className="flex items-center gap-1"><Beaker className="w-3 h-3" /> {designedExperiment.characterization.join(', ')}</span>
                  <span className="flex items-center gap-1"><Clock className="w-3 h-3" /> {designedExperiment.estimated_total_time_hours}h</span>
                  <span className="flex items-center gap-1"><DollarSign className="w-3 h-3" /> ${designedExperiment.estimated_cost_usd}</span>
                </div>
                <button
                  onClick={handleCreateFromDesign}
                  className="px-4 py-2 bg-green-500 hover:bg-green-600 text-white rounded-lg text-sm font-medium transition-colors"
                >
                  Create Experiment
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      <div className="grid grid-cols-3 gap-5">
        <div className="col-span-1 bg-white rounded-xl border border-gray-100 shadow-sm p-4 max-h-[65vh] overflow-y-auto scrollbar-thin">
          {loading ? (
            <div className="animate-pulse space-y-2">
              {[...Array(6)].map((_, i) => (
                <div key={i} className="h-14 bg-gray-50 rounded-lg" />
              ))}
            </div>
          ) : experiments.length === 0 ? (
            <p className="text-sm text-gray-400 py-8 text-center">No experiments yet</p>
          ) : (
            <div className="space-y-0.5">
              {experiments.map((e) => (
                <div
                  key={e.id}
                  onClick={() => loadDetail(e.id)}
                  className={`p-3 rounded-lg cursor-pointer transition-all ${
                    selected?.id === e.id ? 'bg-blue-50 border border-blue-100' : 'hover:bg-gray-50 border border-transparent'
                  }`}
                >
                  <div className="flex items-center justify-between mb-0.5">
                    <p className="text-sm font-medium text-gray-900 truncate mr-2">{e.name}</p>
                    <span className={`shrink-0 px-2 py-0.5 rounded text-[10px] font-medium ${
                      e.status === 'completed' ? 'bg-green-50 text-green-600' :
                      e.status === 'running' ? 'bg-blue-50 text-blue-600' :
                      e.status === 'failed' ? 'bg-red-50 text-red-600' :
                      'bg-orange-50 text-orange-600'
                    }`}>
                      {e.status}
                    </span>
                  </div>
                  <p className="text-xs text-gray-400">{e.experiment_type} · {(e as any).step_count || 0} steps</p>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="col-span-2 bg-white rounded-xl border border-gray-100 shadow-sm p-6 min-h-[400px]">
          {!selected ? (
            <div className="flex items-center justify-center h-full text-sm text-gray-400">
              Select an experiment to view details
            </div>
          ) : (
            <div className="fade-in">
              <div className="flex items-start justify-between mb-6">
                <div>
                  <h2 className="text-xl font-semibold text-gray-900">{selected.name}</h2>
                  <p className="text-sm text-gray-400 mt-0.5">{selected.experiment_type} · {selected.synthesis_method || 'N/A'}</p>
                </div>
                <div className="flex gap-2">
                  {selected.status === 'planned' && (
                    <button onClick={() => handleUpdateStatus(selected.id, 'running')} className="px-3 py-1.5 bg-blue-50 hover:bg-blue-100 text-blue-600 rounded-lg text-xs font-medium transition-colors flex items-center gap-1">
                      <Play className="w-3 h-3" /> Start
                    </button>
                  )}
                  {selected.status === 'running' && (
                    <>
                      <button onClick={() => handleUpdateStatus(selected.id, 'completed', true)} className="px-3 py-1.5 bg-green-50 hover:bg-green-100 text-green-600 rounded-lg text-xs font-medium transition-colors flex items-center gap-1">
                        <CheckCircle2 className="w-3 h-3" /> Complete
                      </button>
                      <button onClick={() => handleUpdateStatus(selected.id, 'failed', false)} className="px-3 py-1.5 bg-red-50 hover:bg-red-100 text-red-600 rounded-lg text-xs font-medium transition-colors flex items-center gap-1">
                        <XCircle className="w-3 h-3" /> Failed
                      </button>
                    </>
                  )}
                </div>
              </div>

              {selected.description && (
                <p className="text-sm text-gray-500 mb-6">{selected.description}</p>
              )}

              <div className="grid grid-cols-2 gap-6">
                <div className="bg-gray-50 rounded-lg p-4">
                  <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">Steps</h3>
                  {selected.steps.length === 0 ? (
                    <p className="text-xs text-gray-400">No steps recorded</p>
                  ) : (
                    <div className="space-y-3">
                      {selected.steps.map((s) => (
                        <div key={s.id} className="flex items-start gap-3">
                          <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium shrink-0 ${
                            s.completed ? 'bg-green-100 text-green-600' : 'bg-gray-100 text-gray-400'
                          }`}>
                            {s.step_number}
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="text-sm text-gray-700">{s.description}</p>
                            <div className="flex gap-2 text-xs text-gray-400 mt-0.5">
                              {s.temperature && <span>{s.temperature}°C</span>}
                              {s.duration_minutes && <span>{s.duration_minutes} min</span>}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                <div className="bg-gray-50 rounded-lg p-4">
                  <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">Results</h3>
                  {selected.results.length === 0 ? (
                    <p className="text-xs text-gray-400">No results yet</p>
                  ) : (
                    <div className="space-y-2">
                      {selected.results.map((r) => (
                        <div key={r.id} className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0">
                          <div>
                            <p className="text-sm font-medium text-gray-700 capitalize">{r.result_type.replace(/_/g, ' ')}</p>
                            <p className="text-xs text-gray-400">{r.characterization_method}</p>
                          </div>
                          {r.value !== null && (
                            <span className="font-mono text-sm text-gray-700">{formatNumber(r.value)} {r.unit}</span>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>

              {selected.status === 'failed' && (
                <div className="mt-4 p-4 rounded-lg bg-orange-50 border border-orange-100">
                  <p className="text-xs font-medium text-orange-600">Failed experiment recorded</p>
                  <p className="text-xs text-gray-500 mt-1">This negative result improves the models. No data goes to waste.</p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
