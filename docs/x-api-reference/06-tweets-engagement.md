# Tweets Engagement (Likes, Retweets, Bookmarks, Quotes)

---

## Likes

### POST /2/users/:id/likes — Like a Tweet

**URL**: `https://api.x.com/2/users/:id/likes`

**Auth**: OAuth 2.0 User Token (scopes: `like.write`, `tweet.read`, `users.read`)

```bash
curl -X POST "https://api.x.com/2/users/123456789/likes" \
  -H "Authorization: Bearer $USER_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"tweet_id": "1228393702244134912"}'
```

**Response**: `{"data": {"liked": true}}`

### DELETE /2/users/:id/likes/:tweet_id — Unlike a Tweet

**URL**: `https://api.x.com/2/users/:id/likes/:tweet_id`

**Auth**: OAuth 2.0 User Token

```bash
curl -X DELETE "https://api.x.com/2/users/123456789/likes/1228393702244134912" \
  -H "Authorization: Bearer $USER_ACCESS_TOKEN"
```

**Response**: `{"data": {"liked": false}}`

### GET /2/tweets/:id/liking_users — Users Who Liked a Tweet

**URL**: `https://api.x.com/2/tweets/:id/liking_users`

**Auth**: Bearer Token or OAuth 2.0 User Token

| Param | Type | Description |
|-------|------|-------------|
| `max_results` | integer | 1-100 |
| `pagination_token` | string | Pagination |
| `user.fields` | string | User fields |
| `expansions` | string | `pinned_tweet_id` |
| `tweet.fields` | string | Tweet fields for expansions |

### GET /2/users/:id/liked_tweets — Tweets Liked by User

**URL**: `https://api.x.com/2/users/:id/liked_tweets`

**Auth**: Bearer Token or OAuth 2.0 User Token

Same parameters as liking_users, plus standard tweet field parameters.

---

## Retweets / Reposts

### POST /2/users/:id/retweets — Retweet

**URL**: `https://api.x.com/2/users/:id/retweets`

**Auth**: OAuth 2.0 User Token (scopes: `tweet.read`, `tweet.write`, `users.read`)

```bash
curl -X POST "https://api.x.com/2/users/123456789/retweets" \
  -H "Authorization: Bearer $USER_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"tweet_id": "1346889436626259968"}'
```

**Response**: `{"data": {"retweeted": true}}`

### DELETE /2/users/:id/retweets/:tweet_id — Undo Retweet

**URL**: `https://api.x.com/2/users/:id/retweets/:tweet_id`

**Auth**: OAuth 2.0 User Token

**Response**: `{"data": {"retweeted": false}}`

### GET /2/tweets/:id/retweeted_by — Users Who Retweeted

**URL**: `https://api.x.com/2/tweets/:id/retweeted_by`

**Auth**: Bearer Token or OAuth 2.0 User Token

| Param | Type | Default | Range |
|-------|------|---------|-------|
| `max_results` | integer | 100 | 1-100 |
| `pagination_token` | string | — | — |
| `user.fields` | string | — | — |

### GET /2/tweets/:id/retweets — Get Reposts of a Tweet

**URL**: `https://api.x.com/2/tweets/:id/retweets`

**Auth**: Bearer Token, OAuth 2.0 User Token

| Param | Type | Default | Range |
|-------|------|---------|-------|
| `max_results` | integer | 100 | 1-100 |
| `pagination_token` | string | — | — |
| `tweet.fields` | string | — | Standard fields |
| `expansions` | string | — | Standard expansions |
| `user.fields` | string | — | — |
| `media.fields` | string | — | — |

### GET /2/users/reposts_of_me — Reposts of Authenticated User's Posts

**URL**: `https://api.x.com/2/users/reposts_of_me`

**Auth**: OAuth 2.0 User Token

---

## Bookmarks

### GET /2/users/:id/bookmarks — Get Bookmarks

**URL**: `https://api.x.com/2/users/:id/bookmarks`

**Auth**: OAuth 2.0 User Token (scopes: `bookmark.read`, `tweet.read`, `users.read`)

| Param | Type | Range | Description |
|-------|------|-------|-------------|
| `max_results` | integer | 1-100 | Results per page |
| `pagination_token` | string | — | Base36 pagination token |
| `tweet.fields` | string | — | Standard tweet fields |
| `expansions` | string | — | Standard expansions |
| `user.fields` | string | — | User fields |
| `media.fields` | string | — | Media fields |
| `place.fields` | string | — | Place fields |
| `poll.fields` | string | — | Poll fields |

### POST /2/users/:id/bookmarks — Bookmark a Tweet

**URL**: `https://api.x.com/2/users/:id/bookmarks`

**Auth**: OAuth 2.0 User Token (scopes: `bookmark.write`, `tweet.read`, `users.read`)

```json
{"tweet_id": "1346889436626259968"}
```

**Response**: `{"data": {"bookmarked": true}}`

### DELETE /2/users/:id/bookmarks/:tweet_id — Remove Bookmark

**URL**: `https://api.x.com/2/users/:id/bookmarks/:tweet_id`

**Auth**: OAuth 2.0 User Token

**Response**: `{"data": {"bookmarked": false}}`

---

## Quote Tweets

### GET /2/tweets/:id/quote_tweets — Get Quote Tweets

**URL**: `https://api.x.com/2/tweets/:id/quote_tweets`

**Auth**: Bearer Token or OAuth 2.0 User Token

| Param | Type | Description |
|-------|------|-------------|
| `max_results` | integer | 10-100 |
| `pagination_token` | string | Pagination |
| `tweet.fields` | string | `created_at,author_id,public_metrics` |
| `expansions` | string | `author_id` |
| `user.fields` | string | `username` |

### Example Response

```json
{
  "data": [
    {
      "id": "1503048567896723461",
      "text": "This is a great point! https://t.co/...",
      "author_id": "12345",
      "created_at": "2022-03-13T15:30:00.000Z"
    }
  ],
  "includes": {
    "users": [{"id": "12345", "username": "example_user"}]
  },
  "meta": {
    "result_count": 5
  }
}
```
