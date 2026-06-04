# Atomcraft User Guide

**Atomcraft** is an AI-driven materials discovery platform that generates novel crystal compositions, predicts their properties, validates candidates via DFT, and improves through active learning.

---

## Table of Contents

1. [Quick Start](#1-quick-start)
2. [What It Can Do](#2-what-it-can-do)
3. [Generation Engine](#3-generation-engine)
4. [Property Predictor](#4-property-predictor)
5. [Space Group Prediction](#5-space-group-prediction)
6. [DFT Input Generation](#6-dft-input-generation)
7. [Active Learning Loop](#7-active-learning-loop)
8. [API Endpoints](#8-api-endpoints)
9. [Model Performance & Limitations](#9-model-performance--limitations)
10. [Example Workflows](#10-example-workflows)

---

## 1. Quick Start

### Prerequisites
- Python 3.13
- 5 GB disk space (for SQLite database + 104k Materials Project entries)

### Setup
```bash
# Backend is already set up
cd backend
python -c "from app.main import app; print('API ready')"
```

### Start the API server
```bash
cd backend
../.venv313/bin/uvicorn app.main:app --reload --port 8000
```

Or use the helper:
```bash
./start.sh
```

### Run scripts directly
```bash
# Predict properties
python -c "
from app.core.trainer import predict_property
gap, conf = predict_property('BaTiO3', 'band_gap')
print(f'BaTiO3 band gap: {gap:.3f} eV (confidence: {conf:.3f})')
"

# Generate de-novo materials
python -c "
import asyncio
from app.core.generator import MaterialsGenerator
gen = MaterialsGenerator()
async def run():
    results = await gen.generate_denovo(num_candidates=5)
    for r in results:
        print(r['formula'], r['space_group'], r['predicted_band_gap'])
asyncio.run(run())
"
```

---

## 2. What It Can Do

| Capability | Description | Status |
|---|---|---|
| **De-novo generation** | Random compositions from 68-element pool, space group predicted, property predicted | ✅ |
| **Substitution generation** | Element substitution on 104k MP templates (e.g. O→S, Li→Na) | ✅ |
| **Property prediction** | 11 properties via RandomForest (gap, formation energy, density, etc.) | ✅ |
| **Space group prediction** | 112 space groups, 95.9% accuracy | ✅ |
| **Batch prediction** | Predict multiple formulas and properties in one call | ✅ |
| **Feature importance** | 56-feature analysis showing what drives each prediction | ✅ |
| **VASP input generation** | INCAR, POSCAR, KPOINTS, POTCAR files | ✅ |
| **QE input generation** | Limited (pymatgen >=2024.6.10 no longer ships pymatgen.io.qe) | ⚠️ |
| **Active learning (pseudo)** | Generate → Predict → Select → Store → Retrain (no DFT needed) | ✅ |
| **Active learning (DFT)** | Full loop with VASP/QE submission | Needs cluster |

### Data
- **104,842** material templates imported from Materials Project
- **11** trained ML models
- **112** space group classifier
- **49** trained `.joblib` files (retained via `retrain_models.py` or recreated by trainer)

---

## 3. Generation Engine

Two generation strategies in `MaterialsGenerator` (`generator.py`):

### De-novo Generation
Creates random compositions from a pool of 68 elements (Li, Na, K, Mg, Ca, Fe, Co, Ni, Mn, Ti, Zr, Zn, Al, Si, O, S, F, Cl, C, N, V, Cr, Cu, Ga, Ge, Se, Br, Rb, Sr, Y, Nb, Mo, Ru, Rh, Pd, Ag, Cd, In, Sn, Sb, Te, I, Cs, Ba, La, Ce, Pr, Nd, Sm, Eu, Gd, Tb, Dy, Ho, Er, Tm, Yb, Lu, Hf, Ta, W, Re, Os, Ir, Pt, Au, Pb, Bi).

```python
import asyncio
from app.core.generator import MaterialsGenerator

gen = MaterialsGenerator()
candidates = asyncio.run(gen.generate_denovo(
    num_candidates=10,
    element_constraints=["Li", "Fe", "O"],  # optional: limit to these elements
    target_properties={"band_gap": 2.0},    # optional: target a specific gap
))
# Each candidate has: formula, space_group, crystal_system,
# predicted_band_gap, predicted_formation_energy, stability_score,
# generation_score, elements, lattice_parameters
```

### Substitution (Template-Based) Generation
Applies elemental substitutions from 17 chemical groups (alkali, alkaline earth, transition metals, halogens, chalcogens, etc.) to existing MP structures.

```python
candidates = asyncio.run(gen.generate_crystal(
    num_candidates=10,
    target_properties={"band_gap": 3.0},
))
# Each candidate also has: substitution (e.g. "O->S"), template_formula
```

### Composition Generation (Random + Substitution)
```python
candidates = asyncio.run(gen.generate_composition(num_candidates=5))
```

---

## 4. Property Predictor

11 trained RandomForest models in `PropertyPredictor` (`predictor.py`):

| Property | Training Samples | R² | Meaning |
|---|---|---|---|
| `density` | 104,842 | 0.97 | g/cm³ |
| `formation_energy` | 104,842 | 0.94 | eV/atom |
| `band_gap` | 52,602 | 0.59 | eV |
| `energy_above_hull` | 104,842 | 0.77 | eV/atom |
| `total_magnetization` | 104,842 | 0.66 | μB |
| `is_stable` | 104,842 | 0.40 | binary |
| `homogeneous_poisson` | 9,359 | 0.04 | ratio |
| `universal_anisotropy` | 9,359 | -0.17 | dimensionless |
| `e_electronic` | 4,958 | 0.20 | dielectric |
| `e_ionic` | 4,958 | 0.16 | dielectric |
| `e_total` | 4,958 | 0.09 | dielectric |

```python
from app.core.predictor import PropertyPredictor
import asyncio

pred = PropertyPredictor()

# Single prediction
result = asyncio.run(pred.predict("LiCoO2", "band_gap"))
# {"formula": "LiCoO2", "property": "band_gap", "predicted_value": 1.227, "confidence": 0.85}

# Batch prediction
results = asyncio.run(pred.batch_predict(
    ["BaTiO3", "SrTiO3"], ["band_gap", "formation_energy"]
))

# Feature importance
fi = asyncio.run(pred.get_feature_importance("band_gap"))
# {"property": "band_gap", "features": {"electronegativity_std": 0.08, ...}}
```

---

## 5. Space Group Prediction

A RandomForest classifier trained on 112 space groups (those with >50 samples in MP). Uses ELEMENT_DATA-based fast feature extraction (no pymatgen overhead).

```python
from app.core.trainer import predict_space_group

num, symbol, confidence = predict_space_group("BaTiO3")
# (140, "I4/mcm", 0.213)
```

Performance: **95.9% training accuracy** across 23,763 samples, 112 classes. Confidences for novel compositions (de-novo) typically range 0.10–0.50 (vs. random baseline of 0.009 for 112 classes).

---

## 6. DFT Input Generation

Generates VASP input files (INCAR, POSCAR, KPOINTS, POTCAR) using pymatgen.

```python
from app.core.dft import generate_vasp_inputs, generate_qe_inputs

lattice = {"a": 4.0, "b": 4.0, "c": 4.0}
elements = ["Ba", "Ti", "O"]

result = generate_vasp_inputs("BaTiO3", "Pm-3m", lattice, elements, "/tmp/dft_job")
# Returns {"status": "inputs_generated", "job_dir": "/tmp/dft_job", "formula": "BaTiO3"}
# Files written: INCAR, POSCAR, KPOINTS, POTCAR
```

**Note**: No DFT software (VASP/QE/CP2K) is installed locally. The generator creates input files and SLURM/PBS submission scripts for cluster submission.

---

## 7. Active Learning Loop

The `ActiveLearningLoop` (`active_learning.py`) runs a 5-step cycle:

```
1. Generate candidates (de-novo + substitution)
2. Predict properties (band_gap, formation_energy, density)
3. Select top candidates by uncertainty (formation_energy proximity to 0)
4. Validate (DFT mode or pseudo mode)
5. Store results in DB + retrain models
```

### Mode A: Pseudo-Validation (No DFT Required)
Most useful for exploration and testing. Uses the predictor's own output as "validation" — stores predicted formation energy and band gap into the DB, then retrains models with the new data points.

```python
from app.core.active_learning import ActiveLearningLoop

# Run 3 iterations as a headless script
summary = ActiveLearningLoop.run_pseudo_loop(
    num_iterations=3,
    candidates_per_iter=10,
    # element_constraints=["Fe", "O"],  # optional
)
print(summary)
# {"total_iterations": 3, "total_validated": 9, "history": [...]}
```

Or step through manually:
```python
import asyncio
from app.core.active_learning import ActiveLearningLoop

async def run_al():
    al = ActiveLearningLoop(dft_mode=False)
    for i in range(3):
        result = await al.run_iteration(
            num_candidates=10,
            max_validate=3,
        )
        print(f"Iteration {i+1}: {result['validation_success']} validated")
    return al.get_summary()

summary = asyncio.run(run_al())
```

### Mode B: DFT Validation (Needs Cluster)
When VASP or QE is installed (or accessible via Slurm/PBS), pass `dft_mode=True`:

```python
al = ActiveLearningLoop(dft_mode=True)
# Requires DFTOrchestrator to find available DFT executables
```

### What Each Iteration Does
1. Generates `num_candidates` materials (half de-novo, half substitution)
2. Predicts band_gap, formation_energy, density for each
3. Ranks by uncertainty: `confidence ∝ 1/(|E_form| + 0.1)` — stable materials near hull get validated first
4. Validates top `max_validate` candidates
5. Stores `formation_energy` and `band_gap` as `Property` rows in DB
6. Retrains ALL 11 models with `force_retrain=True`
7. Logs iteration summary to `history`

### Effect on Models
After each iteration, the models incorporate new data. For example:
- Pre-loop: `formation_energy` at 104,842 samples, R²=0.94
- After 1 iteration with 3 pseudo-validated: 104,845 samples
- After N iterations: N × `max_validate` new data points

The pseudo mode adds modest data since it uses predicted values (not true DFT), but it validates the loop mechanics end-to-end. For real model improvement, DFT-verified values are needed.

---

## 8. API Endpoints

### Generation
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/generate/crystals` | Substitution-based crystal generation |
| `POST` | `/api/generate/compositions` | Random + substitution compositions |
| `POST` | `/api/generate/denovo` | De-novo composition generation |

**Request body** (all three):
```json
{
  "target_properties": {"band_gap": 2.0},
  "element_constraints": ["Fe", "O"],
  "num_candidates": 10
}
```

### Prediction
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/predict/` | Single formula, multiple properties |
| `POST` | `/api/predict/batch` | Multiple formulas, multiple properties |
| `GET` | `/api/predict/feature-importance/{property}` | Feature importance for a model |

**Predict request body**:
```json
{
  "formula": "BaTiO3",
  "properties": ["band_gap", "formation_energy", "density"]
}
```

### Other
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Platform info and endpoint list |
| `GET` | `/health` | Health check |
| `POST` | `/api/discover/` | Multi-criteria screening pipeline |

---

## 9. Model Performance & Limitations

### Strong Models (use with confidence)
| Model | R² | Notes |
|---|---|---|
| `density` | 0.97 | Highly reliable |
| `formation_energy` | 0.94 | Highly reliable |
| `energy_above_hull` | 0.77 | Good for stability screening |
| `band_gap` | 0.59 | Moderate — good for ranking, not absolute values |
| `total_magnetization` | 0.66 | Moderate |

### Weak Models (use with caution)
| Model | R² | Limitation |
|---|---|---|
| `universal_anisotropy` | -0.17 | Worse than mean — only 9,359 samples with extreme outliers |
| `e_total` | 0.09 | Only 4,958 dielectric samples |
| `homogeneous_poisson` | 0.04 | Only 9,359 elastic samples |

To improve weak models, you need more data. Options:
- Run `fetch_properties.py` to pull additional dielectric data from MP API if available
- Run active learning with DFT validation on a cluster
- Collect experimental measurements and add via DB

### Known Issues
- **QE input generation**: `pymatgen.io.qe.PWInput` was removed in pymatgen 2024+. Use VASP engine instead.
- **Structure relaxation**: `relax_structure()` uses UFF force field — reasonable for geometry but not for energies.
- **De-novo space group confidence**: Low (0.1–0.5) for random compositions as expected.
- **DFT submission**: Generates input files + submission scripts but no local DFT to run them.

---

## 10. Example Workflows

### Workflow 1: Discover a high-band-gap material
```python
import asyncio
from app.core.generator import MaterialsGenerator
from app.core.predictor import PropertyPredictor

gen = MaterialsGenerator()
pred = PropertyPredictor()

async def discover():
    # Generate candidates targeting high band gap
    candidates = await gen.generate_crystal(
        target_properties={"band_gap": 3.0},
        num_candidates=20,
    )
    # Predict all properties
    for c in candidates:
        props = await pred.batch_predict([c["formula"]], ["band_gap", "formation_energy", "density"])
        c["predictions"] = props
    # Sort by band gap descending
    candidates.sort(key=lambda x: -x.get("predicted_band_gap", 0))
    for c in candidates[:5]:
        print(f"{c['formula']:20s} gap={c['predicted_band_gap']:.2f} eV  subst={c.get('substitution',''):15s}")

asyncio.run(discover())
```

### Workflow 2: Generate DFT inputs for promising candidates
```python
from app.core.generator import MaterialsGenerator
from app.core.dft import generate_vasp_inputs
import asyncio, os

candidates = asyncio.run(MaterialsGenerator().generate_denovo(num_candidates=3))
for c in candidates:
    formula = c["formula"]
    job_dir = f"/tmp/dft_{formula}"
    os.makedirs(job_dir, exist_ok=True)
    lattice = {"a": 5.0, "b": 5.0, "c": 5.0}
    result = generate_vasp_inputs(formula, c["space_group"], lattice, c["elements"], job_dir)
    print(f"{formula}: inputs -> {job_dir}")
```

### Workflow 3: Run active learning (pseudo mode)
```bash
python -c "
from app.core.active_learning import ActiveLearningLoop
summary = ActiveLearningLoop.run_pseudo_loop(num_iterations=2, candidates_per_iter=6)
print(f'Total validated: {summary[\"total_validated\"]}')
"
```

### Workflow 4: API server + curl
```bash
# Start server
uvicorn app.main:app --port 8000 &

# Predict
curl -X POST http://localhost:8000/api/predict/ \
  -H "Content-Type: application/json" \
  -d '{"formula": "BaTiO3", "properties": ["band_gap", "formation_energy"]}'

# Generate
curl -X POST http://localhost:8000/api/generate/denovo \
  -H "Content-Type: application/json" \
  -d '{"num_candidates": 5, "target_properties": {"band_gap": 2.0}}'

# Feature importance
curl http://localhost:8000/api/predict/feature-importance/band_gap
```
