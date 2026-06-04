import { useState } from 'react'
import { api } from '../api/client'
import { formatNumber, getPropertyColor, getPropertyUnit } from '../lib/utils'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import { LineChart, Send, Table } from 'lucide-react'

const PROPERTIES = ['band_gap', 'formation_energy', 'density']

export function Predictor() {
  const [formula, setFormula] = useState('')
  const [formulas, setFormulas] = useState('')
  const [results, setResults] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [mode, setMode] = useState<'single' | 'batch'>('single')

  async function handlePredict() {
    if (!formula.trim()) return
    setLoading(true)
    try {
      const res = await api.predict.properties(formula, PROPERTIES)
      setResults(res.predictions || [])
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  async function handleBatchPredict() {
    const list = formulas.split('\n').map((f) => f.trim()).filter(Boolean)
    if (list.length === 0) return
    setLoading(true)
    try {
      const res = await api.predict.batch(list, PROPERTIES)
      setResults(res.results || [])
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  const groupedResults = results.reduce((acc: any, r: any) => {
    if (!acc[r.property]) acc[r.property] = []
    acc[r.property].push(r)
    return acc
  }, {} as Record<string, any[]>)

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-semibold text-gray-900">Property Predictor</h1>
        <p className="text-sm text-gray-400 mt-1">Predict materials properties using AI surrogate models trained on DFT data.</p>
      </div>

      <div className="flex gap-2 mb-5">
        <button
          onClick={() => setMode('single')}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${mode === 'single' ? 'bg-blue-500 text-white' : 'bg-gray-100 text-gray-500 hover:bg-gray-200'}`}
        >
          Single Prediction
        </button>
        <button
          onClick={() => setMode('batch')}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${mode === 'batch' ? 'bg-blue-500 text-white' : 'bg-gray-100 text-gray-500 hover:bg-gray-200'}`}
        >
          Batch Prediction
        </button>
      </div>

      <div className="bg-white rounded-xl border border-gray-100 p-6 shadow-sm mb-8">
        {mode === 'single' ? (
          <div className="flex gap-3">
            <input
              type="text"
              value={formula}
              onChange={(e) => setFormula(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handlePredict()}
              placeholder="Enter formula (e.g., LiCoO2)"
              className="flex-1 bg-gray-50 border border-gray-200 rounded-lg px-4 py-3 text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-400 font-mono"
            />
            <button
              onClick={handlePredict}
              disabled={loading}
              className="px-6 py-3 bg-blue-500 hover:bg-blue-600 text-white rounded-xl text-sm font-semibold transition-all disabled:opacity-50 flex items-center gap-2"
            >
              <Send className="w-4 h-4" /> Predict
            </button>
          </div>
        ) : (
          <div className="space-y-3">
            <textarea
              value={formulas}
              onChange={(e) => setFormulas(e.target.value)}
              placeholder="Enter formulas, one per line:&#10;LiCoO2&#10;LiFePO4&#10;LiNi0.8Mn0.1Co0.1O2&#10;NaMnO2"
              className="w-full bg-gray-50 border border-gray-200 rounded-lg px-4 py-3 text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-400 font-mono min-h-[120px]"
            />
            <button
              onClick={handleBatchPredict}
              disabled={loading}
              className="w-full py-3 bg-blue-500 hover:bg-blue-600 text-white rounded-xl text-sm font-semibold transition-all disabled:opacity-50 flex items-center justify-center gap-2"
            >
              <Table className="w-4 h-4" /> {loading ? 'Predicting...' : 'Batch Predict'}
            </button>
          </div>
        )}
      </div>

      {results.length > 0 && (
        <div className="fade-in">
          {mode === 'batch' && (
            <>
              {(Object.entries(groupedResults) as [string, any[]][]).map(([prop, preds]) => (
                <div key={prop} className="bg-white rounded-xl border border-gray-100 p-6 shadow-sm mb-5">
                  <h3 className="text-sm font-semibold text-gray-700 capitalize mb-4">
                    {prop.replace(/_/g, ' ')} ({getPropertyUnit(prop)})
                  </h3>
                  <ResponsiveContainer width="100%" height={Math.max(150, preds.length * 40)}>
                    <BarChart data={preds} layout="vertical" margin={{ left: 80 }}>
                      <XAxis type="number" stroke="#9ca3af" fontSize={12} />
                      <YAxis dataKey="formula" type="category" stroke="#9ca3af" fontSize={11} width={75} />
                      <Tooltip
                        contentStyle={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: '8px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}
                        labelStyle={{ color: '#1d1d1f' }}
                      />
                      <Bar dataKey="predicted_value" radius={[0, 4, 4, 0]}>
                        {preds.map((_: any, i: number) => (
                          <Cell key={i} fill={getPropertyColor(prop)} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              ))}
            </>
          )}

          {mode === 'single' && (
            <div className="grid grid-cols-3 gap-4">
              {results.map((r) => (
                <div key={r.property} className="bg-white rounded-xl border border-gray-100 p-6 shadow-sm text-center">
                  <p className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">
                    {r.property.replace(/_/g, ' ')}
                  </p>
                  <p className="text-3xl font-semibold" style={{ color: getPropertyColor(r.property) }}>
                    {formatNumber(r.predicted_value)}
                  </p>
                  <p className="text-sm text-gray-400 mt-1">{getPropertyUnit(r.property)}</p>
                  <div className="mt-3 flex items-center justify-center gap-2 text-xs text-gray-400">
                    <div className={`w-2 h-2 rounded-full ${r.confidence > 0.7 ? 'bg-green-500' : r.confidence > 0.4 ? 'bg-orange-500' : 'bg-red-500'}`} />
                    <span>{(r.confidence * 100).toFixed(0)}% confidence</span>
                  </div>
                </div>
              ))}
            </div>
          )}

          <div className="bg-white rounded-xl border border-gray-100 p-6 shadow-sm mt-5">
            <h3 className="text-sm font-semibold text-gray-700 mb-4">Raw Predictions</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-gray-400 border-b border-gray-100">
                    <th className="text-left py-2 pr-4 font-medium">Formula</th>
                    <th className="text-left py-2 pr-4 font-medium">Property</th>
                    <th className="text-right py-2 pr-4 font-medium">Value</th>
                    <th className="text-right py-2 font-medium">Confidence</th>
                  </tr>
                </thead>
                <tbody>
                  {results.map((r, i) => (
                    <tr key={i} className="border-b border-gray-50 text-gray-600">
                      <td className="py-2 pr-4 font-mono text-gray-900">{r.formula}</td>
                      <td className="py-2 pr-4 capitalize">{r.property.replace(/_/g, ' ')}</td>
                      <td className="py-2 pr-4 text-right font-mono" style={{ color: getPropertyColor(r.property) }}>
                        {formatNumber(r.predicted_value)}
                      </td>
                      <td className="py-2 text-right">{(r.confidence * 100).toFixed(0)}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
