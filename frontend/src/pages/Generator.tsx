import { useState } from 'react'
import { api } from '../api/client'
import { Candidate } from '../lib/types'
import { Sparkles, FlaskConical, Ruler, Layers, Atom, Hash } from 'lucide-react'

export function Generator() {
  const [description, setDescription] = useState('')
  const [elements, setElements] = useState('')
  const [numCandidates, setNumCandidates] = useState(10)
  const [candidates, setCandidates] = useState<Candidate[]>([])
  const [loading, setLoading] = useState(false)
  const [selectedCandidate, setSelectedCandidate] = useState<Candidate | null>(null)
  const [synthesisCheck, setSynthesisCheck] = useState<any>(null)

  async function handleGenerate() {
    setLoading(true)
    setCandidates([])
    setSelectedCandidate(null)
    setSynthesisCheck(null)
    try {
      const res = await api.generate.crystals({
        target_properties: { description },
        element_constraints: elements ? elements.split(',').map((e: string) => e.trim()) : null,
        num_candidates: numCandidates,
      })
      setCandidates(res.candidates || [])
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  async function handleCheckSynthesis() {
    if (!selectedCandidate) return
    const res = await api.synthesis.feasibility(selectedCandidate.formula)
    setSynthesisCheck(res)
  }

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-semibold text-gray-900">Materials Generator</h1>
        <p className="text-sm text-gray-400 mt-1">Describe the material you need to generate candidate compositions and crystal structures.</p>
      </div>

      <div className="bg-white rounded-xl border border-gray-100 p-6 shadow-sm mb-8">
        <div className="space-y-4">
          <div>
            <label className="text-sm font-medium text-gray-700 mb-2 block">Describe your target material</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="e.g., 'A cathode material for solid-state batteries with high ionic conductivity and stability above 4V'"
              className="w-full bg-gray-50 border border-gray-200 rounded-lg px-4 py-3 text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-400 min-h-[100px]"
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium text-gray-700 mb-2 block">Element constraints (optional)</label>
              <input
                type="text"
                value={elements}
                onChange={(e) => setElements(e.target.value)}
                placeholder="Li, Co, O, Ni, Mn"
                className="w-full bg-gray-50 border border-gray-200 rounded-lg px-3 py-2 text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-400"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-gray-700 mb-2 block">Number of candidates</label>
              <input
                type="number"
                value={numCandidates}
                onChange={(e) => setNumCandidates(parseInt(e.target.value) || 10)}
                min={1}
                max={100}
                className="w-full bg-gray-50 border border-gray-200 rounded-lg px-3 py-2 text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-400"
              />
            </div>
          </div>
          <button
            onClick={handleGenerate}
            disabled={loading || !description.trim()}
            className="w-full py-3 bg-blue-500 hover:bg-blue-600 text-white rounded-xl text-sm font-semibold transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            <Sparkles className="w-4 h-4" />
            {loading ? 'Generating...' : 'Generate Materials'}
          </button>
        </div>
      </div>

      {candidates.length > 0 && (
        <div className="grid grid-cols-3 gap-5">
          <div className="col-span-1 bg-white rounded-xl border border-gray-100 shadow-sm p-4 max-h-[60vh] overflow-y-auto scrollbar-thin">
            <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">Candidates ({candidates.length})</h2>
            <div className="space-y-0.5">
              {candidates.map((c, i) => (
                <div
                  key={c.id}
                  onClick={() => { setSelectedCandidate(c); setSynthesisCheck(null) }}
                  className={`p-3 rounded-lg cursor-pointer transition-all ${
                    selectedCandidate?.id === c.id ? 'bg-blue-50 border border-blue-100' : 'hover:bg-gray-50 border border-transparent'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-sm font-medium text-gray-900">{c.formula}</span>
                    <span className="text-xs text-gray-400">#{i + 1}</span>
                  </div>
                  <div className="flex items-center gap-2 mt-0.5 text-xs text-gray-400">
                    <span>{c.space_group}</span>
                    <span>· {c.num_atoms} atoms</span>
                  </div>
                  <div className="flex gap-2 mt-1">
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-blue-50 text-blue-500">
                      gen: {c.generation_score.toFixed(3)}
                    </span>
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-green-50 text-green-500">
                      synth: {c.synthesis_score.toFixed(3)}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="col-span-2 bg-white rounded-xl border border-gray-100 shadow-sm p-6">
            {!selectedCandidate ? (
              <div className="flex items-center justify-center h-full">
                <p className="text-sm text-gray-400">Select a candidate to view details</p>
              </div>
            ) : (
              <div className="fade-in">
                <div className="flex items-start justify-between mb-6">
                  <div>
                    <h2 className="text-xl font-semibold text-gray-900 font-mono">{selectedCandidate.formula}</h2>
                    <p className="text-sm text-gray-400">{selectedCandidate.space_group}</p>
                  </div>
                  <button
                    onClick={handleCheckSynthesis}
                    className="px-4 py-2 bg-blue-50 hover:bg-blue-100 text-blue-600 rounded-lg text-sm font-medium transition-colors flex items-center gap-1"
                  >
                    <FlaskConical className="w-4 h-4" /> Check Synthesis
                  </button>
                </div>

                <div className="grid grid-cols-2 gap-4 mb-6">
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3 flex items-center gap-1">
                      <Ruler className="w-3 h-3" /> Lattice Parameters
                    </h3>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between"><span className="text-gray-400">a</span><span className="font-mono text-gray-700">{selectedCandidate.lattice_parameters.a} \u00c5</span></div>
                      <div className="flex justify-between"><span className="text-gray-400">b</span><span className="font-mono text-gray-700">{selectedCandidate.lattice_parameters.b} \u00c5</span></div>
                      <div className="flex justify-between"><span className="text-gray-400">c</span><span className="font-mono text-gray-700">{selectedCandidate.lattice_parameters.c} \u00c5</span></div>
                    </div>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3 flex items-center gap-1">
                      <Layers className="w-3 h-3" /> Composition
                    </h3>
                    <div className="flex gap-2 flex-wrap">
                      {selectedCandidate.elements.map((el, i) => (
                        <div key={el} className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-white border border-gray-100 text-sm">
                          <span className="font-medium text-gray-700">{el}</span>
                          <span className="text-gray-400">{selectedCandidate.stoichiometry[i]}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {synthesisCheck && (
                  <div className="bg-gray-50 rounded-lg p-4 fade-in">
                    <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">Synthesis Assessment</h3>
                    <div className="flex items-center gap-2 mb-3">
                      <span className="text-sm text-gray-500">Feasibility Score:</span>
                      <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
                        <div className="h-full bg-gradient-to-r from-red-400 via-orange-400 to-green-500 rounded-full" style={{ width: `${synthesisCheck.feasibility_score * 100}%` }} />
                      </div>
                      <span className="text-sm font-mono text-gray-700">{(synthesisCheck.feasibility_score * 100).toFixed(0)}%</span>
                    </div>
                    <p className="text-xs text-gray-500 mb-3">{synthesisCheck.thermodynamic_notes}</p>
                    <div className="space-y-2">
                      {synthesisCheck.recommended_methods?.map((m: any) => (
                        <div key={m.method} className="flex items-center justify-between text-sm py-1 border-b border-gray-100 last:border-0">
                          <div>
                            <span className="text-gray-700 capitalize">{m.method.replace(/_/g, ' ')}</span>
                            <span className="text-gray-400 ml-2">({m.difficulty})</span>
                          </div>
                          <span className="text-gray-400">{m.estimated_temperature}\u00b0C · {m.estimated_duration_hours}h</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
