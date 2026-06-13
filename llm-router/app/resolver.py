"""
Availability-aware resolver.

Given a requested capability (or a literal model), walk its ordered candidate
pool and return the first one that is usable RIGHT NOW:

  1. backend statically usable  (enabled + key present if cloud)
  2. backend host healthy        (cached probe)
  3. model resident-or-fits      (ollama only: won't force a 20GB model onto
                                  the 3060 while the win11 VM holds the 5090)

The fit check is what folds the GPU-passthrough failover into routing: when the
VM is up, prefect's live VRAM is 12GB, so a 20GB candidate on prefect fails the
fit check and the resolver falls through to the next candidate (kairobox / 8b /
cloud). When the VM is off, prefect reports 32GB and the big model passes.
"""
from __future__ import annotations

import time
import logging
from dataclasses import dataclass
from typing import Optional

import httpx

from config import Config, Backend, Candidate

logger = logging.getLogger("llm-router.resolver")


@dataclass
class Resolution:
    backend: Backend
    model: str
    capability: Optional[str]   # None if the request was a literal model


# --- caches -----------------------------------------------------------------
# health: backend_name -> (expires_at, healthy_bool)
_health: dict[str, tuple[float, bool]] = {}
# residency: backend_name -> (expires_at, {"resident": set[str], "vram_total_gb": float})
_residency: dict[str, tuple[float, dict]] = {}


async def _probe_health(backend: Backend, ttl: float) -> bool:
    now = time.monotonic()
    hit = _health.get(backend.name)
    if hit and hit[0] > now:
        return hit[1]

    healthy = False
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            if backend.type == "ollama":
                r = await client.get(f"{backend.url}/api/tags")
                healthy = r.status_code == 200
            else:
                # Cloud backends: assume reachable if key present; a cheap
                # connectivity check would cost a request, so we trust the key.
                healthy = backend.usable
    except Exception as exc:
        logger.info("health probe failed for %s: %s", backend.name, exc)
        healthy = False

    _health[backend.name] = (now + ttl, healthy)
    return healthy


async def _ollama_residency(backend: Backend, ttl: float) -> dict:
    """Return {'resident': set(model_names), 'vram_total_gb': float}.
    vram_total_gb reflects the GPU currently backing this ollama (detected via
    the largest single GPU's total memory reported by /api/ps + a tags fallback).
    """
    now = time.monotonic()
    hit = _residency.get(backend.name)
    if hit and hit[0] > now:
        return hit[1]

    # `resident` holds only models that are FULLY in VRAM. A model that ollama
    # loaded split across CPU+GPU (size_vram < size) is "loaded" but is exactly
    # the slow partial-offload we route around, so we do NOT count it as resident.
    resident: set[str] = set()
    partial: set[str] = set()
    vram_total_gb = float(backend.raw.get("vram_gb", 0) or 0)

    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            r = await client.get(f"{backend.url}/api/ps")
            if r.status_code == 200:
                data = r.json()
                for m in data.get("models", []):
                    nm = m.get("name") or m.get("model")
                    if not nm:
                        continue
                    total = m.get("size") or 0
                    in_vram = m.get("size_vram") or 0
                    # Treat as fully-resident only if ~all of it is in VRAM.
                    if total and in_vram >= total * 0.98:
                        resident.add(nm)
                    else:
                        partial.add(nm)
    except Exception as exc:
        logger.info("residency probe failed for %s: %s", backend.name, exc)

    # For the prefect backend, the live GPU (3060 vs 5090) changes the ceiling.
    # Detect via the host's nvidia state exposed through ollama is not possible
    # directly, so we infer from configured ceilings: if any resident model is
    # bigger than the 3060 ceiling, the 5090 must be live; otherwise assume the
    # smaller card unless told otherwise. The accurate signal is set by the
    # GPU-switch hook writing a marker; see _prefect_vram_gb().
    if vram_total_gb == 0:
        vram_total_gb = _prefect_vram_gb(backend)

    snap = {"resident": resident, "partial": partial, "vram_total_gb": vram_total_gb}
    _residency[backend.name] = (now + ttl, snap)
    return snap


def _prefect_vram_gb(backend: Backend) -> float:
    """Determine prefect's live VRAM ceiling.

    Source of truth: the GPU-failover switch script writes the active card to
    /config/prefect_gpu (shared volume) as '3060' or '5090'. If that marker is
    missing, fall back to the smaller (safer) ceiling so we never over-promise.
    """
    ceil_3060 = float(backend.raw.get("vram_gb_3060", 12) or 12)
    ceil_5090 = float(backend.raw.get("vram_gb_5090", 32) or 32)
    try:
        with open("/config/prefect_gpu", "r") as fh:
            tag = fh.read().strip()
        if tag == "5090":
            return ceil_5090
        if tag == "3060":
            return ceil_3060
    except OSError:
        pass
    return ceil_3060   # safe default: assume the small card


async def _candidate_ok(cfg: Config, cand: Candidate) -> tuple[bool, str]:
    backend = cfg.backends.get(cand.backend)
    if backend is None:
        return False, f"unknown backend {cand.backend}"
    if not backend.usable:
        return False, f"{backend.name} disabled or missing key"

    if not await _probe_health(backend, cfg.health_ttl()):
        return False, f"{backend.name} unhealthy"

    # Fit check only applies to local ollama backends with a known VRAM ceiling.
    if backend.type == "ollama":
        snap = await _ollama_residency(backend, cfg.residency_ttl())
        # Fully resident in VRAM? Then it definitionally fits — take it.
        if cand.model in snap["resident"]:
            return True, "resident"
        size = cfg.model_sizes_gb.get(cand.model)
        ceil = snap["vram_total_gb"]
        if size is not None and ceil and size > ceil:
            # Would not fit the live card. If it's currently loaded split across
            # CPU+GPU, say so explicitly — that's the case we route around.
            if cand.model in snap.get("partial", set()):
                return False, f"{cand.model} partially on CPU ({size}GB > {backend.name} {ceil}GB live)"
            return False, f"{cand.model} ~{size}GB > {backend.name} {ceil}GB live ceiling"
    return True, "ok"


async def resolve(cfg: Config, requested: str) -> Resolution:
    """Resolve a requested capability/model to a concrete (backend, model).

    `requested` may be:
      - a capability name      -> walk its candidate pool
      - 'model@backend'        -> literal, single candidate
      - 'model'                -> literal on the first ollama backend that has it
    Raises LookupError if nothing is available.
    """
    # Literal model@backend
    if "@" in requested:
        model, _, bname = requested.partition("@")
        cands = [Candidate(model=model, backend=bname)]
        cap_name = None
    elif requested in cfg.capabilities:
        cands = list(cfg.capabilities[requested])
        cap_name = requested
        if cfg.ordering() == "prefer_local":
            cands.sort(key=lambda c: cfg.backends.get(c.backend) is not None
                       and cfg.backends[c.backend].type != "ollama")
    else:
        # Bare model name: try each ollama backend in config order.
        cap_name = None
        cands = [
            Candidate(model=requested, backend=name)
            for name, b in cfg.backends.items() if b.type == "ollama"
        ]

    reasons = []
    for cand in cands:
        ok, why = await _candidate_ok(cfg, cand)
        if ok:
            logger.info("resolved %r -> %s@%s (%s)", requested, cand.model, cand.backend, why)
            return Resolution(backend=cfg.backends[cand.backend], model=cand.model, capability=cap_name)
        reasons.append(f"{cand.model}@{cand.backend}: {why}")

    raise LookupError(f"no available candidate for {requested!r}; tried: " + "; ".join(reasons))
