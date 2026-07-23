"""
Pydantic schemas for the AI/NLP endpoints:
  - NLP voice text → structured request fields (Phase 3)
  - AI worker recommendation engine (Phase 6)
"""
from pydantic import BaseModel, Field
from typing import Optional, List


# ─── Phase 3: Voice NLP ────────────────────────────────────────────────────

class NLPProcessRequest(BaseModel):
    text: str = Field(..., min_length=3, description="Raw voice transcript to parse")


class NLPProcessResponse(BaseModel):
    service: Optional[str] = None
    location: Optional[str] = None
    date: Optional[str] = None
    time: Optional[str] = None
    raw_text: str


# ─── Phase 6: Worker Recommendation ────────────────────────────────────────

class WorkerCandidateSchema(BaseModel):
    worker_id: str
    name: str
    skills: List[str]
    experience_years: int
    average_rating: float
    total_jobs: int
    distance_km: float
    is_available: bool


class AIRecommendRequest(BaseModel):
    service_type: str
    customer_latitude: float
    customer_longitude: float
    candidates: List[WorkerCandidateSchema]


class AIRecommendResponse(BaseModel):
    top_worker_id: str
    reason: str
    confidence: float
    ranking: List[str]  # Ordered list of worker_ids
