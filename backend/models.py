from __future__ import annotations
from typing import Literal
from pydantic import BaseModel


class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    stream: bool = True


class Source(BaseModel):
    type: str       # "aoe4world", "wiki", "liquipedia", "aoe4guides", "gamedata", "youtube"
    title: str      # Human-readable description
    url: str | None = None  # Link if available


class ChatResponseChunk(BaseModel):
    type: Literal["token", "sources", "done", "error", "tool_call"]
    content: str | None = None
    sources: list[Source] | None = None
