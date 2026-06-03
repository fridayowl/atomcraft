import { useState } from 'react'
import { api } from '../api/client'
import { Candidate } from '../lib/types'

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
      <h1 className="text-2xl font-bold gradient-text mb-6">Materials Generator</h1>
      <p className="text-sm text-gray-400 mb-8">Describe the material you need, and AION will generate candidate compositions and crystal structures.</p>

      {/* Input */}
      <div className="glass rounded-xl p-6 mb-8">
        <div className="space-y-4">
          <div>
            <label className="text-sm font-medium text-gray-300 mb-2 block">Describe your target material</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="e.g., 'A cathode material for solid-state batteries with high ionic conductivity and stability above 4V'"
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-3 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500 min-h-[100px]"
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium text-gray-300 mb-2 block">Element constraints (optional)</label>
              <input
                type="text"
                value={elements}
                onChange={(e) => setElements(e.target.value)}
                placeholder="Li, Co, O, Ni, Mn"
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-gray-300 mb-2 block">Number of candidates</label>
              <input
                type="number"
                value={numCandidates}
                onChange={(e) => setNumCandidates(parseInt(e.target.value) || 10)}
                min={1}
                max={100}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500"
              />
            </div>
          </div>
          <button
            onClick={handleGenerate}
            disabled={loading || !description.trim()}
            className="w-full py-3 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 rounded-xl text-sm font-semibold transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Generating...' : 'Generate Materials'}
          </button>
        </div>
      </div>

      {/* Results */}
      {candidates.length > 0 && (
        <div className="grid grid-cols-3 gap-6">
          {/* Candidate List */}
          <div className="col-span-1 glass rounded-xl p-4 max-h-[60vh] overflow-y-auto scrollbar-thin">
            <h2 className="text-sm font-semibold text-gray-300 mb-3">Candidates ({candidates.length})</h2>
            <div className="space-y-1">
              {candidates.map((c, i) => (
                <div
                  key={c.id}
                  onClick={() => { setSelectedCandidate(c); setSynthesisCheck(null) }}
                  className={`p-3 rounded-lg cursor-pointer transition-all ${
                    selectedCandidate?.id === c.id ? 'bg-indigo-500/10 border border-indigo-500/20' : 'hover:bg-white/5'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-sm font-medium">{c.formula}</span>
                    <span className="text-xs text-gray-500">#{i + 1}</span>
                  </div>
                  <div className="flex items-center gap-2 mt-1 text-xs text-gray-500">
                    <span>{c.space_group}</span>
                    <span>· {c.num_atoms} atoms</span>
                  </div>
                  <div className="flex gap-2 mt-1">
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-indigo-500/10 text-indigo-400">
                      gen: {c.generation_score.toFixed(3)}
                    </span>
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400">
                      synth: {c.synthesis_score.toFixed(3)}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Detail */}
          <div className="col-span-2 glass rounded-xl p-6">
            {!selectedCandidate ? (
              <p className="text-gray-500 text-sm">Select a candidate</p>
            ) : (
              <div className="fade-in">
                <div className="flex items-start justify-between mb-6">
                  <div>
                    <h2 className="text-xl font-bold font-mono">{selectedCandidate.formula}</h2>
                    <p className="text-sm text-gray-400">{selectedCandidate.space_group}</p>
                  </div>
                  <button
                    onClick={handleCheckSynthesis}
                    className="px-4 py-2 bg-indigo-600/50 hover:bg-indigo-600 rounded-lg text-sm transition-colors"
                  >
                    Check Synthesis
                  </button>
                </div>

                <div className="grid grid-cols-2 gap-4 mb-6">
                  <div className="glass-light rounded-lg p-4">
                    <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Lattice Parameters</h3>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between"><span className="text-gray-400">a</span><span className="font-mono">{selectedCandidate.lattice_parameters.a} Å</span></div>
                      <div className="flex justify-between"><span className="text-gray-400">b</span><span className="font-mono">{selectedCandidate.lattice_parameters.b} Å</span></div>
                      <div className="flex justify-between"><span className="text-gray-400">c</span><span className="font-mono">{selectedCandidate.lattice_parameters.c} Å</span></div>
                    </div>
                  </div>
                  <div className="glass-light rounded-lg p-4">
                    <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Composition</h3>
                    <div className="flex gap-2 flex-wrap">
                      {selectedCandidate.elements.map((el, i) => (
                        <div key={el} className="flex items-center gap-1 px-2 py-1 rounded bg-gray-800 text-sm">
                          <span className="font-medium">{el}</span>
                          <span className="text-gray-400">{selectedCandidate.stoichiometry[i]}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {synthesisCheck && (
                  <div className="glass-light rounded-lg p-4 fade-in">
                    <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Synthesis Assessment</h3>
                    <div className="flex items-center gap-2 mb-3">
                      <span className="text-sm text-gray-400">Feasibility Score:</span>
                      <div className="flex-1 h-2 bg-gray-800 rounded-full overflow-hidden">
                        <div className="h-full bg-gradient-to-r from-red-500 via-yellow-500 to-green-500 rounded-full" style={{ width: `${synthesisCheck.feasibility_score * 100}%` }} />
                      </div>
                      <span className="text-sm font-mono">{(synthesisCheck.feasibility_score * 100).toFixed(0)}%</span>
                    </div>
                    <p className="text-xs text-gray-500 mb-3">{synthesisCheck.thermodynamic_notes}</p>
                    <div className="space-y-2">
                      {synthesisCheck.recommended_methods?.map((m: any) => (
                        <div key={m.method} className="flex items-center justify-between text-sm py-1 border-b border-gray-800 last:border-0">
                          <div>
                            <span className="text-gray-200 capitalize">{m.method.replace(/_/g, ' ')}</span>
                            <span className="text-gray-500 ml-2">({m.difficulty})</span>
                          </div>
                          <span className="text-gray-400">{m.estimated_temperature}°C · {m.estimated_duration_hours}h</span>
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
