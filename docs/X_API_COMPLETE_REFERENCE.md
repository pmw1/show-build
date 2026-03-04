# X (Twitter) API v2 — Complete Reference

**Last Updated**: 2026-02-25
**Official Docs**: https://docs.x.com/x-api/introduction
**Base URL**: `https://api.x.com`
**API Version**: v2

This is a comprehensive single-document reference for the X API v2. For individual topic files, see `docs/x-api-reference/`.

---

## Table of Contents

1. [Authentication](#1-authentication)
2. [Tweets — Lookup](#2-tweets--lookup)
3. [Tweets — Search](#3-tweets--search)
4. [Tweets — Create & Delete](#4-tweets--create--delete)
5. [Tweets — Timelines](#5-tweets--timelines)
6. [Tweets — Engagement](#6-tweets--engagement)
7. [Tweets — Filtered Stream](#7-tweets--filtered-stream)
8. [Tweets — Hide Replies](#8-tweets--hide-replies)
9. [Users](#9-users)
10. [Spaces](#10-spaces)
11. [Direct Messages](#11-direct-messages)
12. [Lists](#12-lists)
13. [Media Upload](#13-media-upload)
14. [Trends](#14-trends)
15. [Compliance](#15-compliance)
16. [Data Dictionary](#16-data-dictionary)
17. [Rate Limits](#17-rate-limits)
18. [Access Tiers](#18-access-tiers)

---

## 1. Authentication

X API v2 supports three authentication methods:

### OAuth 2.0 App-Only (Bearer Token)

For accessing **public data** only. No user context required. Use for tweet lookup, user lookup, search, trends.

```bash
# Get Bearer Token
curl -u "$API_KEY:$API_SECRET" \
  -d "grant_type=client_credentials" \
  "https://api.x.com/oauth2/token"

# Use Bearer Token
curl "https://api.x.com/2/tweets/123456" \
  -H "Authorization: Bearer $BEARER_TOKEN"
```

### OAuth 2.0 Authorization Code with PKCE (User Token)

For actions **on behalf of a user**. Required for: posting tweets, liking, following, DMs, bookmarks. Uses scopes to limit access.

**Required Scopes by Feature:**

| Feature | Required Scopes |
|---------|----------------|
| Read tweets | `tweet.read`, `users.read` |
| Post tweets | `tweet.read`, `tweet.write`, `users.read` |
| Like/Unlike | `like.read`, `like.write`, `tweet.read`, `users.read` |
| Follow/Unfollow | `follows.read`, `follows.write`, `tweet.read`, `users.read` |
| Bookmarks | `bookmark.read`, `bookmark.write`, `tweet.read`, `users.read` |
| DMs | `dm.read`, `dm.write`, `tweet.read`, `users.read` |
| Lists | `list.read`, `list.write`, `tweet.read`, `users.read` |
| Mute | `mute.read`, `mute.write`, `tweet.read`, `users.read` |
| Block | `block.read`, `block.write`, `tweet.read`, `users.read` |
| Spaces | `space.read`, `tweet.read`, `users.read` |
| Media upload | `media.write` |

### OAuth 1.0a (Legacy User Token)

Also provides user context. Used for media upload endpoints and legacy compatibility.

### API Keys

Manage keys at: https://developer.x.com/en/portal/dashboard

- **API Key** (Consumer Key) — identifies your app
- **API Secret** (Consumer Secret) — app authentication
- **Bearer Token** — app-only access token
- **Access Token + Secret** — user-specific OAuth 1.0a credentials

---

## 2. Tweets — Lookup

### GET /2/tweets/:id — Single Tweet Lookup

**URL**: `https://api.x.com/2/tweets/:id`
**Auth**: Bearer Token, OAuth 2.0 User Token, or OAuth 1.0a

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string (path) | Yes | Tweet ID (1-19 digits) |
| `tweet.fields` | string | No | `attachments`, `author_id`, `created_at`, `entities`, `geo`, `id`, `in_reply_to_user_id`, `lang`, `public_metrics`, `referenced_tweets`, `reply_settings`, `text`, `withheld`, `edit_controls`, `note_tweet`, `organic_metrics`, `promoted_metrics`, `context_annotations`, `conversation_id` |
| `expansions` | string | No | `author_id`, `referenced_tweets.id`, `referenced_tweets.id.author_id`, `attachments.media_keys`, `attachments.poll_ids`, `geo.place_id`, `entities.mentions.username`, `in_reply_to_user_id` |
| `user.fields` | string | No | `id`, `name`, `username`, `created_at`, `description`, `entities`, `location`, `profile_image_url`, `profile_banner_url`, `protected`, `public_metrics`, `verified`, `verified_type`, `url`, `subscription_type` |
| `media.fields` | string | No | `media_key`, `type`, `url`, `preview_image_url`, `alt_text`, `duration_ms`, `height`, `width`, `public_metrics`, `variants` |
| `place.fields` | string | No | `full_name`, `id`, `country`, `country_code`, `geo`, `name`, `place_type` |
| `poll.fields` | string | No | `id`, `options`, `duration_minutes`, `end_datetime`, `voting_status` |

```bash
curl "https://api.x.com/2/tweets/1346889436626259968\
?tweet.fields=created_at,author_id,public_metrics,entities,attachments\
&expansions=author_id,attachments.media_keys\
&user.fields=username,name,profile_image_url,verified\
&media.fields=url,preview_image_url,type,width,height,alt_text" \
  -H "Authorization: Bearer $BEARER_TOKEN"
```

**Response:**
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

### GET /2/tweets — Multiple Tweets Lookup

**URL**: `https://api.x.com/2/tweets`
**Auth**: Bearer Token, OAuth 2.0 User Token, or OAuth 1.0a

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `ids` | string | Yes | Comma-separated tweet IDs (max 100) |

Same field/expansion parameters as single tweet lookup.

```bash
curl "https://api.x.com/2/tweets?ids=1346889436626259968,1346889436626259969\
&tweet.fields=created_at,author_id,public_metrics\
&expansions=author_id" \
  -H "Authorization: Bearer $BEARER_TOKEN"
```

**Rate Limits:** App: 3,500/15min | User: 5,000/15min

---

## 3. Tweets — Search

### GET /2/tweets/search/recent — Recent Search (Last 7 Days)

**URL**: `https://api.x.com/2/tweets/search/recent`
**Auth**: Bearer Token, OAuth 2.0 User Token
**Access**: All tiers (Free, Basic, Pro, Enterprise)

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `query` | string | Yes | Search query (max 512 chars; 4,096 for Enterprise) |
| `max_results` | integer | No | 10-100 per request (default 10) |
| `next_token` | string | No | Pagination token from previous response |
| `since_id` | string | No | Minimum tweet ID (exclusive) |
| `until_id` | string | No | Maximum tweet ID (exclusive) |
| `start_time` | string | No | ISO 8601 earliest timestamp |
| `end_time` | string | No | ISO 8601 latest timestamp |
| `sort_order` | string | No | `recency` or `relevancy` |

Plus standard tweet/expansion/user/media/place/poll field parameters.

```bash
curl "https://api.x.com/2/tweets/search/recent\
?query=(AI OR %22artificial intelligence%22) lang:en -is:retweet has:images\
&max_results=10\
&tweet.fields=created_at,author_id,public_metrics,entities\
&expansions=author_id,attachments.media_keys\
&user.fields=username,profile_image_url\
&media.fields=url,type,preview_image_url" \
  -H "Authorization: Bearer $BEARER_TOKEN"
```

**Rate Limits:** App: 450/15min | User: 180/15min

### GET /2/tweets/search/all — Full-Archive Search (Back to 2006)

**URL**: `https://api.x.com/2/tweets/search/all`
**Auth**: Bearer Token, OAuth 2.0 User Token
**Access**: Pro ($5k/mo) and Enterprise only

Same parameters as recent search. Query max 1,024 chars (4,096 Enterprise). Max results 10-500.

**Rate Limits:** App: 300/15min | User: 1/15min

### Search Query Operators

**Keyword Operators:**

| Operator | Example | Description |
|----------|---------|-------------|
| keyword | `AI` | Matches keyword in tweet text |
| "exact phrase" | `"artificial intelligence"` | Exact phrase match |
| `#hashtag` | `#AI` | Matches hashtag |
| `@mention` | `@elonmusk` | Matches mention |
| `-keyword` | `-spam` | Exclude keyword |
| `OR` | `AI OR ML` | Match either term |

**User Operators:**

| Operator | Example | Description |
|----------|---------|-------------|
| `from:` | `from:elonmusk` | Posts by user |
| `to:` | `to:elonmusk` | Replies to user |
| `retweets_of:` | `retweets_of:elonmusk` | Retweets of user's posts |

**Content Operators:**

| Operator | Example | Description |
|----------|---------|-------------|
| `has:images` | `AI has:images` | Posts with images |
| `has:videos` | `AI has:videos` | Posts with videos |
| `has:media` | `AI has:media` | Posts with any media |
| `has:links` | `AI has:links` | Posts with URLs |
| `has:mentions` | `AI has:mentions` | Posts with @mentions |
| `has:hashtags` | `AI has:hashtags` | Posts with hashtags |
| `url:` | `url:github.com` | Posts linking to domain |
| `has:geo` | `news has:geo` | Posts with geo data |

**Filter Operators:**

| Operator | Example | Description |
|----------|---------|-------------|
| `is:retweet` | `-is:retweet` | Include/exclude retweets |
| `is:reply` | `-is:reply` | Include/exclude replies |
| `is:quote` | `is:quote` | Only quote tweets |
| `is:verified` | `is:verified` | Only verified users |
| `lang:` | `lang:en` | Language filter (BCP 47) |
| `conversation_id:` | `conversation_id:123` | All replies in thread |
| `context:` | `context:10.799022225751871488` | Entity/topic context |
| `entity:` | `entity:"Bitcoin"` | Named entity |
| `place:` | `place:"New York"` | Geo place name |
| `place_country:` | `place_country:US` | Country code |

**Example Queries:**
```
# Tech news with images, no retweets
(AI OR "machine learning" OR "deep learning") has:images -is:retweet lang:en

# Specific user's original posts
from:elonmusk -is:retweet -is:reply

# Posts about a topic with engagement
#Bitcoin has:links is:verified

# Conversation thread
conversation_id:1346889436626259968
```

---

## 4. Tweets — Create & Delete

### POST /2/tweets — Create Tweet

**URL**: `https://api.x.com/2/tweets`
**Auth**: OAuth 2.0 User Token (scopes: `tweet.read`, `tweet.write`, `users.read`)

**Full Request Body:**
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
  "community_id": "1234567890"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `text` | string | Yes* | Tweet content |
| `media.media_ids` | array | No | 1-4 media IDs from upload |
| `media.tagged_user_ids` | array | No | 0-10 user IDs to tag |
| `poll.options` | array | No | 2-4 choices, 1-25 chars each |
| `poll.duration_minutes` | integer | No | 5-10,080 (7 days) |
| `reply.in_reply_to_tweet_id` | string | No | Tweet ID to reply to |
| `reply.exclude_reply_user_ids` | array | No | Users to exclude from reply |
| `quote_tweet_id` | string | No | Tweet ID to quote |
| `reply_settings` | string | No | `following`, `mentionedUsers`, `subscribers`, `verified` |
| `geo.place_id` | string | No | Location place ID |
| `for_super_followers_only` | boolean | No | Exclusive content (default false) |
| `community_id` | string | No | Post to community |
| `nullcast` | boolean | No | Promoted-only post |
| `card_uri` | string | No | Card attachment |

```bash
curl -X POST "https://api.x.com/2/tweets" \
  -H "Authorization: Bearer $USER_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello from Show-Build!"}'
```

**Response (201):** `{"data": {"id": "1445880548472328192", "text": "Hello from Show-Build!"}}`

**Rate Limits:** App: 10,000/24hrs | User: 100/15min

### DELETE /2/tweets/:id — Delete Tweet

**URL**: `https://api.x.com/2/tweets/:id`
**Auth**: OAuth 2.0 User Token (scopes: `tweet.read`, `tweet.write`, `users.read`)
**Restriction**: Can only delete tweets authored by the authenticated user.

```bash
curl -X DELETE "https://api.x.com/2/tweets/1445880548472328192" \
  -H "Authorization: Bearer $USER_ACCESS_TOKEN"
```

**Response:** `{"data": {"deleted": true}}`

---

## 5. Tweets — Timelines

### GET /2/users/:id/tweets — User Tweet Timeline

**URL**: `https://api.x.com/2/users/:id/tweets`
**Auth**: Bearer Token, OAuth 2.0 User Token, or OAuth 1.0a

| Param | Type | Range | Description |
|-------|------|-------|-------------|
| `max_results` | integer | 5-100 | Results per page |
| `pagination_token` | string | — | Token for next page |
| `since_id` | string | — | Minimum tweet ID (exclusive) |
| `until_id` | string | — | Maximum tweet ID (exclusive) |
| `start_time` | string | — | ISO 8601 earliest timestamp |
| `end_time` | string | — | ISO 8601 latest timestamp |
| `exclude` | array | — | `replies`, `retweets` (comma-separated) |

Plus standard tweet/expansion/user/media/place/poll field parameters.

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

**Rate Limits:** App: 1,500/15min | User: 900/15min

### GET /2/users/:id/mentions — User Mentions Timeline

**URL**: `https://api.x.com/2/users/:id/mentions`
**Auth**: Bearer Token, OAuth 2.0 User Token, or OAuth 1.0a

Same parameters as User Tweet Timeline.

**Rate Limits:** App: 450/15min | User: 180/15min

### GET /2/users/:id/timelines/reverse_chronological — Home Timeline

**URL**: `https://api.x.com/2/users/:id/timelines/reverse_chronological`
**Auth**: OAuth 2.0 User Token (scopes: `tweet.read`, `users.read`)

Returns tweets from the authenticated user's home timeline. The authenticated user must match `:id`.

**Rate Limits:** User: 180/15min

---

## 6. Tweets — Engagement

### Likes

**POST /2/users/:id/likes** — Like a Tweet
Auth: OAuth 2.0 User Token (scopes: `like.write`, `tweet.read`, `users.read`)
```bash
curl -X POST "https://api.x.com/2/users/123456789/likes" \
  -H "Authorization: Bearer $USER_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"tweet_id": "1228393702244134912"}'
```
Response: `{"data": {"liked": true}}`

**DELETE /2/users/:id/likes/:tweet_id** — Unlike
Response: `{"data": {"liked": false}}`

**GET /2/tweets/:id/liking_users** — Users Who Liked
Auth: Bearer Token or OAuth 2.0 User Token. Params: `max_results` (1-100), `pagination_token`, `user.fields`

**GET /2/users/:id/liked_tweets** — Tweets Liked by User
Auth: Bearer Token or OAuth 2.0 User Token. Standard tweet field parameters.

### Retweets / Reposts

**POST /2/users/:id/retweets** — Retweet
Auth: OAuth 2.0 User Token (scopes: `tweet.read`, `tweet.write`, `users.read`)
```bash
curl -X POST "https://api.x.com/2/users/123456789/retweets" \
  -H "Authorization: Bearer $USER_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"tweet_id": "1346889436626259968"}'
```
Response: `{"data": {"retweeted": true}}`

**DELETE /2/users/:id/retweets/:tweet_id** — Undo Retweet
Response: `{"data": {"retweeted": false}}`

**GET /2/tweets/:id/retweeted_by** — Users Who Retweeted
Auth: Bearer or User Token. Params: `max_results` (1-100), `pagination_token`, `user.fields`

**GET /2/tweets/:id/retweets** — Get Reposts of a Tweet
Auth: Bearer or User Token. Supports tweet fields and expansions.

**GET /2/users/reposts_of_me** — Reposts of Authenticated User's Posts
Auth: OAuth 2.0 User Token

### Bookmarks

**GET /2/users/:id/bookmarks** — Get Bookmarks
Auth: OAuth 2.0 User Token (scopes: `bookmark.read`, `tweet.read`, `users.read`)
Params: `max_results` (1-100), `pagination_token`, standard tweet/expansion fields

**POST /2/users/:id/bookmarks** — Bookmark a Tweet
Auth: OAuth 2.0 User Token (scopes: `bookmark.write`, `tweet.read`, `users.read`)
```json
{"tweet_id": "1346889436626259968"}
```
Response: `{"data": {"bookmarked": true}}`

**DELETE /2/users/:id/bookmarks/:tweet_id** — Remove Bookmark
Response: `{"data": {"bookmarked": false}}`

### Quote Tweets

**GET /2/tweets/:id/quote_tweets** — Get Quote Tweets
Auth: Bearer Token or OAuth 2.0 User Token
Params: `max_results` (10-100), `pagination_token`, standard tweet/user fields

---

## 7. Tweets — Filtered Stream

Real-time streaming of tweets matching filter rules.

### GET /2/tweets/search/stream — Connect to Stream

**URL**: `https://api.x.com/2/tweets/search/stream`
**Auth**: Bearer Token
**Access**: Pay-per-use and Enterprise

Opens a persistent HTTP connection that delivers matching tweets in real-time.

| Param | Type | Description |
|-------|------|-------------|
| `backfill_minutes` | integer | 0-5, replay missed tweets (Enterprise) |

Plus standard tweet/expansion/user/media/place/poll field parameters.

```bash
curl "https://api.x.com/2/tweets/search/stream\
?tweet.fields=created_at,author_id,public_metrics\
&expansions=author_id,attachments.media_keys\
&user.fields=username,profile_image_url" \
  -H "Authorization: Bearer $BEARER_TOKEN" \
  --no-buffer
```

**Behavior:**
- Persistent HTTP connection with streaming JSON
- Keep-alive signals (blank lines) every ~20 seconds
- ~6-7 seconds P99 delivery latency
- Reconnect with exponential backoff on disconnect
- Each tweet includes `matching_rules` array

### POST /2/tweets/search/stream/rules — Add/Delete Rules

**URL**: `https://api.x.com/2/tweets/search/stream/rules`
**Auth**: Bearer Token

**Add Rules:**
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

**Delete Rules:**
```json
{"delete": {"ids": ["1165037377523306497", "1165037377523306498"]}}
```

### GET /2/tweets/search/stream/rules — List Active Rules

**Rule Limits by Tier:**

| Tier | Max Rules | Max Query Length |
|------|-----------|-----------------|
| Pay-per-use | 1,000 | 1,024 chars |
| Enterprise | 25,000+ | 2,048 chars |

Rules use the same operators as Search (see Section 3).

---

## 8. Tweets — Hide Replies

### PUT /2/tweets/:tweet_id/hidden — Hide/Unhide Reply

**URL**: `https://api.x.com/2/tweets/:tweet_id/hidden`
**Auth**: OAuth 2.0 User Token (PKCE)

```bash
curl -X PUT "https://api.x.com/2/tweets/1346889436626259968/hidden" \
  -H "Authorization: Bearer $USER_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"hidden": true}'
```

Response: `{"data": {"hidden": true}}`

Notes: Can only hide replies to tweets you authored. Hidden replies are still accessible but require an extra click.

---

## 9. Users

### User Lookup

**GET /2/users/:id** — Single User by ID
**GET /2/users?ids=...** — Multiple Users by IDs (max 100)
**GET /2/users/by/username/:username** — Single User by Username
**GET /2/users/by?usernames=...** — Multiple Users by Usernames (max 100)
**GET /2/users/me** — Authenticated User (OAuth 2.0 User Token)

**Auth**: Bearer Token, OAuth 2.0 User Token, or OAuth 1.0a

**User Fields:** `id`, `name`, `username`, `created_at`, `description`, `entities`, `location`, `profile_image_url`, `profile_banner_url`, `protected`, `public_metrics`, `verified`, `verified_type`, `url`, `subscription_type`, `connection_status`

**Expansions:** `pinned_tweet_id`, `most_recent_tweet_id`, `affiliation.user_id`

```bash
curl "https://api.x.com/2/users/2244994945\
?user.fields=created_at,description,public_metrics,profile_image_url,verified" \
  -H "Authorization: Bearer $BEARER_TOKEN"
```

**Rate Limits:** App: 300/15min | User: 900/15min

### Follows

**GET /2/users/:id/followers** — Get Followers
**GET /2/users/:id/following** — Get Following
Auth: Bearer Token, OAuth 2.0 User Token. Params: `max_results` (1-1,000), `pagination_token`

**POST /2/users/:id/following** — Follow User
Auth: OAuth 2.0 User Token (scopes: `follows.write`, `tweet.read`, `users.read`)
```json
{"target_user_id": "2244994945"}
```
Response: `{"data": {"following": true, "pending_follow": false}}`

**DELETE /2/users/:source_user_id/following/:target_user_id** — Unfollow
Response: `{"data": {"following": false}}`

**Rate Limits:** 15/15min for read, 50/15min for write

### Blocks

**GET /2/users/:id/blocking** — Get Blocked Users (Pay-per-use+)
**POST /2/users/:id/blocking** — Block User (Enterprise only)
**DELETE /2/users/:source_user_id/blocking/:target_user_id** — Unblock (Enterprise only)

### Mutes

**GET /2/users/:id/muting** — Get Muted Users
Params: `max_results` (1-1,000), `pagination_token`, `user.fields`

**POST /2/users/:id/muting** — Mute User
```json
{"target_user_id": "9876543210"}
```
Response: `{"data": {"muting": true}}`

**DELETE /2/users/:source_user_id/muting/:target_user_id** — Unmute

---

## 10. Spaces

### GET /2/spaces — Multiple Spaces by IDs

**URL**: `https://api.x.com/2/spaces`
**Auth**: Bearer Token, OAuth 2.0 User Token

| Param | Type | Description |
|-------|------|-------------|
| `ids` | string | Comma-separated Space IDs (1-100) |
| `space.fields` | string | `created_at`, `creator_id`, `ended_at`, `host_ids`, `id`, `invited_user_ids`, `is_ticketed`, `lang`, `participant_count`, `scheduled_start`, `speaker_ids`, `started_at`, `state`, `subscriber_count`, `title`, `topic_ids`, `updated_at` |
| `expansions` | string | `creator_id`, `host_ids`, `invited_user_ids`, `speaker_ids`, `topic_ids` |
| `user.fields` | string | Standard user fields |
| `topic.fields` | string | `description`, `id`, `name` |

### GET /2/spaces/:id — Single Space by ID

### GET /2/spaces/by/creator_ids — Spaces by Creator IDs

Param: `user_ids` (comma-separated, max 100)

### GET /2/spaces/:id/buyers — Ticket Purchasers

Auth: OAuth 2.0 User Token. Returns users who purchased a ticket.

### GET /2/spaces/search — Search Spaces

**URL**: `https://api.x.com/2/spaces/search`
**Auth**: Bearer Token

| Param | Type | Description |
|-------|------|-------------|
| `query` | string | Keyword search term |
| `state` | string | `live`, `scheduled`, `all` (default: `all`) |
| `max_results` | integer | 1-100 (default: 100) |

**Rate Limits:** 300/15min for all Space endpoints

---

## 11. Direct Messages

**Data Window**: Events from up to **30 days ago** are available.

### DM Lookup

**GET /2/dm_events** — All DM Events
**GET /2/dm_conversations/with/:participant_id/dm_events** — 1-to-1 DMs
**GET /2/dm_conversations/:dm_conversation_id/dm_events** — Conversation DMs

**Auth**: OAuth 2.0 User Token (scopes: `dm.read`, `tweet.read`, `users.read`)

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `max_results` | integer | 100 | 1-100 |
| `pagination_token` | string | — | Base32, min 16 chars |
| `event_types` | array | all | `MessageCreate`, `ParticipantsJoin`, `ParticipantsLeave` |
| `dm_event.fields` | string | — | `attachments`, `created_at`, `dm_conversation_id`, `entities`, `event_type`, `id`, `participant_ids`, `referenced_tweets`, `sender_id`, `text` |
| `expansions` | string | — | `attachments.media_keys`, `participant_ids`, `referenced_tweets.id`, `sender_id` |

### DM Management

**POST /2/dm_conversations** — Create New Group Conversation
Auth: OAuth 2.0 User Token (scopes: `dm.write`, `dm.read`)
```json
{
  "conversation_type": "Group",
  "participant_ids": ["2244994945", "6253282"],
  "message": {"text": "Welcome to the group!"}
}
```

**POST /2/dm_conversations/with/:participant_id/messages** — Send 1-to-1 DM
```json
{"text": "Hello!", "attachments": [{"media_id": "1455952740635586573"}]}
```

**POST /2/dm_conversations/:dm_conversation_id/messages** — Send to Existing Conversation

**DELETE /2/dm_events/:id** — Delete a DM Event
Response: `{"data": {"deleted": true}}`

**Rate Limits:** Read: 300/15min per user | Write: 200/24hrs per user

---

## 12. Lists

### List Management

**POST /2/lists** — Create List
Auth: OAuth 2.0 User Token (scopes: `list.read`, `list.write`, `tweet.read`, `users.read`)
```json
{"name": "Tech News", "description": "Top tech accounts", "private": false}
```
Name: 1-25 chars. Description: 0-100 chars.

**PUT /2/lists/:id** — Update List
**DELETE /2/lists/:id** — Delete List

### List Lookup

**GET /2/lists/:id** — Get List by ID
Auth: Bearer Token, OAuth 2.0 User Token
Fields: `created_at`, `description`, `follower_count`, `member_count`, `owner_id`, `private`

**GET /2/users/:id/owned_lists** — User's Lists
Params: `max_results` (1-100), `pagination_token`

### List Members

**GET /2/lists/:id/members** — Get Members
**POST /2/lists/:id/members** — Add Member: `{"user_id": "2244994945"}`
**DELETE /2/lists/:id/members/:user_id** — Remove Member

### List Followers

**GET /2/lists/:id/followers** — Get Followers
**POST /2/users/:id/followed_lists** — Follow a List: `{"list_id": "..."}`
**DELETE /2/users/:id/followed_lists/:list_id** — Unfollow List

### List Tweets

**GET /2/lists/:id/tweets** — Get Tweets from a List
Params: `max_results` (1-100), standard tweet/expansion fields

### List Memberships & Pinning

**GET /2/users/:id/list_memberships** — Lists User Belongs To
**POST /2/users/:id/pinned_lists** — Pin a List
**DELETE /2/users/:id/pinned_lists/:list_id** — Unpin
**GET /2/users/:id/pinned_lists** — Get Pinned Lists

**Rate Limits:** Read: 75-900/15min | Write: 300/15min

---

## 13. Media Upload

### Simple Upload

**POST /2/media/upload** — Upload Media
**Auth**: OAuth 2.0 User Token (scope: `media.write`) or OAuth 1.0a
**Content-Type**: `application/json` or `multipart/form-data`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `media` | binary | Yes | File to upload |
| `media_category` | string | Yes | `tweet_image`, `dm_image`, `subtitles` |
| `media_type` | string | No | MIME type |
| `additional_owners` | array | No | Co-owner user IDs |

**Supported Image Types:** `image/jpeg`, `image/png`, `image/bmp`, `image/webp`, `image/pjpeg`, `image/tiff`

### Chunked Upload (Large Files)

**Step 1: POST /2/media/upload/initialize**
```json
{"media_type": "video/mp4", "total_bytes": 5242880, "media_category": "amplify_video"}
```

| Field | Type | Description |
|-------|------|-------------|
| `media_type` | string | MIME type |
| `total_bytes` | integer | File size in bytes (max ~17 GB) |
| `media_category` | string | `amplify_video`, `tweet_video`, `tweet_image`, `tweet_gif`, `dm_video`, `dm_image`, `dm_gif`, `subtitles` |

**Supported Video Types:** `video/mp4`, `video/webm`, `video/mp2t`, `video/quicktime`
**Supported Subtitle Types:** `text/srt`, `text/vtt`
**Supported 3D Model Types:** `model/gltf-binary`, `model/usdz+zip`

**Step 2: POST /2/media/upload/append**
Upload in chunks (recommended 5 MB each). Params: `media_id`, `segment_index`, `media` (binary)

**Step 3: POST /2/media/upload/finalize**
```json
{"media_id": "1455952740635586573"}
```

### Processing Status

**GET /2/media/upload/status?media_id=...**

States: `pending` → `in_progress` → `succeeded` or `failed`

### Media Size Limits

| Type | Max Size |
|------|----------|
| Images (simple upload) | 5 MB |
| GIFs | 15 MB |
| Video (chunked, tweet) | 512 MB |
| Video (chunked, amplify) | ~17 GB |
| Subtitles | 1 MB |

### Usage: Attach Media to Tweet
```bash
# 1. Upload media
MEDIA_ID=$(curl -X POST "https://api.x.com/2/media/upload" \
  -H "Authorization: Bearer $USER_ACCESS_TOKEN" \
  -F "media=@photo.jpg" \
  -F "media_category=tweet_image" | jq -r '.data.id')

# 2. Create tweet with media
curl -X POST "https://api.x.com/2/tweets" \
  -H "Authorization: Bearer $USER_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"text\": \"Check this out!\", \"media\": {\"media_ids\": [\"$MEDIA_ID\"]}}"
```

**Rate Limits:** 415/15min per user for all upload endpoints

---

## 14. Trends

### GET /2/trends/by/woeid/:id — Trends by Location

**URL**: `https://api.x.com/2/trends/by/woeid/:id`
**Auth**: Bearer Token

**Common WOEID Values:**

| Location | WOEID |
|----------|-------|
| Worldwide | 1 |
| United States | 23424977 |
| United Kingdom | 23424975 |
| Japan | 23424856 |
| Canada | 23424775 |
| Australia | 23424748 |
| Germany | 23424829 |
| France | 23424819 |
| India | 23424848 |
| Brazil | 23424768 |
| New York | 2459115 |
| Los Angeles | 2442047 |
| London | 44418 |
| Tokyo | 1118370 |
| San Francisco | 2487956 |
| Chicago | 2379574 |

```bash
curl "https://api.x.com/2/trends/by/woeid/1" \
  -H "Authorization: Bearer $BEARER_TOKEN"
```

**Response:**
```json
{
  "data": [
    {"trend_name": "#AI", "tweet_count": 250000},
    {"trend_name": "Breaking News", "tweet_count": 180000},
    {"trend_name": "#Bitcoin", "tweet_count": 95000}
  ]
}
```

### GET /2/users/:id/trends — Personalized Trends (Enterprise only)

Auth: OAuth 2.0 User Token. Returns trends personalized to the user's interests.

**Rate Limits:** 75/15min

---

## 15. Compliance

Enterprise-only endpoints for keeping local data stores in sync.

### Batch Compliance

**POST /2/compliance/jobs** — Create Job
```json
{"type": "tweets", "name": "my-compliance-job"}
```
Fields: `type` (tweets/users), `name`, `resumable` (boolean)

**GET /2/compliance/jobs** — List Jobs
Params: `type` (tweets/users), `status` (created/in_progress/complete/expired/failed)

**GET /2/compliance/jobs/:id** — Get Job Status

### Compliance Streams (Enterprise)

**GET /2/tweets/compliance/stream** — Tweet Compliance Stream
**GET /2/users/compliance/stream** — User Compliance Stream
**GET /2/likes/compliance/stream** — Likes Compliance Stream

All require Bearer Token and Enterprise access.

### Event Types

| Event | Description |
|-------|-------------|
| `tweet_delete` | Tweet was deleted by author |
| `tweet_withheld` | Tweet withheld in specific countries |
| `tweet_edit` | Tweet was edited |
| `user_delete` | User account deleted |
| `user_suspend` | User account suspended |
| `user_protect` | User switched to protected |
| `user_unprotect` | User switched to public |
| `user_withheld` | User withheld in specific countries |
| `scrub_geo` | User removed geo data |
| `like_delete` | Like was removed |

---

## 16. Data Dictionary

### Post (Tweet) Object

**Default fields** (always returned): `id`, `text`, `edit_history_tweet_ids`

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique tweet identifier |
| `text` | string | UTF-8 tweet content |
| `author_id` | string | User ID of author |
| `created_at` | ISO 8601 | Creation timestamp |
| `conversation_id` | string | Root tweet ID of thread |
| `in_reply_to_user_id` | string | User being replied to |
| `lang` | string | BCP 47 language code |
| `source` | string | App/client used to post |
| `reply_settings` | string | Who can reply |
| `referenced_tweets` | array | Replied-to, quoted, retweeted |
| `attachments` | object | `media_keys[]`, `poll_ids[]` |
| `entities` | object | Parsed hashtags, URLs, mentions, cashtags |
| `context_annotations` | array | Domain and entity annotations |
| `public_metrics` | object | See below |
| `organic_metrics` | object | Non-promoted metrics (requires auth) |
| `promoted_metrics` | object | Promoted tweet metrics (requires auth) |
| `non_public_metrics` | object | Impressions, clicks (requires auth) |
| `geo` | object | `place_id`, coordinates |
| `withheld` | object | Withholding info by country |
| `edit_controls` | object | Edit window, remaining edits |
| `note_tweet` | object | Full text for posts >280 chars |

**Public Metrics Object:**
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

**Entities Object:**
```json
{
  "hashtags": [{"start": 0, "end": 3, "tag": "AI"}],
  "urls": [{"start": 10, "end": 33, "url": "https://t.co/...", "expanded_url": "https://example.com", "display_url": "example.com", "title": "Page Title", "description": "..."}],
  "mentions": [{"start": 5, "end": 15, "username": "XDevelopers", "id": "2244994945"}],
  "cashtags": [{"start": 0, "end": 5, "tag": "TSLA"}]
}
```

### User Object

**Default fields**: `id`, `name`, `username`

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique user identifier |
| `name` | string | Display name |
| `username` | string | @handle (without @) |
| `created_at` | ISO 8601 | Account creation date |
| `description` | string | Bio text |
| `location` | string | User-defined location |
| `profile_image_url` | string | Profile photo URL |
| `profile_banner_url` | string | Banner image URL |
| `protected` | boolean | Private account |
| `public_metrics` | object | `followers_count`, `following_count`, `tweet_count`, `listed_count` |
| `verified` | boolean | Verified account |
| `verified_type` | string | `blue`, `business`, `government` |
| `url` | string | User's website |
| `pinned_tweet_id` | string | Pinned tweet ID (expandable) |
| `subscription_type` | string | Premium subscription level |
| `connection_status` | array | `following`, `followed_by`, `muting`, `blocking` |

**Profile Image URL Sizes:**
`_normal` (48x48), `_bigger` (73x73), `_400x400` (400x400), (no suffix) = Original

### Media Object

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

**Media Variants:**
```json
{
  "variants": [
    {"bit_rate": 2176000, "content_type": "video/mp4", "url": "https://video.twimg.com/..."},
    {"bit_rate": 832000, "content_type": "video/mp4", "url": "https://video.twimg.com/..."},
    {"content_type": "application/x-mpegURL", "url": "https://video.twimg.com/..."}
  ]
}
```

### Space Object

**Default fields**: `id`, `state`

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Space identifier |
| `state` | string | `live`, `scheduled`, `ended` |
| `title` | string | Space title |
| `host_ids` | array | Host user IDs |
| `speaker_ids` | array | Speaker user IDs |
| `creator_id` | string | Creator user ID |
| `participant_count` | integer | Active participants |
| `is_ticketed` | boolean | Paid access |

### List Object

**Default fields**: `id`, `name`

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | List identifier |
| `name` | string | List name |
| `description` | string | List description |
| `member_count` | integer | Number of members |
| `follower_count` | integer | Number of followers |
| `owner_id` | string | Creator user ID |
| `private` | boolean | Private list |

### Poll Object

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Poll identifier |
| `options` | array | `{position, label, votes}` |
| `duration_minutes` | integer | Poll duration |
| `end_datetime` | ISO 8601 | Poll closing time |
| `voting_status` | string | `open` or `closed` |

### Place Object

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Place identifier |
| `full_name` | string | Full location name |
| `country` | string | Country name |
| `country_code` | string | ISO alpha-2 |
| `place_type` | string | `city`, `admin`, `country`, `neighborhood`, `poi` |
| `geo` | object | GeoJSON bounding box |

### Expansions Reference

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

---

## 17. Rate Limits

All rate limits are per **15-minute window** unless noted otherwise.

### Response Headers

```
x-rate-limit-limit: 900
x-rate-limit-remaining: 899
x-rate-limit-reset: 1609459200
```

When rate limited, the API returns **HTTP 429**. Wait until `x-rate-limit-reset` (Unix epoch) before retrying.

### Tweets Endpoints

| Endpoint | Per App /15min | Per User /15min |
|----------|---------------|-----------------|
| `GET /2/tweets` (lookup) | 3,500 | 5,000 |
| `GET /2/tweets/:id` | 3,500 | 5,000 |
| `POST /2/tweets` (create) | 10,000 /24hrs | 100 /15min |
| `DELETE /2/tweets/:id` | — | 50 |
| `GET /2/tweets/search/recent` | 450 | 180 |
| `GET /2/tweets/search/all` | 300 | 1 |
| `GET /2/tweets/search/stream` | 50 (connects) | — |
| `GET /2/tweets/:id/quote_tweets` | 75 | 75 |
| `GET /2/tweets/:id/retweeted_by` | 75 | 75 |
| `GET /2/tweets/:id/retweets` | 75 | 75 |
| `GET /2/tweets/:id/liking_users` | 75 | 75 |
| `PUT /2/tweets/:id/hidden` | — | 50 |

### Users Endpoints

| Endpoint | Per App /15min | Per User /15min |
|----------|---------------|-----------------|
| `GET /2/users/:id` | 300 | 900 |
| `GET /2/users` (by IDs) | 300 | 900 |
| `GET /2/users/by/username/:username` | 300 | 900 |
| `GET /2/users/by` (by usernames) | 300 | 900 |
| `GET /2/users/me` | — | 75 |
| `GET /2/users/:id/followers` | 15 | 15 |
| `GET /2/users/:id/following` | 15 | 15 |
| `POST /2/users/:id/following` | — | 50 |
| `DELETE /2/users/:id/following/:id` | — | 50 |
| `GET /2/users/:id/blocking` | — | 15 |
| `POST /2/users/:id/blocking` | — | 50 |
| `GET /2/users/:id/muting` | — | 15 |
| `POST /2/users/:id/muting` | — | 50 |

### Timelines

| Endpoint | Per App /15min | Per User /15min |
|----------|---------------|-----------------|
| `GET /2/users/:id/tweets` | 1,500 | 900 |
| `GET /2/users/:id/mentions` | 450 | 180 |
| `GET /2/users/:id/timelines/reverse_chronological` | — | 180 |

### Engagement

| Endpoint | Per App /15min | Per User /15min |
|----------|---------------|-----------------|
| `POST /2/users/:id/likes` | — | 200 /24hrs |
| `DELETE /2/users/:id/likes/:id` | — | 50 |
| `GET /2/users/:id/liked_tweets` | 75 | 75 |
| `POST /2/users/:id/retweets` | — | 50 |
| `DELETE /2/users/:id/retweets/:id` | — | 50 |
| `GET /2/users/:id/bookmarks` | — | 180 |
| `POST /2/users/:id/bookmarks` | — | 50 |
| `DELETE /2/users/:id/bookmarks/:id` | — | 50 |

### Direct Messages

| Endpoint | Per User /15min |
|----------|-----------------|
| `GET /2/dm_events` | 300 |
| `GET /2/dm_conversations/with/:id/dm_events` | 300 |
| `GET /2/dm_conversations/:id/dm_events` | 300 |
| `POST /2/dm_conversations` | 200 /24hrs |
| `POST /2/dm_conversations/with/:id/messages` | 200 /24hrs |
| `POST /2/dm_conversations/:id/messages` | 200 /24hrs |

### Lists

| Endpoint | Per App /15min | Per User /15min |
|----------|---------------|-----------------|
| `GET /2/lists/:id` | 75 | 75 |
| `POST /2/lists` (create) | — | 300 |
| `PUT /2/lists/:id` | — | 300 |
| `DELETE /2/lists/:id` | — | 300 |
| `GET /2/lists/:id/members` | 900 | 900 |
| `POST /2/lists/:id/members` | — | 300 |
| `GET /2/lists/:id/tweets` | 900 | 900 |

### Spaces

| Endpoint | Per App /15min | Per User /15min |
|----------|---------------|-----------------|
| `GET /2/spaces` | 300 | 300 |
| `GET /2/spaces/:id` | 300 | 300 |
| `GET /2/spaces/search` | 300 | 300 |

### Trends

| Endpoint | Per App /15min | Per User /15min |
|----------|---------------|-----------------|
| `GET /2/trends/by/woeid/:id` | 75 | 75 |

### Media Upload

| Endpoint | Per User /15min |
|----------|-----------------|
| `POST /2/media/upload` | 415 |
| `POST /2/media/upload/initialize` | 415 |
| `POST /2/media/upload/append` | 415 |
| `POST /2/media/upload/finalize` | 415 |

### Monthly Post Read Cap

| Tier | Posts/month |
|------|------------|
| Free | 0 (write only) |
| Basic | 10,000 |
| Pro | 1,000,000 |
| Enterprise | Custom |

---

## 18. Access Tiers

| Tier | Cost | Post Reads/mo | Post Creates/mo | Key Limits |
|------|------|---------------|-----------------|------------|
| Free | $0 | — | 1,500 | Write-only, 1 app |
| Basic | $200/mo | 10,000 | 3,000 | 2 apps |
| Pro | $5,000/mo | 1,000,000 | 300,000 | 3 apps |
| Enterprise | Custom | Custom | Custom | Unlimited apps |

---

## Show-Build Integration Notes

For the whiteboard tweet card feature:
1. Use **Tweet Lookup** (`GET /2/tweets/:id`) to fetch tweet content, author, and media
2. Use **expansions** to get author profile image and media attachments in one call
3. Store the tweet data in the whiteboard card's metadata field
4. Use the stored data to render full-screen graphics later

**Optimal tweet fetch for rendering:**
```bash
curl "https://api.x.com/2/tweets/TWEET_ID\
?tweet.fields=created_at,author_id,public_metrics,entities,attachments,note_tweet\
&expansions=author_id,attachments.media_keys\
&user.fields=username,name,profile_image_url,verified,verified_type\
&media.fields=url,preview_image_url,type,width,height,alt_text,variants" \
  -H "Authorization: Bearer $BEARER_TOKEN"
```
