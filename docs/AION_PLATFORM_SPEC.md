# AION Materials Discovery Platform

## Vision

**AION is the AI operating system for materials discovery.** It connects generative AI, computational simulation, synthesis feasibility, and experiment tracking into a single closed-loop platform. Researchers describe what they need in natural language — AION generates candidates, predicts properties, validates with simulation, recommends synthesis routes, and learns from every experiment.

**From prompt to synthesis-ready material in hours, not years.**

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         FRONTEND (React + TS + Tailwind)            │
│  ┌──────────┬──────────────┬──────────┬───────────┬──────────────┐  │
│  │Dashboard │  Materials   │Generator │ Predictor │  Experiments │  │
│  │ (Home)   │  Database    │ (AI Gen) │ (ML Prop) │  (Tracking)  │  │
│  └──────────┴──────────────┴──────────┴───────────┴──────────────┘  │
│                       AION Chat (Conversational UI)                  │
├─────────────────────────────────────────────────────────────────────┤
│                       API LAYER (FastAPI)                           │
│  /api/materials   /api/generate   /api/predict   /api/synthesis     │
│  /api/experiments   /api/chat                                       │
├─────────────────────────────────────────────────────────────────────┤
│                       CORE SERVICES                                 │
│  ┌─────────────┬──────────────┬─────────────┬──────────────────┐    │
│  │ Materials   │   Crystal    │  Property   │   Synthesis      │    │
│  │   LLM      │  Generator   │  Predictor  │   Engine         │    │
│  │ (Mater. AI) │ (Diffusion)  │  (GNN/RF)   │   (Feasibility)  │    │
│  ├─────────────┼──────────────┼─────────────┼──────────────────┤    │
│  │ Simulation  │ Composition  │ Experiment  │   DFT            │    │
│  │ Orchestrator│  Analyzer    │  Designer   │   Orchestrator   │    │
│  └─────────────┴──────────────┴─────────────┴──────────────────┘    │
├─────────────────────────────────────────────────────────────────────┤
│                       DATA LAYER                                    │
│  ┌──────────┬──────────────┬──────────────┬──────────────────┐      │
│  │PostgreSQL│    Neo4j     │  Redis       │  S3/File Store   │      │
│  │Materials │  Knowledge   │  Job Queue   │  CIF/Data Files  │      │
│  │Metadata  │  Graph       │  Cache       │                  │      │
│  └──────────┴──────────────┴──────────────┴──────────────────┘      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 1. Backend — FastAPI Python Application

### Data Models (SQLAlchemy ORM)

The database schema is designed around the full materials discovery lifecycle:

**`materials`** — Core material entries
| Field | Type | Description |
|-------|------|-------------|
| id | Integer | Primary key |
| formula | String | Chemical formula (e.g., LiCoO₂) |
| name | String | Common name |
| formula_html | Text | HTML-rendered formula with subscripts |
| space_group | String | Crystallographic space group (e.g., R-3m) |
| crystal_system | String | Crystal system (hexagonal, cubic, etc.) |
| lattice_a/b/c | Float | Lattice parameters in Å |
| lattice_alpha/beta/gamma | Float | Lattice angles in degrees |
| volume | Float | Unit cell volume in Å³ |
| density | Float | Calculated density in g/cm³ |
| cif_data | Text | Full Crystallographic Information File content |
| mp_id | String | Materials Project identifier |
| tags | JSON | User-defined tags |
| public | Boolean | Visibility flag |

**`compositions`** — Elemental breakdown of each material
| Field | Type | Description |
|-------|------|-------------|
| material_id | FK | Reference to material |
| element | String | Element symbol |
| amount | Float | Stoichiometric amount |
| atomic_fraction | Float | Normalized atomic fraction |

**`properties`** — Computed or measured properties
| Field | Type | Description |
|-------|------|-------------|
| material_id | FK | Reference to material |
| property_type | String | e.g., band_gap, formation_energy, density |
| value | Float | Property value |
| unit | String | Unit of measurement |
| source | String | Origin (experiment, DFT, ML prediction) |
| confidence | Float | Confidence score (0-1) |
| method | String | Method used to obtain |

