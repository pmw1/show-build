# Data Dictionary

Complete field reference for all X API v2 objects.

---

## Post (Tweet) Object

**Default fields** (always returned): `id`, `text`, `edit_history_tweet_ids`

| Field | Type | Description | Use Case |
|-------|------|-------------|----------|
| `id` | string | Unique tweet identifier | Programmatic retrieval |
| `text` | string | UTF-8 tweet content | Content display, keyword extraction |
| `author_id` | string | User ID of author | Hydrate user object via expansion |
| `created_at` | ISO 8601 | Creation timestamp | Time-series analysis |
| `conversation_id` | string | Root tweet ID of thread | Thread tracking |
| `in_reply_to_user_id` | string | User being replied to | Conversation mapping |
| `lang` | string | BCP 47 language code | Language filtering |
| `source` | string | App/client used to post | Platform analysis |
| `reply_settings` | string | Who can reply | Content moderation |
| `referenced_tweets` | array | Replied-to, quoted, retweeted | Engagement mapping |
| `attachments` | object | `media_keys[]`, `poll_ids[]` | Media/poll expansion |
| `entities` | object | Parsed hashtags, URLs, mentions, cashtags | Entity extraction |
| `context_annotations` | array | Domain and entity annotations | Topic classification |
| `public_metrics` | object | See metrics below | Engagement analysis |
| `organic_metrics` | object | Non-promoted metrics (requires auth) | Analytics |
| `promoted_metrics` | object | Promoted tweet metrics (requires auth) | Ad analytics |
| `non_public_metrics` | object | Impressions, clicks (requires auth) | Deep analytics |
| `geo` | object | `place_id`, coordinates | Location mapping |
| `withheld` | object | Withholding info by country | Compliance |
| `edit_controls` | object | Edit window, remaining edits | Edit tracking |
| `note_tweet` | object | Full text for posts >280 chars | Long-form content |
| `media_metadata` | array | Alt text, stickers | Accessibility |

### Public Metrics Object

```json
{
  "retweet_count": 11,
  "reply_count": 2,
  "like_count": 45,
  "quote_count": 3,
  "impression_count": 1250,
  "bookmark_count": 5
}
```

### Entities Object

```json
{
  "hashtags": [
    {"start": 0, "end": 3, "tag": "AI"}
  ],
  "urls": [
    {"start": 10, "end": 33, "url": "https://t.co/...", "expanded_url": "https://example.com", "display_url": "example.com", "title": "Page Title", "description": "..."}
  ],
  "mentions": [
    {"start": 5, "end": 15, "username": "XDevelopers", "id": "2244994945"}
  ],
  "cashtags": [
    {"start": 0, "end": 5, "tag": "TSLA"}
  ]
}
```

---

## User Object

**Default fields**: `id`, `name`, `username`

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique user identifier |
| `name` | string | Display name |
| `username` | string | @handle (without @) |
| `created_at` | ISO 8601 | Account creation date |
| `description` | string | Bio text |
| `entities` | object | Parsed URLs/mentions in bio |
| `location` | string | User-defined location |
| `profile_image_url` | string | Profile photo URL (append `_normal`, `_bigger`, `_400x400`, or remove suffix for original) |
| `profile_banner_url` | string | Banner image URL |
| `protected` | boolean | Private account |
| `public_metrics` | object | `followers_count`, `following_count`, `tweet_count`, `listed_count` |
| `verified` | boolean | Verified account |
| `verified_type` | string | `blue`, `business`, `government` |
| `url` | string | User's website |
| `pinned_tweet_id` | string | Pinned tweet ID (expandable) |
| `subscription_type` | string | Premium subscription level |
| `connection_status` | array | Relationship: `following`, `followed_by`, `muting`, `blocking` |

### Profile Image URL Sizes

| Suffix | Size |
|--------|------|
| `_normal` | 48x48 |
| `_bigger` | 73x73 |
| `_400x400` | 400x400 |
| (no suffix) | Original |

