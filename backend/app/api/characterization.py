from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from app.core.xrd import simulate_xrd_pattern

router = APIRouter(prefix="/api/characterization", tags=["characterization"])


class XrdRequest(BaseModel):
    space_group: str
    lattice_parameters: dict
    elements: list[str]
    wavelength: float = 1.5406


@router.post("/xrd/simulate")
async def simulate_xrd(req: XrdRequest):
    result = simulate_xrd_pattern(
        space_group=req.space_group,
        lattice_params=req.lattice_parameters,
        elements=req.elements,
        wavelength=req.wavelength,
    )
    return result