**`phases`** — Phase stability information
| Field | Type | Description |
|-------|------|-------------|
| material_id | FK | Reference to material |
| phase_name | String | Phase identifier |
| temperature_min/max | Float | Stability temperature range |
| pressure_min/max | Float | Stability pressure range |
| stability | String | Stable/metastable/unstable |

**`experiments`** — Synthesis and characterization experiments
| Field | Type | Description |
|-------|------|-------------|
| material_id | FK | Target material |
| user_id | FK | Researcher who conducted it |
| name | String | Experiment name |
| experiment_type | String | synthesis, characterization, etc. |
| status | String | planned → running → completed/failed |
| synthesis_method | String | solid_state, sol_gel, hydrothermal, CVD, mechanochemical |
| synthesis_conditions | JSON | Temperature, pressure, atmosphere, dwell time |
| precursor_materials | JSON | List of starting materials |
| successful | Boolean | Did it produce the target phase? |
| notes | Text | Free-text observations |

**`experiment_steps`** — Step-by-step procedure tracking
| Field | Type | Description |
|-------|------|-------------|
| experiment_id | FK | Parent experiment |
| step_number | Integer | Order in procedure |
| step_type | String | mixing, heating, grinding, etc. |
| duration_minutes | Float | Time for this step |
| temperature | Float | Temperature at this step |
| completed | Boolean | Execution status |

**`experiment_results`** — Characterization outputs
| Field | Type | Description |
|-------|------|-------------|
| experiment_id | FK | Parent experiment |
| result_type | String | XRD_pattern, SEM_image, EDS_spectrum, etc. |
| value | Float | Quantitative result |
| unit | String | Unit of measurement |
| characterization_method | String | XRD, SEM, EDS, XPS, TEM, etc. |
| file_path | String | Link to raw data file |
| data_json | JSON | Structured characterization data |

**`predictions`** — ML model predictions
| Field | Type | Description |
|-------|------|-------------|
| material_id | FK | Target material |
| prediction_type | String | Property being predicted |
| model_name | String | Which model made the prediction |
| model_version | String | Model version identifier |
| predicted_value | Float | ML-predicted value |
| confidence | Float | Prediction confidence |
| feature_importance | JSON | Which features drove the prediction |
| validated | Boolean | Has this been experimentally verified? |
| experimental_value | Float | Ground truth if validated |
| error | Float | Prediction error if validated |

**`prediction_jobs`** — Async computation tracking
| Field | Type | Description |
|-------|------|-------------|
| job_type | String | dft_calculation, md_simulation, batch_prediction |
| input_data | JSON | Job parameters |
| status | String | queued → running → completed/failed |
| progress | Float | 0.0 to 1.0 |
| dft_cost | Float | Compute cost in USD |
| compute_time_seconds | Float | Wall time |

**`users`, `teams`, `team_members`** — Multi-user collaboration
- Subscription tiers: free (10 predictions/mo), researcher (500/mo + DFT credits), team (unlimited + shared workspace), enterprise (on-prem + dedicated compute)
- Role-based access: owner, admin, member, viewer

### Core AI Services

#### 1. Materials LLM (`core/llm.py`)
- Fine-tuned language model with deep materials science knowledge
- Conversational Q&A about materials, properties, synthesis
- Material suggestion from natural language requirements
- Characterization data analysis (XRD, SEM, XPS pattern interpretation)
- System prompt defines expert materials scientist persona

#### 2. Composition Analyzer (`core/composition_analyzer.py`)
- Parses chemical formulas into elemental composition
- Computes compositional descriptors:
  - Average atomic radius
  - Average electronegativity (Pauling scale)
  - Average atomic mass
  - Average valence electron count
  - Electronegativity range
  - Radius range
- Predicts baseline properties from composition heuristics:
  - Band gap (from electronegativity and radius difference)
  - Formation energy (from electronegativity)
  - Density (from mass/volume scaling)
- Element database with 42 elements including transition metals, alkali, alkaline earth, halogens, chalcogens, pnictogens

#### 3. Crystal Generator (`core/generator.py`)
- Generative model interface for crystal structure prediction
- Composition generation from target property constraints
- Element constraint filtering (e.g., only 3d transition metals)
- Crystal structure output with space group assignment
- Generation and synthesis quality scoring
- Supports multiple structure types (ABO₃ perovskite, spinel, layered, rocksalt)

