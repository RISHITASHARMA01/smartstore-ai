import os
import json
import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from google import genai
from google.genai import types

from ..database import get_db
from ..auth.bypass import get_user_dependency
from ..config import settings
from ..services.recommendations import get_recommendation_data

logger = logging.getLogger(__name__)
get_current_user = get_user_dependency()

router = APIRouter(
    prefix="/recommendations",
    tags=["recommendations"],
    dependencies=[Depends(get_current_user)],
)

_SYSTEM_PROMPT = (
    "You are SmartStore AI's inventory analyst. "
    "Analyze the provided product data and return actionable, prioritized recommendations. "
    "Focus on business impact — prioritize products most likely to cause stockouts or lost sales."
)


class RecommendationRequest(BaseModel):
    product_id: Optional[int] = None


@router.post("")
def get_recommendations(payload: RecommendationRequest, db: Session = Depends(get_db)):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY not configured")

    data = get_recommendation_data(db, payload.product_id)

    if not data["products"]:
        return {"recommendations": [], "summary": "No products found to analyze."}

    prompt = (
        "Analyze this inventory data and return up to 5 product recommendations.\n\n"
        f"Inventory snapshot:\n{json.dumps(data, default=str, indent=2)}\n\n"
        "Return a JSON object with this exact structure (valid JSON only, no markdown):\n"
        "{\n"
        '  "recommendations": [\n'
        "    {\n"
        '      "product_id": <integer>,\n'
        '      "product_name": "<string>",\n'
        '      "action": "<one of: restock, promote, monitor, clearance, cross-sell>",\n'
        '      "reason": "<2-3 sentence explanation referencing the actual data>",\n'
        '      "priority": "<one of: high, medium, low>"\n'
        "    }\n"
        "  ],\n"
        '  "summary": "<1-2 sentence overall inventory health analysis>"\n'
        "}"
    )

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=settings.gemini_model,
            config=types.GenerateContentConfig(system_instruction=_SYSTEM_PROMPT),
            contents=prompt,
        )

        raw = (response.text or "").strip()
        # Strip markdown code fences if Gemini wraps the JSON
        if raw.startswith("```"):
            parts = raw.split("```")
            raw = parts[1] if len(parts) > 1 else raw
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        return json.loads(raw)

    except json.JSONDecodeError as e:
        logger.error("Recommendations JSON parse error: %s", e)
        raise HTTPException(
            status_code=500, detail="AI returned an unparseable response. Please retry."
        )
    except Exception as e:
        logger.error("Recommendations error: %s", e)
        raise HTTPException(status_code=500, detail="AI service error. Please try again.")
