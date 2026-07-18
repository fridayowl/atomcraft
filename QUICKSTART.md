# Atomcraft Quick Start Guide

## Prerequisites
- Python 3.13+
- ~5 GB disk (for the 104k materials database + ML models)
- ~30 min initial setup time

## Step 1: Clone & Setup

```bash
git clone https://github.com/fridayowl/atomcraft.git
cd atomcraft
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

## Step 2: Bootstrap the Database & Models

> Run these once before using the app, demo, or frontend.

```bash
cd backend

# Populate the database (requires MP_API_KEY)
python scripts/fetch_mp_data.py --num 100

# Optional: full import path
python scripts/bulk_fetch_mp.py --retrain

# Retrain the .joblib models from the populated DB
python scripts/retrain_models.py
```

## Step 3: Verify It Works

```bash
# Check database loads (104,842 materials)
cd backend
python -c "
from app.database import SessionLocal
from app.models.material import Material
db = SessionLocal()
print(f'Materials: {db.query(Material).count()}')
db.close()
"

# Test a prediction
python -c "
import sys; sys.path.insert(0, '.')
from app.core.trainer import predict_property
gap, conf = predict_property('BaTiO3', 'band_gap')
print(f'BaTiO3 band gap = {gap:.3f} eV')
"
```

Expected output:
```
Materials: 104842
BaTiO3 band gap = 2.197 eV
```

## Step 4: Run the Demo (Cathode Discovery)

```bash
cd atomcraft
source .venv/bin/activate
python backend/run_demo.py
```

This runs the full pipeline:
1. Generates 15 novel cathode candidates (Li-Ni-Mn-Co-O space)
2. Predicts band gap, formation energy, density for each
3. Shows top 5 most stable + top 5 highest band gap
4. Runs 10 substitution-based candidates from MP templates
5. Prints feature importance analysis
6. Generates VASP input files for the best candidate
7. Runs 1 active learning iteration (adds 3 pseudo-validated samples + retrains models)

Takes ~5-10 min on a modern laptop.

## Step 5: Try Your Own Exploration

### Quick one-liners:

```bash
# Predict any formula
python -c "
import sys; sys.path.insert(0, 'backend')
from app.core.trainer import predict_property
for f in ['LiCoO2', 'LiFePO4', 'NaMnO2', 'KFeO2']:
    gap, _ = predict_property(f, 'band_gap')
    eform, _ = predict_property(f, 'formation_energy')
    print(f'{f:12s} gap={gap:.3f} eV  E_form={eform:.3f} eV/atom')
"
```

```bash
# Generate novel materials in any element space
python -c "
import sys; sys.path.insert(0, 'backend')
import asyncio
from app.core.generator import MaterialsGenerator
gen = MaterialsGenerator()
async def go():
    r = await gen.generate_denovo(element_constraints=['Fe','O','Si'], num_candidates=5)
    for c in r:
        print(f\"{c['formula']:20s} {c['space_group']:8s} gap={c['predicted_band_gap']:.3f}\")
asyncio.run(go())
"
```

```bash
# Predict space group
python -c "
import sys; sys.path.insert(0, 'backend')
from app.core.trainer import predict_space_group
for f in ['BaTiO3', 'Fe2O3', 'MgO', 'LiCoO2', 'SrTiO3']:
    num, sym, conf = predict_space_group(f)
    print(f'{f:10s} -> {sym:8s} (#{num:3d}) conf={conf:.3f}')
"
```

```bash
# Run active learning (3 iterations, slow ~30 min)
python -c "
import sys; sys.path.insert(0, 'backend')
from app.core.active_learning import ActiveLearningLoop
ActiveLearningLoop.run_pseudo_loop(num_iterations=3, candidates_per_iter=10)
"
```

### Start the API server:

```bash
cd atomcraft
source .venv/bin/activate
uvicorn backend.app.main:app --reload --port 8000
```

Then open http://localhost:8000/docs for the interactive Swagger UI.

### Curl examples:

```bash
# Predict
curl -X POST http://localhost:8000/api/predict/ \
  -H "Content-Type: application/json" \
  -d '{"formula": "BaTiO3", "properties": ["band_gap", "formation_energy"]}'

# Generate
curl -X POST http://localhost:8000/api/generate/denovo \
  -H "Content-Type: application/json" \
  -d '{"num_candidates": 5, "element_constraints": ["Li", "Co", "O"]}'

# Feature importance
curl http://localhost:8000/api/predict/feature-importance/band_gap
```

## What's Included

| File | Size | Description |
|---|---|---|
| `aion.db` | ~500 MB | 104,842 Materials Project entries |
| `backend/app/core/models/*.joblib` | ~300 MB (gitignored) | 11 RandomForest models + space group classifier |
| `backend/app/core/models/model_config.json` | ~3 KB | Model metadata (R², MAE, sample count) |
| `backend/app/core/models/spg_cache.json` | ~4 KB | 269 space group symbol→number mappings |

Models are recreated by `train_and_save_models()` if `.joblib` files are missing.