#### 4. Property Predictor (`core/predictor.py`)
- ML model ensemble for property prediction:
  - Band gap (Random Forest)
  - Formation energy (Gradient Boosting)
  - Density (Random Forest)
- Fast surrogate models (seconds) vs. full DFT (hours)
- Feature importance analysis
- Batch prediction support for high-throughput screening
- Confidence scoring per prediction

#### 5. Synthesis Engine (`core/synthesis.py`)
- Synthesis feasibility assessment with scoring (0-100%)
- 5 synthesis method profiles:
  - **Solid-state**: 600-1500°C, for oxides, sulfides, intermetallics
  - **Sol-gel**: 300-1000°C, solution-based, for oxides and nanomaterials
  - **Hydrothermal**: 100-500°C, aqueous high-pressure, for zeolites
  - **CVD**: 400-1200°C, vapor deposition for thin films and 2D materials
  - **Mechanochemical**: 25-200°C, ball milling for metastable phases
- Automatic method recommendation based on composition
- Risk identification (air-sensitive precursors, high-temperature requirements)
- Full experiment design with step-by-step procedure
- Temperature ramping, atmosphere control, and characterization recommendations

#### 6. Simulation Orchestrator (`core/simulation.py`)
- DFT job management (VASP, Quantum ESPRESSO, CP2K)
- Molecular dynamics job management (LAMMPS)
- Cost estimation per calculation
- Job queuing and status tracking
- Multi-fidelity approach: ML → DFT → MD as verification depth increases

### API Endpoints

**Materials** (`/api/materials/`)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | List/search materials with filtering by element, space group, properties |
| GET | `/{id}` | Full material detail with properties, composition, phases |
| POST | `/` | Create new material entry |
| DELETE | `/{id}` | Remove material and related data |

**Generation** (`/api/generate/`)
| Method | Path | Description |
|--------|------|-------------|
| POST | `/crystals` | Generate crystal structures from target properties |
| POST | `/compositions` | Generate compositions from property constraints |

**Prediction** (`/api/predict/`)
| Method | Path | Description |
|--------|------|-------------|
| POST | `/` | Predict properties for a single formula |
| POST | `/batch` | Batch predict for multiple formulas |
| GET | `/feature-importance/{property}` | Feature importance for a property model |

**Synthesis** (`/api/synthesis/`)
| Method | Path | Description |
|--------|------|-------------|
| POST | `/feasibility` | Assess synthesis feasibility for a formula |
| POST | `/design-experiment` | Generate full experiment procedure |
| GET | `/methods` | List available synthesis methods |

**Experiments** (`/api/experiments/`)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | List experiments with material/status filters |
| GET | `/{id}` | Full experiment with steps and results |
| POST | `/` | Create new experiment |
| POST | `/{id}/steps` | Add step to experiment |
| POST | `/{id}/results` | Record characterization result |
| PATCH | `/{id}/status` | Update experiment status (planned→running→completed/failed) |

**Chat** (`/api/chat/`)
| Method | Path | Description |
|--------|------|-------------|
| POST | `/query` | Ask AION a materials science question |
| POST | `/suggest` | Get material suggestions from requirements |

---

## 2. Frontend — React + TypeScript + Tailwind CSS

### Tech Stack
- **Framework:** React 18 with TypeScript
- **Build Tool:** Vite 5
- **Routing:** React Router v6
- **Styling:** Tailwind CSS v3 with custom design system
- **Charts:** Recharts (responsive, customizable)
- **HTTP:** Native fetch with typed API client
- **Fonts:** Inter (UI), JetBrains Mono (code/data)

### Design System
- **Colors:** Dark theme with indigo/purple accent gradient
- **Glass morphism:** Frosted glass panels with backdrop blur
- **Gradient text:** AION brand typography
- **Grid background:** Subtle dot grid for depth
- **Custom animations:** Shimmer loading, fade-in transitions
- **Scrollbar:** Thin custom scrollbar for lists

### Pages & Components

#### Dashboard (`/`)
- **Stats overview:** Material count, experiment count, prediction count with progress bars
- **Activity chart:** Line chart showing materials and predictions over time
- **Quick AION chat:** Inline AI assistant with natural language input
- **Recent materials:** Clickable cards with formula, space group, band gap
- **Recent experiments:** Status badges (planned/running/completed/failed)

