# Tweets Lookup

## GET /2/tweets/:id — Single Tweet Lookup

Retrieve a single tweet by its ID.

**URL**: `https://api.x.com/2/tweets/:id`

**Auth**: Bearer Token, OAuth 2.0 User Token, or OAuth 1.0a

### Path Parameters

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Tweet ID (1-19 digits) |

### Query Parameters

| Param | Type | Description |
|-------|------|-------------|
| `tweet.fields` | string | Comma-separated: `attachments`, `author_id`, `created_at`, `entities`, `geo`, `id`, `in_reply_to_user_id`, `lang`, `public_metrics`, `referenced_tweets`, `reply_settings`, `text`, `withheld`, `edit_controls`, `note_tweet`, `organic_metrics`, `promoted_metrics`, `context_annotations`, `conversation_id` |
| `expansions` | string | Comma-separated: `author_id`, `referenced_tweets.id`, `referenced_tweets.id.author_id`, `attachments.media_keys`, `attachments.poll_ids`, `geo.place_id`, `entities.mentions.username`, `in_reply_to_user_id` |
| `user.fields` | string | Comma-separated: `id`, `name`, `username`, `created_at`, `description`, `entities`, `location`, `profile_image_url`, `profile_banner_url`, `protected`, `public_metrics`, `verified`, `verified_type`, `url`, `subscription_type` |
| `media.fields` | string | Comma-separated: `media_key`, `type`, `url`, `preview_image_url`, `alt_text`, `duration_ms`, `height`, `width`, `public_metrics`, `variants` |
| `place.fields` | string | Comma-separated: `full_name`, `id`, `country`, `country_code`, `geo`, `name`, `place_type` |
| `poll.fields` | string | Comma-separated: `id`, `options`, `duration_minutes`, `end_datetime`, `voting_status` |

### Example Request

```bash
curl "https://api.x.com/2/tweets/1346889436626259968\
?tweet.fields=created_at,author_id,public_metrics,entities,attachments\
&expansions=author_id,attachments.media_keys\
&user.fields=username,name,profile_image_url,verified\
&media.fields=url,preview_image_url,type,width,height,alt_text" \
  -H "Authorization: Bearer $BEARER_TOKEN"
```

### Example Response

```json
{
  "data": {
    "id": "1346889436626259968",
    "text": "Learn how to use the user Tweet timeline...",
    "author_id": "2244994945",
    "created_at": "2021-01-06T18:40:40.000Z",
    "public_metrics": {
      "retweet_count": 11,
      "reply_count": 2,
      "like_count": 45,
      "quote_count": 3,
      "impression_count": 1250,
      "bookmark_count": 5
    },
    "entities": {
      "urls": [...],
      "hashtags": [...],
      "mentions": [...]
    }
  },
  "includes": {
    "users": [
      {
        "id": "2244994945",
        "name": "X Dev",
        "username": "XDevelopers",
        "profile_image_url": "https://pbs.twimg.com/...",
        "verified": true
      }
    ],
    "media": [
      {
        "media_key": "3_1346889436626259968",
        "type": "photo",
        "url": "https://pbs.twimg.com/media/...",
        "width": 1200,
        "height": 675
      }
    ]
  }
}
```

---

## GET /2/tweets — Multiple Tweets Lookup

Retrieve up to 100 tweets by their IDs.

**URL**: `https://api.x.com/2/tweets`

**Auth**: Bearer Token, OAuth 2.0 User Token, or OAuth 1.0a

### Query Parameters

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `ids` | string | Yes | Comma-separated tweet IDs (max 100) |
| `tweet.fields` | string | No | Same fields as single lookup |
| `expansions` | string | No | Same expansions as single lookup |
| `user.fields` | string | No | Same user fields |
| `media.fields` | string | No | Same media fields |
| `place.fields` | string | No | Same place fields |
| `poll.fields` | string | No | Same poll fields |

### Example Request

```bash
curl "https://api.x.com/2/tweets?ids=1346889436626259968,1346889436626259969\
&tweet.fields=created_at,author_id,public_metrics\
&expansions=author_id" \
  -H "Authorization: Bearer $BEARER_TOKEN"
```

### Example Response

```json
{
  "data": [
    {
      "id": "1346889436626259968",
      "text": "First tweet content...",
      "author_id": "2244994945",
      "created_at": "2021-01-06T18:40:40.000Z"
    },
    {
      "id": "1346889436626259969",
      "text": "Second tweet content...",
      "author_id": "2244994945",
      "created_at": "2021-01-06T18:45:00.000Z"
    }
  ],
  "includes": {
    "users": [...]
  }
}
```

### Rate Limits

| Endpoint | Per App (15 min) | Per User (15 min) |
|----------|-----------------|-------------------|
| `GET /2/tweets` | 3,500 | 5,000 |
| `GET /2/tweets/:id` | 3,500 | 5,000 |
