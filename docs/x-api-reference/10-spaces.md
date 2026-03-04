# Spaces

## Space Lookup

### GET /2/spaces — Multiple Spaces by IDs

**URL**: `https://api.x.com/2/spaces`

**Auth**: Bearer Token, OAuth 2.0 User Token

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `ids` | string | Yes | Comma-separated Space IDs (1-100, pattern: `^[a-zA-Z0-9]{1,13}$`) |
| `space.fields` | string | No | `created_at`, `creator_id`, `ended_at`, `host_ids`, `id`, `invited_user_ids`, `is_ticketed`, `lang`, `participant_count`, `scheduled_start`, `speaker_ids`, `started_at`, `state`, `subscriber_count`, `title`, `topic_ids`, `updated_at` |
| `expansions` | string | No | `creator_id`, `host_ids`, `invited_user_ids`, `speaker_ids`, `topic_ids` |
| `user.fields` | string | No | Standard user fields |
| `topic.fields` | string | No | `description`, `id`, `name` |

### Example Request

```bash
curl "https://api.x.com/2/spaces?ids=1SLjjRYNejbKM\
&space.fields=created_at,host_ids,title,state,participant_count\
&expansions=host_ids\
&user.fields=username,profile_image_url" \
  -H "Authorization: Bearer $BEARER_TOKEN"
```

### Example Response

```json
{
  "data": [
    {
      "id": "1SLjjRYNejbKM",
      "state": "live",
      "title": "Spaces are Awesome",
      "created_at": "2021-07-06T18:40:40.000Z",
      "participant_count": 150,
      "host_ids": ["2244994945"]
    }
  ],
  "includes": {
    "users": [
      {"id": "2244994945", "username": "XDevelopers"}
    ]
  }
}
```

### GET /2/spaces/:id — Single Space by ID

**URL**: `https://api.x.com/2/spaces/:id`

Same query parameters as above (minus `ids`).

### GET /2/spaces/by/creator_ids — Spaces by Creator IDs

**URL**: `https://api.x.com/2/spaces/by/creator_ids`

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `user_ids` | string | Yes | Comma-separated user IDs (max 100) |

### GET /2/spaces/:id/buyers — Ticket Purchasers

**URL**: `https://api.x.com/2/spaces/:id/buyers`

**Auth**: OAuth 2.0 User Token

Returns users who purchased a ticket to a ticketed Space.

---

## Space Search

### GET /2/spaces/search — Search Spaces

**URL**: `https://api.x.com/2/spaces/search`

**Auth**: Bearer Token

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `query` | string | Yes | Keyword search term |
| `state` | string | No | `live`, `scheduled`, `all` (default: `all`) |
| `max_results` | integer | No | 1-100 (default: 100) |
| `space.fields` | string | No | Standard space fields |
| `expansions` | string | No | Standard expansions |
| `user.fields` | string | No | Standard user fields |

```bash
curl "https://api.x.com/2/spaces/search?query=AI&state=live\
&space.fields=title,host_ids,participant_count" \
  -H "Authorization: Bearer $BEARER_TOKEN"
```
