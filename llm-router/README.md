# llm-router

A small capability-pool LLM router. Clients ask for a **capability** (a logical
role like `description-writer`) instead of a concrete model. The router resolves
the capability to the first **available** backend candidate — health-checked and
VRAM-fit-aware — and proxies the call, translating between OpenAI / ollama /
Anthropic dialects in both directions. Streaming is supported on every path.

It packages with show-build but runs fully standalone (its own Docker image).

## Why

The prefect host's ollama shares a GPU with a Windows VM: when the VM is running
it grabs the RTX 5090, leaving ollama on the RTX 3060 (12 GB) with only a small
model resident. Statically pointing a client at `qwen3:32b` then forces a 20 GB
model onto a 12 GB card (heavy CPU spill) or 404s. The router makes that a
non-issue: a capability lists several candidates across machines/models, and the
resolver skips any that can't run right now.

## Concept: capability → ordered candidate pool

In `router.yaml`:

```yaml
capabilities:
  description-writer:
    candidates:
      - {model: qwen3:8b,         backend: prefect}   # cheap, always-on local
      - {model: qwen3:32b-q4_K_M, backend: prefect}   # only when VM is off
      - {model: qwen3:32b-q4_K_M, backend: kairobox}  # offload target
      - {model: grok-2-latest,    backend: xai}        # cloud last resort
```

A request for `description-writer` is satisfied by the first candidate whose:
1. backend is enabled and (for cloud) has its API key present,
2. host passes a cached health probe,
3. model is resident or fits the backend's *live* VRAM ceiling.

The live VRAM ceiling for `prefect` is read from `prefect_gpu` (this dir),
which the GPU-failover switch script writes as `3060` or `5090`.

## Endpoints

| Method | Path | Dialect |
|---|---|---|
| POST | `/v1/chat/completions` | OpenAI (SSE stream) |
| POST | `/api/chat` | ollama (ndjson stream) |
| POST | `/api/generate` | ollama (ndjson stream) |
| GET  | `/capabilities` | live availability per candidate |
| GET  | `/health` | liveness |
| GET/PUT | `/admin/config` | read/replace `router.yaml` (`X-API-Key`) |

`model` in the request body is the capability name. A literal `model@backend`
or bare `model` also works (passthrough).

## Run standalone

```bash
cd /srv/show-build/llm-router
docker compose -f docker-compose.router.yml up -d --build
curl localhost:11500/health
```

Keys are read from `.env` in this dir (derived from show-build's `.env`).

## Run packaged with show-build

Add to `/srv/show-build/docker-compose.yml`:

```yaml
include:
  - llm-router/docker-compose.include.yml
```

In-cluster services then reach it at `http://llm-router:11500`.

## API reference

Full request/response docs — endpoints, the capability `model` field, streaming
formats, errors, and copy-paste curl/Python examples — are in **[API.md](API.md)**.

## Client integration (show-build)

- OpenAI path (`providers.js`): point `baseURL` at `http://llm-router:11500/v1`
  and set `model` to a capability name. No other change.
- ollama path (`ollama_resolver.py`): set the ollama host to
  `http://llm-router:11500` and use a capability as the model. The existing
  404-fallback still works as a second safety net.

## Editing routes live

`router.yaml` hot-reloads on save (mtime poll). Or via the admin API:

```bash
curl -H "X-API-Key: $LLM_STATE_API_KEY" localhost:11500/admin/config        # read
curl -X PUT -H "X-API-Key: $LLM_STATE_API_KEY" --data-binary @router.yaml \
     localhost:11500/admin/config                                            # replace
```

## Not in v1

- Streaming is supported, but no token-level retry/failover mid-stream (a
  backend that dies mid-stream ends the stream cleanly rather than re-routing).
- No weighted load-balancing across equal candidates (strict order / prefer_local).
- Cloud adapters present for OpenAI & Anthropic but disabled until their keys
  are set; x.ai (Grok) is live.
