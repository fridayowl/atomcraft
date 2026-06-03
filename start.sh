#!/bin/bash
echo "=== AION Materials Discovery Platform ==="
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required"
    exit 1
fi

# Create virtualenv if needed
if [ ! -d "backend/.venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv backend/.venv
fi

# Install backend deps
echo "Installing backend dependencies..."
source backend/.venv/bin/activate
pip install -r backend/requirements.txt -q

# Check Node
if ! command -v node &> /dev/null; then
    echo "Error: Node.js is required"
    exit 1
fi

# Install frontend deps
echo "Installing frontend dependencies..."
cd frontend
npm install --silent
cd ..

# Start backend
echo "Starting backend on http://localhost:8000..."
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

# Start frontend
echo "Starting frontend on http://localhost:5173..."
cd frontend
npm run dev -- --host 0.0.0.0 &
FRONTEND_PID=$!
cd ..

echo ""
echo "=== AION is running ==="
echo "  Frontend: http://localhost:5173"
echo "  Backend:  http://localhost:8000"
echo "  API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" SIGINT SIGTERM
wait
