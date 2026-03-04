# Filtered Stream

Real-time streaming of tweets matching filter rules.

---

## GET /2/tweets/search/stream — Connect to Stream

**URL**: `https://api.x.com/2/tweets/search/stream`

**Auth**: Bearer Token

**Access**: Pay-per-use and Enterprise

Opens a persistent HTTP connection that delivers matching tweets in real-time.

### Query Parameters

| Param | Type | Description |
|-------|------|-------------|
| `tweet.fields` | string | Standard tweet fields |
| `expansions` | string | Standard expansions |
| `user.fields` | string | Standard user fields |
| `media.fields` | string | Standard media fields |
| `place.fields` | string | Standard place fields |
| `poll.fields` | string | Standard poll fields |
| `backfill_minutes` | integer | 0-5, replay missed tweets (Enterprise) |

### Behavior

- Persistent HTTP connection with streaming JSON
- Keep-alive signals (blank lines) sent every ~20 seconds
- ~6-7 seconds P99 delivery latency
- Reconnect with exponential backoff on disconnect
- Each tweet includes `matching_rules` array showing which rules matched

### Example Request

```bash
curl "https://api.x.com/2/tweets/search/stream\
?tweet.fields=created_at,author_id,public_metrics\
&expansions=author_id,attachments.media_keys\
&user.fields=username,profile_image_url" \
  -H "Authorization: Bearer $BEARER_TOKEN" \
  --no-buffer
```

### Example Streamed Response (one line per tweet)

```json
{
  "data": {
    "id": "1346889436626259968",
    "text": "Matching tweet content...",
    "author_id": "2244994945",
    "created_at": "2021-01-06T18:40:40.000Z"
  },
  "includes": {
    "users": [{"id": "2244994945", "username": "XDevelopers"}]
  },
  "matching_rules": [
    {"id": "1", "tag": "AI news"}
  ]
}
```

---

## POST /2/tweets/search/stream/rules — Add/Delete Rules

**URL**: `https://api.x.com/2/tweets/search/stream/rules`

**Auth**: Bearer Token

### Add Rules

```bash
curl -X POST "https://api.x.com/2/tweets/search/stream/rules" \
  -H "Authorization: Bearer $BEARER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "add": [
      {"value": "AI lang:en -is:retweet", "tag": "AI news"},
      {"value": "#Bitcoin has:images", "tag": "Bitcoin with images"}
    ]
  }'
```

### Delete Rules

```bash
curl -X POST "https://api.x.com/2/tweets/search/stream/rules" \
  -H "Authorization: Bearer $BEARER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "delete": {
      "ids": ["1165037377523306497", "1165037377523306498"]
    }
  }'
```

### Response

```json
{
  "data": [
    {
      "id": "1165037377523306497",
      "value": "AI lang:en -is:retweet",
      "tag": "AI news"
    }
  ],
  "meta": {
    "sent": "2021-01-06T18:40:40.000Z",
    "summary": {
      "created": 2,
      "not_created": 0
    }
  }
}
```

---

## GET /2/tweets/search/stream/rules — List Active Rules

**URL**: `https://api.x.com/2/tweets/search/stream/rules`

**Auth**: Bearer Token

```bash
curl "https://api.x.com/2/tweets/search/stream/rules" \
  -H "Authorization: Bearer $BEARER_TOKEN"
```

### Rule Limits by Tier

| Tier | Max Rules | Max Query Length |
|------|-----------|-----------------|
| Pay-per-use | 1,000 | 1,024 chars |
| Enterprise | 25,000+ | 2,048 chars |

Rules use the same operators as Search (see [03-tweets-search.md](03-tweets-search.md)).
