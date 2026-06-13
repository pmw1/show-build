# llm-router — API Reference

How to form requests against the capability-pool LLM router.

The key idea: **you send a capability name in the `model` field, not a real
model.** The router picks an available backend for you (local GPU or cloud) and
returns the result in whichever dialect you called. You never name a physical
model or worry about which GPU is live.

---

## 1. Base URL

| From | URL |
|---|---|
| Host / LAN | `http://192.168.51.238:11500` |
| Inside show-build's docker network | `http://llm-router:11500` |
| Same host, localhost | `http://localhost:11500` |

No authentication is required for inference endpoints. (Only `/admin/config`
needs an `X-API-Key`.)

---

## 2. What to put in the `model` field

Three accepted forms, checked in this order:

1. **A capability name** (the normal case) — e.g. `description-writer`. The
   router walks that capability's candidate pool and uses the first one
   available right now.
2. **`model@backend`** — pin a literal model on a specific backend, e.g.
   `qwen3:8b@prefect`. Skips capability logic; still health/fit-checked.
3. **A bare model name** — e.g. `qwen3:8b`. Tried on each ollama backend in
   config order. Use a capability instead unless you have a reason not to.

### Current capabilities

| Capability | Use it for | Routes to (in order, first available wins) |
|---|---|---|
| `description-writer` | short cheap text: descriptions, slugs, titles | qwen3:8b@prefect → qwen3:32b@prefect → qwen3:32b@kairobox → grok-4.3@xai |
| `generation` | general quality generation | qwen3:32b@prefect → qwen3:32b@kairobox → qwen3:8b@prefect → grok-4.3@xai |
| `meta-extractor` | structured extraction from transcripts/segments (JSON) | qwen3:8b@prefect → qwen3:32b@kairobox → grok-4.3@xai |
| `long-context-reasoner` | long-context reasoning | qwen3:32b@kairobox → grok-4.20-reasoning@xai → qwen3:32b@prefect |

"First available" means: backend enabled (+ cloud key present), host healthy,
and the model fully fits the backend's **live** VRAM (a model ollama would have
to split onto CPU is skipped). So during VM-up windows the 32B prefect
candidates are auto-skipped and routing falls through to the 8B or cloud.

To see live routing right now: `curl http://192.168.51.238:11500/capabilities`.

---

## 3. Endpoints

| Method | Path | Dialect | Streaming |
|---|---|---|---|
| POST | `/v1/chat/completions` | OpenAI chat | SSE (`data:` lines) |
| POST | `/api/chat` | ollama chat | ndjson (one JSON/line) |
| POST | `/api/generate` | ollama generate (single prompt) | ndjson |
| GET | `/capabilities` | — | live availability per candidate |
| GET | `/health` | — | liveness + lists |
| GET/PUT | `/admin/config` | text/yaml | read/replace router.yaml (`X-API-Key`) |

Pick the dialect your client already speaks — the router translates to the
backend and back. An OpenAI client and an ollama client get the same routing.

---

## 4. Request shapes

### 4a. OpenAI dialect — `POST /v1/chat/completions`

```json
{
  "model": "description-writer",
  "messages": [
    {"role": "system", "content": "You write terse one-line video descriptions."},
    {"role": "user", "content": "Segment: mayor resigns amid budget scandal."}
  ],
  "temperature": 0.2,
  "max_tokens": 200,
  "stream": false
}
```

Fields:
- `model` (required) — a capability name (see §2).
- `messages` (required) — standard `[{role, content}]`; roles `system|user|assistant`.
- `temperature` (optional, default 0.2)
- `max_tokens` (optional) — **see the thinking-model caveat in §6.**
- `top_p` (optional)
- `response_format: {"type":"json_object"}` (optional) — ask for JSON output.
- `stream` (optional, default false)

Non-streaming response:

```json
{
  "id": "chatcmpl-router-...",
  "object": "chat.completion",
  "model": "description-writer",
  "choices": [{
    "index": 0,
    "message": {"role": "assistant", "content": "Mayor quits as budget scandal widens."},
    "finish_reason": "stop"
  }],
  "usage": {"prompt_tokens": 41, "completion_tokens": 9, "total_tokens": 50},
  "x_router": {"backend_model": "qwen3:8b"}
}
```

`x_router.backend_model` tells you which physical model actually served it.

### 4b. ollama dialect — `POST /api/chat`

```json
{
  "model": "meta-extractor",
  "messages": [{"role": "user", "content": "Extract people and orgs as JSON."}],
  "format": "json",
  "stream": false,
  "options": {"temperature": 0.2, "num_predict": 1000}
}
```

`options.num_predict` is the ollama equivalent of `max_tokens`;
`format: "json"` is the JSON-mode switch. Response carries
`message.content` plus `done`, `prompt_eval_count`, `eval_count`.

