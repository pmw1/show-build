"""
Common types for backend adapters.

Every adapter takes a normalized ChatRequest and yields normalized ChatChunks
(for streaming) or returns a single ChatResult (for batch). The endpoint layer
re-serializes these into whatever dialect the *client* asked for (OpenAI or
ollama), so the client never sees backend-specific shapes.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Optional


@dataclass
class ChatRequest:
    model: str                          # concrete backend model (already resolved)
    messages: list[dict]                # [{"role","content"}, ...]
    temperature: float = 0.2
    max_tokens: Optional[int] = None
    top_p: Optional[float] = None
    json_mode: bool = False
    stream: bool = False
    extra: dict = field(default_factory=dict)


@dataclass
class ChatChunk:
    delta: str                          # incremental text
    done: bool = False
    finish_reason: Optional[str] = None


@dataclass
class ChatResult:
    content: str
    finish_reason: str = "stop"
    model: str = ""
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None


class BackendError(Exception):
    """Raised when a backend call fails after being selected. The endpoint maps
    this to a 502 (the resolver already confirmed availability, so a failure
    here is a backend-side problem, not a routing one)."""
    def __init__(self, message: str, status: int = 502):
        super().__init__(message)
        self.status = status
