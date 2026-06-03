from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from app.database import get_db
from app.core.predictor import PropertyPredictor

router = APIRouter(prefix="/api/predict", tags=["prediction"])
predictor = PropertyPredictor()


class PredictRequest(BaseModel):
    formula: str
    properties: list[str] = ["band_gap", "formation_energy", "density"]


class BatchPredictRequest(BaseModel):
    formulas: list[str]
    properties: list[str] = ["band_gap", "formation_energy", "density"]


@router.post("/")
async def predict_properties(req: PredictRequest):
    results = []
    for prop in req.properties:
        pred = await predictor.predict(req.formula, prop)
        results.append(pred)
    return {"formula": req.formula, "predictions": results}


@router.post("/batch")
async def batch_predict(req: BatchPredictRequest):
    results = await predictor.batch_predict(req.formulas, req.properties)
    return {"results": results, "total": len(results)}


@router.get("/feature-importance/{property_type}")
async def feature_importance(property_type: str):
    return await predictor.get_feature_importance(property_type)
