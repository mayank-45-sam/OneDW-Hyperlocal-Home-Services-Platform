"""
Gemini AI integration service.
Handles:
  - Phase 3: Voice NLP parsing (text → structured service request fields)
  - Phase 6: AI worker recommendation (ranked list with reason + confidence)
"""
import json
import logging
import re
from typing import Optional

from app.config import settings
from app.schemas.ai_schema import (
    NLPProcessResponse,
    AIRecommendResponse,
    AIRecommendRequest,
)

logger = logging.getLogger("onedw.gemini")


def _get_model():
    """Lazy-init Gemini model; returns None if API key is not configured."""
    if not settings.gemini_api_key:
        logger.warning("GEMINI_API_KEY not set — using mock fallback responses.")
        return None
    try:
        import google.generativeai as genai  # type: ignore
        genai.configure(api_key=settings.gemini_api_key)
        return genai.GenerativeModel("gemini-1.5-flash")
    except Exception as exc:
        logger.error(f"Failed to initialise Gemini model: {exc}")
        return None


def _extract_json(text: str) -> dict:
    """
    Try to parse JSON from a Gemini response.
    Handles both raw JSON and JSON wrapped inside ```json ... ``` code fences.
    """
    # Strip markdown fences if present
    cleaned = re.sub(r"```(?:json)?\s*|\s*```", "", text).strip()
    return json.loads(cleaned)


# ─── Phase 3: NLP Voice Parsing ────────────────────────────────────────────

_NLP_PROMPT_TEMPLATE = """
You are a service request parser for a home services platform.
Extract the following fields from the user's natural language text and return ONLY valid JSON with no other text.

Fields to extract:
- service: The type of home service (e.g. Electrician, Plumber, Painter, Cleaner, Mechanic, Carpenter, AC Repair). If unclear, return null.
- location: The location/area mentioned. If none, return null.
- date: The date mentioned in YYYY-MM-DD format if an exact date, or a descriptive word like "tomorrow", "today", etc. If none, return null.
- time: The time mentioned in HH:MM 24-hour format. If none, return null.

User text: "{text}"

Return ONLY this JSON structure:
{{"service": "...", "location": "...", "date": "...", "time": "..."}}
"""

_NLP_MOCK_RESPONSES = {
    "electrician": {
        "service": "Electrician",
        "location": "Tambaram",
        "date": "tomorrow",
        "time": "17:00",
    },
    "plumber": {
        "service": "Plumber",
        "location": "Puducherry",
        "date": "today",
        "time": "10:00",
    },
}


async def parse_voice_text(text: str) -> NLPProcessResponse:
    """
    Parse a natural-language voice transcript into structured request fields.
    Falls back to a mock response when Gemini is unavailable.
    """
    model = _get_model()

    if model is None:
        # Provide a sensible mock for development without an API key
        lower = text.lower()
        for keyword, mock in _NLP_MOCK_RESPONSES.items():
            if keyword in lower:
                return NLPProcessResponse(raw_text=text, **mock)
        return NLPProcessResponse(
            raw_text=text,
            service="Electrician",
            location="Tambaram",
            date="tomorrow",
            time="17:00",
        )

    try:
        prompt = _NLP_PROMPT_TEMPLATE.format(text=text)
        response = model.generate_content(prompt)
        parsed = _extract_json(response.text)
        return NLPProcessResponse(
            raw_text=text,
            service=parsed.get("service"),
            location=parsed.get("location"),
            date=parsed.get("date"),
            time=parsed.get("time"),
        )
    except Exception as exc:
        logger.error(f"Gemini NLP parsing failed: {exc}")
        return NLPProcessResponse(raw_text=text)


# ─── Phase 6: AI Worker Recommendation ─────────────────────────────────────

_RECOMMEND_PROMPT_TEMPLATE = """
You are an AI assistant for a home services platform. Select the best worker for a customer job.

Service type requested: {service_type}
Customer location: ({lat}, {lon})

Available workers (JSON array):
{workers_json}

Evaluate each worker based on:
1. Relevance of their skills to the service type
2. Average rating (higher is better)
3. Experience in years (more is better)
4. Distance from customer in km (closer is better)
5. Availability (must be true)

Return ONLY valid JSON with no other text:
{{
  "top_worker_id": "<worker_id>",
  "reason": "<1-2 sentence explanation>",
  "confidence": <float 0.0-1.0>,
  "ranking": ["<worker_id1>", "<worker_id2>", ...]
}}
"""


async def recommend_worker(request: AIRecommendRequest) -> AIRecommendResponse:
    """
    Use Gemini to rank workers and pick the best match.
    Falls back to a simple heuristic ranking when Gemini is unavailable.
    """
    model = _get_model()

    candidates = [c for c in request.candidates if c.is_available]
    if not candidates:
        # No available workers — return empty
        return AIRecommendResponse(
            top_worker_id="",
            reason="No available workers found for this service.",
            confidence=0.0,
            ranking=[],
        )

    if model is None:
        # Heuristic fallback: score = rating * 2 - distance * 0.1 + experience * 0.3
        def score(w):
            return w.average_rating * 2 - w.distance_km * 0.1 + w.experience_years * 0.3

        ranked = sorted(candidates, key=score, reverse=True)
        top = ranked[0]
        return AIRecommendResponse(
            top_worker_id=top.worker_id,
            reason=f"{top.name} has a {top.average_rating:.1f}⭐ rating with {top.experience_years} years of experience and is only {top.distance_km:.1f} km away.",
            confidence=round(min(score(top) / 10, 1.0), 2),
            ranking=[w.worker_id for w in ranked],
        )

    try:
        workers_json = json.dumps(
            [
                {
                    "worker_id": c.worker_id,
                    "name": c.name,
                    "skills": c.skills,
                    "experience_years": c.experience_years,
                    "average_rating": c.average_rating,
                    "total_jobs": c.total_jobs,
                    "distance_km": c.distance_km,
                    "is_available": c.is_available,
                }
                for c in candidates
            ],
            indent=2,
        )
        prompt = _RECOMMEND_PROMPT_TEMPLATE.format(
            service_type=request.service_type,
            lat=request.customer_latitude,
            lon=request.customer_longitude,
            workers_json=workers_json,
        )
        response = model.generate_content(prompt)
        parsed = _extract_json(response.text)
        return AIRecommendResponse(
            top_worker_id=parsed["top_worker_id"],
            reason=parsed["reason"],
            confidence=float(parsed.get("confidence", 0.85)),
            ranking=parsed.get("ranking", [parsed["top_worker_id"]]),
        )
    except Exception as exc:
        logger.error(f"Gemini recommendation failed: {exc}")
        # Fall back to top by rating
        top = max(candidates, key=lambda w: w.average_rating)
        return AIRecommendResponse(
            top_worker_id=top.worker_id,
            reason=f"{top.name} is the highest rated available worker.",
            confidence=0.7,
            ranking=[w.worker_id for w in sorted(candidates, key=lambda w: w.average_rating, reverse=True)],
        )
