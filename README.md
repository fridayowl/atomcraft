# Atomcraft ⚗️

<p align="center">
  <img src="https://img.shields.io/github/license/fridayowl/atomcraft?style=flat-square" alt="License">
  <img src="https://img.shields.io/github/stars/fridayowl/atomcraft?style=flat-square" alt="GitHub Stars">
  <img src="https://img.shields.io/github/actions/workflow/status/fridayowl/atomcraft/.github/workflows/ci.yml?branch=main&style=flat-square" alt="CI Status">
  <img src="https://img.shields.io/badge/python-3.12%2B-blue?style=flat-square" alt="Python 3.12+">
  <img src="https://img.shields.io/badge/node-18%2B-green?style=flat-square" alt="Node 18+">
  <img src="https://img.shields.io/badge/docker-ready-2496ED?style=flat-square&logo=docker" alt="Docker Ready">
  <img src="https://img.shields.io/badge/PRs-welcome-brightgreen?style=flat-square" alt="PRs Welcome">
</p>

**Atomcraft** (formerly AION) is the **AI operating system for accelerated materials discovery**. It connects generative AI, computational simulation, synthesis feasibility, and experiment tracking into a single closed-loop platform.

Researchers describe their target requirements in **natural language** — Atomcraft generates candidates, predicts properties, validates with simulation (DFT/MD), recommends synthesis routes, and learns from every experiment (both successes and failures).

> **From prompt to synthesis-ready material in hours, not years.**

---

## 📡 Quick Navigation