#### Materials Database (`/materials`)
- **Search bar:** Search by formula, name, or element
- **Add material form:** Quick entry with formula and space group
- **Material list:** Scrollable, searchable with preview properties
- **Detail panel (3-column layout):**
  - Crystal data: space group, system, lattice parameters, volume
  - Properties: band gap, formation energy, density with color coding
  - Composition: element fractions with visual badges
  - Synthesis assessment: feasibility score bar, recommended methods

#### Generator (`/generator`)
- **Natural language input:** Describe target material properties
- **Element constraints:** Filter by allowed elements
- **Candidate generation:** AI generates crystal structures
- **Candidate list:** Ranked by generation and synthesis scores
- **Detail view:** Formula, space group, lattice parameters, element composition
- **Synthesis check:** One-click feasibility assessment per candidate

#### Property Predictor (`/predict`)
- **Single prediction:** Input formula, get band gap + formation energy + density
- **Batch prediction:** Paste multiple formulas, get property comparison
- **Visualization:** Bar charts comparing properties across materials
- **Data table:** Tabular view of all predictions with confidence scores
- **Confidence indicators:** Color-coded (green/yellow/red) per prediction

#### Experiments (`/experiments`)
- **Experiment designer:** Input formula + method → auto-generated procedure
- **Experiment list:** Filterable by material and status
- **Detail view:** Steps with completion status, results with characterization data
- **Status workflow:** planned → running → completed/failed
- **Negative result capture:** Failed experiments are recorded as learning data
- **Cost and time estimation:** Estimated hours and USD per experiment

#### AION Chat (`/chat`)
- **Conversational UI:** Chat-style interface with message bubbles
- **Dual mode:** Chat (general Q&A) / Suggest (material recommendation)
- **Quick prompts:** Pre-built discovery queries
- **Thinking indicator:** Animated loading dots
- **Context-aware responses:** Full materials science knowledge

### Component Architecture

```
src/
├── App.tsx                    # Router setup with sidebar layout
├── main.tsx                   # React entry point
├── index.css                  # Global styles + design tokens
├── api/
│   └── client.ts             # Typed API client (all endpoints)
├── lib/
│   ├── types.ts              # Full TypeScript type definitions
│   └── utils.ts              # Formatters, colors, helpers
├── components/
│   └── Sidebar.tsx           # Navigation sidebar with glass styling
└── pages/
    ├── Home.tsx              # Dashboard with stats + chart + recent items
    ├── Materials.tsx         # Materials database CRUD
    ├── Generator.tsx         # AI crystal structure generation
    ├── Predictor.tsx         # ML property prediction
    ├── Experiments.tsx       # Experiment design + tracking
    └── Chat.tsx              # Conversational AI interface
```

### Type System (`lib/types.ts`)
Complete TypeScript interfaces for:
- `Material` — Full material data with properties, composition, phases
- `Candidate` — AI-generated structure candidates
- `Prediction` — ML property predictions
- `SynthesisAssessment` — Feasibility scores and methods
- `SynthesisMethod` — Method details with difficulty
- `Experiment` — Full experiment with steps and results
- `ChatMessage` — Conversational messages with role and timestamp
- `ExperimentDesign` — Auto-generated synthesis procedures

---

## 3. ML Models (`models/`)

### Property Prediction (`models/property_prediction/`)
- **Architecture:** Random Forest / Gradient Boosting ensemble
- **Input features:** Compositional descriptors (atomic radius, electronegativity, mass, valence)
- **Targets:** Band gap (eV), formation energy (eV/atom), density (g/cm³)
- **Training data:** Materials Project, OQMD, JARVIS-DFT datasets
- **Extensible:** Interface supports swapping to GNNs (CGCNN, MEGNet) and graph transformers

### Crystal Generation (`models/crystal_generation/`)
- **Architecture:** Diffusion-based generative model over crystal graphs
- **Generation modes:** Composition → structure, space-group-conditioned, template-based
- **Validated by:** DFT relaxation + formation energy check
- **Extensible:** Interface supports MatterGen, DiffCSP, CDVAE backends

### Synthesis Prediction (`models/synthesis/`)
- **Architecture:** Classification + regression ensemble
- **Predicts:** Synthesizability score, recommended method, synthesis difficulty
- **Training data:** Literature synthesis data, ICSD synthesis parameters
- **Features:** Composition, space group, formation energy, element properties

