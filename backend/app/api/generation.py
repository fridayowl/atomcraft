from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.core.generator import MaterialsGenerator

router = APIRouter(prefix="/api/generate", tags=["generation"])
generator = MaterialsGenerator()


class GenerateRequest(BaseModel):
    target_properties: dict = {}
    element_constraints: Optional[list[str]] = None
    num_candidates: int = 10
    description: Optional[str] = None


@router.post("/crystals")
async def generate_crystals(req: GenerateRequest):
    candidates = await generator.generate_crystal(
        target_properties=req.target_properties,
        element_constraints=req.element_constraints,
        num_candidates=req.num_candidates,
    )
    return {
        "candidates": candidates,
        "total": len(candidates),
        "request": {
            "target_properties": req.target_properties,
            "element_constraints": req.element_constraints,
        },
    }


@router.post("/compositions")
async def generate_compositions(req: GenerateRequest):
    candidates = await generator.generate_composition(
        target_properties=req.target_properties,
        num_candidates=req.num_candidates,
    )
    return {
        "candidates": candidates,
        "total": len(candidates),
    }


@router.post("/denovo")
async def generate_denovo(req: GenerateRequest):
    candidates = await generator.generate_denovo(
        target_properties=req.target_properties,
        element_constraints=req.element_constraints,
        num_candidates=req.num_candidates,
    )
    return {
        "candidates": candidates,
        "total": len(candidates),
        "request": {
            "target_properties": req.target_properties,
            "element_constraints": req.element_constraints,
        },
    }
