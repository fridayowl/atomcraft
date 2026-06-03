import { useState, useEffect, useRef } from 'react'
import { api } from '../api/client'
import { Material } from '../lib/types'
import { formatNumber, getPropertyColor, getPropertyUnit } from '../lib/utils'
import CrystalViewer from '../components/CrystalViewer'

export function Materials() {
  const [materials, setMaterials] = useState<Material[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [selected, setSelected] = useState<Material | null>(null)
  const [formula, setFormula] = useState('')
  const [spaceGroup, setSpaceGroup] = useState('')
  const [importing, setImporting] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    loadMaterials()
  }, [])

  async function loadMaterials() {
    try {
      const res = await api.materials.list('?limit=50')
      setMaterials(res.data || [])
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  async function handleSearch() {
    if (!search.trim()) return loadMaterials()
    try {
      const res = await api.materials.search(search)
      setMaterials(res.data || [])
    } catch (e) {
      console.error(e)
    }
  }

  async function handleCreate() {
    if (!formula.trim()) return
    try {
      await api.materials.create({ formula, space_group: spaceGroup || undefined })
      setFormula('')
      setSpaceGroup('')
      loadMaterials()
    } catch (e) {
      console.error(e)
    }
  }

  async function handleDelete(id: number) {
    try {
      await api.materials.delete(id)
      setSelected(null)
      loadMaterials()
    } catch (e) {
      console.error(e)
    }
  }

  async function loadDetail(id: number) {
    try {
      const res = await api.materials.get(id)
      setSelected(res)
    } catch (e) {
      console.error(e)
    }
  }

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <h1 className="text-2xl font-bold gradient-text mb-6">Materials Database</h1>

      {/* Search & Create */}
      <div className="grid grid-cols-2 gap-6 mb-8">
        <div className="glass rounded-xl p-4">
          <h2 className="text-sm font-semibold text-gray-300 mb-3">Search Materials</h2>
          <div className="flex gap-2">
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              placeholder="Search by formula, name, element..."
              className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500"
            />
            <button onClick={handleSearch} className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 rounded-lg text-sm font-medium transition-colors">
              Search
            </button>
          </div>
        </div>

        <div className="glass rounded-xl p-4">
          <h2 className="text-sm font-semibold text-gray-300 mb-3">Add Material</h2>
          <div className="flex gap-2 mb-3">
            <input
              type="text"
              value={formula}
              onChange={(e) => setFormula(e.target.value)}
              placeholder="Formula (e.g., LiCoO2)"
              className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500 font-mono"
            />
            <input
              type="text"
              value={spaceGroup}
              onChange={(e) => setSpaceGroup(e.target.value)}
              placeholder="Space group"
              className="w-28 bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500"
            />
            <button onClick={handleCreate} className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 rounded-lg text-sm font-medium transition-colors">
              Add
            </button>
          </div>
          <div className="border-t border-gray-700 pt-3">
            <input
              ref={fileInputRef}
              type="file"
              accept=".cif"
              className="hidden"
              onChange={async (e) => {
                const file = e.target.files?.[0]
                if (!file) return
                setImporting(true)
                try {
                  await api.materials.importCif(file)
                  loadMaterials()
                } catch (e: any) {
                  alert(e.message)
                } finally {
                  setImporting(false)
                  if (fileInputRef.current) fileInputRef.current.value = ''
                }
              }}
            />
            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={importing}
              className="w-full px-4 py-2 bg-purple-600/50 hover:bg-purple-600 rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
            >
              {importing ? 'Importing...' : 'Import CIF File'}
            </button>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-6">
        {/* Materials List */}
        <div className="col-span-1 glass rounded-xl p-4 max-h-[70vh] overflow-y-auto scrollbar-thin">
          {loading ? (
            <div className="shimmer h-64 rounded-lg" />
          ) : materials.length === 0 ? (
            <p className="text-sm text-gray-500 py-8 text-center">No materials found</p>
          ) : (
            <div className="space-y-1">
              {materials.map((m) => (
                <div
                  key={m.id}
                  onClick={() => loadDetail(m.id)}
                  className={`p-3 rounded-lg cursor-pointer transition-all text-sm ${
                    selected?.id === m.id ? 'bg-indigo-500/10 border border-indigo-500/20' : 'hover:bg-white/5'
                  }`}
                >
                  <p className="font-mono font-medium" dangerouslySetInnerHTML={{ __html: m.formula }} />
                  <div className="flex items-center gap-2 mt-1 text-xs text-gray-500">
                    <span>{m.space_group || '—'}</span>
                    {Object.keys(m.properties || {}).length > 0 && (
                      <span>· {Object.keys(m.properties).length} properties</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Detail View */}
        <div className="col-span-2 glass rounded-xl p-6 min-h-[400px]">
          {!selected ? (
            <div className="flex items-center justify-center h-full">
              <p className="text-gray-500 text-sm">Select a material to view details</p>
            </div>
          ) : (
            <div className="fade-in">
                <div className="flex items-start justify-between mb-6">
                <div>
                  <h2 className="text-xl font-bold font-mono" dangerouslySetInnerHTML={{ __html: selected.formula }} />
                  <p className="text-sm text-gray-400 mt-1">{selected.name || selected.formula}</p>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => {
                      api.materials.exportCif(selected.id).then((cif) => {
                        const blob = new Blob([cif], { type: 'chemical/x-cif' })
                        const url = URL.createObjectURL(blob)
                        const a = document.createElement('a')
                        a.href = url
                        a.download = `${selected.formula}.cif`
                        a.click()
                        URL.revokeObjectURL(url)
                      })
                    }}
                    className="px-3 py-1.5 bg-emerald-600/50 hover:bg-emerald-600 rounded-lg text-xs transition-colors"
                  >
                    Export CIF
                  </button>
                  <button
                    onClick={() => {
                      api.synthesis.feasibility(selected.formula).then((r) => {
                        setSelected({ ...selected, _synthesis: r } as any)
                      })
                    }}
                    className="px-3 py-1.5 bg-indigo-600/50 hover:bg-indigo-600 rounded-lg text-xs transition-colors"
                  >
                    Check Synthesis
                  </button>
                  <button onClick={() => handleDelete(selected.id)} className="px-3 py-1.5 bg-red-600/50 hover:bg-red-600 rounded-lg text-xs transition-colors">
                    Delete
                  </button>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4 mb-6">
                <div className="glass-light rounded-lg p-4">
                  <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Crystal Data</h3>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between"><span className="text-gray-400">Space Group</span><span className="font-mono">{selected.space_group || '—'}</span></div>
                    <div className="flex justify-between"><span className="text-gray-400">Crystal System</span><span>{selected.crystal_system || '—'}</span></div>
                    <div className="flex justify-between"><span className="text-gray-400">a</span><span className="font-mono">{selected.lattice_parameters?.a ? `${selected.lattice_parameters.a} Å` : '—'}</span></div>
                    <div className="flex justify-between"><span className="text-gray-400">b</span><span className="font-mono">{selected.lattice_parameters?.b ? `${selected.lattice_parameters.b} Å` : '—'}</span></div>
                    <div className="flex justify-between"><span className="text-gray-400">c</span><span className="font-mono">{selected.lattice_parameters?.c ? `${selected.lattice_parameters.c} Å` : '—'}</span></div>
                    <div className="flex justify-between"><span className="text-gray-400">Volume</span><span className="font-mono">{selected.volume ? `${selected.volume.toFixed(2)} Å³` : '—'}</span></div>
                  </div>
                </div>
                <div className="glass-light rounded-lg p-4">
                  <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">3D Structure</h3>
                  <CrystalViewer
                    structure={(selected as any).structure}
                    elements={(selected as any).elements || Object.keys(selected.composition || {})}
                    latticeParameters={selected.lattice_parameters}
                  />
                </div>

                <div className="glass-light rounded-lg p-4">
                  <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Properties</h3>
                  <div className="space-y-2 text-sm">
                    {Object.entries(selected.properties || {}).length === 0 && (
                      <p className="text-gray-500">No properties recorded</p>
                    )}
                    {Object.entries(selected.properties || {}).map(([key, val]) => (
                      <div key={key} className="flex justify-between">
                        <span className="text-gray-400 capitalize">{key.replace(/_/g, ' ')}</span>
                        <span className="font-mono" style={{ color: getPropertyColor(key) }}>
                          {formatNumber(val.value)} {val.unit}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Composition */}
              {Object.keys(selected.composition || {}).length > 0 && (
                <div className="glass-light rounded-lg p-4">
                  <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Composition</h3>
                  <div className="flex gap-2 flex-wrap">
                    {Object.entries(selected.composition).map(([el, data]) => {
                      const frac = typeof data === 'number' ? data : (data as any).atomic_fraction || 0
                      return (
                        <div key={el} className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-gray-800 text-sm">
                          <span className="font-medium">{el}</span>
                          <span className="text-gray-400">{(frac * 100).toFixed(1)}%</span>
                        </div>
                      )
                    })}
                  </div>
                </div>
              )}

              {/* Synthesis assessment if available */}
              {(selected as any)._synthesis && (
                <div className="glass-light rounded-lg p-4 mt-4 fade-in">
                  <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Synthesis Assessment</h3>
                  <div className="flex items-center gap-2 mb-3">
                    <span className="text-sm text-gray-400">Feasibility:</span>
                    <div className="flex-1 h-2 bg-gray-800 rounded-full overflow-hidden">
                      <div className="h-full bg-gradient-to-r from-red-500 via-yellow-500 to-green-500 rounded-full" style={{ width: `${(selected as any)._synthesis.feasibility_score * 100}%` }} />
                    </div>
                    <span className="text-sm font-mono">{((selected as any)._synthesis.feasibility_score * 100).toFixed(0)}%</span>
                  </div>
                  {(selected as any)._synthesis.recommended_methods?.map((m: any) => (
                    <div key={m.method} className="flex items-center justify-between text-sm py-1">
                      <span className="text-gray-300">{m.method.replace(/_/g, ' ')}</span>
                      <span className="text-gray-500">{m.estimated_temperature}°C · {m.difficulty}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
