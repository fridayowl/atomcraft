import { clsx, type ClassValue } from 'clsx'

export function cn(...inputs: ClassValue[]) {
  return clsx(inputs)
}

export function formatNumber(n: number, decimals: number = 4): string {
  if (n === 0) return '0'
  if (Math.abs(n) < 0.001) return n.toExponential(2)
  return n.toFixed(decimals)
}

export function formulaToHtml(formula: string): string {
  return formula.replace(/(\d+)/g, '<sub>$1</sub>')
}

export function getPropertyColor(property: string): string {
  const colors: Record<string, string> = {
    band_gap: '#818cf8',
    formation_energy: '#22c55e',
    density: '#f59e0b',
    hardness: '#ef4444',
    conductivity: '#06b6d4',
    magnetism: '#ec4899',
  }
  return colors[property] || '#6366f1'
}

export function getPropertyUnit(property: string): string {
  const units: Record<string, string> = {
    band_gap: 'eV',
    formation_energy: 'eV/atom',
    density: 'g/cm³',
    hardness: 'GPa',
    conductivity: 'S/cm',
    volume: 'Å³',
    temperature: 'K',
  }
  return units[property] || ''
}

export function getStatusColor(status: string): string {
  const colors: Record<string, string> = {
    planned: '#f59e0b',
    running: '#3b82f6',
    completed: '#22c55e',
    failed: '#ef4444',
    queued: '#8b5cf6',
  }
  return colors[status] || '#6b7280'
}

export function getDifficultyColor(difficulty: string): string {
  const colors: Record<string, string> = {
    easy: '#22c55e',
    moderate: '#f59e0b',
    hard: '#ef4444',
  }
  return colors[difficulty] || '#6b7280'
}

export function daysSince(dateStr: string | null): number {
  if (!dateStr) return 0
  const date = new Date(dateStr)
  return Math.floor((Date.now() - date.getTime()) / (1000 * 60 * 60 * 24))
}
