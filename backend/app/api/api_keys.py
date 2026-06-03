import secrets
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.api.auth import get_current_user

router = APIRouter(prefix="/api/keys", tags=["api_keys"])


class ApiKeyResponse(BaseModel):
    api_key: str
    message: str


@router.post("/generate")
def generate_api_key(current_user: User = Depends(get_current_user),
                     db: Session = Depends(get_db)):
    new_key = f"aion_{secrets.token_hex(24)}"
    current_user.api_key = new_key
    db.commit()
    return ApiKeyResponse(api_key=new_key, message="API key generated")


@router.get("/")
def get_api_key(current_user: User = Depends(get_current_user)):
    if not current_user.api_key:
        return {"api_key": None, "message": "No API key generated"}
    return {
        "api_key": f"{current_user.api_key[:16]}...{current_user.api_key[-4:]}",
        "message": "Full key shown only on generation",
    }


@router.post("/revoke")
def revoke_api_key(current_user: User = Depends(get_current_user),
                   db: Session = Depends(get_db)):
    current_user.api_key = None
    db.commit()
    return {"message": "API key revoked"}
