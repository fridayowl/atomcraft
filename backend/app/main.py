from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.api import materials, generation, prediction, synthesis, experiments, chat, auth

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AION Materials Discovery Platform",
    description="AI-powered platform for accelerated materials discovery",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(materials.router)
app.include_router(generation.router)
app.include_router(prediction.router)
app.include_router(synthesis.router)
app.include_router(experiments.router)
app.include_router(chat.router)
app.include_router(auth.router)


@app.get("/")
def root():
    return {
        "name": "AION Materials Discovery Platform",
        "version": "0.1.0",
        "status": "operational",
        "endpoints": {
            "materials": "/api/materials/",
            "generation": "/api/generate/",
            "prediction": "/api/predict/",
            "synthesis": "/api/synthesis/",
            "experiments": "/api/experiments/",
            "chat": "/api/chat/",
        }
    }


@app.get("/health")
def health():
    return {"status": "healthy"}
