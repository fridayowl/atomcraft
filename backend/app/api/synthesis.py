from fastapi import APIRouter
from pydantic import BaseModel
from app.core.synthesis import SynthesisEngine

router = APIRouter(prefix="/api/synthesis", tags=["synthesis"])
engine = SynthesisEngine()


class FeasibilityRequest(BaseModel):
    formula: str


class ExperimentDesignRequest(BaseModel):
    formula: str
    method: str = "solid_state"


@router.post("/feasibility")
async def check_feasibility(req: FeasibilityRequest):
    result = await engine.assess_feasibility(req.formula)
    return result


@router.post("/design-experiment")
async def design_experiment(req: ExperimentDesignRequest):
    result = await engine.design_experiment(req.formula, req.method)
    return result


@router.get("/methods")
async def list_methods():
    return {
        "methods": [
            {"id": k, "description": v["description"],
             "temp_range": list(v["temp_range"]),
             "suitable_for": v["suitable_for"]}
            for k, v in engine.methods.items()
        ]
    }
