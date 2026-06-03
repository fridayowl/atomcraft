export interface Material {
  id: number
  formula: string
  name: string | null
  formula_html: string | null
  space_group: string | null
  crystal_system: string | null
  lattice_parameters: {
    a: number | null
    b: number | null
    c: number | null
    alpha: number | null
    beta: number | null
    gamma: number | null
  }
  volume: number | null
  density: number | null
  properties: Record<string, { value: number; unit: string; source?: string; confidence?: number }>
  composition: Record<string, number | { amount: number; atomic_fraction: number }>
  phases: Phase[]
  cif_data: string | null
  mp_id: string | null
  tags: string[]
  created_at: string | null
}

export interface Phase {
  name: string
  temp_min: number | null
  temp_max: number | null
  stability: string | null
}

export interface Candidate {
  id: string
  formula: string
  space_group: string
  lattice_parameters: { a: number; b: number; c: number }
  num_atoms: number
  elements: string[]
  stoichiometry: number[]
  generation_score: number
  synthesis_score: number
}

export interface Prediction {
  formula: string
  property: string
  predicted_value: number
  confidence: number
  model: string
}

export interface SynthesisAssessment {
  formula: string
  feasibility_score: number
  n_elements: number
  has_oxygen: boolean
  has_transition_metal: boolean
  recommended_methods: SynthesisMethod[]
  known_precursors: string[]
  thermodynamic_notes: string
  risks: string[]
}

export interface SynthesisMethod {
  method: string
  description: string
  estimated_temperature: number
  estimated_duration_hours: number
  difficulty: string
  success_probability: number
}

export interface Experiment {
  id: number
  material_id: number
  name: string
  experiment_type: string
  description: string | null
  status: string
  synthesis_method: string | null
  synthesis_conditions: Record<string, any> | null
  successful: boolean | null
  notes: string | null
  tags: string[]
  steps: ExperimentStep[]
  results: ExperimentResult[]
  created_at: string | null
  completed_at: string | null
}

export interface ExperimentStep {
  id: number
  step_number: number
  step_type: string
  description: string
  duration_minutes: number | null
  temperature: number | null
  completed: boolean
}

export interface ExperimentResult {
  id: number
  result_type: string
  value: number | null
  unit: string | null
  characterization_method: string
  notes: string | null
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

export interface ExperimentDesign {
  formula: string
  method: string
  parameters: Record<string, any>
  steps: { step: number; action: string }[]
  characterization: string[]
  estimated_total_time_hours: number
  estimated_cost_usd: number
}
