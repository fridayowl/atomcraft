import io
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.models.material import Material, Property, Composition
from app.models.prediction import Prediction
from pydantic import BaseModel


def _generate_structure(material):
    try:
        from pymatgen.core import Structure, Lattice
        from pymatgen.io.cif import CifParser
        import io

        if material.cif_data:
            parser = CifParser(io.StringIO(material.cif_data))
            structure = parser.parse_structures()[0]
        else:
            elements = [c.element for c in material.compositions]
            n = len(elements)
            if n == 0:
                return {"atoms": [], "lattice": {}}

            lattice = Lattice.from_parameters(
                material.lattice_a or 5.0,
                material.lattice_b or 5.0,
                material.lattice_c or 5.0,
                material.lattice_alpha or 90.0,
                material.lattice_beta or 90.0,
                material.lattice_gamma or 90.0,
            )
            frac_coords = []
            species = []
            for i, el in enumerate(elements):
                frac_coords.append([(i % 4) / 4.0, ((i // 4) % 4) / 4.0, (i // 16) / 4.0])
                species.append(el)
            structure = Structure(lattice, species, frac_coords)

        result = []
        for i, site in enumerate(structure):
            result.append({
                "element": str(site.specie.symbol),
                "x": round(float(site.frac_coords[0]), 6),
                "y": round(float(site.frac_coords[1]), 6),
                "z": round(float(site.frac_coords[2]), 6),
                "radius": round(float(structure.lattice.a) * 0.3, 4),
            })

        return {
            "atoms": result,
            "lattice": {
                "a": round(float(structure.lattice.a), 4),
                "b": round(float(structure.lattice.b), 4),
                "c": round(float(structure.lattice.c), 4),
                "alpha": round(float(structure.lattice.alpha), 2),
                "beta": round(float(structure.lattice.beta), 2),
                "gamma": round(float(structure.lattice.gamma), 2),
            },
        }
    except Exception:
        return None

router = APIRouter(prefix="/api/materials", tags=["materials"])


class MaterialCreate(BaseModel):
    formula: str
    name: Optional[str] = None
    space_group: Optional[str] = None
    crystal_system: Optional[str] = None
    lattice_a: Optional[float] = None
    lattice_b: Optional[float] = None
    lattice_c: Optional[float] = None
    public: bool = True


class MaterialResponse(BaseModel):
    id: int
    formula: str
    name: Optional[str]
    space_group: Optional[str]
    crystal_system: Optional[str]
    public: bool
    created_at: str

    model_config = {"from_attributes": True}


@router.get("/")
def list_materials(
    search: Optional[str] = Query(None),
    element: Optional[str] = Query(None),
    space_group: Optional[str] = Query(None),
    property_min: Optional[float] = Query(None),
    property_max: Optional[float] = Query(None),
    property_type: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    query = db.query(Material).filter(Material.public == True)

    if search:
        query = query.filter(
            Material.formula.contains(search) | Material.name.contains(search)
        )
    if element:
        query = query.join(Composition).filter(Composition.element == element)
    if space_group:
        query = query.filter(Material.space_group == space_group)
    if property_type and (property_min is not None or property_max is not None):
        query = query.join(Property).filter(Property.property_type == property_type)
        if property_min is not None:
            query = query.filter(Property.value >= property_min)
        if property_max is not None:
            query = query.filter(Property.value <= property_max)

    total = query.count()
    materials = query.offset(skip).limit(limit).all()

    results = []
    for m in materials:
        props = {p.property_type: {"value": p.value, "unit": p.unit} for p in m.properties}
        comp = {c.element: c.atomic_fraction for c in m.compositions}
        elements = [c.element for c in m.compositions] if m.compositions else []
        results.append({
            "id": m.id,
            "formula": m.formula,
            "name": m.name,
            "formula_html": m.formula_html,
            "space_group": m.space_group,
            "crystal_system": m.crystal_system,
            "lattice_parameters": {
                "a": m.lattice_a, "b": m.lattice_b, "c": m.lattice_c,
                "alpha": m.lattice_alpha, "beta": m.lattice_beta, "gamma": m.lattice_gamma,
            },
            "volume": m.volume,
            "density": m.density,
            "properties": props,
            "composition": comp,
            "elements": elements,
            "mp_id": m.mp_id,
            "tags": m.tags,
            "created_at": m.created_at.isoformat() if m.created_at else None,
        })

    return {"total": total, "skip": skip, "limit": limit, "data": results}


@router.get("/{material_id}")
def get_material(material_id: int, db: Session = Depends(get_db)):
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")

    props = {p.property_type: {"value": p.value, "unit": p.unit, "source": p.source, "confidence": p.confidence}
             for p in material.properties}
    comp = {c.element: {"amount": c.amount, "atomic_fraction": c.atomic_fraction}
            for c in material.compositions}
    phases = [{"name": p.phase_name, "temp_min": p.temperature_min, "temp_max": p.temperature_max,
               "stability": p.stability} for p in material.phases]

    structure = _generate_structure(material)
    elements = [c.element for c in material.compositions] if material.compositions else []

    return {
        "id": material.id,
        "formula": material.formula,
        "name": material.name,
        "formula_html": material.formula_html,
        "space_group": material.space_group,
        "crystal_system": material.crystal_system,
        "lattice_parameters": {
            "a": material.lattice_a, "b": material.lattice_b, "c": material.lattice_c,
            "alpha": material.lattice_alpha, "beta": material.lattice_beta, "gamma": material.lattice_gamma,
        },
        "volume": material.volume,
        "density": material.density,
        "cif_data": material.cif_data,
        "properties": props,
        "composition": comp,
        "phases": phases,
        "elements": elements,
        "structure": structure,
        "mp_id": material.mp_id,
        "tags": material.tags,
        "created_at": material.created_at.isoformat() if material.created_at else None,
    }


@router.post("/")
def create_material(data: MaterialCreate, db: Session = Depends(get_db)):
    from app.core.composition_analyzer import CompositionAnalyzer
    analyzer = CompositionAnalyzer()
    composition_dict = analyzer.parse_formula(data.formula)

    material = Material(
        formula=data.formula,
        name=data.name or data.formula,
        space_group=data.space_group,
        crystal_system=data.crystal_system,
        lattice_a=data.lattice_a,
        lattice_b=data.lattice_b,
        lattice_c=data.lattice_c,
        public=data.public,
    )
    db.add(material)
    db.flush()

    for element, amount in composition_dict.items():
        total = sum(composition_dict.values())
        comp = Composition(
            material_id=material.id,
            element=element,
            amount=amount,
            atomic_fraction=amount / total,
        )
        db.add(comp)

    db.commit()
    db.refresh(material)
    return {"id": material.id, "formula": material.formula, "message": "Material created"}


@router.post("/import-cif")
async def import_cif(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename or not file.filename.endswith(".cif"):
        raise HTTPException(status_code=400, detail="File must be a .cif file")
    content = await file.read()
    cif_text = content.decode("utf-8")

    try:
        from pymatgen.io.cif import CifParser
        parser = CifParser(io.StringIO(cif_text))
        structure = parser.parse_structures()[0]
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse CIF: {str(e)}")

    formula = structure.composition.reduced_formula
    material = Material(
        formula=formula,
        name=formula,
        space_group=structure.get_space_group_info()[1],
        crystal_system=structure.get_space_group_info()[0],
        lattice_a=structure.lattice.a,
        lattice_b=structure.lattice.b,
        lattice_c=structure.lattice.c,
        lattice_alpha=structure.lattice.alpha,
        lattice_beta=structure.lattice.beta,
        lattice_gamma=structure.lattice.gamma,
        volume=structure.volume,
        density=structure.density,
        cif_data=cif_text,
    )
    db.add(material)
    db.flush()

    for el, amt in structure.composition.as_dict().items():
        total = structure.composition.num_atoms
        comp = Composition(
            material_id=material.id,
            element=el,
            amount=amt,
            atomic_fraction=amt / total,
        )
        db.add(comp)

    db.commit()
    db.refresh(material)
    return {
        "id": material.id,
        "formula": material.formula,
        "space_group": material.space_group,
        "crystal_system": material.crystal_system,
        "message": "Material imported from CIF",
    }


@router.get("/{material_id}/cif")
def export_cif(material_id: int, db: Session = Depends(get_db)):
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    if material.cif_data:
        return PlainTextResponse(
            content=material.cif_data,
            media_type="chemical/x-cif",
            headers={"Content-Disposition": f'attachment; filename="{material.formula}.cif"'},
        )

    try:
        from pymatgen.core import Structure, Lattice
        from pymatgen.io.cif import CifWriter
        import numpy as np

        elements = [c.element for c in material.compositions]
        frac_coords = []
        for i, el in enumerate(elements):
            frac_coords.append([0.0, 0.0, 0.0])

        lattice = Lattice.from_parameters(
            material.lattice_a or 5.0,
            material.lattice_b or 5.0,
            material.lattice_c or 5.0,
            material.lattice_alpha or 90.0,
            material.lattice_beta or 90.0,
            material.lattice_gamma or 90.0,
        )
        structure = Structure(lattice, elements, frac_coords)
        cif_str = str(CifWriter(structure))
        material.cif_data = cif_str
        db.commit()
        return PlainTextResponse(
            content=cif_str,
            media_type="chemical/x-cif",
            headers={"Content-Disposition": f'attachment; filename="{material.formula}.cif"'},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate CIF: {str(e)}")


@router.delete("/{material_id}")
def delete_material(material_id: int, db: Session = Depends(get_db)):
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    db.delete(material)
    db.commit()
    return {"message": "Material deleted"}