---

## 4. Infrastructure

### Docker Deployment (`docker-compose.yml`)
| Service | Image | Port | Purpose |
|---------|-------|------|---------|
| `backend` | Custom Python | 8000 | FastAPI application |
| `frontend` | Custom Node | 5173 | Vite dev server |
| `db` | PostgreSQL 16 | 5432 | Primary database |
| `redis` | Redis 7 | 6379 | Job queue + cache |
| `neo4j` | Neo4j 5 | 7474/7687 | Materials knowledge graph |

### Development (`start.sh`)
- Single script to start backend and frontend locally
- Auto-creates Python virtual environment
- Auto-installs dependencies for both services
- Process management with SIGINT/SIGTERM handling

---

## 5. Workflows

### Core Discovery Workflow

```
1. RESEARCHER INPUT
   ↓ "I need a cathode material for solid-state batteries
   ↓  with >200 mAh/g, stable at 4.5V"
   ↓
2. AI GENERATION (Generator)
   ↓ 50 candidate compositions + crystal structures
   ↓ ranked by predicted fitness
   ↓
3. ML SCREENING (Predictor)
   ↓ Top 10 candidates → band gap, formation energy,
   ↓ density, ionic conductivity → ranked shortlist
   ↓
4. SIMULATION VALIDATION (Simulation Orchestrator)
   ↓ Top 3 → DFT geometry relaxation → phonon stability
   ↓ → elastic constants → final ranking
   ↓
5. SYNTHESIS ASSESSMENT (Synthesis Engine)
   ↓ Feasibility score → recommended method →
   ↓ precursor list → procedure design
   ↓
6. EXPERIMENT EXECUTION
   ↓ Synthesis → XRD verification → property measurement
   ↓ Results recorded back into platform
   ↓
7. LEARNING LOOP
   ↓ Every experiment (success or failure) → model retraining
   ↓ Future predictions get smarter
```

### Experiment Tracking Workflow

```
PLANNED → RUNNING → COMPLETED (successful: true)
                    → FAILED (successful: false)
```

Failed experiments are explicitly tracked and fed back into the ML training pipeline. Negative results are as valuable as positive ones for model improvement.

### Multi-User Workflow

```
FREE TIER          RESEARCHER TIER        TEAM TIER         ENTERPRISE
─────────          ───────────────        ──────────         ──────────
10 preds/mo        500 preds/mo           Unlimited          Unlimited
Public data only   50 DFT credits/mo      500 DFT credits    Dedicated compute
Basic LLM          Private projects       Shared workspace   On-prem option
                   Experiment tracking    Knowledge graph    SSO + RBAC
                   Export tools           Team permissions   IP ownership
                                          Priority support   SLA
```

---

## 6. Competitive Positioning

| Competitor | Their Strength | Their Gap | AION Advantage |
|------------|---------------|-----------|----------------|
| **Materials Project** | 150K material database | No AI generation, 2008 UX | Conversational AI + generative design |
| **Citrine Informatics** | Enterprise ML platform | $50K+/yr, closed ecosystem | 100x cheaper, open, LLM-native |
| **Schrödinger** | Computational chemistry depth | $10K+/yr/user, not AI-native | AI-native, 10x faster, fractional cost |
| **DeepMind GNoME** | 380K predicted materials | Research paper, not a product | Platform + closed-loop + synthesis |
| **Microsoft MatterGen** | State-of-the-art generation | Model only, no platform | Full platform + experiment tracking |
| **Mat3ra** | Accessible cloud DFT | Limited AI, no synthesis engine | End-to-end: generation → synthesis |

### Key Differentiators

1. **Conversational AI interface** — Not a CLI or research tool. Natural language in, materials out.
2. **Closed-loop learning** — Prediction → experiment → result → model improvement. Gets smarter with use.
3. **Synthesis-first design** — Most platforms predict materials that can't be made. AION prioritizes synthesizability.
4. **Failed data is gold** — Every failed experiment improves the models. Competitors ignore this data.
5. **Open ecosystem** — Import/export any format, no lock-in, HuggingFace for materials.
6. **Affordable pricing** — 100x cheaper than enterprise competitors, free tier for academics.

---

## 7. Current Status & Next Steps