---

## Media Object

**Default fields**: `media_key`, `type`

| Field | Type | Description |
|-------|------|-------------|
| `media_key` | string | Unique identifier |
| `type` | string | `photo`, `video`, `animated_gif` |
| `url` | string | Direct media file URL (images only) |
| `preview_image_url` | string | Static preview/thumbnail |
| `alt_text` | string | Accessibility description (max 1000 chars) |
| `duration_ms` | integer | Video duration in milliseconds |
| `height` | integer | Pixel height |
| `width` | integer | Pixel width |
| `public_metrics` | object | `view_count` |
| `variants` | array | Different resolutions/formats |

### Media Variants

```json
{
  "variants": [
    {
      "bit_rate": 2176000,
      "content_type": "video/mp4",
      "url": "https://video.twimg.com/ext_tw_video/..."
    },
    {
      "bit_rate": 832000,
      "content_type": "video/mp4",
      "url": "https://video.twimg.com/ext_tw_video/..."
    },
    {
      "content_type": "application/x-mpegURL",
      "url": "https://video.twimg.com/ext_tw_video/..."
    }
  ]
}
```

---

## Space Object

**Default fields**: `id`, `state`

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Space identifier |
| `state` | string | `live`, `scheduled`, `ended` |
| `title` | string | Space title |
| `created_at` | ISO 8601 | Creation time |
| `started_at` | ISO 8601 | Start time |
| `ended_at` | ISO 8601 | End time |
| `scheduled_start` | ISO 8601 | Planned start |
| `host_ids` | array | Host user IDs |
| `speaker_ids` | array | Speaker user IDs |
| `invited_user_ids` | array | Invited user IDs |
| `creator_id` | string | Creator user ID |
| `participant_count` | integer | Active participants |
| `subscriber_count` | integer | Subscribers |
| `is_ticketed` | boolean | Paid access |
| `lang` | string | Detected language |
| `topic_ids` | array | Topic identifiers |

---

## List Object

**Default fields**: `id`, `name`

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | List identifier |
| `name` | string | List name |
| `created_at` | ISO 8601 | Creation time |
| `description` | string | List description |
| `member_count` | integer | Number of members |
| `follower_count` | integer | Number of followers |
| `owner_id` | string | Creator user ID |
| `private` | boolean | Private list |

---

## Poll Object

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Poll identifier |
| `options` | array | `{position, label, votes}` |
| `duration_minutes` | integer | Poll duration |
| `end_datetime` | ISO 8601 | Poll closing time |
| `voting_status` | string | `open` or `closed` |

---

## Place Object

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Place identifier |
| `full_name` | string | Full location name |
| `name` | string | Short name |
| `country` | string | Country name |
| `country_code` | string | ISO alpha-2 |
| `place_type` | string | `city`, `admin`, `country`, `neighborhood`, `poi` |
| `geo` | object | GeoJSON bounding box |

---

## Expansions Reference

Use `expansions` parameter to include related objects in `includes` section:

| Expansion | Includes | Available On |
|-----------|----------|-------------|
| `author_id` | `users[]` | Tweets |
| `referenced_tweets.id` | `tweets[]` | Tweets |
| `referenced_tweets.id.author_id` | `users[]` | Tweets |
| `attachments.media_keys` | `media[]` | Tweets |
| `attachments.poll_ids` | `polls[]` | Tweets |
| `geo.place_id` | `places[]` | Tweets |
| `in_reply_to_user_id` | `users[]` | Tweets |
| `entities.mentions.username` | `users[]` | Tweets |
| `pinned_tweet_id` | `tweets[]` | Users |
| `most_recent_tweet_id` | `tweets[]` | Users |
| `creator_id` | `users[]` | Spaces |
| `host_ids` | `users[]` | Spaces |
| `speaker_ids` | `users[]` | Spaces |
| `owner_id` | `users[]` | Lists |
