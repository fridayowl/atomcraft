from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from app.core.llm import MaterialsLLM
from app.config import settings

router = APIRouter(prefix="/api/chat", tags=["chat"])
llm = MaterialsLLM(api_key=settings.openai_api_key)


class ChatRequest(BaseModel):
    message: str
    context: Optional[dict] = None


class SuggestRequest(BaseModel):
    requirements: dict
    num_suggestions: int = 5


@router.post("/query")
async def chat_query(req: ChatRequest):
    result = await llm.query(req.message)
    return result


@router.post("/suggest")
async def suggest_materials(req: SuggestRequest):
    suggestions = await llm.suggest_material(req.requirements)
    return {"suggestions": suggestions[:req.num_suggestions]}
