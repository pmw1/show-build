"""
Config loader for llm-router.

Loads router.yaml into a typed-ish in-memory model and hot-reloads it when the
file's mtime changes. Thread-safe for the read path (FastAPI handlers call
get_config() on every request); reloads happen lazily on read when mtime moved.
"""
from __future__ import annotations

import os
import threading
import logging
from dataclasses import dataclass, field
from typing import Any, Optional

import yaml

logger = logging.getLogger("llm-router.config")

CONFIG_PATH = os.environ.get("ROUTER_CONFIG", "/config/router.yaml")


@dataclass
class Backend:
    name: str
    type: str                      # ollama | openai | anthropic
    url: str
    enabled: bool = True
    key_env: Optional[str] = None
    raw: dict = field(default_factory=dict)

    @property
    def api_key(self) -> Optional[str]:
        if not self.key_env:
            return None
        return os.environ.get(self.key_env) or None

    @property
    def usable(self) -> bool:
        """Statically usable: enabled, and if it needs a key, the key is present.
        (Host health is a separate runtime check in the resolver.)"""
        if not self.enabled:
            return False
        if self.key_env and not self.api_key:
            return False
        return True


@dataclass
class Candidate:
    model: str
    backend: str


@dataclass
class Config:
    version: int
    policy: dict
    backends: dict[str, Backend]
    capabilities: dict[str, list[Candidate]]
    model_sizes_gb: dict[str, float]
    mtime: float

    def health_ttl(self) -> float:
        return float(self.policy.get("health_ttl", 15))

    def residency_ttl(self) -> float:
        return float(self.policy.get("residency_ttl", 5))

    def unavailable_status(self) -> int:
        return int(self.policy.get("unavailable_status", 503))

    def ordering(self) -> str:
        return str(self.policy.get("ordering", "as_listed"))


_lock = threading.Lock()
_cached: Optional[Config] = None


def _parse(doc: dict, mtime: float) -> Config:
    backends: dict[str, Backend] = {}
    for name, b in (doc.get("backends") or {}).items():
        backends[name] = Backend(
            name=name,
            type=b["type"],
            url=b["url"].rstrip("/"),
            enabled=bool(b.get("enabled", True)),
            key_env=b.get("key_env"),
            raw=b,
        )

    capabilities: dict[str, list[Candidate]] = {}
    for cap, body in (doc.get("capabilities") or {}).items():
        cands = []
        for c in (body.get("candidates") or []):
            cands.append(Candidate(model=c["model"], backend=c["backend"]))
        capabilities[cap] = cands

    return Config(
        version=int(doc.get("version", 1)),
        policy=doc.get("policy") or {},
        backends=backends,
        capabilities=capabilities,
        model_sizes_gb={k: float(v) for k, v in (doc.get("model_sizes_gb") or {}).items()},
        mtime=mtime,
    )


def load(force: bool = False) -> Config:
    """Return the current config, reloading from disk if the file changed."""
    global _cached
    try:
        mtime = os.path.getmtime(CONFIG_PATH)
    except OSError as exc:
        if _cached is not None:
            logger.warning("config stat failed (%s); serving cached", exc)
            return _cached
        raise

    with _lock:
        if _cached is None or force or mtime != _cached.mtime:
            with open(CONFIG_PATH, "r") as fh:
                doc = yaml.safe_load(fh) or {}
            _cached = _parse(doc, mtime)
            logger.info(
                "config loaded: %d capabilities, %d backends",
                len(_cached.capabilities), len(_cached.backends),
            )
        return _cached


def get_config() -> Config:
    return load()


def raw_text() -> str:
    with open(CONFIG_PATH, "r") as fh:
        return fh.read()


def write_text(new_text: str) -> Config:
    """Validate then atomically replace the config file. Returns reloaded Config.
    Raises yaml.YAMLError / KeyError on invalid content (caller maps to 400)."""
    doc = yaml.safe_load(new_text) or {}
    # Validate by parsing into the model (raises on structural problems).
    _parse(doc, 0.0)
    tmp = CONFIG_PATH + ".tmp"
    with open(tmp, "w") as fh:
        fh.write(new_text)
    os.replace(tmp, CONFIG_PATH)
    return load(force=True)