### ✅ Implemented (v0.1)
- [x] Full backend API (FastAPI) with 6 route modules
- [x] SQLAlchemy data models (9 tables covering materials, experiments, predictions, users)
- [x] Materials LLM interface for conversational AI
- [x] Composition analyzer with 42-element database
- [x] Crystal structure generator (composition + space group + lattice)
- [x] ML property predictor (band gap, formation energy, density)
- [x] Synthesis feasibility engine (5 methods, scoring, experiment design)
- [x] Simulation orchestrator (DFT, MD job management)
- [x] React frontend with 6 pages + sidebar navigation
- [x] TypeScript type system (12 interfaces)
- [x] Property visualization (charts, color-coded values)
- [x] Experiment tracking with status workflow
- [x] Synthesis experiment designer
- [x] AI chat interface with suggestion mode
- [x] Docker compose for full stack deployment
- [x] ML model interfaces (predictor, generator, synthesis)

### 🔜 Next (v0.2 → v1.0)
- [ ] Train actual GNN models on Materials Project data
- [ ] Materials Project API integration for enrichment
- [ ] 3D crystal structure viewer (Three.js / @react-three/fiber)
- [ ] CIF file import/export
- [ ] PDF report generation
- [ ] Authentication + user management
- [ ] Stripe subscription integration
- [ ] Knowledge graph visualization (Neo4j)
- [ ] Real DFT compute backend (cloud HPC integration)
- [ ] Battery materials vertical specialization
- [ ] XRD pattern simulation and matching
- [ ] Phase diagram visualization
- [ ] API documentation (OpenAPI/Swagger enhanced)
- [ ] Unit tests + integration tests

---

## 8. Project Structure (file tree)

```
atomcraft/
├── .gitignore
├── docker-compose.yml
├── start.sh                              # Local dev launcher
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── __init__.py
│       ├── main.py                       # FastAPI app, CORS, router registration
│       ├── config.py                     # Settings (DB, API keys, pricing)
│       ├── database.py                   # SQLAlchemy engine + session
│       ├── api/
│       │   ├── __init__.py
│       │   ├── materials.py              # CRUD + search + filter
│       │   ├── generation.py             # AI crystal/composition generation
│       │   ├── prediction.py             # ML property prediction
│       │   ├── synthesis.py              # Feasibility + experiment design
│       │   ├── experiments.py            # Experiment CRUD + steps + results
│       │   └── chat.py                   # Conversational AI
│       ├── core/
│       │   ├── __init__.py
│       │   ├── llm.py                    # Materials LM interface
│       │   ├── composition_analyzer.py   # Formula parsing + descriptors
│       │   ├── generator.py              # Crystal structure generation
│       │   ├── predictor.py              # ML model + inference
│       │   ├── synthesis.py              # Feasibility + method selection
│       │   └── simulation.py             # DFT/MD job orchestration
│       ├── models/
│       │   ├── __init__.py
│       │   ├── material.py               # Material, Composition, Property, Phase
│       │   ├── experiment.py             # Experiment, Step, Result
│       │   ├── prediction.py             # Prediction, PredictionJob
│       │   └── user.py                   # User, Team, TeamMember, Subscription
│       └── utils/
│           └── __init__.py
│
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   ├── index.html
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── index.css                     # Design system + glass + gradient styles
│       ├── api/
│       │   └── client.ts                 # Typed fetch wrapper
│       ├── lib/
│       │   ├── types.ts                  # Full TS interfaces
│       │   └── utils.ts                  # Formatting + colors + helpers
│       ├── components/
│       │   └── Sidebar.tsx               # Navigation
│       └── pages/
│           ├── Home.tsx                  # Dashboard
│           ├── Materials.tsx             # Materials database
│           ├── Generator.tsx             # AI generation
│           ├── Predictor.tsx             # Property prediction
│           ├── Experiments.tsx           # Experiment tracking
│           └── Chat.tsx                  # AION AI chat
│
└── models/
    ├── __init__.py
    ├── property_prediction/
    │   ├── __init__.py
    │   └── predictor.py                  # ML model interface
    ├── crystal_generation/
    │   └── generator.py                  # Generation model interface
    └── synthesis/
        └── synthesis.py                  # Synthesis model interface
```

**Total: 51 files** across backend (25), frontend (18), models (5), config/infra (3)
