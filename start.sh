#!/bin/bash
set -e

echo "=== AION Materials Discovery Platform ==="
echo ""
echo "Options:"
echo "  1) docker   - Start full stack with Docker Compose"
echo "  2) local    - Start backend + frontend locally"
echo "  3) seed     - Seed database with sample data"
echo ""

MODE="${1:-local}"

if [ "$MODE" = "docker" ]; then
    echo "Starting with Docker Compose..."
    docker compose up --build -d
    echo ""
    echo "=== AION is running ==="
    echo "  Frontend: http://localhost:5173"
    echo "  Backend:  http://localhost:8000"
    echo "  API Docs: http://localhost:8000/docs"
    echo "  Neo4j:    http://localhost:7474"
    echo ""
    echo "To stop: docker compose down"
    exit 0
fi

if [ "$MODE" = "local" ]; then
    echo "Starting locally..."

    # Check Python
    if ! command -v python3 &> /dev/null; then
        echo "Error: Python 3 is required"
        exit 1
    fi

    # Use .venv313 if available, else .venv
    VENV_DIR="backend/.venv"
    if [ -d "backend/.venv313" ]; then
        VENV_DIR="backend/.venv313"
    fi

    # Create virtualenv if needed
    if [ ! -d "$VENV_DIR" ]; then
        echo "Creating Python virtual environment..."
        python3 -m venv "$VENV_DIR"
    fi

    # Install backend deps
    echo "Installing backend dependencies..."
    source "$VENV_DIR/bin/activate"
    pip install -r backend/requirements.txt -q

    # Check Node
    if ! command -v node &> /dev/null; then
        echo "Error: Node.js is required"
        exit 1
    fi

    # Install frontend deps
    echo "Installing frontend dependencies..."
    cd frontend && npm install --silent && cd ..

    # Train models if needed
    if [ ! -f "backend/app/core/models/model_config.json" ]; then
        echo "Training ML models..."
        source "$VENV_DIR/bin/activate"
        python -c "from app.core.trainer import train_and_save_models; train_and_save_models(force_retrain=True)" 2>/dev/null
    fi

    # Start backend
    echo "Starting backend on http://localhost:8000..."
    source "$VENV_DIR/bin/activate"
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
    BACKEND_PID=$!

    # Start frontend
    echo "Starting frontend on http://localhost:5173..."
    cd frontend && npm run dev -- --host 0.0.0.0 &
    FRONTEND_PID=$!
    cd ..

    echo ""
    echo "=== AION is running ==="
    echo "  Frontend: http://localhost:5173"
    echo "  Backend:  http://localhost:8000"
    echo "  API Docs: http://localhost:8000/docs"
    echo ""
    echo "Press Ctrl+C to stop"

    trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" SIGINT SIGTERM
    wait
fi

if [ "$MODE" = "seed" ]; then
    echo "Seeding database with sample materials..."
    source "${VENV_DIR:-backend/.venv313}/bin/activate"
    python -c "
from app.database import SessionLocal
from app.models.material import Material, Composition, Property

db = SessionLocal()
samples = [
    ('LiCoO2', 'R-3m', [('Li',1),('Co',1),('O',2)], [('band_gap', 2.7, 'eV'), ('formation_energy', -1.5, 'eV/atom')]),
    ('Fe2O3', 'R-3c', [('Fe',2),('O',3)], [('band_gap', 2.1, 'eV'), ('formation_energy', -1.2, 'eV/atom')]),
    ('BaTiO3', 'P4mm', [('Ba',1),('Ti',1),('O',3)], [('band_gap', 3.2, 'eV'), ('formation_energy', -1.8, 'eV/atom')]),
    ('NaCl', 'Fm-3m', [('Na',1),('Cl',1)], [('band_gap', 8.5, 'eV'), ('formation_energy', -0.9, 'eV/atom')]),
    ('MgO', 'Fm-3m', [('Mg',1),('O',1)], [('band_gap', 7.8, 'eV'), ('formation_energy', -1.6, 'eV/atom')]),
]
for formula, sg, comps, props in samples:
    if db.query(Material).filter(Material.formula == formula).first():
        continue
    m = Material(formula=formula, name=formula, space_group=sg)
    db.add(m)
    db.flush()
    for el, amt in comps:
        db.add(Composition(material_id=m.id, element=el, amount=amt, atomic_fraction=amt/sum(a for _,a in comps)))
    for ptype, val, unit in props:
        db.add(Property(material_id=m.id, property_type=ptype, value=val, unit=unit, confidence=0.9))
db.commit()
db.close()
print('Seeded 5 sample materials.')
"
fi
