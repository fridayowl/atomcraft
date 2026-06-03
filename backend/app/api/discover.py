from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.core.generator import MaterialsGenerator
from app.core.predictor import PropertyPredictor
from app.core.synthesis import SynthesisEngine
from app.core.battery import assess_battery_suitability
from app.core.xrd import simulate_xrd_pattern
from app.core.composition_analyzer import CompositionAnalyzer

router = APIRouter(prefix="/api/discover", tags=["discover"])
generator = MaterialsGenerator()
predictor = PropertyPredictor()
synthesis = SynthesisEngine()
analyzer = CompositionAnalyzer()


class PropertyConstraint(BaseModel):
    band_gap_min: Optional[float] = None
    band_gap_max: Optional[float] = None
    formation_energy_min: Optional[float] = None
    formation_energy_max: Optional[float] = None
    density_min: Optional[float] = None
    density_max: Optional[float] = None


class DiscoverRequest(BaseModel):
    elements: Optional[list[str]] = None
    num_candidates: int = 50
    top_k: int = 10
    constraints: Optional[PropertyConstraint] = None
    application: Optional[str] = None


class CandidateResult(BaseModel):
    rank: int
    formula: str
    elements: list[str]
    space_group: str
    crystal_system: str
    lattice_parameters: dict
    predictions: dict
    synthesis: dict
    battery: Optional[dict] = None
    xrd: Optional[dict] = None
    overall_score: float


@router.post("/")
async def discover(req: DiscoverRequest):
    candidates = await generator.generate_crystal(
        element_constraints=req.elements,
        num_candidates=req.num_candidates,
    )

    results = []
    constraints = req.constraints or PropertyConstraint()

    for c in candidates:
        formula = c["formula"]
        elements = c["elements"]
        sg = c["space_group"]
        system = c["crystal_system"]
        lattice = c["lattice_parameters"]
        gap = c.get("predicted_band_gap", 0)
        eform = c.get("predicted_formation_energy", 0)

        density_pred = await predictor.predict(formula, "density")
        density = density_pred.get("predicted_value", 0)

        feasibility = await synthesis.assess_feasibility(formula)
        syn_score = feasibility.get("feasibility_score", 0)

        battery_assessment = None
        if req.application == "battery":
            comp = analyzer.parse_formula(formula)
            if comp:
                battery_assessment = assess_battery_suitability(formula, gap, eform, comp)

        xrd_result = None
        try:
            xrd_result = simulate_xrd_pattern(sg, lattice, elements)
        except Exception:
            pass

        score_weight = 1.0
        if constraints.band_gap_min is not None and gap < constraints.band_gap_min:
            score_weight *= 0.5
        if constraints.band_gap_max is not None and gap > constraints.band_gap_max:
            score_weight *= 0.5
        if constraints.formation_energy_max is not None and eform > constraints.formation_energy_max:
            score_weight *= 0.5
        if constraints.formation_energy_min is not None and eform < constraints.formation_energy_min:
            score_weight *= 0.5
        if constraints.density_max is not None and density > constraints.density_max:
            score_weight *= 0.5
        if constraints.density_min is not None and density < constraints.density_min:
            score_weight *= 0.5

        battery_score = 0
        if battery_assessment:
            for app_name, info in battery_assessment.items():
                battery_score = max(battery_score, info.get("score", 0))

        overall_score = round(
            syn_score * 0.3 +
            (1.0 - min(gap / 8.0, 1.0)) * 0.1 +
            score_weight * 0.3 +
            (battery_score if req.application == "battery" else 0.5) * 0.3,
            3,
        )

        results.append(CandidateResult(
            rank=0,
            formula=formula,
            elements=elements,
            space_group=sg,
            crystal_system=system,
            lattice_parameters=lattice,
            predictions={
                "band_gap": gap,
                "formation_energy": eform,
                "density": density,
            },
            synthesis={
                "feasibility_score": syn_score,
                "recommended_methods": feasibility.get("recommended_methods", []),
                "risks": feasibility.get("risks", []),
            },
            battery=battery_assessment,
            xrd=xrd_result,
            overall_score=overall_score,
        ))

    results.sort(key=lambda r: r.overall_score, reverse=True)
    for i, r in enumerate(results[:req.top_k]):
        r.rank = i + 1

    return {
        "candidates": results[:req.top_k],
        "total_generated": len(candidates),
        "application": req.application,
    }
