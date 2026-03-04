# Tweets Timelines

## GET /2/users/:id/tweets — User Tweet Timeline

Retrieve tweets authored by a user.

**URL**: `https://api.x.com/2/users/:id/tweets`

**Auth**: Bearer Token, OAuth 2.0 User Token, or OAuth 1.0a

### Path Parameters

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | User ID (1-19 digits). Example: `2244994945` |

### Query Parameters

| Param | Type | Default | Range | Description |
|-------|------|---------|-------|-------------|
| `max_results` | integer | — | 5-100 | Results per page |
| `pagination_token` | string | — | — | Token for next page |
| `since_id` | string | — | — | Minimum tweet ID (exclusive) |
| `until_id` | string | — | — | Maximum tweet ID (exclusive) |
| `start_time` | string | — | — | ISO 8601 earliest timestamp |
| `end_time` | string | — | — | ISO 8601 latest timestamp |
| `exclude` | array | — | — | `replies`, `retweets` (comma-separated) |
| `tweet.fields` | string | — | — | Standard tweet fields |
| `expansions` | string | — | — | Standard expansions |
| `user.fields` | string | — | — | Standard user fields |
| `media.fields` | string | — | — | Standard media fields |
| `place.fields` | string | — | — | Standard place fields |
| `poll.fields` | string | — | — | Standard poll fields |

### Example Request

```bash
curl "https://api.x.com/2/users/2244994945/tweets\
?max_results=10\
&exclude=retweets,replies\
&tweet.fields=created_at,author_id,public_metrics\
&expansions=author_id,attachments.media_keys\
&user.fields=username,profile_image_url\
&media.fields=url,type" \
  -H "Authorization: Bearer $BEARER_TOKEN"
```

### Example Response

```json
{
  "data": [
    {
      "id": "1346889436626259968",
      "text": "Tweet content here...",
      "author_id": "2244994945",
      "created_at": "2021-01-06T18:40:40.000Z",
      "public_metrics": {
        "retweet_count": 11,
        "reply_count": 2,
        "like_count": 45,
        "impression_count": 1250,
        "bookmark_count": 5
      }
    }
  ],
  "includes": {
    "users": [...],
    "media": [...]
  },
  "meta": {
    "result_count": 10,
    "newest_id": "1346889436626259968",
    "oldest_id": "1346889436626259960",
    "next_token": "b26v89c19zqg8o3fpza01xsqx6k8u0awx2lah14s00000"
  }
}
```

---

## GET /2/users/:id/mentions — User Mentions Timeline

Retrieve tweets that mention a specific user.

**URL**: `https://api.x.com/2/users/:id/mentions`

**Auth**: Bearer Token, OAuth 2.0 User Token, or OAuth 1.0a

### Parameters

Same query parameters as User Tweet Timeline above.

### Example Request

```bash
curl "https://api.x.com/2/users/2244994945/mentions\
?max_results=10\
&tweet.fields=created_at,author_id,public_metrics" \
  -H "Authorization: Bearer $BEARER_TOKEN"
```

---

## GET /2/users/:id/timelines/reverse_chronological — Reverse Chronological Timeline

Returns tweets from the authenticated user's home timeline in reverse chronological order.

**URL**: `https://api.x.com/2/users/:id/timelines/reverse_chronological`

**Auth**: OAuth 2.0 User Token (scopes: `tweet.read`, `users.read`)

### Parameters

Same query parameters as User Tweet Timeline, plus the authenticated user must match `:id`.

### Rate Limits

| Endpoint | Per App (15 min) | Per User (15 min) |
|----------|-----------------|-------------------|
| User tweets | 1,500 | 900 |
| Mentions | 450 | 180 |
| Reverse chronological | 180 | 180 |
