# Manage Tweets (Create, Delete, Edit)

## POST /2/tweets — Create Tweet

**URL**: `https://api.x.com/2/tweets`

**Auth**: OAuth 2.0 User Token (scopes: `tweet.read`, `tweet.write`, `users.read`)

### Request Body

```json
{
  "text": "Hello world!",
  "media": {
    "media_ids": ["1455952740635586573"],
    "tagged_user_ids": ["2244994945"]
  },
  "poll": {
    "options": ["Option A", "Option B", "Option C"],
    "duration_minutes": 1440
  },
  "reply": {
    "in_reply_to_tweet_id": "1346889436626259968",
    "exclude_reply_user_ids": ["6253282"]
  },
  "quote_tweet_id": "1346889436626259968",
  "reply_settings": "mentionedUsers",
  "geo": {
    "place_id": "5a110d312052166f"
  },
  "for_super_followers_only": false,
  "community_id": "1234567890",
  "share_with_followers": false
}
```

### Request Body Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `text` | string | Yes* | Tweet content |
| `media` | object | No | Media attachments (mutually exclusive with `poll`, `quote_tweet_id`, `card_uri`) |
| `media.media_ids` | array | Yes (if media) | 1-4 media IDs from upload |
| `media.tagged_user_ids` | array | No | 0-10 user IDs to tag |
| `poll` | object | No | Poll (mutually exclusive with `media`) |
| `poll.options` | array | Yes (if poll) | 2-4 choices, 1-25 chars each |
| `poll.duration_minutes` | integer | Yes (if poll) | 5-10,080 (7 days) |
| `poll.reply_settings` | string | No | `following`, `mentionedUsers`, `subscribers`, `verified` |
| `reply` | object | No | Reply metadata |
| `reply.in_reply_to_tweet_id` | string | Yes (if reply) | Tweet ID to reply to |
| `reply.exclude_reply_user_ids` | array | No | Users to exclude |
| `quote_tweet_id` | string | No | Tweet ID to quote |
| `reply_settings` | string | No | Who can reply |
| `geo.place_id` | string | No | Location place ID |
| `for_super_followers_only` | boolean | No | Exclusive content (default false) |
| `community_id` | string | No | Post to community |
| `share_with_followers` | boolean | No | Share community post publicly |
| `nullcast` | boolean | No | Promoted-only post |
| `card_uri` | string | No | Card attachment |
| `direct_message_deep_link` | string | No | DM link |
| `edit_options` | object | No | Edit an existing post (requires `previous_post_id`) |

### Example Request

```bash
curl -X POST "https://api.x.com/2/tweets" \
  -H "Authorization: Bearer $USER_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello from Show-Build!"}'
```

### Response (201 Created)

```json
{
  "data": {
    "id": "1445880548472328192",
    "text": "Hello from Show-Build!"
  }
}
```

### Rate Limits

| Metric | Limit |
|--------|-------|
| Per App | 10,000 / 24 hours |
| Per User | 100 / 15 minutes |

---

## DELETE /2/tweets/:id — Delete Tweet

**URL**: `https://api.x.com/2/tweets/:id`

**Auth**: OAuth 2.0 User Token (scopes: `tweet.read`, `tweet.write`, `users.read`)

**Restriction**: Can only delete tweets authored by the authenticated user.

### Path Parameters

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Tweet ID to delete |

### Example Request

```bash
curl -X DELETE "https://api.x.com/2/tweets/1445880548472328192" \
  -H "Authorization: Bearer $USER_ACCESS_TOKEN"
```

### Response (200 OK)

```json
{
  "data": {
    "deleted": true
  }
}
```
