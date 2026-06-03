# Atomcraft ⚗️

**Atomcraft** (formerly AION) is the AI operating system for accelerated materials discovery. It connects generative AI, computational simulation, synthesis feasibility, and experiment tracking into a single closed-loop platform.

Researchers describe their target requirements in natural language—Atomcraft generates candidates, predicts properties, validates with simulation, recommends synthesis routes, and learns from every experiment (both successes and failures).

> **From prompt to synthesis-ready material in hours, not years.**

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         FRONTEND (React + TS + Tailwind)            │
│  ┌──────────┬──────────────┬──────────┬───────────┬──────────────┐  │
│  │Dashboard │  Materials   │Generator │ Predictor │  Experiments │  │
│  │ (Home)   │  Database    │ (AI Gen) │ (ML Prop) │  (Tracking)  │  │
│  └──────────┴──────────────┴──────────┴───────────┴──────────────┘  │
│                     Atomcraft Chat (Conversational UI)              │
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

## 🌟 Key Features

1. **Conversational AI Interface (`Atomcraft Chat`)**: Ask materials science questions, search the database, or suggest new materials using natural language.
2. **Crystal Structure Generator**: Diffusion-based generative model generating candidate compositions and crystal structures under specific property and space group constraints.
3. **ML Property Predictor**: Fast surrogate model ensemble (Random Forest, Gradient Boosting) predicting band gap (eV), formation energy (eV/atom), and density (g/cm³) in seconds.
4. **Synthesis Feasibility Engine**: Automatically recommends synthesis methods and conditions (Solid-state, Sol-gel, Hydrothermal, CVD, Mechanochemical) and auto-designs step-by-step experimental procedures.
5. **Simulation Orchestrator**: Manages DFT (VASP, Quantum ESPRESSO, CP2K) and MD (LAMMPS) verification jobs.
6. **Closed-Loop Learning**: Seamlessly captures negative results. Failed experiments are stored as gold-standard training data to improve the accuracy of future predictions.

---

## 📂 Project Structure

```
atomcraft/
├── backend/                   # FastAPI Python Application
│   ├── app/
│   │   ├── api/               # API Router endpoints
│   │   ├── core/              # Materials LLM, composition analyzer, predictor, synthesis
│   │   ├── models/            # SQLAlchemy schemas (materials, experiments, users)
│   │   └── database.py        # SQLAlchemy engine and session
│   └── Dockerfile
├── frontend/                  # React + TypeScript + Tailwind App
│   ├── src/
│   │   ├── api/               # Typed fetch API client wrapper
│   │   ├── components/        # Navigation sidebar & common UI components
│   │   └── pages/             # Dashboard, Materials, Generator, Predictor, Experiments, Chat
│   ├── tailwind.config.js
│   └── Dockerfile
├── models/                    # ML Model Interface scripts
│   ├── property_prediction/
│   ├── crystal_generation/
│   └── synthesis/
├── docs/                      # Specification & Platform documentation
├── docker-compose.yml         # Container configuration (FastAPI, React, Postgres, Redis, Neo4j)
└── start.sh                   # Local development launcher
```

---

## 🚀 Getting Started

### Prerequisites

- **Docker & Docker Compose**
- **Python 3.10+** (if running locally without Docker)
- **Node.js 18+ & npm** (if running locally without Docker)

### Run with Docker Compose (Recommended)

To start the entire stack (Frontend, Backend, PostgreSQL, Redis, Neo4j):

```bash
docker-compose up --build
```

- **Frontend:** http://localhost:5173
- **Backend API Docs:** http://localhost:8000/docs

### Run Locally (Without Docker)

Use the helper script `start.sh` at the root of the project to initialize virtual environments, install dependencies, and run both frontend and backend concurrently:

```bash
chmod +x start.sh
./start.sh
```

---

## ⚖️ License

Distributed under the MIT License. See `LICENSE` for more information.
