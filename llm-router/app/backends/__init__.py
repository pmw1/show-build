"""Backend adapter dispatch by backend.type."""
from config import Backend
from backends import ollama, openai, anthropic
from backends.base import ChatRequest, ChatChunk, ChatResult, BackendError

_ADAPTERS = {
    "ollama": ollama,
    "openai": openai,
    "anthropic": anthropic,
}


def adapter_for(backend: Backend):
    a = _ADAPTERS.get(backend.type)
    if a is None:
        raise BackendError(f"no adapter for backend type {backend.type!r}")
    return a
