import os
import json
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List
from sqlalchemy.orm import Session
import anthropic

from ..database import get_db
from ..auth.dependencies import get_current_user
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

TOOLS = [
    {
        "name": "get_low_stock_products",
        "description": (
            "Get all active products running low on stock (stock at or below reorder threshold). "
            "Use this to answer questions about low stock, restocking needs, or inventory alerts."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "threshold_pct": {
                    "type": "integer",
                    "description": "Optional threshold percentage override. Default is 20.",
                }
            },
            "required": [],
        },
    },
    {
        "name": "get_product_detail",
        "description": "Get detailed information about a specific product by ID or name.",
        "input_schema": {
            "type": "object",
            "properties": {
                "product_id": {
                    "type": "integer",
                    "description": "The product ID to look up.",
                },
                "product_name": {
                    "type": "string",
                    "description": "The product name to search for (partial match supported).",
                },
            },
            "required": [],
        },
    },
    {
        "name": "get_po_history",
        "description": (
            "Get purchase order history from the last N days, "
            "optionally filtered by supplier name."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "supplier_name": {
                    "type": "string",
                    "description": "Optional supplier name filter (partial match supported).",
                },
                "days": {
                    "type": "integer",
                    "description": "Number of days to look back. Default is 30.",
                },
            },
            "required": [],
        },
    },
    {
        "name": "get_expiring_products",
        "description": "Get products expiring within the next N days.",
        "input_schema": {
            "type": "object",
            "properties": {
                "days_ahead": {
                    "type": "integer",
                    "description": "Number of days ahead to check for expiry. Default is 14.",
                }
            },
            "required": [],
        },
    },
]


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[Message]


@router.post("/chat")
def chat(payload: ChatRequest, db: Session = Depends(get_db)):
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY not configured")

    client = anthropic.Anthropic(api_key=api_key)
    messages = [{"role": m.role, "content": m.content} for m in payload.messages]

    try:
        for _ in range(10):
            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                tools=TOOLS,
                messages=messages,
            )

            if response.stop_reason == "end_turn":
                text = next(
                    (block.text for block in response.content if hasattr(block, "text")),
                    "",
                )
                return {"response": text}

            if response.stop_reason == "tool_use":
                assistant_content = []
                for block in response.content:
                    if block.type == "tool_use":
                        assistant_content.append(
                            {
                                "type": "tool_use",
                                "id": block.id,
                                "name": block.name,
                                "input": block.input,
                            }
                        )
                    elif block.type == "text":
                        assistant_content.append({"type": "text", "text": block.text})

                messages.append({"role": "assistant", "content": assistant_content})

                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        result = _run_tool(block.name, block.input, db)
                        tool_results.append(
                            {
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": json.dumps(result, default=str),
                            }
                        )

                messages.append({"role": "user", "content": tool_results})

    except anthropic.AuthenticationError:
        raise HTTPException(
            status_code=500,
            detail="Invalid ANTHROPIC_API_KEY — update .env with your real Anthropic API key",
        )

    raise HTTPException(status_code=500, detail="Max tool iterations reached without final response")


def _run_tool(name: str, inputs: dict, db: Session):
    if name == "get_low_stock_products":
        return get_low_stock_products(db, **inputs)
    if name == "get_product_detail":
        return get_product_detail(db, **inputs)
    if name == "get_po_history":
        return get_po_history(db, **inputs)
    if name == "get_expiring_products":
        return get_expiring_products(db, **inputs)
    return {"error": f"Unknown tool: {name}"}
