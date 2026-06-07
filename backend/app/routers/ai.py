import os
import json
import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import List
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)
from google import genai
from google.genai import types

from ..database import get_db
from ..auth.dependencies import get_current_user
from ..config import settings
from ..services.ai_tools import (
    get_low_stock_products,
    get_product_detail,
    get_po_history,
    get_expiring_products,
)

router = APIRouter(dependencies=[Depends(get_current_user)])

SYSTEM_PROMPT = (
    "You are SmartStore AI assistant. You help manage inventory for a retail business. "
    "Always use the provided tools to get real data before answering questions about "
    "stock levels, products, suppliers, or purchase orders. Never make up numbers."
)

_TOOL_DECLARATIONS = [
    types.FunctionDeclaration(
        name="get_low_stock_products",
        description=(
            "Get all active products running low on stock (at or below reorder threshold). "
            "Use this to answer questions about low stock, restocking needs, or inventory alerts."
        ),
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "threshold_pct": types.Schema(
                    type=types.Type.INTEGER,
                    description="Optional threshold percentage override. Default is 20.",
                )
            },
        ),
    ),
    types.FunctionDeclaration(
        name="get_product_detail",
        description="Get detailed information about a specific product by ID or name.",
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "product_id": types.Schema(
                    type=types.Type.INTEGER,
                    description="The product ID to look up.",
                ),
                "product_name": types.Schema(
                    type=types.Type.STRING,
                    description="The product name to search for (partial match supported).",
                ),
            },
        ),
    ),
    types.FunctionDeclaration(
        name="get_po_history",
        description=(
            "Get purchase order history from the last N days, "
            "optionally filtered by supplier name."
        ),
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "supplier_name": types.Schema(
                    type=types.Type.STRING,
                    description="Optional supplier name filter (partial match supported).",
                ),
                "days": types.Schema(
                    type=types.Type.INTEGER,
                    description="Number of days to look back. Default is 30.",
                ),
            },
        ),
    ),
    types.FunctionDeclaration(
        name="get_expiring_products",
        description="Get products expiring within the next N days.",
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "days_ahead": types.Schema(
                    type=types.Type.INTEGER,
                    description="Number of days ahead to check for expiry. Default is 14.",
                )
            },
        ),
    ),
]

GEMINI_TOOLS = [types.Tool(function_declarations=_TOOL_DECLARATIONS)]


# Prompt injection patterns — phrases that attempt to hijack system instructions
_INJECTION_PATTERNS = [
    "ignore previous instructions",
    "ignore all previous",
    "forget your instructions",
    "disregard your",
    "you are now",
    "act as if you are",
    "pretend you are",
    "your new instructions",
    "override instructions",
    "system prompt",
    "new system prompt",
    "jailbreak",
    "dan mode",
    "developer mode",
    "unrestricted mode",
]


def _check_prompt_injection(content: str) -> None:
    lower = content.lower()
    for pattern in _INJECTION_PATTERNS:
        if pattern in lower:
            raise HTTPException(
                status_code=400,
                detail="Message contains disallowed content.",
            )


class Message(BaseModel):
    role: str = Field(pattern="^(user|assistant)$")
    content: str = Field(min_length=1, max_length=4000)


class ChatRequest(BaseModel):
    messages: List[Message] = Field(min_length=1, max_length=50)


@router.post("/chat")
def chat(payload: ChatRequest, db: Session = Depends(get_db)):
    # Guard against prompt injection in user messages
    for msg in payload.messages:
        if msg.role == "user":
            _check_prompt_injection(msg.content)

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY not configured in .env")

    try:
        client = genai.Client(api_key=api_key)

        messages = payload.messages
        # Convert prior messages to Gemini history format (all but the last)
        history = []
        for msg in messages[:-1]:
            gemini_role = "model" if msg.role == "assistant" else "user"
            history.append(
                types.Content(role=gemini_role, parts=[types.Part(text=msg.content)])
            )

        last_message = messages[-1].content

        chat_session = client.chats.create(
            model=settings.gemini_model,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                tools=GEMINI_TOOLS,
            ),
            history=history,
        )

        response = chat_session.send_message(last_message)

        for _ in range(10):
            fn_calls = response.function_calls
            if not fn_calls:
                return {"response": response.text or ""}

            # Execute all function calls and collect results
            result_parts = []
            for fc in fn_calls:
                result = _run_tool(fc.name, dict(fc.args), db)
                result_parts.append(
                    types.Part.from_function_response(
                        name=fc.name,
                        response={"result": json.dumps(result, default=str)},
                    )
                )

            response = chat_session.send_message(result_parts)

    except HTTPException:
        raise
    except Exception as e:
        err = str(e)
        logger.error("Gemini chat error: %s", err)
        if "API_KEY_INVALID" in err or "API key not valid" in err or "invalid" in err.lower():
            raise HTTPException(status_code=500, detail="AI service configuration error")
        raise HTTPException(status_code=500, detail="AI service error. Please try again.")

    raise HTTPException(status_code=500, detail="Max tool iterations reached without final response")


def _run_tool(name: str, inputs: dict, db: Session):
    # Validate and clamp all AI tool parameters before passing to DB functions
    if name == "get_low_stock_products":
        safe = {"threshold_pct": max(0, min(100, int(inputs.get("threshold_pct", 20))))}
        return get_low_stock_products(db, **safe)
    if name == "get_product_detail":
        safe = {}
        if "product_id" in inputs:
            safe["product_id"] = int(inputs["product_id"])
        if "product_name" in inputs:
            safe["product_name"] = str(inputs["product_name"])[:100]
        return get_product_detail(db, **safe)
    if name == "get_po_history":
        safe = {
            "days": max(1, min(365, int(inputs.get("days", 30)))),
        }
        if "supplier_name" in inputs:
            safe["supplier_name"] = str(inputs["supplier_name"])[:100]
        return get_po_history(db, **safe)
    if name == "get_expiring_products":
        safe = {"days_ahead": max(1, min(365, int(inputs.get("days_ahead", 14))))}
        return get_expiring_products(db, **safe)
    return {"error": "Unknown tool"}
