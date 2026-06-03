from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.models.experiment import Experiment, ExperimentStep, ExperimentResult
from pydantic import BaseModel

router = APIRouter(prefix="/api/experiments", tags=["experiments"])


class ExperimentCreate(BaseModel):
    material_id: int
    name: str
    experiment_type: str
    description: Optional[str] = None
    synthesis_method: Optional[str] = None
    synthesis_conditions: Optional[dict] = None


class StepCreate(BaseModel):
    step_number: int
    step_type: str
    description: str
    duration_minutes: Optional[float] = None
    temperature: Optional[float] = None


class ResultCreate(BaseModel):
    result_type: str
    value: Optional[float] = None
    unit: Optional[str] = None
    characterization_method: str
    notes: Optional[str] = None


@router.get("/")
def list_experiments(
    material_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    query = db.query(Experiment)
    if material_id:
        query = query.filter(Experiment.material_id == material_id)
    if status:
        query = query.filter(Experiment.status == status)

    total = query.count()
    experiments = query.order_by(Experiment.created_at.desc()).offset(skip).limit(limit).all()

    return {
        "total": total,
        "data": [{
            "id": e.id,
            "material_id": e.material_id,
            "name": e.name,
            "experiment_type": e.experiment_type,
            "status": e.status,
            "synthesis_method": e.synthesis_method,
            "successful": e.successful,
            "created_at": e.created_at.isoformat() if e.created_at else None,
            "step_count": len(e.steps),
        } for e in experiments]
    }


@router.get("/{experiment_id}")
def get_experiment(experiment_id: int, db: Session = Depends(get_db)):
    experiment = db.query(Experiment).filter(Experiment.id == experiment_id).first()
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")

    return {
        "id": experiment.id,
        "material_id": experiment.material_id,
        "name": experiment.name,
        "experiment_type": experiment.experiment_type,
        "description": experiment.description,
        "status": experiment.status,
        "synthesis_method": experiment.synthesis_method,
        "synthesis_conditions": experiment.synthesis_conditions,
        "successful": experiment.successful,
        "notes": experiment.notes,
        "tags": experiment.tags,
        "steps": [{
            "id": s.id,
            "step_number": s.step_number,
            "step_type": s.step_type,
            "description": s.description,
            "duration_minutes": s.duration_minutes,
            "temperature": s.temperature,
            "completed": s.completed,
        } for s in experiment.steps],
        "results": [{
            "id": r.id,
            "result_type": r.result_type,
            "value": r.value,
            "unit": r.unit,
            "characterization_method": r.characterization_method,
            "notes": r.notes,
        } for r in experiment.results],
        "created_at": experiment.created_at.isoformat() if experiment.created_at else None,
        "completed_at": experiment.completed_at.isoformat() if experiment.completed_at else None,
    }


@router.post("/")
def create_experiment(data: ExperimentCreate, db: Session = Depends(get_db)):
    experiment = Experiment(
        material_id=data.material_id,
        name=data.name,
        experiment_type=data.experiment_type,
        description=data.description,
        synthesis_method=data.synthesis_method,
        synthesis_conditions=data.synthesis_conditions or {},
        status="planned",
    )
    db.add(experiment)
    db.commit()
    db.refresh(experiment)
    return {"id": experiment.id, "message": "Experiment created"}


@router.post("/{experiment_id}/steps")
def add_step(experiment_id: int, data: StepCreate, db: Session = Depends(get_db)):
    experiment = db.query(Experiment).filter(Experiment.id == experiment_id).first()
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")

    step = ExperimentStep(
        experiment_id=experiment_id,
        **data.model_dump(),
    )
    db.add(step)
    db.commit()
    db.refresh(step)
    return {"id": step.id, "message": "Step added"}


@router.post("/{experiment_id}/results")
def add_result(experiment_id: int, data: ResultCreate, db: Session = Depends(get_db)):
    experiment = db.query(Experiment).filter(Experiment.id == experiment_id).first()
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")

    result = ExperimentResult(
        experiment_id=experiment_id,
        **data.model_dump(),
    )
    db.add(result)
    db.commit()
    db.refresh(result)
    return {"id": result.id, "message": "Result recorded"}


@router.patch("/{experiment_id}/status")
def update_status(experiment_id: int, status: str, successful: bool = None, db: Session = Depends(get_db)):
    experiment = db.query(Experiment).filter(Experiment.id == experiment_id).first()
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")

    experiment.status = status
    if successful is not None:
        experiment.successful = successful

    import datetime
    if status in ["completed", "failed"]:
        experiment.completed_at = datetime.datetime.utcnow()

    db.commit()
    return {"message": f"Experiment status updated to {status}"}
