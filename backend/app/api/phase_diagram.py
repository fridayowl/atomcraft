from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.material import Material, Composition
from app.core.composition_analyzer import CompositionAnalyzer

router = APIRouter(prefix="/api/phase-diagram", tags=["phase_diagram"])


class PhaseDiagramRequest(BaseModel):
    elements: list[str]
    temperature: Optional[float] = None


@router.post("/")
async def get_phase_diagram(req: PhaseDiagramRequest, db: Session = Depends(get_db)):
    if len(req.elements) < 2 or len(req.elements) > 3:
        raise HTTPException(status_code=400, detail="Phase diagrams supported for 2 or 3 elements")

    analyzer = CompositionAnalyzer()
    query = (
        db.query(Material)
        .join(Composition)
        .filter(Composition.element.in_(req.elements))
        .distinct()
        .limit(100)
    )
    materials = query.all()

    points = []
    for m in materials:
        comps = {c.element: c.atomic_fraction for c in m.compositions}
        if all(e in comps for e in req.elements):
            points.append({
                "formula": m.formula,
                "composition": {e: comps.get(e, 0) for e in req.elements},
                "space_group": m.space_group,
            })

    if len(req.elements) == 2:
        return {
            "type": "binary",
            "elements": req.elements,
            "temperature": req.temperature or 298,
            "points": sorted(points, key=lambda p: p["composition"].get(req.elements[0], 0)),
        }

    return {
        "type": "ternary",
        "elements": req.elements,
        "temperature": req.temperature or 298,
        "points": points,
    }
