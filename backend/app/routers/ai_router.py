"""
AI endpoints:
  - POST /api/nlp/process  — Phase 3: Voice text → structured fields (no auth required)
  - POST /api/ai/recommend — Phase 6: Gemini AI worker recommendation
"""
from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.schemas.ai_schema import (
    NLPProcessRequest,
    NLPProcessResponse,
    AIRecommendRequest,
    AIRecommendResponse,
)
from app.services import gemini_service
from app.database.connection import get_database
from app.utils.dependencies import get_current_user

router = APIRouter(tags=["AI"])


@router.post("/api/nlp/process", response_model=NLPProcessResponse)
async def process_nlp(payload: NLPProcessRequest):
    """
    Parse a voice transcript into structured service request fields using Gemini.
    No authentication required — this is a public AI utility endpoint.
    """
    return await gemini_service.parse_voice_text(payload.text)


@router.post("/api/ai/recommend", response_model=AIRecommendResponse)
async def recommend_worker(
    payload: AIRecommendRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """Use Gemini AI to rank and recommend the best available worker."""
    return await gemini_service.recommend_worker(payload)
