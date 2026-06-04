import { useState, useEffect, useRef } from 'react'
import { api } from '../api/client'
import { Material } from '../lib/types'
import { formatNumber, getPropertyColor } from '../lib/utils'
import CrystalViewer from '../components/CrystalViewer'
import {
  Search,
  Plus,
  Upload,
  Download,
  Trash2,
  FlaskConical,
  Atom,
  Ruler,
  BarChart3,
  Layers,
  Eye,
} from 'lucide-react'

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
      <div className="mb-6">
        <h1 className="text-2xl font-semibold text-gray-900">Materials Database</h1>
        <p className="text-sm text-gray-400 mt-1">Browse, search, and manage your materials</p>
      </div>

      <div className="grid grid-cols-2 gap-5 mb-6">
        <div className="bg-white rounded-xl border border-gray-100 p-4 shadow-sm">
          <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">Search Materials</h2>
          <div className="flex gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                placeholder="Search by formula, name, element..."
                className="w-full pl-9 bg-gray-50 border border-gray-200 rounded-lg px-3 py-2 text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-400"
              />
            </div>
            <button onClick={handleSearch} className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg text-sm font-medium transition-colors">
              Search
            </button>
          </div>
        </div>

        <div className="bg-white rounded-xl border border-gray-100 p-4 shadow-sm">
          <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">Add Material</h2>
          <div className="flex gap-2 mb-3">
            <input
              type="text"
              value={formula}
              onChange={(e) => setFormula(e.target.value)}
              placeholder="Formula (e.g., LiCoO2)"
              className="flex-1 bg-gray-50 border border-gray-200 rounded-lg px-3 py-2 text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-400 font-mono"
            />
            <input
              type="text"
              value={spaceGroup}
              onChange={(e) => setSpaceGroup(e.target.value)}
              placeholder="Space group"
              className="w-28 bg-gray-50 border border-gray-200 rounded-lg px-3 py-2 text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-400"
            />
            <button onClick={handleCreate} className="px-4 py-2 bg-green-500 hover:bg-green-600 text-white rounded-lg text-sm font-medium transition-colors flex items-center gap-1">
              <Plus className="w-4 h-4" /> Add
            </button>
          </div>
          <div className="border-t border-gray-100 pt-3">
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
              className="w-full px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg text-sm font-medium transition-colors disabled:opacity-50 flex items-center justify-center gap-1"
            >
              <Upload className="w-4 h-4" /> {importing ? 'Importing...' : 'Import CIF File'}
            </button>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-5">
        <div className="col-span-1 bg-white rounded-xl border border-gray-100 shadow-sm p-4 max-h-[65vh] overflow-y-auto scrollbar-thin">
          {loading ? (
            <div className="animate-pulse space-y-2">
              {[...Array(6)].map((_, i) => (
                <div key={i} className="h-14 bg-gray-50 rounded-lg" />
              ))}
            </div>
          ) : materials.length === 0 ? (
            <p className="text-sm text-gray-400 py-8 text-center">No materials found</p>
          ) : (
            <div className="space-y-0.5">
              {materials.map((m) => (
                <div
                  key={m.id}
                  onClick={() => loadDetail(m.id)}
                  className={`p-3 rounded-lg cursor-pointer transition-all text-sm ${
                    selected?.id === m.id ? 'bg-blue-50 border border-blue-100' : 'hover:bg-gray-50 border border-transparent'
                  }`}
                >
                  <p className="font-mono font-medium text-gray-900" dangerouslySetInnerHTML={{ __html: m.formula }} />
                  <div className="flex items-center gap-2 mt-0.5 text-xs text-gray-400">
                    <span>{m.space_group || '\u2014'}</span>
                    {Object.keys(m.properties || {}).length > 0 && (
                      <span>· {Object.keys(m.properties).length} properties</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="col-span-2 bg-white rounded-xl border border-gray-100 shadow-sm p-6 min-h-[400px]">
          {!selected ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <Eye className="w-8 h-8 text-gray-300 mx-auto mb-2" />
                <p className="text-sm text-gray-400">Select a material to view details</p>
              </div>
            </div>
          ) : (
            <div className="fade-in">
              <div className="flex items-start justify-between mb-6">
                <div>
                  <h2 className="text-xl font-semibold text-gray-900">
                    <span className="font-mono" dangerouslySetInnerHTML={{ __html: selected.formula }} />
                  </h2>
                  <p className="text-sm text-gray-400 mt-0.5">{selected.name || selected.formula}</p>
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
                    className="px-3 py-1.5 bg-green-50 hover:bg-green-100 text-green-600 rounded-lg text-xs font-medium transition-colors flex items-center gap-1"
                  >
                    <Download className="w-3 h-3" /> Export CIF
                  </button>
                  <button
                    onClick={() => {
                      api.synthesis.feasibility(selected.formula).then((r) => {
                        setSelected({ ...selected, _synthesis: r } as any)
                      })
                    }}
                    className="px-3 py-1.5 bg-blue-50 hover:bg-blue-100 text-blue-600 rounded-lg text-xs font-medium transition-colors flex items-center gap-1"
                  >
                    <FlaskConical className="w-3 h-3" /> Check Synthesis
                  </button>
                  <button
                    onClick={() => handleDelete(selected.id)}
                    className="px-3 py-1.5 bg-red-50 hover:bg-red-100 text-red-600 rounded-lg text-xs font-medium transition-colors flex items-center gap-1"
                  >
                    <Trash2 className="w-3 h-3" /> Delete
                  </button>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4 mb-6">
                <div className="bg-gray-50 rounded-lg p-4">
                  <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3 flex items-center gap-1">
                    <Ruler className="w-3 h-3" /> Crystal Data
                  </h3>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between"><span className="text-gray-400">Space Group</span><span className="font-mono text-gray-700">{selected.space_group || '\u2014'}</span></div>
                    <div className="flex justify-between"><span className="text-gray-400">Crystal System</span><span className="text-gray-700">{selected.crystal_system || '\u2014'}</span></div>
                    <div className="flex justify-between"><span className="text-gray-400">a</span><span className="font-mono text-gray-700">{selected.lattice_parameters?.a ? `${selected.lattice_parameters.a} \u00c5` : '\u2014'}</span></div>
                    <div className="flex justify-between"><span className="text-gray-400">b</span><span className="font-mono text-gray-700">{selected.lattice_parameters?.b ? `${selected.lattice_parameters.b} \u00c5` : '\u2014'}</span></div>
                    <div className="flex justify-between"><span className="text-gray-400">c</span><span className="font-mono text-gray-700">{selected.lattice_parameters?.c ? `${selected.lattice_parameters.c} \u00c5` : '\u2014'}</span></div>
                    <div className="flex justify-between"><span className="text-gray-400">Volume</span><span className="font-mono text-gray-700">{selected.volume ? `${selected.volume.toFixed(2)} \u00c5\u00b3` : '\u2014'}</span></div>
                  </div>
                </div>
                <div className="bg-gray-50 rounded-lg p-4">
                  <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3 flex items-center gap-1">
                    <Atom className="w-3 h-3" /> 3D Structure
                  </h3>
                  <CrystalViewer
                    structure={(selected as any).structure}
                    elements={(selected as any).elements || Object.keys(selected.composition || {})}
                    latticeParameters={selected.lattice_parameters}
                  />
                </div>

                <div className="bg-gray-50 rounded-lg p-4">
                  <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3 flex items-center gap-1">
                    <BarChart3 className="w-3 h-3" /> Properties
                  </h3>
                  <div className="space-y-2 text-sm">
                    {Object.entries(selected.properties || {}).length === 0 && (
                      <p className="text-gray-400">No properties recorded</p>
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

                {Object.keys(selected.composition || {}).length > 0 && (
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3 flex items-center gap-1">
                      <Layers className="w-3 h-3" /> Composition
                    </h3>
                    <div className="flex gap-2 flex-wrap">
                      {Object.entries(selected.composition).map(([el, data]) => {
                        const frac = typeof data === 'number' ? data : (data as any).atomic_fraction || 0
                        return (
                          <div key={el} className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white border border-gray-100 text-sm">
                            <span className="font-medium text-gray-700">{el}</span>
                            <span className="text-gray-400">{(frac * 100).toFixed(1)}%</span>
                          </div>
                        )
                      })}
                    </div>
                  </div>
                )}
              </div>

              {(selected as any)._synthesis && (
                <div className="bg-gray-50 rounded-lg p-4 fade-in">
                  <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">Synthesis Assessment</h3>
                  <div className="flex items-center gap-2 mb-3">
                    <span className="text-sm text-gray-500">Feasibility:</span>
                    <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
                      <div className="h-full bg-gradient-to-r from-red-400 via-orange-400 to-green-500 rounded-full" style={{ width: `${(selected as any)._synthesis.feasibility_score * 100}%` }} />
                    </div>
                    <span className="text-sm font-mono text-gray-700">{((selected as any)._synthesis.feasibility_score * 100).toFixed(0)}%</span>
                  </div>
                  {(selected as any)._synthesis.recommended_methods?.map((m: any) => (
                    <div key={m.method} className="flex items-center justify-between text-sm py-1">
                      <span className="text-gray-600">{m.method.replace(/_/g, ' ')}</span>
                      <span className="text-gray-400">{m.difficulty}</span>
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