### 4c. ollama dialect — `POST /api/generate`

For a single prompt instead of a message list:

```json
{
  "model": "generation",
  "prompt": "Write a two-sentence teaser for tonight's show.",
  "system": "You are a broadcast promo writer.",
  "stream": false,
  "options": {"num_predict": 400}
}
```

Response has `response` (the text), `done`, and token counts.

---

## 5. Streaming

Set `"stream": true`.

**OpenAI dialect** emits Server-Sent Events — lines beginning `data: ` whose
payload is a `chat.completion.chunk`, terminated by `data: [DONE]`:

```
data: {"choices":[{"delta":{"content":"Mayor "},"finish_reason":null}], ...}
data: {"choices":[{"delta":{"content":"quits"},"finish_reason":null}], ...}
data: {"choices":[{"delta":{},"finish_reason":"stop"}], ...}
data: [DONE]
```

**ollama dialect** emits newline-delimited JSON, one object per line, last one
has `"done": true`:

```
{"message":{"role":"assistant","content":"Mayor "},"done":false}
{"message":{"role":"assistant","content":"quits"},"done":false}
{"message":{"role":"assistant","content":""},"done":true,"done_reason":"stop"}
```

(`/api/generate` streams `response` deltas instead of `message`.)

Note: if the chosen backend dies mid-stream the stream ends cleanly; v1 does not
re-route a half-finished stream to another candidate.

---

## 6. Caveats worth knowing

- **Thinking models (qwen3).** They reason internally before answering. If you
  set `max_tokens`/`num_predict` too low, the budget is spent thinking and the
  answer comes back empty. Give it room (≥512, often ≥1000 for non-trivial
  tasks). If content would otherwise be empty, the router returns the thinking
  text with `finish_reason: "length_thinking_truncated"` so you're never handed
  a silent blank.
- **JSON mode is best-effort.** `response_format`/`format:"json"` strongly
  steers the model but does not hard-guarantee valid JSON. Validate downstream.
- **Cloud models change.** `xai` is live; valid ids today are `grok-4.3` and
  `grok-4.20-*`. `openai` and `anthropic` adapters exist but are disabled until
  their keys are set in show-build's `.env`.

---

## 7. Errors

| HTTP | Meaning | What to do |
|---|---|---|
| 503 | No candidate available for the capability | All backends down / nothing fits. Body lists each candidate's reason. Retry later or widen the pool. |
| 502 | Selected backend failed the call | Backend-side error (bad model id, upstream 4xx/5xx). Check `detail`. |
| 400 | Bad request body / invalid admin config | Fix the payload. |
| 401 | Bad/missing `X-API-Key` on `/admin/config` | Supply the key. |

A 503 body shows exactly why each candidate was skipped, e.g.:

```json
{"detail": "no available candidate for 'generation'; tried: qwen3:32b-q4_K_M@prefect: qwen3:32b-q4_K_M partially on CPU (20.0GB > prefect 12.0GB live); qwen3:32b-q4_K_M@kairobox: kairobox unhealthy; ..."}
```

---

## 8. Copy-paste examples

Capability, batch, OpenAI dialect:

```bash
curl -s http://192.168.51.238:11500/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "description-writer",
    "messages": [{"role":"user","content":"One-line teaser: city council meeting on zoning."}],
    "max_tokens": 300
  }'
```

Capability, streaming, OpenAI dialect:

```bash
curl -sN http://192.168.51.238:11500/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"model":"generation","messages":[{"role":"user","content":"Write a 3-line promo."}],"max_tokens":800,"stream":true}'
```

JSON extraction, ollama dialect:

```bash
curl -s http://192.168.51.238:11500/api/chat \
  -H 'Content-Type: application/json' \
  -d '{"model":"meta-extractor","messages":[{"role":"user","content":"Return {\"people\":[],\"orgs\":[]} for: Jane Smith met with Acme Corp."}],"format":"json","options":{"num_predict":1000}}'
```

Pin a specific model/backend (bypass capability logic):

```bash
curl -s http://192.168.51.238:11500/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"model":"qwen3:8b@prefect","messages":[{"role":"user","content":"hi"}],"max_tokens":300}'
```

Python (OpenAI SDK) — just point it at the router and use a capability:

```python
from openai import OpenAI
client = OpenAI(base_url="http://192.168.51.238:11500/v1", api_key="not-needed")
r = client.chat.completions.create(
    model="description-writer",
    messages=[{"role": "user", "content": "One-line teaser for a weather segment."}],
    max_tokens=300,
)
print(r.choices[0].message.content)
```

Inspect live routing / health:

```bash
curl -s http://192.168.51.238:11500/health        | python3 -m json.tool
curl -s http://192.168.51.238:11500/capabilities  | python3 -m json.tool
```