- [Architecture](#-architecture-overview)
- [Technical Deep Dive](#-technical-deep-dive)
- [Run Locally](#-run-locally)
- [Run with Docker](#-run-with-docker)
- [API Reference](#-api-reference)
- [ML Models & Performance](#-ml-models--performance)
- [Vision & Roadmap](#-vision--roadmap)
- [Expanding to Drug Discovery](#-expanding-to-drug-discovery--molecular-medicine)
- [LLM Strategy](#-llm-strategy)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🏗️ Architecture Overview

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         FRONTEND (React 18 + TS + Tailwind)             │
│  ┌──────────┬──────────────┬─────────────┬────────────┬──────────────┐  │
│  │Dashboard │  Materials   │  Generator  │ Predictor  │ Experiments  │  │
│  │ (Home)   │  Database    │  (AI Gen)   │ (ML Prop)  │ (Tracking)   │  │
│  └──────────┴──────────────┴─────────────┴────────────┴──────────────┘  │
│  ┌──────────────────────────────────────────────────────────────────────┤
│  │                  Discover (Multi-stage Pipeline)                     │
│  │         Chat (Conversational AI Interface)                           │
│  └──────────────────────────────────────────────────────────────────────┘
├──────────────────────────────────────────────────────────────────────────┤
│                       API LAYER (FastAPI + Uvicorn)                      │
│  ┌──────────┬──────────────┬─────────────┬────────────┬──────────────┐  │
│  │Materials │   Generate   │   Predict   │ Synthesis  │ Experiments  │  │
│  │  CRUD    │  /crystals   │  / + /batch │ /feasibility│ CRUD+Steps   │  │
│  │  Search  │ /compositions│/feature-imp │/design-exp  │  +Results    │  │
│  ├──────────┼──────────────┼─────────────┼────────────┼──────────────┤  │
│  │  Chat    │    Auth      │  Discover   │ Screening  │ Phase Diagram│  │
│  │  /query  │  /signup     │ / (pipeline)│ /constrain │  /            │  │
│  │  /suggest│  /login      │             │ /screen+gen│              │  │
│  ├──────────┼──────────────┼─────────────┼────────────┼──────────────┤  │
│  │Charact.  │   Reports    │  API Keys   │            │              │  │
│  │/xrd/sim  │  /pdf        │  /manage    │            │              │  │
│  └──────────┴──────────────┴─────────────┴────────────┴──────────────┘  │
├──────────────────────────────────────────────────────────────────────────┤
│                       CORE SERVICES                                     │
│  ┌─────────────────┬──────────────────┬───────────────────┬───────────┐ │
│  │ Materials LLM   │ Crystal Generator│ Property Predictor│ Synthesis │ │
│  │ (GPT-4o via     │ (Diffusion-based │ (11 RandomForest  │ Engine    │ │
│  │  LangChain)     │  + template-based│  models, 56-feat  │ (5 methods│ │
│  │                 │  substitution)   │  descriptor vec)  │  + scoring)│ │
│  ├─────────────────┼──────────────────┼───────────────────┼───────────┤ │
│  │ DFT Orchestrator│ Composition      │ Active Learning   │ Battery   │ │
│  │ (VASP/QE/CP2K/  │ Analyzer         │ Loop (pseudo +    │ Suitability│ │
│  │  LAMMPS inputs) │ (67-element db)  │  DFT mode)        │ Assessor  │ │
│  └─────────────────┴──────────────────┴───────────────────┴───────────┘ │
│  ┌──────────────────────────────────────────────────────────────────────┐ │
│  │  Celery Workers (async job queue via Redis broker)                   │ │
│  │  run_property_prediction | run_simulation_job                        │ │
│  └──────────────────────────────────────────────────────────────────────┘ │
├──────────────────────────────────────────────────────────────────────────┤
│                       DATA LAYER                                        │
│  ┌──────────────┬─────────────────┬──────────────┬──────────────────┐   │
│  │ PostgreSQL    │     Neo4j       │    Redis     │  SQLite (dev)    │   │
│  │ (primary DB) │ Knowledge Graph │ Job Queue +  │ (104,842 MP     │   │
│  │              │ (async driver)  │ Cache        │  entries seeded) │   │
│  └──────────────┴─────────────────┴──────────────┴──────────────────┘   │
└──────────────────────────────────────────────────────────────────────────┘
```

### Service Architecture

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | React 18, TypeScript, Vite 5, Tailwind CSS, Recharts, Three.js | Dashboard, materials DB, generator, predictor, experiments, chat, 3D crystal viewer |
| **API** | FastAPI, Pydantic v2, Uvicorn (4 workers) | RESTful endpoints with automatic OpenAPI docs |
| **AI/ML** | 11 RandomForest models, 112-class space group classifier, LangChain + GPT-4o | Property prediction, crystal generation, conversational AI |
| **Compute** | Celery + Redis (async tasks), DFT input generators (VASP/QE/CP2K/LAMMPS) | Background job processing, simulation orchestration |
| **Storage** | PostgreSQL, Neo4j (knowledge graph), Redis (cache/queue), SQLite (dev fallback) | Structured data, graph relationships, job queuing, local development |
| **Auth** | JWT (python-jose), bcrypt, API key generation | User management, team collaboration, API access control |

---

## 🔬 Technical Deep Dive

### 1. Materials Data Model

9 SQLAlchemy ORM tables covering the full discovery lifecycle:

**`materials`** — Core material entries with crystallographic data
| Field | Type | Description |
|-------|------|-------------|
| `id` | Integer | Primary key |
| `formula` | String | Chemical formula (e.g., LiCoO₂) |
| `name` | String | Common name |
| `formula_html` | Text | HTML-rendered formula with subscripts |
| `space_group` | String | Crystallographic space group (e.g., R-3m) |
| `crystal_system` | String | Crystal system (hexagonal, cubic, etc.) |
| `lattice_a/b/c` | Float | Lattice parameters in Å |
| `lattice_alpha/beta/gamma` | Float | Lattice angles in degrees |
| `volume` | Float | Unit cell volume in Å³ |
| `density` | Float | Calculated density in g/cm³ |
| `cif_data` | Text | Full Crystallographic Information File content |
| `mp_id` | String | Materials Project identifier |
| `tags` | JSON | User-defined tags |
| `public` | Boolean | Visibility flag |

**`compositions`** — Elemental breakdown (element, amount, atomic_fraction)
**`properties`** — Computed or measured properties (type, value, unit, source, confidence)
**`phases`** — Phase stability (temperature/pressure ranges, stability classification)

**`experiments`** — Synthesis and characterization experiments
| Field | Type | Description |
|-------|------|-------------|
| `synthesis_method` | String | solid_state, sol_gel, hydrothermal, CVD, mechanochemical |
| `synthesis_conditions` | JSON | Temperature, pressure, atmosphere, dwell time |
| `precursor_materials` | JSON | List of starting materials |
| `successful` | Boolean | Did it produce the target phase? |

**`experiment_steps`** — Step-by-step procedure tracking (step_number, step_type, duration, temperature, pressure, atmosphere)
**`experiment_results`** — Characterization outputs (XRD, SEM, EDS, XPS, TEM, etc.)

**`predictions`** — ML model outputs with feature importance and validation tracking
**`prediction_jobs`** — Async computation tracking with DFT cost accounting

**`users`, `teams`, `team_members`** — Multi-user collaboration with role-based access

### 2. Composition Analyzer

The `CompositionAnalyzer` (`backend/app/core/composition_analyzer.py`) parses chemical formulas using regex + pymatgen fallback, then computes **17 compositional descriptors** from a **67-element database** including:

- Average atomic radius, electronegativity (Pauling scale), atomic mass, valence electron count
- Electronegativity range, radius range
- Baseline property heuristics (band gap from electronegativity difference, formation energy from electronegativity, density from mass/volume scaling)

### 3. Crystal Generator

`MaterialsGenerator` (`backend/app/core/generator.py`) uses two strategies:

**De-novo generation**: Random compositions from a **68-element pool** (all transition metals, alkali, alkaline earth, halogens, chalcogens, lanthanides). Space group predicted from composition via ML classifier. Properties predicted via ensemble models.

**Substitution (template-based)**: Element substitutions from **17 chemical groups** applied to **104,842 Materials Project template structures**. Groups include alkali (Li→Na→K→Rb→Cs), halogens (F→Cl→Br→I), chalcogens (O→S→Se→Te), and transition metal series.

Supports **230 space group numbers** mapped to **7 crystal systems**. Each candidate includes formula, space group, crystal system, lattice parameters, element composition, and multiple fitness scores.

### 4. ML Property Predictor

`PropertyPredictor` (`backend/app/core/predictor.py`) loads **11 trained RandomForest models**:

| Property | Samples | R² | Utility |
|----------|---------|----|---------|
| density | 104,842 | **0.97** | Highly reliable density estimation |
| formation_energy | 104,842 | **0.94** | Thermodynamic stability screening |
| energy_above_hull | 104,842 | 0.77 | Decomposition tendency |
| total_magnetization | 104,842 | 0.66 | Magnetic property screening |
| band_gap | 52,602 | 0.59 | Electronic property ranking |
| is_stable | 104,842 | 0.40 | Binary stability classifier |
| homogeneous_poisson | 9,359 | 0.04 | Elastic property (data-limited) |
| universal_anisotropy | 9,359 | -0.17 | Elastic anisotropy (data-limited) |
| e_electronic | 4,958 | 0.20 | Dielectric constant |
| e_ionic | 4,958 | 0.16 | Ionic contribution to dielectric |
| e_total | 4,958 | 0.09 | Total dielectric constant |

Each model uses a **56-feature compositional descriptor vector** (elemental properties aggregated via mean, variance, range, min, max across constituent elements). The `trainer.py` module handles auto-retraining when new experimental data is added.

### 5. Space Group Classification

A RandomForest classifier trained on **112 space groups** (those with >50 samples in MP). Achieves **95.9% training accuracy** across 23,763 samples. Features extracted via ELEMENT_DATA (no pymatgen overhead, fast inference).

### 6. Synthesis Engine

`SynthesisEngine` (`backend/app/core/synthesis.py`) assesses feasibility for **5 synthesis methods**:

| Method | Temp Range | Best For | Scoring Factors |
|--------|-----------|----------|-----------------|
| **Solid-state** | 600–1500°C | Oxides, sulfides, intermetallics | Melting point, decomposition, precursor cost |
| **Sol-gel** | 300–1000°C | Oxides, nanomaterials, thin films | Hydrolysis rate, pH sensitivity, solvent compatibility |
| **Hydrothermal** | 100–500°C | Zeolites, metastable phases, MOFs | Aqueous solubility, pressure limits, autoclave constraints |
| **CVD** | 400–1200°C | Thin films, 2D materials, coatings | Vapor pressure, precursor volatility, substrate matching |
| **Mechanochemical** | 25–200°C | Metastable phases, alloys, nanocomposites | Milling energy, ductility, contamination risk |

Feasibility scoring (0–100%) considers: elemental melting points, decomposition temperatures, air/moisture sensitivity of precursors, and equipment availability. Automatically designs step-by-step experimental procedures with temperature ramping, atmosphere control, and characterization recommendations.

### 7. DFT Simulation Orchestrator

`DFTOrchestrator` (`backend/app/core/dft.py`) generates production-ready input files for:

- **VASP**: INCAR, POSCAR, KPOINTS, POTCAR generation with pymatgen
- **Quantum ESPRESSO**: PW input generation
- **CP2K**: Input file generation
- **LAMMPS**: Molecular dynamics input generation

Supports job submission via **local** (subprocess), **Slurm** (sbatch), and **PBS** (qsub) schedulers. Parses OUTCAR, vasprun.xml, OSZICAR for VASP outputs. Cost estimation in USD based on atom count and calculation type.

### 8. Active Learning Loop

`ActiveLearningLoop` (`backend/app/core/active_learning.py`) implements a **5-step closed-loop cycle**:

```
1. GENERATE → 2. PREDICT → 3. SELECT (by uncertainty) → 4. VALIDATE → 5. RETRAIN
```

**Pseudo mode** (no DFT required): Uses predictor output as validation — stores predicted values into DB, retrains all 11 models. Perfect for testing and exploration.

**DFT mode** (needs cluster): Submits VASP/QE jobs for the most uncertain candidates, uses DFT-relaxed values for retraining.

Selection strategy: `confidence ∝ 1 / (|E_form| + 0.1)` — materials near the convex hull (most likely synthesizable) get validated first.

### 9. Battery Materials Assessment

`BatteryAssessor` (`backend/app/core/battery.py`) evaluates materials for **cathode, anode, and solid electrolyte** applications using:
- Band gap thresholds (cathode: 1.5–3.5 eV, electrolyte: >4.0 eV)
- Formation energy stability (anode: <0 eV, cathode: <0 eV)
- Element overlap with known battery element pools (Li, Na, Ni, Mn, Co, Fe, etc.)
- Composite scoring with application-specific weights

### 10. Knowledge Graph (Neo4j)

`KnowledgeGraphClient` (`backend/app/core/neo4j_client.py`) provides async Cypher queries for:
- Property-specific material search
- Related material discovery via graph traversal
- Synthesis pathway exploration
- Element statistics across the dataset
- Bulk data seeding

### 11. XRD Simulation

`XRDSimulator` (`backend/app/core/xrd.py`) simulates powder XRD patterns from space group + lattice parameters. Computes d-spacings, simulates intensities with Lorentz-polarization factor, assigns Miller indices. Integrated into the discovery pipeline for rapid phase identification.

### 12. Materials LLM (Conversational AI)

`MaterialsLLM` (`backend/app/core/llm.py`) wraps **OpenAI GPT-4o** via LangChain with a materials science system prompt. Supports:
- **Query mode**: Answer materials science questions, explain concepts, interpret results
- **Suggest mode**: Recommend materials from natural language requirements
- **Characterization analysis**: Interpret XRD, SEM, XPS patterns

Gracefully falls back to canned responses if no API key is configured. Models zero-shot performance with materials science RAG augmentation planned for v0.2.

### 13. Celery Async Workers

`Celery` (`backend/app/celery_app.py`) with Redis broker handles:
- `run_property_prediction`: Batch property prediction tasks
- `run_simulation_job`: DFT/MD simulation orchestration

### 14. Frontend Architecture

| Page | Route | Features |
|------|-------|----------|
| **Dashboard** | `/` | Stats overview, activity chart (Recharts), quick AI chat, recent materials & experiments |
| **Materials** | `/materials` | Full CRUD, search, CIF import/export, 3D crystal viewer (Three.js), property visualization |
| **Generator** | `/generator` | Natural language input, element constraints, candidate ranking, synthesis check |
| **Discover** | `/discover` | Multi-stage pipeline: generate → filter by application → property constraints → ranked candidates |
| **Predictor** | `/predict` | Single + batch prediction, bar chart comparison, feature importance, confidence indicators |
| **Experiments** | `/experiments` | Experiment designer, step-by-step tracking, status workflow, negative result capture |
| **Chat** | `/chat` | Conversational AI, dual mode (chat/suggest), quick prompts, thinking indicator |

**Design system**: Dark theme with indigo/purple accent gradient, glass morphism panels, subtle dot grid background, custom scrollbar, shimmer loading animations, JetBrains Mono for data display.

**3D Crystal Viewer**: Renders atoms as colored spheres with bonds using `@react-three/fiber` and `drei`. Supports 40+ element colors, auto-rotation, and interactive orbit controls.

---

## 🚀 Run Locally

### Prerequisites

- **Python 3.12+** (recommended: 3.13)
- **Node.js 18+ & npm**
- **~5 GB free disk** (for 104k materials database + ML models)

### Step 1: Clone & Setup Backend

```bash
git clone https://github.com/fridayowl/atomcraft.git
cd atomcraft

# Create virtual environment
python3.13 -m venv .venv
source .venv/bin/activate

# Install Python dependencies
pip install -r backend/requirements.txt
```

### Step 2: Verify the Database & Models

```bash
cd backend

# Check database loads (104,842 materials)
python -c "
from app.database import SessionLocal
from app.models.material import Material
db = SessionLocal()
print(f'Materials in DB: {db.query(Material).count()}')
db.close()
"

# Test a prediction
python -c "
import sys; sys.path.insert(0, '.')
from app.core.trainer import predict_property
gap, conf = predict_property('BaTiO3', 'band_gap')
print(f'BaTiO3 band gap = {gap:.3f} eV (confidence: {conf:.3f})')
"
```

Expected output:
```
Materials in DB: 104842
BaTiO3 band gap = 2.197 eV (confidence: 0.850)
```

### Step 3: Run the Demo

```bash
python backend/run_demo.py
```

This runs the full cathode discovery pipeline:
1. Generates 15 novel cathode candidates (Li-Ni-Mn-Co-O space)
2. Predicts band gap, formation energy, density for each
3. Shows top 5 most stable + top 5 highest band gap
4. Runs 10 substitution-based candidates from MP templates
5. Prints feature importance analysis (which compositional features drive each property)
6. Generates VASP input files for the best candidate
7. Runs 1 active learning iteration (adds 3 pseudo-validated samples + retrains all 11 models)

### Step 4: Start the Full Stack (Backend + Frontend)

**Option A: Helper script**
```bash
./start.sh
```
This auto-creates venvs, installs deps (backend + frontend), and runs both concurrently.

**Option B: Manual**
```bash
# Terminal 1 - Backend API
source .venv/bin/activate
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 - Frontend
cd frontend
npm install
npm run dev
```

**Access:**
- **Frontend**: http://localhost:5173
- **API Docs (Swagger UI)**: http://localhost:8000/docs
- **API Docs (ReDoc)**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

### Quick API Tests

```bash
# Predict properties for a material
curl -X POST http://localhost:8000/api/predict/ \
  -H "Content-Type: application/json" \
  -d '{"formula": "BaTiO3", "properties": ["band_gap", "formation_energy", "density"]}'

# Generate de-novo candidate materials
curl -X POST http://localhost:8000/api/generate/denovo \
  -H "Content-Type: application/json" \
  -d '{"num_candidates": 5, "element_constraints": ["Li", "Co", "O"], "target_properties": {"band_gap": 2.0}}'

# Get feature importance
curl http://localhost:8000/api/predict/feature-importance/band_gap
```

---

## 🐳 Run with Docker

### Single Command

```bash
docker-compose up --build
```

This starts the full stack with 5 services:

| Service | Image | Port | Purpose |
|---------|-------|------|---------|
| `backend` | Custom Python 3.12-slim | `8000` | FastAPI + Uvicorn (4 workers) |
| `frontend` | Custom Node 20-alpine | `5173` | Vite dev server |
| `db` | PostgreSQL 16 | `5432` | Primary relational database |
| `redis` | Redis 7 | `6379` | Celery broker + cache |
| `neo4j` | Neo4j 5 | `7474` (web) / `7687` (bolt) | Materials knowledge graph |

### Service URLs

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Neo4j Browser**: http://localhost:7474 (default credentials: neo4j/atomcraft123)

### Docker Compose Configuration

```yaml
services:
  backend:    # FastAPI on :8000, 4 uvicorn workers, auto-trains models on build
  frontend:   # Vite on :5173, proxies /api -> backend:8000
  db:         # PostgreSQL 16 with persistent volume
  redis:      # Redis 7, ephemeral (no volume needed)
  neo4j:      # Neo4j 5 with persistent volume + auth
```

### Persistent Volumes

- `postgres_data` → `/var/lib/postgresql/data`
- `neo4j_data` → `/data`
- `aion_data` → Shared volume for uploaded CIF files and job artifacts

### Environment Variables

Configure via `backend/.env` or environment overrides:

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:///./aion.db` | PostgreSQL in Docker: `postgresql://aion:aion123@db:5432/aion` |
| `NEO4J_URI` | `bolt://localhost:7687` | Neo4j connection string |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection string |
| `OPENAI_API_KEY` | `""` | GPT-4o API key (optional, fallback responses used if empty) |
| `MP_API_KEY` | — | Materials Project API key |
| `JWT_SECRET` | Auto-generated | JWT signing secret |

---

## 📖 API Reference

### Materials

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/materials/` | List/search materials (filter by element, space_group, property range) |
| `GET` | `/api/materials/{id}` | Full detail with properties, composition, phases, 3D structure |
| `POST` | `/api/materials/` | Create new material entry |
| `DELETE` | `/api/materials/{id}` | Remove material and related data |
| `POST` | `/api/materials/import-cif` | Import material from CIF file |
| `GET` | `/api/materials/{id}/export-cif` | Export material as CIF file |

### Generation

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/generate/crystals` | Substitution-based crystal generation from MP templates |
| `POST` | `/api/generate/compositions` | Random + substitution composition generation |
| `POST` | `/api/generate/denovo` | De-novo composition & crystal generation |

**Request body:**
```json
{
  "target_properties": {"band_gap": 3.0},
  "element_constraints": ["Li", "Mn", "O"],
  "num_candidates": 10
}
```

### Prediction

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/predict/` | Single property prediction |
| `POST` | `/api/predict/batch` | Batch prediction for multiple formulas |
| `GET` | `/api/predict/feature-importance/{property}` | Feature importance for a property model |

**Predict request:**
```json
{
  "formula": "BaTiO3",
  "properties": ["band_gap", "formation_energy", "density"]
}
```

### Synthesis

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/synthesis/feasibility` | Assess synthesis feasibility (scoring + recommended methods) |
| `POST` | `/api/synthesis/design-experiment` | Generate full step-by-step experimental procedure |
| `GET` | `/api/synthesis/methods` | List available synthesis methods with profiles |

### Experiments

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/experiments/` | List experiments (filter by material, status) |
| `GET` | `/api/experiments/{id}` | Full experiment with steps and results |
| `POST` | `/api/experiments/` | Create new experiment |
| `POST` | `/api/experiments/{id}/steps` | Add procedural step |
| `POST` | `/api/experiments/{id}/results` | Record characterization result |
| `PATCH` | `/api/experiments/{id}/status` | Update experiment status |

### Chat & AI

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/chat/query` | Ask materials science questions |
| `POST` | `/api/chat/suggest` | Get material suggestions from requirements |

### Discovery Pipeline

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/discover/` | Full pipeline: generate → predict → assess synthesis → battery check → XRD → ranking |

### Screening

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/screening/` | Basic property-based screening |
| `POST` | `/api/screening/constrained` | Screening with element + property constraints |
| `POST` | `/api/screening/generate-and-screen` | Generate then screen candidates |

### System

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Platform info with all available endpoints |
| `GET` | `/health` | Health check (DB, Redis, Neo4j status) |
| `POST` | `/api/auth/signup` | User registration |
| `POST` | `/api/auth/login` | JWT authentication (OAuth2 password flow) |
| `GET` | `/api/auth/me` | Current user profile |

---

## 🧠 ML Models & Performance

### Best Performing Models

| Property | R² | MAE | Samples | Recommended Use |
|----------|-----|-----|---------|-----------------|
| density | **0.97** | 0.18 g/cm³ | 104,842 | High-confidence density estimation |
| formation_energy | **0.94** | 0.11 eV/atom | 104,842 | Reliable stability screening |
| energy_above_hull | **0.77** | 0.08 eV/atom | 104,842 | Good decomposition predictor |
| total_magnetization | **0.66** | 1.21 μB | 104,842 | Moderate magnetic screening |
| band_gap | **0.59** | 0.84 eV | 52,602 | Useful for ranking, not absolute values |

### Data-Limited Models (Improve with more data)

| Property | R² | Samples | Bottleneck |
|----------|-----|---------|------------|
| universal_anisotropy | -0.17 | 9,359 | Extreme outliers in elastic data |
| e_total | 0.09 | 4,958 | Very limited dielectric measurements |
| homogeneous_poisson | 0.04 | 9,359 | Small elastic dataset |

### Model Architecture

- **Algorithm**: RandomForest (scikit-learn) — chosen for fast training, interpretability, and strong performance on tabular compositional data
- **Features**: 56-dimensional vector of compositional descriptors (mean, variance, range, min, max of: atomic radius, electronegativity, atomic mass, valence electrons, period, group, block, etc.)
- **Space Group Classifier**: 112 classes, 95.9% accuracy on 23,763 training samples
- **Training Pipeline**: Auto-trains on startup if `.joblib` files are missing; auto-retrains when new experimental data is added
- **Interface**: Extensible — swap to GNNs (CGCNN, MEGNet) or graph transformers via the `models/` interface layer

### Model Storage

All models are serialized as `.joblib` files (tracked via Git LFS) in `backend/app/core/models/`:
- 11 RandomForest regressors (one per property)
- 1 RandomForest classifier (space group)
- `model_config.json`: R², MAE, sample count per model
- `spg_cache.json`: 269 space group symbol↔number mappings

---

## 🔭 Vision & Roadmap

### Near-Term (v0.2 → v0.5)

- [ ] **GNN-based property prediction** — Replace RandomForest with CGCNN / MEGNet for higher accuracy on all properties
- [ ] **Diffusion-based crystal generation** — Integrate MatterGen / DiffCSP for state-of-the-art structure prediction
- [ ] **Materials Project live sync** — Auto-enrich materials with latest MP data on import
- [ ] **HuggingFace model hub integration** — Push/pull fine-tuned materials models
- [ ] **Stripe subscription billing** — Free → Researcher → Team → Enterprise tiers
- [ ] **Cloud DFT backend** — Auto-deploy VASP/QE jobs to AWS/Azure/GCP HPC
- [ ] **Multi-fidelity active learning** — Bayesian optimization across ML → DFT → Experiment
- [ ] **Phase diagram auto-generation** — Binary and ternary phase diagrams from DB entries
- [ ] **PDF report generator** — One-click material reports with WeasyPrint
- [ ] **Knowledge graph visualization** — Interactive Neo4j graph in the browser

### Long-Term (v0.5 → v1.0+)

- [ ] **Multi-modal materials AI** — Combine text, structure, graph, and image understanding in one model
- [ ] **Autonomous lab integration** — Connect to robotic synthesis + automated characterization rigs
- [ ] **400K+ material universe** — Expand from 104K MP entries to include OQMD, JARVIS-DFT, ICSD, COD
- [ ] **Inverse design at scale** — Given target properties, directly generate synthesizable candidates
- [ ] **Fine-tuned open-source LLM** — Replace GPT-4o with Llama/Mistral fine-tuned on materials literature
- [ ] **Collaborative research workspaces** — Real-time shared projects, versioned experiments, team knowledge graphs

### Platform Expansion

Atomcraft is designed as a **domain-agnostic AI discovery platform**. The architecture generalizes to any structured discovery problem:

| Domain | Atomcraft Adaptation |
|--------|---------------------|
| **Thermoelectrics** | Predict ZT, power factor, thermal conductivity; screen Zintl phases, half-Heuslers |
| **Catalysis** | Predict adsorption energy, activity descriptors; screen alloys, oxides, MOFs |
| **Photovoltaics** | Predict PCE, absorption spectrum; screen perovskites, chalcogenides |
| **Superconductors** | Predict Tc from composition + structure; screen hydrides, intermetallics |
| **2D Materials** | Predict exfoliation energy, band structure; screen layered compounds |
| **MOFs/COFs** | Predict pore size, gas uptake; screen building blocks for target applications |
| **Energy Storage (beyond Li)** | Na-ion, K-ion, Mg-ion, Zn-ion battery material discovery |
| **Structural Materials** | Predict yield strength, toughness; screen high-entropy alloys |

---

## 💊 Expanding to Drug Discovery & Molecular Medicine

Atomcraft's architecture is inherently **cross-domain**. The same closed-loop AI discovery pipeline applies to molecular medicine with targeted adaptations:

### Conceptual Mapping

| Atomcraft (Materials) | Parallel in Drug Discovery |
|----------------------|---------------------------|
| Crystal structure generator | Molecular generator (SMILES → 3D conformer) |
| 56-feature compositional descriptors | Molecular fingerprints (ECFP, MACCS, Mordred) |
| Band gap / formation energy prediction | Bioactivity / toxicity / ADME prediction |
| Synthesis feasibility (solid-state, sol-gel, CVD) | Retrosynthesis (forward/reverse synthesis planning) |
| DFT simulation orchestration | Molecular docking + MD simulation orchestration |
| Materials Project database (104K entries) | ChEMBL / PubChem / ZINC (millions of compounds) |
| Battery suitability assessment | Target-specific activity scoring (kinase, GPCR, etc.) |
| Space group classification | Molecular property classification (Lipinski, logP, etc.) |
| CIF / MPID identifiers | SMILES / InChI / PubChem CID identifiers |

### How to Extend

**1. Swap the Generator**
```
MaterialsGenerator.generate_denovo()
    ↓
MolecularGenerator.generate_molecules()
    - SMILES enumeration
    - Fragment-based growth
    - Reinforcement learning (REINVENT, MolDQN)
    - Diffusion models (DiG, GeoDiff)
```

**2. Swap the Property Predictor**
```
PropertyPredictor.predict(formula, "band_gap")
    ↓
BioactivityPredictor.predict(SMILES, "pIC50_target_EGFR")
    - Graph Neural Networks (AttentiveFP, MPNN)
    - Transformer-based (ChemBERTa, MolFormer)
    - Multi-task: activity + toxicity + solubility + metabolism
```

**3. Add Docking Orchestrator**
```
DFTOrchestrator (VASP/QE for materials)
    ↓
DockingOrchestrator (AutoDock Vina, Glide, Gold for molecules)
    - Protein-ligand docking
    - MD simulation (GROMACS, Amber)
    - Binding free energy estimation (MM-PBSA, FEP)
```

**4. Add Retrosynthesis Engine**
```
SynthesisEngine (solid-state methods)
    ↓
RetrosynthesisEngine (forward/reverse synthesis)
    - Template-based (Pistachio, Reaxys)
    - Template-free (Molecular Transformer)
    - Route scoring by yield, cost, step count
```

**5. Update the LLM Prompt**
```
System prompt: "You are an expert materials scientist..."
    ↓
System prompt: "You are an expert medicinal chemist..."
    - Druglikeness rules (Lipinski, Veber)
    - Target biology knowledge
    - Assay interpretation
    - Patent landscape awareness
```

### What Stays the Same

- **Frontend** (Dashboard, Search, Generator, Predictor, Experiments, Chat) — all UI components are domain-agnostic
- **API Layer** (FastAPI routers, JWT auth, API keys, async jobs) — identical
- **Active Learning Loop** — identical: generate → predict → select → validate → retrain
- **Celery Workers** — identical async job infrastructure
- **Experiment Tracking** — identical: planned → running → completed/failed with negative result capture
- **Knowledge Graph** — Neo4j schema adapts trivially (nodes become molecules/proteins instead of materials)
- **Multi-user tiers** — identical pricing model

### Integration with KREO & Generative Medicine

KREO (Knowledge-driven Retrosynthetic Exploration & Optimization) systems can be integrated as a **plug-in synthesis module**:

1. **KREO Integration Point**: Replace the `SynthesisEngine` with KREO's retrosynthesis API
2. **Dual-mode generation**: Materials-style de-novo generation + KREO-style scaffold hopping
3. **Shared active learning**: KREO's synthesis outcomes feed Atomcraft's retraining pipeline
4. **Combined scoring**: Synthesizability (KREO) × Bioactivity (Atomcraft predictor) × ADME

This creates a **unified generative medicine platform** where:
- A medicinal chemist describes the target profile in natural language
- Atomcraft generates candidate molecules + predicts bioactivity
- KREO plans the synthesis route + scores feasibility
- The platform designs experiments, tracks results, and learns from failures

---

## 🧬 LLM Strategy

### Current: GPT-4o via LangChain

The `MaterialsLLM` wraps OpenAI's GPT-4o with structured prompts for materials science reasoning. This works well for zero-shot Q&A but has limitations: domain nuance, hallucination risk, API cost, and no private deployment.

### Planned Upgrade Path

**Phase 1 — Retrieval-Augmented Generation (RAG)**
```
User Query → Embed (text-ada-002) → Vector Search (Pgvector / Pinecone)
    → Retrieved context (papers, databases, past predictions)
    → GPT-4o with context → Grounded Answer
```
- Reduces hallucination
- Grounds answers in actual database materials
- Enables citation-aware responses

**Phase 2 — Fine-tuned Open-Source LLM**
Fine-tune a **7B–70B parameter model** (Llama 3, Mistral, Qwen) on:
- 10M+ tokens of materials science literature (arXiv, journal corpora)
- Structured prediction data from the platform (formulas → properties)
- Experimental procedure texts (synthesis methods, characterization protocols)
- User interaction logs (chat queries + preferred responses)

**Fine-tuning architecture:**
```
Base: Llama-3-8B / Mistral-7B / Qwen2.5-7B
Method: QLoRA (Quantized Low-Rank Adaptation)
Data: ~1M instruction pairs (generated + human-curated)
Cost: ~$50–500 per fine-tuning run (RunPod / Lambda Labs / Together)
Storage: 8–16 GB (4-bit quantized)
Inference: Single GPU (A10G / RTX 4090) or CPU (llama.cpp)
```

**Phase 3 — Multi-modal Materials AI**
```
Single model handling:
  ┌─ Text: "What's the band gap of LiCoO2?"
  ├─ Structure: CIF files, crystal graphs
  ├─ Image: XRD patterns, SEM micrographs, phase diagrams
  └─ Data: Property tables, composition graphs
→ Unified embedding space for materials
```

**Phase 4 — Autonomous Materials Scientist**
- LLM agent with tool use (execute predictions, run generators, design experiments)
- Self-improving via chain-of-thought + experiment feedback
- Natural language → SQL → API calls → Results → Natural language summary
- Fine-tuned on successful discovery trajectories

**Phase 5 — Domain-Adapted Fine-Tuning for Medicine**
```
Same pipeline, different training corpus:
Materials science text → Biomolecular / pharmacological text
CIF data → SMILES / Protein sequences
Synthesis methods → Retrosynthesis routes
DFT validation → Docking / MD validation
```

---

## 🤝 Contributing

We welcome contributions! Whether it's new models, UI improvements, documentation, or bug fixes:

1. **Fork** the repo
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Commit** your changes: `git commit -m 'Add amazing feature'`
4. **Push**: `git push origin feature/amazing-feature`
5. **Open a Pull Request**

### Development Setup

```bash
# Backend
source .venv/bin/activate
cd backend
pip install -r requirements.txt
pytest tests/ -v  # Run tests

# Frontend
cd frontend
npm install
npm run build  # TypeScript + Vite build
npx playwright test  # E2E tests (if browsers installed)

# Linting
cd backend
ruff check .
mypy app/
```

### CI Pipeline

Every PR runs automatically:
- **Backend**: Python 3.12, install deps, train models, run 195+ API tests + 307+ core tests (with PostgreSQL service)
- **Frontend**: Node 20, npm ci, full TypeScript build
- **Lint**: Ruff (Python) + MyPy (type checking)
- **Docker**: Build backend + frontend images, verify compose starts

---

## 📦 What's Included

| File | Size | Description |
|------|------|-------------|
| `aion.db` | ~500 MB | 104,842 Materials Project entries (SQLite) |
| `*.joblib` (11 files) | ~300 MB | Trained RandomForest property prediction models |
| `model_config.json` | ~3 KB | Model metadata (R², MAE, sample count per property) |
| `spg_cache.json` | ~4 KB | 269 space group symbol → number mappings |
| `test.db` | — | Pre-populated test database |
| `docs/AION_PLATFORM_SPEC.md` | 615 lines | Complete platform specification |
| `docs/USER_GUIDE.md` | 424 lines | Detailed user guide with code examples |
| `docs/samples/cathode_discovery_demo.txt` | 70 lines | Sample demo output |

---

## ⚖️ License

Distributed under the **MIT License**. See `LICENSE` for more information.

---

<p align="center">
  <b>Star ⭐ on GitHub</b> — Help us accelerate materials and molecular discovery with AI.
  <br>
  <a href="https://github.com/fridayowl/atomcraft/issues">Report Bug</a> ·
  <a href="https://github.com/fridayowl/atomcraft/issues">Request Feature</a> ·
  <a href="https://github.com/fridayowl/atomcraft/discussions">Join Discussion</a>
</p>
