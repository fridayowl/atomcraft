from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.material import Material
from app.core.reports import material_report_html, experiment_report_html, generate_pdf, HAS_WEASYPRINT

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/materials/{material_id}/pdf")
def download_material_report(material_id: int, db: Session = Depends(get_db)):
    if not HAS_WEASYPRINT:
        raise HTTPException(status_code=501, detail="PDF generation unavailable. Install weasyprint.")
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")

    props = {p.property_type: {"value": p.value, "unit": p.unit} for p in material.properties}
    comp = {c.element: {"amount": c.amount, "atomic_fraction": c.atomic_fraction} for c in material.compositions}

    data = {
        "id": material.id,
        "formula": material.formula,
        "name": material.name,
        "space_group": material.space_group,
        "crystal_system": material.crystal_system,
        "lattice_parameters": {"a": material.lattice_a, "b": material.lattice_b, "c": material.lattice_c},
        "volume": material.volume,
        "density": material.density,
        "properties": props,
        "composition": comp,
        "created_at": material.created_at.isoformat() if material.created_at else None,
        "_synthesis": {"feasibility_score": 0.5, "recommended_methods": [], "risks": [], "thermodynamic_notes": ""},
    }

    html = material_report_html(data)
    pdf_bytes = generate_pdf(html)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{material.formula}_report.pdf"'},
    )
