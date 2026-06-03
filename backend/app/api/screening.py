from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from app.core.predictor import PropertyPredictor
from app.core.synthesis import SynthesisEngine
from app.core.generator import MaterialsGenerator

router = APIRouter(prefix="/api/screening", tags=["screening"])
predictor = PropertyPredictor()
synthesis = SynthesisEngine()
generator = MaterialsGenerator()


class ScreeningRequest(BaseModel):
    formulas: list[str]
    properties: list[str] = ["band_gap", "formation_energy", "density"]
    min_feasibility: Optional[float] = None


class PropertyConstraint(BaseModel):
    property: str
    min: Optional[float] = None
    max: Optional[float] = None


class ConstrainedScreeningRequest(BaseModel):
    formulas: list[str]
    constraints: list[PropertyConstraint]


@router.post("/")
async def screen_materials(req: ScreeningRequest):
    predictions = await predictor.batch_predict(req.formulas, req.properties)
    predictions_by_formula = {}
    for p in predictions:
        f = p["formula"]
        if f not in predictions_by_formula:
            predictions_by_formula[f] = {}
        predictions_by_formula[f][p["property"]] = p["predicted_value"]

    results = []
    for formula in req.formulas:
        feasibility = await synthesis.assess_feasibility(formula)
        score = feasibility["feasibility_score"]

        if req.min_feasibility is not None and score < req.min_feasibility:
            continue

        results.append({
            "formula": formula,
            "predictions": predictions_by_formula.get(formula, {}),
            "feasibility_score": score,
            "recommended_methods": [m["method"] for m in feasibility["recommended_methods"]],
        })

    results.sort(key=lambda x: x.get("feasibility_score", 0), reverse=True)
    return {"results": results, "total": len(results)}


@router.post("/constrained")
async def screen_with_constraints(req: ConstrainedScreeningRequest):
    predictions = await predictor.batch_predict(
        req.formulas,
        [c.property for c in req.constraints],
    )

    pred_map = {}
    for p in predictions:
        f = p["formula"]
        if f not in pred_map:
            pred_map[f] = {}
        pred_map[f][p["property"]] = p["predicted_value"]

    results = []
    for formula in req.formulas:
        props = pred_map.get(formula, {})
        passes = True
        for c in req.constraints:
            val = props.get(c.property)
            if val is None:
                passes = False
                break
            if c.min is not None and val < c.min:
                passes = False
                break
            if c.max is not None and val > c.max:
                passes = False
                break

        if passes:
            feasibility = await synthesis.assess_feasibility(formula)
            results.append({
                "formula": formula,
                "properties": props,
                "feasibility_score": feasibility["feasibility_score"],
            })

    return {"results": results, "total": len(results)}


@router.post("/generate-and-screen")
async def generate_and_screen(element_constraints: Optional[list[str]] = None,
                               target_properties: Optional[dict] = None,
                               num_candidates: int = 20):
    candidates = await generator.generate_crystal(
        target_properties=target_properties,
        element_constraints=element_constraints,
        num_candidates=num_candidates,
    )

    results = []
    for c in candidates:
        feasibility = await synthesis.assess_feasibility(c["formula"])
        c["feasibility_score"] = feasibility["feasibility_score"]
        c["risks"] = feasibility["risks"]
        results.append(c)

    results.sort(key=lambda x: x.get("generation_score", 0) * x.get("feasibility_score", 0), reverse=True)
    return {"results": results, "total": len(results)}
